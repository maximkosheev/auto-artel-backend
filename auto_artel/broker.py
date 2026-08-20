import json
import logging

from django.conf import settings
from pika import BlockingConnection, URLParameters
from pika.spec import BasicProperties

logger = logging.getLogger(__name__)


class Broker:
    CHAT_QUEUE_NAME = 'chat_messages'
    NOTIFICATION_QUEUE_NAME = 'automatic_notifications'

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
        self._channel.queue_declare(self.CHAT_QUEUE_NAME, durable=True)
        self._channel.queue_declare(self.NOTIFICATION_QUEUE_NAME, durable=True)

    def send_chat_message(self, message):
        self._publish(self.CHAT_QUEUE_NAME, message)

    def send_notification_message(self, message):
        self._publish(self.NOTIFICATION_QUEUE_NAME, message)

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

    def send_order_change_status(self, client, order):
        self.send_notification_message({
            'to': client.id,
            'to_telegram_id': client.telegram_id,
            'type': 'TEXT',
            'data': f"Статус вашего заказа #{order.id} от {order.created_date_formatted()} изменился. "
                    f"Новый статус <b>{order.get_client_status_display()}</b>\n"
        })

    def send_order_agreement_notification(self, client, order, agreement_link, due_to):
        due_to_str = due_to.strftime("%d/%m/%Y, %H:%M:%S")
        self.send_notification_message({
            'to': client.id,
            'to_telegram_id': client.telegram_id,
            'type': 'ORDER_AGREEMENT_REQUIRED',
            'data': {
                'text': f"Требуется согласие по вашему заказу #{order.id} от {order.created_date_formatted()}.\n"
                        f"Для согласования перейдите по ссылке ниже. Ссылка действует до {due_to_str}Мск",
                'details': {
                    'link': agreement_link
                }
            }
        })


broker = Broker()
