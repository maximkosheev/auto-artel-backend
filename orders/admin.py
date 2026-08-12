from datetime import timezone as dt_timezone

from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils import timezone

from .admin_forms import ClientForm, ManagerForm, OrderForm
from .models import Client, Manager, Order


class ClientAdmin(admin.ModelAdmin):
    form = ClientForm


class ManagerAdmin(admin.ModelAdmin):
    form = ManagerForm

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not change:
            manager_group = Group.objects.get_by_natural_key('manager')
            obj.user.groups.add(manager_group)


class OrderAdmin(admin.ModelAdmin):
    form = OrderForm
    list_display = ('id', 'client', 'status', 'client_status', 'manager', 'created_utc')

    @admin.display(description='created at (UTC)', ordering='created')
    def created_utc(self, obj):
        return timezone.localtime(obj.created, dt_timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')


# Register your models here.
admin.site.register(Client, ClientAdmin)
admin.site.register(Manager, ManagerAdmin)
admin.site.register(Order, OrderAdmin)
