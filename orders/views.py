import json

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from django.views import generic, View
from django.views.generic.edit import FormMixin
from django.shortcuts import get_object_or_404
import logging
from django.conf import settings

from parts_providers import ProviderApiError
from .forms import OrderForm, OrderNewForm, OrderItemFormSet
from .models import Order, Manager, OrderItem


def is_manager(user):
    return user.groups.filter(name='manager').exists()


class ManagerMixin(UserPassesTestMixin):
    def get_user(self):
        return self.request.user

    def test_func(self):
        return is_manager(self.get_user())

    def get_manager(self) -> Manager:
        return Manager.objects.get(user=self.get_user())


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


class OrderItemsSearch(ManagerMixin, generic.TemplateView):
    template_name = "orders/order_items_search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = get_object_or_404(Order, pk=self.kwargs['pk'])
        context['order'] = order
        context['order_items'] = order.order_item_list.all()
        return context


items_search_logger = logging.getLogger("ItemsSearchResultView")


class ItemsSearchResult(ManagerMixin, View):
    def post(self, request):
        article_number = request.POST.get('article_number', '').strip()

        if len(article_number) == 0:
            return JsonResponse({"error": "Article number is required."}, status=400)

        service = settings.AUTO_PARTS_PROVIDERS["arm_teck"]["instance"]

        try:
            results = service.search(article_number)

            items_data = [
                {
                    "article_number": item.article_number,
                    "manufacture": item.manufacture,
                    "name": item.name,
                    "price": item.price,
                    "count": item.count,
                    "delivery_time": item.delivery_time,
                    "warehouse_location": item.warehouse_location,
                }
                for item in results
            ]
            return JsonResponse({"items": items_data})
        except ProviderApiError as ex:
            items_search_logger.error(f"Provider error for order: {ex}")
            return JsonResponse({"error": "Поставщик недоступен"}, status=502)


class AddOrderItem(ManagerMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, 400)

        article_number = data.get("article_number", "").strip()
        manufacture = data.get("manufacture", "").strip()
        name = data.get("name", "").strip()
        price = data.get("price")

        order_item = OrderItem.objects.create(
            order=order,
            article_number=article_number,
            manufacture=manufacture,
            name=name,
            price=price)

        if not article_number:
            return JsonResponse({"error": "article_number is required."}, status=400)

        return JsonResponse({
            "success": True,
            "item": {
                "id": order_item.id,
                "article_number": order_item.article_number,
                "manufacture": order_item.manufacture,
                "name": order_item.name,
                "price": str(order_item.price),
            },
        }, status=201)