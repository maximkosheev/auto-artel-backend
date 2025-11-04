from rest_framework import serializers
from rest_framework.fields import empty

from api.serializers import utils
from api.serializers.fields import ClientPhoneField
from orders.models import Order, OrderItem, Client


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"


class ManagerNameField(serializers.CharField):
    def to_representation(self, value):
        return value.name


class ClientStatusField(serializers.ChoiceField):
    def to_representation(self, value):
        if value == '' and self.allow_blank:
            return value
        return self.choices[value]


class OrderSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    client_status = ClientStatusField(choices=Order.CLIENT_STATUS_CHOICES, read_only=True)
    manager = ManagerNameField(required=False, read_only=True)
    created = serializers.DateTimeField()
    initial_requirements = serializers.CharField(read_only=True)
    order_item_list = OrderItemSerializer(read_only=True, many=True)

    class Meta:
        model = Order
        fields = ['id', 'client_status', 'manager', 'created', 'initial_requirements', 'order_item_list']


class OrderCreateSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(required=True)

    class Meta:
        model = Order
        fields = ['client_id', 'initial_requirements']

    def __init__(self, instance, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.client = None

    def validate(self, attrs):
        self.client = Client.objects.get(pk=attrs.get('client_id'))
        return attrs

    def create(self, validated_data):
        order = Order.objects.create(
            client=self.client,
            initial_requirements=validated_data['initial_requirements']
        )
        return order

