from django.urls import path

from .views import OrderListView, OrderDetailView, OrderItemsSearch, AddOrderItem, ItemsSearchResult

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='detail'),
    path('<int:pk>/items-search', OrderItemsSearch.as_view(), name='items_search'),
    path('<int:pk>/items-search/add', AddOrderItem.as_view(), name='add_order_item'),
    path('items-search/results', ItemsSearchResult.as_view(), name='items_search_results'),
]

