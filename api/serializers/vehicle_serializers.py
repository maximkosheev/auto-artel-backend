from rest_framework import serializers
from rest_framework.fields import empty

from api.serializers import utils
from api.serializers.fields import ClientPhoneField
from orders.models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    vin = serializers.CharField(required=False, allow_null=True)
    manufacture = serializers.CharField()
    model = serializers.CharField()
    year = serializers.IntegerField()

    class Meta:
        model = Vehicle
        fields = ['id', 'vin', 'manufacture', 'model', 'year']


class CreateVehicleSerializer(serializers.Serializer):
    client_telegram_id = serializers.IntegerField(required=False, write_only=True)
    client_phone = ClientPhoneField(required=False)
    vehicle = VehicleSerializer()

    class Meta:
        model = Vehicle
        fields = ['client_telegram_id', 'client_phone', 'vehicle']

    def __init__(self, instance, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.client = None

    def validate(self, attrs):
        self.client = utils.get_client(
            client_phone=attrs.get('client_phone'),
            client_telegram_id=attrs.get('client_telegram_id')
        )
        return attrs

    def create(self, validated_data):
        return Vehicle.objects.create(
            client=self.client,
            vin=validated_data['vehicle']['vin'],
            manufacture=validated_data['vehicle']['manufacture'],
            model=validated_data['vehicle']['model'],
            year=validated_data['vehicle']['year']
        )
