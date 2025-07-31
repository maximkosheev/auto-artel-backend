from rest_framework import serializers

from orders.models import Order, Client
from . import validators


class OrderCreateSerializer(serializers.ModelSerializer):
    client_telegram_id = serializers.IntegerField(required=False, write_only=True)
    client_phone = serializers.CharField(required=False, validators=[validators.phone_validator])

    class Meta:
        model = Order
        fields = ['client_telegram_id', 'client_phone', 'initial_requirements']

    def validate(self, attrs):
        client_telegram_id = attrs.get('client_telegram_id')
        client_phone = attrs.get('client_phone')

        if client_telegram_id:
            try:
                Client.get_by_telegram_id(client_telegram_id)
            except Client.DoesNotExist:
                raise serializers.ValidationError(f"Client with telegram_id {client_telegram_id} does not exist.")
        elif client_phone:
            try:
                Client.get_by_phone(client_phone)
            except Client.DoesNotExist:
                raise serializers.ValidationError(f"Client with phone {client_phone} does not exist.")
        else:
            raise serializers.ValidationError("At least one 'client_telegram_id' or 'client_phone' must be provided")
        return attrs

    def create(self, validated_data):
        client = None
        if 'client_telegram_id' in validated_data:
            client = Client.get_by_telegram_id(validated_data.pop('client_telegram_id'))
        elif 'client_phone' in validated_data:
            client = Client.get_by_phone(validated_data.pop('client_phone'))

        order = Order.objects.create(
            client=client,
            **validated_data
        )
        return order
