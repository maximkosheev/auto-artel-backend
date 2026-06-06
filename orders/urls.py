from django.urls import path

from .views import OrderListView, OrderDetailView, OrderItemsSearch, AddOrderItem, ItemsSearchResult, ItemsFullSearchResult, PartsSearchView

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='detail'),
    path('<int:pk>/items-search', OrderItemsSearch.as_view(), name='items_search'),
    path('<int:pk>/items-search/add', AddOrderItem.as_view(), name='add_order_item'),
    path('items-search/results', ItemsSearchResult.as_view(), name='items_search_results'),
    path('items-search/full-results', ItemsFullSearchResult.as_view(), name='items_full_search_results'),
    path('parts/search/', PartsSearchView.as_view(), name='parts_search'),
]

