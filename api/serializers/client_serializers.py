import uuid

from django.contrib.auth.models import Group, User
from rest_framework import serializers

from api.serializers import utils
from api.serializers.fields import ClientPhoneField
from api.serializers.vehicle_serializers import VehicleSerializer
from orders.models import Client
from utils import phone_utils


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"


class ClientRegisterSerializer(serializers.ModelSerializer):
    phone = ClientPhoneField()

    class Meta:
        model = Client
        fields = ['name', 'phone', 'telegram_id']

    def validate(self, attrs):
        if utils.is_client_exists(
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


class ClientDetailSerializer(serializers.ModelSerializer):
    vehicle_list = VehicleSerializer(read_only=True, many=True)

    class Meta:
        model = Client
        fields = ['id', 'name', 'phone', 'telegram_id', 'vehicle_list']
