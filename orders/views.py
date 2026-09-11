import json
import logging
import math
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic, View
from django.views.generic.edit import FormMixin

from auto_artel.broker import broker
from chat.models import ChatMessage
from parts_providers import ProviderApiError
from utils.date_utils import parse_date
from .errors import BusinessError
from .forms import OrderForm, OrderNewForm
from .models import Order, Manager, OrderItem, Client
from .urls_helper import OrderLinkGenerator, InvalidOrderLinkToken

ORDER_CLIENT_STATUSES = {
    Order.ClientStatuses.CANCELED:          {'index': 0, 'can_move_next': False},
    Order.ClientStatuses.NOT_ASSIGNED:      {'index': 1, 'can_move_next': False},
    Order.ClientStatuses.ASSIGNED:          {'index': 2, 'can_move_next': False},
    Order.ClientStatuses.WAIT_APPROVAL:     {'index': 3, 'can_move_next': False},
    Order.ClientStatuses.APPROVED:          {'index': 4, 'can_move_next': False},
    Order.ClientStatuses.WAIT_PAYMENT:      {'index': 5, 'can_move_next': True},
    Order.ClientStatuses.PAID:              {'index': 6, 'can_move_next': False},
    Order.ClientStatuses.WAIT_SEND:         {'index': 7, 'can_move_next': True},
    Order.ClientStatuses.DELIVERY:          {'index': 8, 'can_move_next': True},
    Order.ClientStatuses.READY:             {'index': 9, 'can_move_next': True},
    Order.ClientStatuses.FINISHED:          {'index': 10, 'can_move_next': False},
}


def has_next_order_client_status(current_client_status):
    return (ORDER_CLIENT_STATUSES[current_client_status]['index']
            < ORDER_CLIENT_STATUSES[Order.ClientStatuses.FINISHED]['index'])


def get_order_next_client_status(client_status):
    order_next_client_status_id = ORDER_CLIENT_STATUSES[client_status]['index'] + 1
    if order_next_client_status_id > ORDER_CLIENT_STATUSES[Order.ClientStatuses.FINISHED]['index']:
        raise IndexError('Index out of range')
    for k, v in ORDER_CLIENT_STATUSES:
        if v['index'] == order_next_client_status_id:
            return k


def calc_final_price(purchase_price: Decimal, count: int, discount: int, extra: int):
    """
    @param purchase_price: цена закупки
    @param count: количество
    @param discount: скидка (0 - без скидки; 100 - бесплатно)
    @param extra: надбавка (в процентах)
    @return: итоговая стоимость
    """
    # стоимость закупки
    purchase_cost = purchase_price * count
    # наша надбавка
    extra_cost = purchase_cost * extra / 100
    # надбавка с учетом скидки
    extra_with_discount = extra_cost * (100 - discount) / 100
    # итоговая стоимость = стоимость закупки + надбавка с учетом скидки
    price_with_discount = purchase_cost + extra_with_discount
    # округляем до большего кратного 50р
    final_price = math.ceil(price_with_discount / 50) * 50
    return final_price


def is_manager(user):
    return user.groups.filter(name='manager').exists()


class ManagerMixin(UserPassesTestMixin):
    def get_user(self):
        return self.request.user

    def test_func(self):
        return is_manager(self.get_user())

    def get_manager(self) -> Manager:
        return Manager.objects.get(user=self.get_user())


class OrderStatusMixin:
    required_order_status_list = ['NEW']

    def get_order(self, request, *args, **kwargs):
        return get_object_or_404(Order, pk=kwargs['pk'])

    def dispatch(self, request, *args, **kwargs):
        self.order = self.get_order(request, *args, **kwargs)
        if self.order.status not in self.required_order_status_list:
            return JsonResponse({"error": "Заказ уже в работе"}, status=422)
        return super().dispatch(request, *args, **kwargs)


class OrderIsAvailableMixin:
    def order_is_available_for_me(self, request):
        pass

    def get_order(self, request, *args, **kwargs):
        return get_object_or_404(Order, pk=kwargs['pk'])

    def dispatch(self, request, *args, **kwargs):
        self.order = self.get_order(request, *args, **kwargs)
        if not self.order_is_available_for_me(request):
            return JsonResponse({"error": "Вы не можете работать над этим заказом"}, status=403)
        return super().dispatch(request, *args, **kwargs)


