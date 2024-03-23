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

    game_group_name = "game_group"
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
                playerNum = len(self.players)
                async with self.update_lock:
                    self.players[playerNum] = {
                        "user": self.player,
                        "id": self.player_id,
                        "playerNum": playerNum,
                        "paddleY": (self.canvas_height - self.paddle_height) / 2,
                        "upPressed": False,
                        "downPressed": False,
                        "score": 0,
                    }
                self.room_name = '_'.join(sorted([str(self.player.id), recipient]))
                self.room_group_name = 'game_%s' % self.room_name

                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )

                await self.accept()
            else:
                await self.close()
        else:
            await self.close()
        # self.player_id = str(uuid.uuid4())
        # await self.accept()
        # await self.channel_layer.group_add(
        #     self.game_group_name, self.channel_name
        # )
        # await self.send(
        #     text_data=json.dumps({"type": "playerId", "playerId": self.player_id, "playerNum": playerNum})
        # )
        
        # if (len(self.players) == 2):
        #     asyncio.create_task(self.game_loop())
        #     await self.channel_layer.group_send(
        #             self.game_group_name,
        #             {
        #                 "type": "game_start",
        #             },
        #         )

    async def disconnect(self, close_code):
        async with self.update_lock:
            if self.player_id in self.players:
                del self.players[self.player_id]

        await self.channel_layer.group_discard(
            self.game_group_name, self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "")
        player_id = text_data_json["playerId"]
        playerNum = text_data_json["playerNum"]
        if message_type == 'game_update':
            self.players[playerNum]["upPressed"] = text_data_json["upPressed"]
            self.players[playerNum]["downPressed"] = text_data_json["downPressed"]
        else:
            pass
            
    async def game_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "game_update",
                    "x": event["x"],
                    "y": event["y"],
                    "dx": event["dx"],
                    "dy": event["dy"],
                    "players": event["players"],
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
        
    async def game_loop(self):
        x = self.canvas_width / 2
        y = self.canvas_height - 30
        dx = 1
        dy = -1
        while len(self.players) > 1:
            await asyncio.sleep(0.01)
            async with self.update_lock:
                if (self.players[0]["score"] == 1 or self.players[1]["score"] == 1):
                    await self.channel_layer.group_send(
                        self.game_group_name,
                        {
                            "type": "game_end",
                        },
                    )
                    player1 = self.players[0]["id"]
                    player2 = self.players[1]["id"]
                    score1 = self.players[0]["score"]
                    score2 = self.players[1]["score"]
                    winner = player1 if score1 > score2 else player2
                    date = time.strftime('%Y-%m-%d %H:%M:%S')
                    await game_save(player1, player2, score1, score2, winner, date)
                    break
                for player in self.players.values():
                    if player["upPressed"] and player["paddleY"] > 0:
                        player["paddleY"] -= 7
                    elif player["downPressed"] and player["paddleY"] < self.canvas_height - self.paddle_height:
                        player["paddleY"] += 7
                if (y + dy > self.canvas_height - self.ball_radius or y + dy < self.ball_radius):
                    dy = -dy
                if (x + dx < self.ball_radius):
                    if (y > self.players[0]["paddleY"] and y < self.players[0]["paddleY"] + self.paddle_height):
                        dx = -dx
                    else:
                        self.players[1]["score"] += 1
                        x = self.canvas_width / 2
                        y = self.canvas_height - 30
                        dx = 1
                        dy = -1
                        self.players[0]["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                        self.players[1]["paddleY"] = (self.canvas_height - self.paddle_height) / 2

                elif (x + dx > self.canvas_width - self.ball_radius):
                    if (y > self.players[1]["paddleY"] and y < self.players[1]["paddleY"] + self.paddle_height):
                        dx = -dx
                    else:
                        self.players[0]["score"] += 1
                        x = self.canvas_width / 2
                        y = self.canvas_height - 30
                        dx = 1
                        dy = -1
                        self.players[0]["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                        self.players[1]["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                x += dx
                y += dy

                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        "type": "game_update",
                        "x": x,
                        "y": y,
                        "dx": dx,
                        "dy": dy,
                        "players": self.players,
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