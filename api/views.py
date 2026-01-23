from django.db.models import Q
from rest_framework import status
from rest_framework.generics import (
    RetrieveAPIView,
    ListAPIView,
    ListCreateAPIView,
    get_object_or_404)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from api.serializers.chat_message_serializers import CreateChatMessageSerializer, PatchChatMessageSerializer
from api.serializers.client_serializers import ClientRegisterSerializer, ClientDetailSerializer, ClientSerializer
from api.serializers.order_serializers import OrderSerializer, OrderCreateSerializer
from api.serializers.vehicle_serializers import CreateVehicleSerializer
from chat.models import ChatMessage
from orders.models import Client, Order
from django.db import connection


class IsApiUser(IsAuthenticated):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.groups.filter(name='api').exists()


def query_param_as_array(query_param: str) -> list[str]:
    return [part.strip() for part in query_param.split(',')]


class ClientView(ListCreateAPIView):
    permission_classes = [IsApiUser]
    lookup_field = ['telegram_id', 'phone']

    def post(self, request, **kwargs):
        serializer = ClientRegisterSerializer(data=request.data, instance=None)
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
        serializer = ClientSerializer(queryset, many=True)
        return Response(serializer.data)

    def get_paginated_response(self, data):
        pass


class ClientDetailView(RetrieveAPIView):
    permission_classes = [IsApiUser]
    serializer_class = ClientDetailSerializer
    queryset = Client.objects.all()
    lookup_field = ['telegram_id']

    def get_object(self):
        client_filter = {}
        for field in self.lookup_field:
            if self.kwargs.get(field):
                client_filter[field] = self.kwargs[field]
        return get_object_or_404(queryset=self.queryset, **client_filter)


class ClientOrdersView(ListAPIView):
    permission_classes = [IsApiUser]

    def get(self, request, *args, **kwargs):
        client_id = kwargs['client_id']
        queryset = Order.objects.filter(client__id=client_id)
        serializer = OrderSerializer(queryset, many=True)
        # data = serializer.data
        # print(connection.queries)
        return Response(serializer.data)


class VehicleView(APIView):
    permission_classes = [IsApiUser]
    serializers_class = CreateVehicleSerializer

    def post(self, request):
        print(f"Vehicle register request: {request.data}")
        serializer = self.serializers_class(data=request.data, instance=None)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.validated_data, status.HTTP_201_CREATED)


class OrderView(APIView):
    permission_classes = [IsApiUser]
    serializer_class = OrderCreateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, instance=None)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.validated_data, status.HTTP_201_CREATED)


class ChatView(APIView):
    permission_classes = [IsApiUser]
    chat_message_from_client_serializer = CreateChatMessageSerializer

    def post(self, request):
        serializer = self.chat_message_from_client_serializer(data=request.data, instance=None)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.validated_data, status.HTTP_201_CREATED)


class ChatMessageView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsApiUser]

    def patch(self, request, *args, **kwargs):
        try:
            if 'id' in request.GET:
                instance = ChatMessage.objects.get(pk=request.GET['id'])
            elif 'telegram_id' in request.GET:
                instance = ChatMessage.objects.get(telegram_id=request.GET['telegram_id'])
            else:
                return Response("Parameter 'id' or 'telegram_id' must be specified", status.HTTP_400_BAD_REQUEST)
        except ChatMessage.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PatchChatMessageSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(status=status.HTTP_200_OK)
