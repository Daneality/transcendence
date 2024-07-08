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

from game.consumers import PrivateGameConsumer
from game.consumers import MatchmakingConsumer
from game.consumers import AIConsumer

websocket_urlpatterns = [
    re_path(r'ws/private_game/(?P<opponent>\w+)/$', PrivateGameConsumer.as_asgi()),
    re_path(r'ws/matchmaking/', MatchmakingConsumer.as_asgi()),
    re_path(r'ws/ai/', AIConsumer.as_asgi()),
]
