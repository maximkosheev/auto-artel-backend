from django.db.models import Q
from django.views import generic

from auto_artel.mixins import ManagerMixin
from orders.models import Client, Order


def get_filter_values(params: dict):
    return {
        'filter_name': params.get('client_name', '').strip()[:100],
        'filter_phone': params.get('client_phone', '').strip()[:10],
        'filter_vin': params.get('vin', '').strip()[:20],
    }


def build_client_filter(filters):
    where = Q()
    active = False

    name = filters['filter_name']
    if name:
        where &= Q(name__icontains=name)
        active = True

    phone = filters['filter_phone']
    if phone:
        where &= Q(phone__icontains=phone)
        active = True

    vin = filters['filter_vin']
    if vin:
        where &= Q(vehicle_list__vin__startswith=vin)
        active = True

    return where if active else None


def build_clients_filtered_by(params):
    filter_params = get_filter_values(params)
    where = build_client_filter(filter_params)
    if where:
        return Client.objects.filter(where).distinct().all()
    else:
        return Client.objects.all()


class ClientsListView(ManagerMixin, generic.ListView):
    template_name = 'clients/list.html'
    model = Client
    context_object_name = 'clients'

    def get_queryset(self):
        return build_clients_filtered_by(self.request.GET)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_filter_values(self.request.GET))
        return context


class ClientDetailsView(ManagerMixin, generic.DetailView):
    template_name = 'clients/details.html'
    model = Client

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_filter_values(self.request.GET))
        context["clients"] = build_clients_filtered_by(self.request.GET)
        context["client"] = self.object
        context["vehicles"] = self.object.vehicle_list.all()
        context["orders"] = Order.objects.filter(client=self.object).order_by('-created')
        return context
