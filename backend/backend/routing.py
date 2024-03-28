from django.urls import re_path, include, path
from channels.routing import URLRouter
from chat import routing as chat
from notifications import routing as notifications
from game.consumers import GameConsumer

websocket_urlpatterns = [
    re_path('', URLRouter(chat.websocket_urlpatterns)),
    re_path('', URLRouter(notifications.websocket_urlpatterns)),
    path('ws/game_consumer/', GameConsumer.as_asgi()),
]