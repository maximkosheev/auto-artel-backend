from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from auto_artel.broker import broker
from .models import Order


@receiver(post_save, sender=Order)
def order_saved_handler(sender, instance, **kwargs):
    if instance.client_status_changed:
        transaction.on_commit(
            lambda: broker.send_order_change_status(instance.client, instance)
        )
