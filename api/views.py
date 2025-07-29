from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import serializers


class IsApiUser(IsAuthenticated):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.groups.filter(name='api').exists()


class OrderView(APIView):
    permission_classes = [IsApiUser]
    serializer_class = serializers.OrderSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.validated_data, status.HTTP_201_CREATED)

