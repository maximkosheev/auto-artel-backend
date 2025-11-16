from rest_framework import serializers
from rest_framework.fields import empty

from chat.models import ChatMessage
from orders.models import Client


class MessageFromClientSerializer(serializers.Serializer):
    # идентификатор сообщения из telegram.
    id = serializers.IntegerField(required=True, min_value=1)
    reply_to_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    text = serializers.CharField()
    media = serializers.ListField(required=False, allow_null=True, allow_empty=True, max_length=10)


class CreateChatMessageSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    message = MessageFromClientSerializer()

    def __init__(self, instance, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.client = None

    def validate(self, attrs):
        # Throw Client.DoesNotExists if client not found
        self.client = Client.objects.get(pk=attrs.get("client_id"))
        return attrs

    def create(self, validated_data):
        message_date = validated_data['message']
        new_chat_message = ChatMessage.objects.create(
            telegram_id=message_date['id'],
            reply_to_telegram_id=message_date.get('reply_to_id', 0),
            client=self.client,
            text=message_date['text'],
            media=message_date['media']
        )
        return new_chat_message
