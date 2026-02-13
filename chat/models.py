from django.contrib.postgres import fields
from django.db import models
from datetime import datetime, UTC
from orders.models import Client, Manager


class ChatMessage(models.Model):
    id = models.BigAutoField(primary_key=True)
    telegram_id = models.BigIntegerField(null=True, db_index=True)
    reply_to = models.ForeignKey('self', null=True, related_name="+",  on_delete=models.RESTRICT)
    client = models.ForeignKey(Client, on_delete=models.RESTRICT)
    manager = models.ForeignKey(Manager, null=True, on_delete=models.RESTRICT)
    created = models.DateTimeField(default=datetime.now(UTC))
    edited = models.DateTimeField(null=True)
    deleted = models.DateTimeField(null=True)
    text = models.TextField()
    media = fields.ArrayField(
        models.TextField(),
        null=True,
        size=10
    )
    viewed = models.BooleanField(default=False)
