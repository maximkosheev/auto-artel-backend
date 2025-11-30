from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    def receive(self, text_data=None, bytes_data=None):
        print(f"Chat consumer received data")
