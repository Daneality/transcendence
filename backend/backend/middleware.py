from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs

@database_sync_to_async
def get_user(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()

class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        return TokenAuthMiddlewareInstance(scope, self, receive, send)

class TokenAuthMiddlewareInstance:
    def __init__(self, scope, middleware, receive, send):
        self.middleware = middleware
        self.scope = dict(scope)
        self.inner = self.middleware.inner
        self.receive = receive
        self.send = send

    async def __call__(self):
        query_string = self.scope['query_string'].decode()
        token_key = query_string.split('token=')[1]
        self.scope['user'] = await get_user(token_key)
        inner = self.middleware.inner(self.scope)
        return await inner(self.scope, self.receive, self.send)
