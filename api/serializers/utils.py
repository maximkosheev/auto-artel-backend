from rest_framework import serializers

from orders.models import Client


def get_client(client_phone, client_telegram_id):
    if client_telegram_id and client_phone:
        raise serializers.ValidationError(f"Either client_phone or client_telegram_id can be specified")
    elif client_telegram_id:
        try:
            return Client.get_by_telegram_id(client_telegram_id)
        except Client.DoesNotExist:
            raise serializers.ValidationError(f"Client with telegram_id {client_telegram_id} does not exist.")
    elif client_phone:
        try:
            return Client.get_by_phone(client_phone)
        except Client.DoesNotExist:
            raise serializers.ValidationError(f"Client with phone {client_phone} does not exist.")
    else:
        raise serializers.ValidationError("Either 'client_telegram_id' or 'client_phone' must be provided")


def is_client_exists(client_phone, client_telegram_id):
    if client_telegram_id:
        return Client.objects.filter(telegram_id=client_telegram_id).exists()
    elif client_phone:
        return Client.objects.filter(phone=client_phone).exists()
    else:
        raise serializers.ValidationError("Either 'client_telegram_id' or 'client_phone' must be provided")

