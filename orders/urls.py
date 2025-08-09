from django.urls import path

from .views import OrderUpdateView, OrderListView, OrderDetailView

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', OrderUpdateView.as_view(), name='edit')
]

