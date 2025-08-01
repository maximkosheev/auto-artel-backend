from django.contrib import admin
from .models import Client, Manager
from .admin_forms import ClientForm, ManagerForm


class ClientAdmin(admin.ModelAdmin):
    form = ClientForm


class ManagerAdmin(admin.ModelAdmin):
    form = ManagerForm


# Register your models here.
admin.site.register(Client, ClientAdmin)
admin.site.register(Manager, ManagerAdmin)
