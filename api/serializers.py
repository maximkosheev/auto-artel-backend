from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from orders.models import Order

from . import validators


class OrderSerializer(serializers.Serializer):
    client_telegram_id = serializers.IntegerField(required=False, write_only=True)
    client_phone = serializers.CharField(required=False, validators=[validators.phone_validator])
    initial_requirements = serializers.CharField()

    def validate(self, attrs):
        request = self.context.get('request')

        if request and request.method == 'POST':
            client_telegram_id = attrs.get('client_telegram_id')
            client_phone = attrs.get('client_phone')

            if client_telegram_id is None and client_phone is None:
                raise ValidationError("At least one 'client_telegram_id' or 'client_phone' must be provided")

        return attrs

    def create(self, validated_data):
        new_order = Order()
        return new_order
