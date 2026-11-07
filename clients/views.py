from django.db.models import Q
from django.views import generic

from auto_artel.mixins import ManagerMixin
from orders.models import Client


class ClientsListView(ManagerMixin, generic.ListView):
    template_name = 'clients/list.html'
    model = Client
    context_object_name = 'clients'

    def get_queryset(self):
        filter_params = self.get_filter_values()
        where = self.build_filter(filter_params)
        if where:
            return Client.objects.filter(where).distinct().all()
        else:
            return Client.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_filter_values())
        return context

    def get_filter_values(self):
        return {
            'filter_name': self.request.GET.get('client_name', '').strip()[:100],
            'filter_phone': self.request.GET.get('client_phone', '').strip()[:10],
            'filter_vin': self.request.GET.get('vin', '').strip()[:20],
        }

    def build_filter(self, filters):
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


class ClientDetailsView(ManagerMixin, generic.DetailView):
    template_name = 'clients/details.html'
    pass
