from django.urls import path

from .views import OrderListView, OrderDetailView, OrderItemSearch, OrderItemAdd, OrderItemBulkRemove, OrderItemUpdateCount, AssortmentSearchResult, ItemsFullSearchResult, PartsSearchView

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='detail'),
    path('<int:pk>/items-search', OrderItemSearch.as_view(), name='items_search'),
    path('<int:pk>/items-search/add', OrderItemAdd.as_view(), name='add_order_item'),
    path('<int:pk>/items/remove', OrderItemBulkRemove.as_view(), name='remove_order_items'),
    path('items/<int:item_pk>/update-count', OrderItemUpdateCount.as_view(), name='update_order_item_count'),
    path('parts/search/', PartsSearchView.as_view(), name='parts_search'),
    path('items-search/results', AssortmentSearchResult.as_view(), name='assortment_search_results'),
    path('items-search/full-results', ItemsFullSearchResult.as_view(), name='items_full_search_results'),
]

