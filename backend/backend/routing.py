from django.urls import re_path, include
from channels.routing import URLRouter
from chat import routing as chat

websocket_urlpatterns = [
    re_path('', URLRouter(chat.websocket_urlpatterns)),
]