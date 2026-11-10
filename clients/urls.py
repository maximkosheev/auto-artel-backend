from django.urls import path
from .views import ClientsListView, ClientDetailsView

app_name = 'clients'

urlpatterns = [
    path('', ClientsListView.as_view(), name='list'),
    path('<int:pk>/', ClientDetailsView.as_view(), name='details')
]
