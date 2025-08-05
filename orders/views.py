from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import FormMixin

from .forms import OrderForm, OrderItemFormSet
from .models import Order


def is_manager(user):
    return user.groups.filter(name='manager').exists()


class IsManagerMixin(UserPassesTestMixin):
    def test_func(self):
        return is_manager(self.request.user)


class OrderFormMixin(FormMixin):
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['formset'] = OrderItemFormSet(self.request.POST, instance=self.object)
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


class OrderCreateView(OrderFormMixin, generic.CreateView):
    def get_success_url(self):
        return reverse('edit', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create New Order'
        return context


class OrderUpdateView(OrderFormMixin, generic.UpdateView):
    def get_success_url(self):
        return reverse('edit', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Order for {self.object.client}'
        return context


class OrderListView(IsManagerMixin, generic.ListView):
    template_name = 'orders/list.html'
    model = Order
    context_object_name = 'orders'


class OrderDetailView(generic.DetailView):
    pass
