from django.contrib.auth.mixins import UserPassesTestMixin
from django.views import generic

from .models import Order


def is_manager(user):
    return user.groups.filter(name='manager').exists()


class IsManagerMixin(UserPassesTestMixin):
    def test_func(self):
        return is_manager(self.request.user)


class OrderListView(IsManagerMixin, generic.ListView):
    template_name = 'orders/list.html'
    model = Order
    context_object_name = 'orders'


class OrderDetailView(generic.DetailView):
    pass
