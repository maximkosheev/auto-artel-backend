from django.contrib import admin
from .models import Client, Manager
from .admin_forms import ClientForm


class ClientAdmin(admin.ModelAdmin):
    form = ClientForm


# Register your models here.
admin.site.register(Client, ClientAdmin)
admin.site.register(Manager)