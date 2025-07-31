from django.contrib import admin
from .models import Client
from .admin_forms import ClientForm


class ClientAdmin(admin.ModelAdmin):
    form = ClientForm


# Register your models here.
admin.site.register(Client, ClientAdmin)
