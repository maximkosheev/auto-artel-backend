from django.contrib import admin
from django.contrib.auth.models import Group

from .admin_forms import ClientForm, ManagerForm
from .models import Client, Manager


class ClientAdmin(admin.ModelAdmin):
    form = ClientForm


class ManagerAdmin(admin.ModelAdmin):
    form = ManagerForm

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not change:
            manager_group = Group.objects.get_by_natural_key('manager')
            obj.user.groups.add(manager_group)


# Register your models here.
admin.site.register(Client, ClientAdmin)
admin.site.register(Manager, ManagerAdmin)
