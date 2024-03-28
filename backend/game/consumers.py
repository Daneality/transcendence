import json
import uuid
import asyncio
import time

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from games.models import Game
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs
from django.core.cache import cache

@database_sync_to_async
def game_save(self, player1, player2, score1, score2, winner, date):
    result = Game(player1=player1, player2=player2, p1_score=score1, p2_score=score2, winner=winner, date=date)
    result.save()
    all_records = Game.objects.all()
    print(all_records)

@database_sync_to_async
def get_user(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()

class GameConsumer(AsyncWebsocketConsumer):

    players = {}
    ball_radius = 10
    paddle_height = 75
    canvas_width = 480
    canvas_height = 480

    update_lock = asyncio.Lock()

    async def connect(self):
        query_string = parse_qs(self.scope['query_string'].decode())
        token_key = query_string.get('token')


        if token_key:
            self.player = await get_user(token_key[0])
            if self.player.is_authenticated:
                await self.accept()
                opponent = self.scope['url_route']['kwargs']['opponent']
                playerLen = len(self.players)
                self.room_name = '_'.join(sorted([str(self.player.id), opponent]))
                self.room_group_name = 'game_%s' % self.room_name
                count = cache.get(self.room_group_name, 0)
                cache.set(self.room_group_name, count + 1)
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.send(
                    text_data=json.dumps({"type": "playerNum", "playerNum": count})
                )
                async with self.update_lock:
                    self.players[playerLen] = {
                        "userId": str(self.player.id),
                        "room_group_name": self.room_group_name,
                        "playerNum": count,
                        "paddleY": (self.canvas_height - self.paddle_height) / 2,
                        "upPressed": False,
                        "downPressed": False,
                        "score": 0,
                    }
                if count == 1:
                    opponent_index = next((index for index, player in enumerate(self.players.values()) if player["userId"] == opponent), None)
                    asyncio.create_task(self.game_loop(player1_index=opponent_index, player2_index=playerLen))
                    await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                "type": "game_start",
                            },
                        )

                
            else:
                await self.close()
        else:
            await self.close()
        # self.player_id = str(uuid.uuid4())
        # await self.accept()
        # await self.channel_layer.group_add(
        #     self.game_group_name, self.channel_name
        # )
        
        

    async def disconnect(self, close_code):
        pass
        # async with self.update_lock:
        #     if self.player_id in self.players:
        #         del self.players[self.player_id]

        # await self.channel_layer.group_discard(
        #     self.room_group_name, self.channel_name
        # )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "")
        if message_type == 'game_update':
            playerNum = text_data_json["playerNum"]
            player_index = next((index for index, player in self.players.items() if player["room_group_name"] == self.room_group_name and player["playerNum"] == playerNum), None)
            self.players[player_index]["upPressed"] = text_data_json["upPressed"]
            self.players[player_index]["downPressed"] = text_data_json["downPressed"]
        else:
            pass
            
    async def game_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "game_update",
                    "x": event["x"],
                    "y": event["y"],
                    "player1_paddleY": event["player1_paddleY"],
                    "player2_paddleY": event["player2_paddleY"],
                    "player1_score": event["player1_score"],
                    "player2_score": event["player2_score"],
                }
            )
        )

    async def game_start(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "game_start",
                }
            )
        )
    
    async def game_end(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "game_end",
                }
            )
        )
        
    async def game_loop(self, player1_index, player2_index):
        x = self.canvas_width / 2
        y = self.canvas_height - 30
        dx = 1
        dy = -1
        while len(self.players) > 1:
            await asyncio.sleep(0.01)
            async with self.update_lock:
                if (self.players[player1_index]["score"] == 1 or self.players[player2_index]["score"] == 1):
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "game_end",
                        },
                    )
                    player1 = self.players[player1_index]["userId"]
                    player2 = self.players[player2_index]["userId"]
                    score1 = self.players[player1_index]["score"]
                    score2 = self.players[player2_index]["score"]
                    winner = player1 if score1 > score2 else player2
                    date = time.strftime('%Y-%m-%d %H:%M:%S')
                    await game_save(player1, player2, score1, score2, winner, date)
                    break
                if self.players[player1_index]["upPressed"] and self.players[player1_index]["paddleY"] > 0:
                    self.players[player1_index]["paddleY"] -= 7
                elif self.players[player1_index]["downPressed"] and self.players[player1_index]["paddleY"] < self.canvas_height - self.paddle_height:
                    self.players[player1_index]["paddleY"] += 7
                if self.players[player2_index]["upPressed"] and self.players[player2_index]["paddleY"] > 0:
                    self.players[player2_index]["paddleY"] -= 7
                elif self.players[player2_index]["downPressed"] and self.players[player2_index]["paddleY"] < self.canvas_height - self.paddle_height:
                    self.players[player2_index]["paddleY"] += 7
                if (y + dy > self.canvas_height - self.ball_radius or y + dy < self.ball_radius):
                    dy = -dy
                if (x + dx < self.ball_radius):
                    if (y > self.players[player1_index]["paddleY"] and y < self.players[player1_index]["paddleY"] + self.paddle_height):
                        dx = -dx
                    else:
                        self.players[player2_index]["score"] += 1
                        x = self.canvas_width / 2
                        y = self.canvas_height - 30
                        dx = 1
                        dy = -1
                        self.players[player1_index]["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                        self.players[player2_index]["paddleY"] = (self.canvas_height - self.paddle_height) / 2

                elif (x + dx > self.canvas_width - self.ball_radius):
                    if (y > self.players[player2_index]["paddleY"] and y < self.players[player2_index]["paddleY"] + self.paddle_height):
                        dx = -dx
                    else:
                        self.players[player1_index]["score"] += 1
                        x = self.canvas_width / 2
                        y = self.canvas_height - 30
                        dx = 1
                        dy = -1
                        self.players[player1_index]["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                        self.players[player2_index]["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                x += dx
                y += dy

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "game_update",
                        "x": x,
                        "y": y,
                        "player1_paddleY": self.players[player1_index]["paddleY"],
                        "player2_paddleY": self.players[player2_index]["paddleY"],
                        "player1_score": self.players[player1_index]["score"],
                        "player2_score": self.players[player2_index]["score"],
                    },
                )

# game_state = {
#     'game_started': False,
#     'score': {'player1': 0, 'player2': 0}
#     'ball': {'x': 240, 'y': 240, 'dx': -1, 'dy': -1},
#     'paddles': {
#         'player1_y': 0,
#         'player2_y': 0,
#     },
# }