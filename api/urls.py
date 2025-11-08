from django.urls import path
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

app_name = 'api'

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('clients/', ClientView.as_view(), name='client'),
    path('clients/<int:telegram_id>/detail/', ClientDetailView.as_view(), name='client_detail'),
    path('clients/<int:client_id>/orders/', ClientOrdersView.as_view(), name='client_orders'),
    path('vehicle/', VehicleView.as_view(), name='vehicle'),
    path('orders/', OrderView.as_view(), name='orders'),
]

