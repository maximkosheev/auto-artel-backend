import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from chat.models import ChatMessage
from orders.models import Client, Manager

from datetime import datetime, UTC

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close(code=401, reason="Anonymous connection are not allowed")
            return

        self.room_group_name = 'chat_updates'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        print(f"received data: {data}")

        action = data.get('action')

        if action == 'mark_read':
            await self.mark_messages_read(data['client_id'])
        elif action == 'send_message':
            await self.send_message(data)

    @database_sync_to_async
    def mark_messages_read(self, client_id):
        ChatMessage.objects.filter(
            client_id=client_id,
            viewed=False
        ).update(viewed=True)

    @database_sync_to_async
    def send_message(self, data):
        client = Client.objects.get(pk=data['client_id'])
        manager = Manager.objects.get(user=self.scope['user'])

        message = ChatMessage.objects.create(
            client=client,
            manager=manager,
            text=data['text'],
            reply_to_id=data.get('reply_to'),
            viewed=True,
            created=datetime.now(UTC)
        )
