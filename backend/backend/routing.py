from django.urls import re_path
from channels.routing import URLRouter
from chat import routing as chat
from game import routing as game

websocket_urlpatterns = [
    re_path('', URLRouter(chat.websocket_urlpatterns)),
    re_path('', URLRouter(game.websocket_urlpatterns)),
]