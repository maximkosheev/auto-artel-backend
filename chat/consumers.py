import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from chat.models import ChatMessage
from orders.models import Client, Manager

from datetime import datetime, UTC
from django.views.decorators.csrf import csrf_exempt


class ChatConsumer(AsyncWebsocketConsumer):

    @csrf_exempt
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

        action = data.get('action')
        if action == 'mark_read':
            await self.mark_messages_read(data['client_id'])
        elif action == 'send_message':
            message = await self.send_message(data)
            await self.new_message({
                'message': message
            })

    @database_sync_to_async
    def mark_messages_read(self, client_id):
        ChatMessage.objects.filter(
            client_id=client_id,
            viewed=False
        ).update(viewed=True)

    @database_sync_to_async
    def send_message(self, data) -> ChatMessage:
        client = Client.objects.get(pk=data['client_id'])
        manager = Manager.objects.get(user=self.scope['user'])

        message = ChatMessage.objects.create(
            client=client,
            manager=manager,
            text=data['text'],
            reply_to_id=data.get('reply_to_id'),
            viewed=True,
            created=datetime.now(UTC)
        )
        return message

    async def new_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': {
                'id': message.id,
                'client_id': message.client.id,
                'is_manager': message.manager is not None,
                'text': message.text,
                'reply_to_id': message.reply_to.id if message.reply_to is not None else None,
                'reply_to_text': message.reply_to.text if message.reply_to is not None else None,
                'created': message.created.strftime("%d.%m.%Y %H:%M")
            }
        }))