class OrderIsFree(OrderIsAvailableMixin):
    def order_is_available_for_me(self, request):
        return self.order.manager is None


class OrderIsMine(OrderIsAvailableMixin):
    def order_is_available_for_me(self, request):
        return self.order.manager and self.order.manager.user == request.user


class OrderListView(ManagerMixin, generic.ListView):
    template_name = 'orders/list.html'
    model = Order
    context_object_name = 'orders'

    SORT_FIELDS = {
        'id': 'id',
        'created': 'created',
    }
    DEFAULT_SORT = ('-created', '-id')
    PAGE_SIZE_CHOICES = (20, 50, 100, 150, 200)
    DEFAULT_PAGE_SIZE = 20

    def get_queryset(self):
        where = Q()

        try:
            client_ids = {int(client_id) for client_id in self.request.GET.getlist('client')}
        except (TypeError, ValueError):
            client_ids = set()
        if client_ids:
            where &= Q(client_id__in=client_ids)

        client_statuses = self.request.GET.getlist('client_status')
        if client_statuses:
            where &= Q(client_status__in=client_statuses)

        if self.request.GET.get('mine') == '1':
            where &= Q(manager=self.get_manager())

        return Order.objects.filter(where).select_related('client', 'manager').order_by(*self.get_ordering())

    def get_ordering(self):
        field = self.SORT_FIELDS.get(self.request.GET.get('sort'))
        if field is None:
            return self.DEFAULT_SORT

        direction = self.request.GET.get('dir')
        prefix = '-' if direction == 'desc' else ''
        return f'{prefix}{field}', f'{prefix}id'

    def get_paginate_by(self, queryset):
        try:
            page_size = int(self.request.GET.get('page_size', self.DEFAULT_PAGE_SIZE))
        except (TypeError, ValueError):
            return self.DEFAULT_PAGE_SIZE
        return page_size if page_size in self.PAGE_SIZE_CHOICES else self.DEFAULT_PAGE_SIZE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_clients'] = Client.objects.all()
        context['client_status_choices'] = Order.ClientStatuses.choices
        return context


