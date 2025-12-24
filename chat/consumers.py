import json
import logging
from datetime import datetime, UTC

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.views.decorators.csrf import csrf_exempt

from chat.models import ChatMessage
from orders.models import Client, Manager
from auto_artel.broker import broker

logger = logging.getLogger(__name__)


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
        reply_to = self._get_reply_to(data.get('reply_to_id'))

        message = ChatMessage.objects.create(
            client=client,
            manager=manager,
            text=data['text'],
            reply_to=reply_to,
            viewed=True,
            created=datetime.now(UTC)
        )
        broker.send_chat_message({
            'id': message.id,
            'to': client.id,
            'to_telegram_id': client.telegram_id,
            'manager': manager.name,
            'text': data['text'],
            'reply_to_telegram_id': reply_to.telegram_id if reply_to is not None else None
        })
        return message

    async def new_message(self, event):
        message = event['message']
        if message.reply_to:
            reply_to = {
                'id': message.reply_to.id,
                'text': message.reply_to.text
            }
        else:
            reply_to = None

        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': {
                'id': message.id,
                'client_id': message.client.id,
                'is_manager': message.manager is not None,
                'text': message.text,
                'reply_to': reply_to,
                'created': message.created.strftime("%d.%m.%Y %H:%M")
            }
        }))

    def _get_reply_to(self, reply_to_id) -> ChatMessage | None:
        if reply_to_id:
            try:
                return ChatMessage.objects.get(pk=reply_to_id)
            except ChatMessage.DoesNotExist:
                logger.error(f"Chat message with id {reply_to_id} not found")
                return None
        else:
            return None
