from django.urls import path
from .views import ChatListView, ChatWithClient

app_name = 'chat'

urlpatterns = [
    path('', ChatListView.as_view(), name='list'),
    path('<int:client_id>/', ChatWithClient.as_view(), name='chat_with_client')
]