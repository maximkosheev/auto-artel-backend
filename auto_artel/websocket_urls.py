from django.urls import re_path

from chat.consumers import ChatConsumer

websocket_url_patterns = [
    re_path(r'ws/chat/$', ChatConsumer.as_asgi())
]
