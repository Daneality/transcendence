# from django.urls import path
# from .consumers import MyConsumer
# from channels.routing import ProtocolTypeRouter, URLRouter
# from myapp.routing import websocket_urlpatterns

# websocket_urlpatterns = [
#     path('ws/my_consumer/', MyConsumer.as_asgi()),
# ]
# application = ProtocolTypeRouter({
#     'websocket': URLRouter(websocket_urlpatterns),
# })
from django.urls import re_path

from game.consumers import GameConsumer

websocket_urlpatterns = [
    re_path(r'ws/game_consumer/(?P<opponent>\w+)/$', GameConsumer.as_asgi()),
]