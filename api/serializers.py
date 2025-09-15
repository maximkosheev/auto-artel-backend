import uuid

from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework.fields import empty

from orders.models import Order, Client, Vehicle
from utils import phone_utils
from . import validators


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


class OrderCreateSerializer(serializers.ModelSerializer):
    client_telegram_id = serializers.IntegerField(required=False, write_only=True)
    client_phone = serializers.CharField(required=False, validators=[validators.phone_validator])

    class Meta:
        model = Order
        fields = ['client_telegram_id', 'client_phone', 'initial_requirements']

    def __init__(self, instance, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.client = None

    def validate(self, attrs):
        self.client = get_client(
            client_phone=attrs.get('client_phone'),
            client_telegram_id=attrs.get('client_telegram_id')
        )
        return attrs

    def create(self, validated_data):
        order = Order.objects.create(
            client=self.client,
            **validated_data
        )
        return order


class ClientRegisterSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(validators=[validators.phone_validator])

    class Meta:
        model = Client
        fields = ['name', 'phone', 'telegram_id']

    def validate(self, attrs):
        if is_client_exists(
            client_phone=attrs.get('phone'),
            client_telegram_id=attrs.get('telegram_id')
        ):
            raise serializers.ValidationError("Client is already exists")
        return attrs

    def _create_user(self):
        client_group = Group.objects.get(name='client')
        user = User.objects.create_user(uuid.uuid4(), None, None)
        user.groups.set([client_group])
        user.save()
        return user

    def create(self, validated_data):
        validated_data['phone'] = phone_utils.before_save_to_db(validated_data['phone'])

        client = Client.objects.create(
            user=self._create_user(),
            **validated_data
        )
        return client


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class CreateVehicleSerializer(serializers.ModelSerializer):
    client_telegram_id = serializers.IntegerField(required=False, write_only=True)
    client_phone = serializers.CharField(required=False, validators=[validators.phone_validator])

    class Meta:
        model = Vehicle
        fields = ['client_telegram_id', 'client_phone', 'vin', 'manufacture', 'model', 'year']

    def __init__(self, instance, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.client = None

    def validate(self, attrs):
        self.client = get_client(
            client_phone=attrs.get('client_phone'),
            client_telegram_id=attrs.get('client_telegram_id')
        )
        return attrs

    def create(self, validated_data):
        return Vehicle.objects.create(
            client=self.client,
            vin=validated_data['vin'],
            manufacture=validated_data['manufacture'],
            model=validated_data['model'],
            year=validated_data['year']
        )


class VehicleListSerialize(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'vin', 'manufacture', 'model', 'year']


class ClientDetailSerializer(serializers.ModelSerializer):
    vehicleList = VehicleListSerialize(read_only=True, many=True)

    class Meta:
        model = Client
        fields = ['name', 'phone', 'telegram_id', 'vehicleList']
