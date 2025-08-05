from django.urls import path

from .views import OrderCreateView, OrderUpdateView, OrderListView, OrderDetailView

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='list'),
    path('new/', OrderCreateView.as_view(), name='create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='detail'),
    path('<int:pk>/edit', OrderUpdateView.as_view(), name='edit')
]

