from django.shortcuts import render
from django.views import generic


class OrderListView(generic.ListView):
    pass


class OrderDetailView(generic.DetailView):
    pass
