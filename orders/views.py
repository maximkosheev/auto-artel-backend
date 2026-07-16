import json
import logging
import math
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic, View
from django.views.generic.edit import FormMixin

from parts_providers import ProviderApiError
from utils.date_utils import parse_date
from .forms import OrderForm, OrderNewForm, OrderItemFormSet
from .models import Order, Manager, OrderItem


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


class OrderListView(ManagerMixin, generic.ListView):
    template_name = 'orders/list.html'
    model = Order
    context_object_name = 'orders'


class OrderFormMixin(FormMixin):
    model = Order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            formset_data = self.request.POST
            context['formset'] = OrderItemFormSet(formset_data, instance=self.object)
        else:
            context['formset'] = OrderItemFormSet(instance=self.object)

        context['is_edit'] = (hasattr(self, 'object')
                              and self.object is not None
                              and self.object.pk is not None)

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    self.object = form.save()
                    formset.instance = self.object
                    formset.save()

                    return super().form_valid(form)
            except Exception as e:
                messages.error(self.request, f'Ошибка при сохранении заказа: {str(e)}')
                return self.form_invalid(form)
        else:
            messages.error(self.request, 'Пожалуйста, исправьте ошибки')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки')
        return super().form_invalid(form)


class OrderDetailView(ManagerMixin, OrderFormMixin, generic.UpdateView):

    def get_template_names(self):
        if self.object.status == 'NEW':
            return ['orders/order_new_form.html']
        elif self.object.manager != self.get_manager():
            return ['orders/order_lock_form.html']
        else:
            return ['orders/order_form.html']

    def get_form_class(self):
        if self.object.status == 'NEW':
            return OrderNewForm
        elif self.object.manager != self.get_manager():
            return None
        else:
            return OrderForm

    def get_success_url(self):
        return reverse('orders:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Информация о заказе {self.object.client}'
        return context


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
                    "delivery_time": item.delivery_time.strftime("%Y-%m-%d %H:%M") if item.delivery_time else None,
                    "warehouse_location": item.warehouse_location,
                }
                for item in results
            ]
            return JsonResponse({"items": items_data})
        except ProviderApiError as ex:
            items_search_logger.error(f"Provider error: {ex}")
            return JsonResponse({"error": "Поставщик недоступен"}, status=502)


class OrderItemAdd(ManagerMixin, OrderStatusMixin, View):
    def get_order(self, request, *args, **kwargs):
        return get_object_or_404(Order, pk=kwargs['pk'])

    def post(self, request, pk):
        order = self.get_order(request, pk=pk)

        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, 400)

        article_number = data.get("article_number", "").strip()
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
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid count value."}, status=400)
        discount = 0
        price = calc_final_price(purchase_price, count, discount, 30)

        order_item = self.insert_or_update(
            order=order,
            article_number=article_number,
            internal_id=internal_art_id,
            manufacture=manufacture,
            name=name,
            provider=provider,
            delivery_dt=delivery_dt,
            warehouse=warehouse,
            purchase_price=purchase_price,
            count=count,
            discount=discount,
            price=price
        )

        if not article_number:
            return JsonResponse({"error": "article_number is required."}, status=400)

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
                         purchase_price, count, discount, price):

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
                discount=discount,
                price=price
            )

        return item


class OrderItemBulkRemove(ManagerMixin, OrderStatusMixin, View):
    def get_order(self, request, *args, **kwargs):
        return get_object_or_404(Order, pk=kwargs['pk'])

    def delete(self, request, pk):
        order = self.get_order(request, pk=pk)

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

        deleted_count, _ = OrderItem.objects.filter(order=order, id__in=item_ids).delete()

        return JsonResponse({"success": True, "deleted": deleted_count})


class OrderItemUpdateCount(ManagerMixin, OrderStatusMixin, View):
    def get_order(self, request, *args, **kwargs):
        return get_object_or_404(OrderItem, pk=kwargs['item_pk']).order

    def patch(self, request, item_pk):
        item = get_object_or_404(OrderItem, pk=item_pk)

        try:
            data = json.loads(request.body.decode('utf-8'))
            count = int(data.get("count"))
            if count < 1:
                return JsonResponse({"error": "Count must be at least 1."}, status=400)
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
