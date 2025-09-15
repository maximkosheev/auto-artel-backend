from django.db.models import Q
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Client
from . import serializers


class IsApiUser(IsAuthenticated):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.groups.filter(name='api').exists()


def query_param_as_array(query_param: str) -> list[str]:
    return [part.strip() for part in query_param.split(',')]


class ClientView(ListCreateAPIView):
    permission_classes = [IsApiUser]
    serializer_class = serializers.ClientRegisterSerializer

    def post(self, request, **kwargs):
        serializer = self.serializer_class(data=request.data, instance=None)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.validated_data, status.HTTP_201_CREATED)

    def get(self, request, **kwargs):
        telegram_id = request.GET.get('telegram_id')
        phone = request.GET.get('phone')

        where = Q()
        if telegram_id:
            where &= Q(telegram_id__in=query_param_as_array(telegram_id))
        if phone:
            where &= Q(phone__in=query_param_as_array(phone))
        queryset = Client.objects.filter(where)
        print(queryset.query)
        serializer = serializers.ClientSerializer(queryset, many=True)
        return Response(serializer.data)


class ClientDetailView(RetrieveAPIView):
    permission_classes = [IsApiUser]
    serializer_class = serializers.ClientDetailSerializer

    def get(self, request, **kwargs):
        telegram_id = kwargs.pop('telegram_id')
        client = Client.objects.filter(telegram_id=telegram_id).first()
        if client is None:
            return Response(data=f"Client {telegram_id} not found", status=404)
        return Response(self.serializer_class(client).data)


class VehicleView(APIView):
    permission_classes = [IsApiUser]
    serializers_class = serializers.CreateVehicleSerializer

    def post(self, request):
        serializer = self.serializers_class(data=request.data, instance=None)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.validated_data, status.HTTP_201_CREATED)


class OrderView(APIView):
    permission_classes = [IsApiUser]
    serializer_class = serializers.OrderCreateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, instance=None)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.validated_data, status.HTTP_201_CREATED)