class OrderDetailView(ManagerMixin, generic.UpdateView):
    model = Order

    def order_is_not_available_to_me(self):
        return self.object.manager is not None and self.object.manager != self.get_manager()

    def get_template_names(self):
        if self.object.manager is None:
            return ['orders/order_new_form.html']
        elif self.order_is_not_available_to_me():
            return ['orders/order_lock_form.html']
        else:
            return ['orders/order_form.html']

    def get_form_class(self):
        return OrderNewForm if self.object.status == 'NEW' else OrderForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.order_is_not_available_to_me():
            return self.render_to_response(self.get_context_data(form=None))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.order_is_not_available_to_me():
            return JsonResponse({"error": "Вы не можете работать над этим заказом"}, status=403)
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('orders:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Информация о заказе {self.object.client}'
        # Проверяем, что заказ находится не на последнем шаге
        if has_next_order_client_status(self.object.client_status):
            # Начиная с определенного шага (в данном случае WAIT_PAYMENT), последовательность шагов имеет линейный
            # характер. Т.е. мы точно знаем какой должен быть шаг в happy path, если просто укажем "перейти на следующий"
            # Фактически allow_next_status как раз определяет, пересек ли заказ эту границу или нет. Если пересек,
            # на странице должна появится кнопка, которая просто переведет заказ на следующий шаг, без дополнительных вопросов.
            context['allow_next_status'] = ORDER_CLIENT_STATUSES[self.object.client_status]['can_move_next']
            # Это как раз название этой самой кнопки перевода заказа на следующий шаг
            context['btn_next_status_title'] = get_order_next_client_status(self.object.client_status).label
        return context

    def form_valid(self, form):
        if form.is_valid():
            try:
                self.object = form.save(commit=False)

                if isinstance(form, OrderNewForm):
                    self.object.manager = self.get_manager()
                    self.object.update_status(Order.Statuses.PROCESSING)
                    self.object.update_client_status(Order.ClientStatuses.ASSIGNED)

                self.object.save()
                return FormMixin.form_valid(self, form)
            except Exception as e:
                messages.error(self.request, f'Ошибка при сохранении заказа: {str(e)}')
                return self.form_invalid(form)
        else:
            print(f"form or formset are not valid")
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки')
        return super().form_invalid(form)


class PartsSearchView(ManagerMixin, View):
    def get(self, request):
        order_id = request.GET.get('order_id')
        order = None
        order_items = []
        if order_id:
            order = get_object_or_404(Order, pk=order_id)
            order_items = order.order_item_list.all()
        return render(request, 'orders/order_items_search.html', {
            'order': order,
            'order_items': order_items,
        })


class OrderItemSearch(ManagerMixin, View):
    def get(self, request, pk):
        return redirect(reverse('orders:parts_search') + f'?order_id={pk}')


items_search_logger = logging.getLogger("ItemsSearchResultView")


class AssortmentSearchResult(ManagerMixin, View):
    def post(self, request):
        article_number = request.POST.get('article_number', '').strip()

        if len(article_number) == 0:
            return JsonResponse({"error": "Article number is required."}, status=400)

        service = settings.AUTO_PARTS_PROVIDERS["armtek"]["instance"]

        try:
            service.init()
            results = service.assortment_search(article_number)
            items_data = [
                {
                    "article_number": item.article_number,
                    "manufacture": item.manufacture,
                    "name": item.name,
                }
                for item in results
            ]
            return JsonResponse({"items": items_data})
        except ProviderApiError as ex:
            items_search_logger.error(f"Provider error for order: {ex}")
            return JsonResponse({"error": "Поставщик недоступен"}, status=502)


class ItemsFullSearchResult(ManagerMixin, View):
    def post(self, request):
        article_number = request.POST.get('article_number', '').strip()
        manufacture = request.POST.get('manufacture', '').strip()

        if not article_number:
            return JsonResponse({"error": "Article number is required."}, status=400)

        service = settings.AUTO_PARTS_PROVIDERS["armtek"]["instance"]

        try:
            service.init()
            results = service.search(article_number, manufacture)
            if manufacture:
                results = sorted(results, key=lambda r: 0 if r.manufacture == manufacture else 1)
            items_data = [
                {
                    "article_number": item.article_number,
                    "internal_art_id": item.internal_art_id,
                    "manufacture": item.manufacture,
                    "name": item.name,
                    "price": item.price,
                    "count": item.count,
                    "multiplicity": item.multiplicity,
                    "delivery_time": item.delivery_time.strftime("%Y-%m-%d %H:%M") if item.delivery_time else None,
                    "warehouse_location": item.warehouse_location,
                }
                for item in results
            ]
            return JsonResponse({"items": items_data})
        except ProviderApiError as ex:
            items_search_logger.error(f"Provider error: {ex}")
            return JsonResponse({"error": "Поставщик недоступен"}, status=502)


class OrderItemAdd(ManagerMixin, OrderIsMine, View):
    def post(self, request, pk):
        try:
            data = json.loads(request.body.decode('utf-8'))
            print(f"Adding new order item with data: {data}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, 400)

        article_number = data.get("article_number", "").strip()
        if not article_number:
            return JsonResponse({"error": "article_number is required."}, status=400)
        internal_art_id = data.get("internal_art_id", "").strip()
        manufacture = data.get("manufacture", "").strip()
        name = data.get("name", "").strip()
        provider = data.get("provider", "armtek")
        try:
            purchase_price = Decimal(str(data.get("price")))
        except (InvalidOperation, TypeError):
            return JsonResponse({"error": "Invalid price value."}, status=400)
        delivery_dt = parse_date(data.get("delivery_time"), '%Y-%m-%d %H:%M')
        warehouse = data.get("warehouse_location")
        try:
            count = max(1, int(data.get("count", 1)))
            multiplicity = max(1, int(data.get("multiplicity", 1)))
            if count % multiplicity != 0:
                raise ValueError
        except (TypeError, ValueError):
            return JsonResponse({"error": f"Необходимо указать количество кратное указанному значению"}, status=400)
        discount = 0
        price = calc_final_price(purchase_price, count, discount, 30)

        order_item = self.insert_or_update(
            order=self.order,
            article_number=article_number,
            internal_id=internal_art_id,
            manufacture=manufacture,
            name=name,
            provider=provider,
            delivery_dt=delivery_dt,
            warehouse=warehouse,
            purchase_price=purchase_price,
            count=count,
            multiplicity=multiplicity,
            discount=discount,
            price=price,
            status=OrderItem.Statuses.DEFAULT
        )

        return JsonResponse({
            "success": True,
            "item": {
                "id": order_item.id,
                "article_number": order_item.article_number,
                "manufacture": order_item.manufacture,
                "name": order_item.name,
                "count": order_item.count,
                "price": str(order_item.price),
            },
        }, status=201)

    def insert_or_update(self, order, article_number, internal_id, manufacture, name, provider, delivery_dt, warehouse,
                         purchase_price, count, multiplicity, discount, price, status):

        item = OrderItem.objects.filter(
            order=order,
            article_number=article_number,
            internal_id=internal_id
        ).first()

        if item:
            item.count += count
            item.price += price
            item.save()
        else:
            item = OrderItem.objects.create(
                order=order,
                article_number=article_number,
                internal_id=internal_id,
                manufacture=manufacture,
                name=name,
                provider=provider,
                delivery_dt=delivery_dt,
                warehouse=warehouse,
                purchase_price=purchase_price,
                count=count,
                multiplicity=multiplicity,
                discount=discount,
                price=price,
                status=status
            )

        return item


class OrderItemBulkRemove(ManagerMixin, OrderIsMine, View):
    STATUSES_ALLOWED_TO_REMOVE = (OrderItem.Statuses.DEFAULT, OrderItem.Statuses.REJECTED)

    def delete(self, request, pk):
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        item_ids = data.get("item_ids")
        if not isinstance(item_ids, list) or not item_ids:
            return JsonResponse({"error": "item_ids is required."}, status=400)

        try:
            item_ids = [int(item_id) for item_id in item_ids]
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid item id."}, status=400)

        deleted_count, _ = OrderItem.objects.filter(order=self.order,
                                                    id__in=item_ids,
                                                    status__in=self.STATUSES_ALLOWED_TO_REMOVE).delete()

        return JsonResponse({"success": True, "deleted": deleted_count})


class OrderItemUpdateCount(ManagerMixin, OrderIsMine, View):
    def patch(self, request, pk, item_pk):
        item = get_object_or_404(OrderItem, pk=item_pk, order_id=pk)

        if item.status != OrderItem.Statuses.DEFAULT:
            return JsonResponse({"error": "Позиция находится на согласовании, поэтому не может быть изменена"},
                                status=422)
        try:
            data = json.loads(request.body.decode('utf-8'))
            count = int(data.get("count"))
            if count < 1:
                return JsonResponse({"error": f"Количество должно быть не меньше 1"}, status=400)
            elif count % item.multiplicity != 0:
                return JsonResponse({"error": f"Количество должно быть кратно {item.multiplicity}"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid count value."}, status=400)

        item.price = calc_final_price(item.purchase_price, count, item.discount, 30)
        item.count = count

        item.save(update_fields=["count", "price"])

        return JsonResponse({
            "success": True,
            "item": {
                "id": item.id,
                "count": item.count,
                "price": str(item.price),
            },
        })


class OrderItemsAgreementConfirmView(ManagerMixin, OrderIsMine, View):
    """
    Страница подтверждения оправки позиций заказа на согласование клиенту.
    Станица предназначена для менеджера, работающего над заказом.
    :param pk: Идентификатор заказа.
    Список идентификаторов позиций, которые отправляются на согласование, передаются через query-parameter items_ids
    """

    def get(self, request, pk):
        item_ids_param = request.GET.get('item_ids', '')
        try:
            item_ids = [int(item_id) for item_id in item_ids_param.split(',') if item_id]
        except ValueError:
            item_ids = []

        if not item_ids:
            messages.error(request, 'Не выбрано ни одной позиции для согласования')
            return redirect(reverse('orders:detail', kwargs={'pk': pk}))

        selected_items = list(OrderItem.objects.filter(order=self.order, id__in=item_ids))

        if not selected_items:
            messages.error(request, 'Выбранные позиции не найдены в заказе')
            return redirect(reverse('orders:detail', kwargs={'pk': pk}))

        total_cost = sum((item.price for item in selected_items), Decimal('0'))

        return render(request, 'orders/order_agreement_confirm.html', {
            'order': self.order,
            'selected_items': selected_items,
            'total_count': len(selected_items),
            'total_cost': total_cost,
        })


class OrderItemBulkAgreement(ManagerMixin, OrderIsMine, View):
    """
    Отправка позиций заказа на согласование клиенту
    """

    def post(self, request, pk):
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        item_ids = data.get("item_ids")
        if not isinstance(item_ids, list) or not item_ids:
            return JsonResponse({"error": "item_ids is required."}, status=400)

        try:
            item_ids = list({int(item_id) for item_id in item_ids})
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid item id."}, status=400)

        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(pk=pk)

                # check if all early approved items are in current list for approve.
                approved_item_ids = order.order_item_list.filter(status=OrderItem.Statuses.APPROVED).values_list('id', flat=True)
                if not all(item_id in item_ids for item_id in approved_item_ids):
                    raise BusinessError("В заказе есть позиции, которые клиент ранее согласовал, но они не включены в данный список. "
                                        "Добавьте все согласованные ранее позиции и повторите попытку")

                # Позициям, которые ранее не участвовали в согласовании (статус DEFAULT) или были отклонены (REJECTED),
                # изменяем статус на AGREEMENT. На форме у клиента они будут unchecked
                # Позициям, которые ранее уже были согласованы, ничего не меняем. На форме у клиента они будут checked.
                updated_count = OrderItem.objects.filter(order=order, id__in=item_ids, status__in=[OrderItem.Statuses.DEFAULT, OrderItem.Statuses.REJECTED]).update(status=OrderItem.Statuses.AGREEMENT)

                order.update_client_status(Order.ClientStatuses.WAIT_APPROVAL, commit=True)
                ChatMessage.objects.create(
                    client=order.client,
                    manager=self.get_manager(),
                    text=f'Заказ #{order.id} отправлен на согласование. Ссылка на заказ: {settings.BASE_URL}{reverse("orders:detail", kwargs={"pk": self.order.id})}'
                )
        except BusinessError as ex:
            return JsonResponse({"error": f"{ex}"}, status=422)
        except Exception as ex:
            return JsonResponse({"error": f"{ex}"}, status=500)

        due_to = datetime.now(tz=timezone.utc) + timedelta(hours=3)
        agreement_link = OrderLinkGenerator.build_url(
            f"{settings.BASE_URL}{reverse('orders:client_approve')}",
            order.client,
            order,
            due_to)
        broker.send_order_agreement_notification(
            order.client,
            order,
            agreement_link,
            due_to.astimezone(settings.MSK_ZONE))

        return JsonResponse({"success": True, "updated": updated_count})


class ForbiddenException(Exception):
    pass


class UnexpectedStatusException(Exception):
    pass


class OrderClientApproveView(generic.FormView):

    def get(self, request, *args, **kwargs):
        try:
            token = request.GET.get('hash')
            order = self.get_order(token)
        except InvalidOrderLinkToken as ex:
            return render(request, "orders/errors/expired.html", {}, status=400)
        except ForbiddenException as ex:
            return render(request, "orders/errors/forbidden.html", {}, status=403)
        except UnexpectedStatusException as ex:
            return render(request, "orders/errors/unexpected_status.html", {}, status=422)

        items = list(OrderItem.objects.filter(order=order, status__in=[OrderItem.Statuses.AGREEMENT, OrderItem.Statuses.APPROVED]))
        total_cost = sum((item.price for item in items), Decimal('0'))
        return render(request, "orders/order_client_approve_form.html", {
            'order': order,
            'items': items,
            'total_count': len(items),
            'total_cost': total_cost,
            'hash': token
        })

    def post(self, request, *args, **kwargs):
        try:
            order = self.get_order(request.POST.get('hash'))
        except InvalidOrderLinkToken as ex:
            return render(request, "orders/errors/expired.html", {}, status=400)
        except ForbiddenException as ex:
            return render(request, "orders/errors/forbidden.html", {}, status=403)
        except UnexpectedStatusException as ex:
            return render(request, "orders/errors/unexpected_status.html", {}, status=422)

        def parse_ids(field_name):
            ids = set()
            for raw_id in request.POST.getlist(field_name):
                try:
                    ids.add(int(raw_id))
                except (TypeError, ValueError):
                    continue
            return ids

        # known_item_ids carries every item id that was actually rendered on the
        # approval form (checked or not) so we know exactly which items belong to
        # this approval request, without needing to persist that fact anywhere.
        # item_ids carries only the ones the client left checked.
        known_ids = parse_ids('known_item_ids')
        selected_ids = parse_ids('item_ids') & known_ids

        with transaction.atomic():
            # Scoped to this order so a tampered known_item_ids can't reach items
            # belonging to a different client's order; deliberately not filtered
            # by status, since an item may be sent for approval regardless of its
            # current status.
            last_request_items = list(
                OrderItem.objects.select_for_update().filter(order=order, id__in=known_ids)
            )
            approved_ids = [item.id for item in last_request_items if item.id in selected_ids]
            rejected_ids = [item.id for item in last_request_items if item.id not in selected_ids]

            if approved_ids:
                OrderItem.objects.filter(id__in=approved_ids).update(status=OrderItem.Statuses.APPROVED)
            if rejected_ids:
                OrderItem.objects.filter(id__in=rejected_ids).update(status=OrderItem.Statuses.REJECTED)

            # If client have approved whole list, and order contains at least one APPROVED item - change Order status to the APPROVED
            if len(rejected_ids) == 0 and order.order_item_list.filter(status=OrderItem.Statuses.APPROVED).exists():
                order.update_client_status(Order.ClientStatuses.APPROVED, commit=True)

        if len(approved_ids) > 0 and len(rejected_ids) > 0:
            return render(request, "orders/partial_approved_by_client.html", context={}, status=200)
        elif len(approved_ids) > 0:
            return render(request, "orders/successfully_approved_by_client.html", context={}, status=200)
        else:
            return render(request, "orders/empty_approved_by_client.html", context={}, status=200)

    def get_order(self, token):
        order_claim = OrderLinkGenerator.verify_for_order(token)
        order = get_object_or_404(Order, pk=order_claim.order_id)
        if order.client.id != order_claim.client_id:
            raise ForbiddenException()
        if order.client_status != Order.ClientStatuses.WAIT_APPROVAL:
            raise UnexpectedStatusException()
        return order


class OrderInvoiceView(ManagerMixin, OrderIsMine, View):
    def post(self, request, pk):
        invoice = request.POST.get('invoice_link', '').strip()
        if not invoice:
            messages.error(request, "Не указан счет на оплату")
            return redirect(reverse('orders:detail', kwargs={'pk': pk}))

        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(pk=pk)
                order.update_client_status(Order.ClientStatuses.WAIT_PAYMENT)
                order.invoice_link = invoice
                order.save()
                ChatMessage.objects.create(
                    client=order.client,
                    manager=self.get_manager(),
                    text=f'Заказ #{order.id} выставлен счет на оплату.'
                )
            broker.send_order_invoice_notification(order.client, order, invoice)
            messages.info(request, "Счет на оплату отправлен клиенту")
        except Exception as ex:
            messages.error(request, "Возникла непредвиденная ошибка. Обратитесь к администратору")

        return redirect(reverse('orders:detail', kwargs={'pk': pk}))


class OrderNextStatus(ManagerMixin, OrderIsMine, View):
    def post(self, request, pk):
        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(pk=pk)
                if has_next_order_client_status(order.client_status):
                    order.update_client_status(get_order_next_client_status(order.client_status), commit=True)
                messages.info(request, "Статус заказа обновлен")
        except Exception as ex:
            messages.error(request, "Возникла непредвиденная ошибка. Обратитесь к администратору")

        return redirect(reverse('orders:detail', kwargs={'pk': pk}))
