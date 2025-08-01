from django.shortcuts import render
from django.views import generic

from .models import Order


class OrderListView(generic.ListView):
    template_name = 'orders/list.html'
    model = Order
    context_object_name = 'orders'


class OrderDetailView(generic.DetailView):
    pass
