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
    
@database_sync_to_async
def has_blocked(sender, recipient):
    recipient = User.objects.get(id=recipient)
    return recipient.profile.blocked_users.filter(id=sender.id).exists()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = parse_qs(self.scope['query_string'].decode())
        token_key = query_string.get('token')

        if token_key:
            self.sender = await get_user(token_key[0])
            if self.sender.is_authenticated:
                recipient = self.scope['url_route']['kwargs']['recipient']

                # Ensure the room name is the same regardless of the order of sender and recipient
                self.room_name = '_'.join(sorted([str(self.sender.id), recipient]))
                self.room_group_name = 'chat_%s' % self.room_name

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

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        recipient = self.scope['url_route']['kwargs']['recipient']

        if not await has_blocked(self.sender, recipient):
            await sync_to_async(Message.objects.create)(
                sender=self.sender,
                text=message,
                chat=await sync_to_async(Chat.objects.get)(
                    id = self.room_name
                )
            )
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': str(self.sender),
                    'recipient': recipient
                }
            )
        else:
            print(f"Message not sent. User {recipient} has blocked {self.sender}")

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        recipient = event['recipient']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'recipient': recipient
        }))
