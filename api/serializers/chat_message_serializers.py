from datetime import datetime, UTC

from rest_framework import serializers
from rest_framework.fields import empty

from chat.models import ChatMessage
from orders.models import Client


class MessageFromClientSerializer(serializers.Serializer):
    # идентификатор сообщения из telegram.
    message_telegram_id = serializers.IntegerField(required=True, min_value=1)
    reply_to_message_telegram_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    text = serializers.CharField()
    media = serializers.ListField(required=False, allow_null=True, allow_empty=True, max_length=10)


class CreateChatMessageSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    message = MessageFromClientSerializer()

    def __init__(self, instance, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.client = None
        self.reply_to = None

    def validate(self, attrs):
        # Throw Client.DoesNotExists if client not found
        self.client = Client.objects.get(pk=attrs['client_id'])
        message_data = attrs['message']
        if message_data.get('reply_to_message_telegram_id'):
            try:
                self.reply_to = ChatMessage.objects.get(telegram_id=message_data.get('reply_to_message_telegram_id'))
            except ChatMessage.DoesNotExist:
                self.reply_to = None
        return attrs

    def create(self, validated_data):
        message_data = validated_data['message']
        new_chat_message = ChatMessage.objects.create(
            telegram_id=message_data['message_telegram_id'],
            reply_to=self.reply_to,
            client=self.client,
            text=message_data['text'],
            media=message_data['media']
        )
        return new_chat_message


class PatchChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['telegram_id', 'text']
        read_only_fields = ['edited']

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if (
            request
            and request.method == 'PATCH'
            and 'text' in self.initial_data
        ):
            instance.edited = datetime.now(UTC)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
