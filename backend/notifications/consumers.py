import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs
from user.models import User
from chat.models import Chat, Message
from asgiref.sync import sync_to_async

@database_sync_to_async
def get_user(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = parse_qs(self.scope['query_string'].decode())
        token_key = query_string.get('token')

        if token_key:
            self.sender = await get_user(token_key[0])
            if self.sender.is_authenticated:
                # Ensure the room name is the same regardless of the order of sender and recipient
                self.room_name = '_'.join(str(self.sender.id))
                self.room_group_name = 'notification_%s' % self.room_name

                # Join room group
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )

                await self.accept()
            else:
                # Close the connection if the user is not authenticated
                await self.close()
        else:
            # Close the connection if no token is provided
            await self.close()

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_notification',
                'message': message,
                'sender': self.sender.username
            }
        )
 
    # Receive message from room group
    async def chat_notification(self, event):
        message = event['message']
        sender = event['sender']
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'type': event['type']
        }))
    
    async def game_invite_notification(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'type': event['type']
        }))

    async def tournament_game_notification(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'type': event['type']
        }))