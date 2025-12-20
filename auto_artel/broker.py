import json
import logging

from django.conf import settings
from pika import BlockingConnection, URLParameters
from pika.spec import BasicProperties

logger = logging.getLogger(__name__)


class Broker:
    def __init__(self):
        self.connection_properties = URLParameters(settings.BROKER['URI'])
        self.message_properties = BasicProperties(
            content_type='application/json',
            content_encoding='utf-8'
        )
        self._connection = None
        self._channel = None

    @property
    def connection(self):
        if not self._connection or not self._connection.is_open:
            self._connection = BlockingConnection(self.connection_properties)
            self._channel = None
        return self._connection

    @property
    def channel(self):
        if not self._channel or not self._channel.is_open:
            self._channel = self.connection.channel()
            self._configure()
        return self._channel

    def close(self):
        self._channel.close()
        self._connection.close()

    def _configure(self):
        self._channel.queue_declare('chat_messages', durable=True)

    def send_chat_message(self, message):
        self._publish('chat_messages', message)

    def _publish(self, queue_name, message):
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=self.message_properties
            )
        except Exception as ex:
            logger.error("Failed to send message to broker due error", ex)
        finally:
            self.close()


broker = Broker()
