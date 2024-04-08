import json
import uuid
import asyncio
import time

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from games.models import Game
from user.models import Profile
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs
from django.core.cache import cache
from user.models import GameInvite
from channels.layers import get_channel_layer
import random
import math

@database_sync_to_async
def game_save(player1_id, player2_id, score1, score2):
    print("Saving game")
    user1 = User.objects.get(id=player1_id)
    user2 = User.objects.get(id=player2_id)
    player1 = Profile.objects.get(user=user1)
    player2 = Profile.objects.get(user=user2)
    winner = 1 if score1 > score2 else 2
    result = Game(player1=player1, player2=player2, p1_score=score1, p2_score=score2, winner=winner)
    
    result.save()
    if (player1.tournament is not None):
        tournament = player1.tournament
        print(tournament.game1)
        print(tournament.game2)
        print(tournament.game3)
        if (tournament.game1 is None):
            tournament.game1 = result
            tournament.save()
        elif (tournament.game2 is None):
            tournament.game2 = result
            winner1 = tournament.game1.player1 if tournament.game1.winner == 1 else tournament.game1.player2
            winner2 = tournament.game2.player1 if tournament.game2.winner == 1 else tournament.game2.player2
            GameInvite.objects.create(from_user = "tournament", to_user = winner1, from_user_id = winner2)
            GameInvite.objects.create(from_user = "tournament", to_user = winner2, from_user_id = winner1)
            tournament.save()
            channel_layer = get_channel_layer()
            room_name = '_'.join(str(winner1.id))
            room_group_name = 'notification_%s' % room_name
            message = 'You have an invitation to join tournament final game against %s, check your dashboard' % winner2.user.username
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'tournament_game_notification',
                    'message': message,
                }
            )
            room_name = '_'.join(str(winner2.id))
            room_group_name = 'notification_%s' % room_name
            message = 'You have an invitation to join tournament final game against %s, check your dashboard' % winner1.user.username
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'tournament_game_notification',
                    'message': message,
                }
            )
        elif (tournament.game3 is None):
            tournament.game3 = result
            tournament.save()
    all_records = Game.objects.all()
    print(all_records)

@database_sync_to_async
def get_user(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()



class PrivateGameConsumer(AsyncWebsocketConsumer):

    player = None
    players = {}
    # playerLen = 0
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
                # playerLen = len(PrivateGameConsumer.players)

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
                # print(PrivateGameConsumer.playerLen)
                async with self.update_lock:
                    PrivateGameConsumer.players[str(self.player.id)] = {
                        "room_group_name": self.room_group_name,
                        "playerNum": count,
                        "connected": True,
                        "paddleY": (self.canvas_height - self.paddle_height) / 2,
                        "upPressed": False,
                        "downPressed": False,
                        "score": 0,
                    }
                if count == 1:
                    
                    # print(opponent_index)
                    asyncio.create_task(self.game_loop(player1Id=opponent, player2Id=str(self.player.id)))
                    await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                "type": "game_start",
                            },
                        )
                
                # PrivateGameConsumer.playerLen += 1

                
            else:
                await self.close()
        else:
            await self.close()
        
        

    async def disconnect(self, close_code):
        async with self.update_lock:
            if str(self.player.id) in PrivateGameConsumer.players:
                PrivateGameConsumer.players[str(self.player.id)]["connected"] = False

        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )
        cache.set(self.room_group_name, cache.get(self.room_group_name) - 1)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "")
        if message_type == 'game_update':
            playerNum = text_data_json["playerNum"]
            player_index = next((index for index, player in PrivateGameConsumer.players.items() if player["room_group_name"] == self.room_group_name and player["playerNum"] == playerNum), None)
            PrivateGameConsumer.players[player_index]["upPressed"] = text_data_json["upPressed"]
            PrivateGameConsumer.players[player_index]["downPressed"] = text_data_json["downPressed"]
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
        
    async def game_loop(self, player1Id, player2Id):
        x = self.canvas_width / 2
        y = self.canvas_height / 2
        speed = 1.5
        angle1 = random.uniform(0.67 * math.pi, 0.8 * math.pi)
        angle2 = random.uniform(0.2 * math.pi, 0.33 * math.pi)
        angle = random.choice([angle1, angle2]) + random.choice([0, math.pi])
        dx = self.speed * math.sin(self.angle)
        dy = self.speed * math.cos(self.angle)
        while len(PrivateGameConsumer.players) > 1:
            await asyncio.sleep(0.01)
            async with self.update_lock:
                if (PrivateGameConsumer.players[str(player1Id)]["connected"] == False):
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "game_end",
                        },
                    )
                    channel_layer = get_channel_layer()
                    room_name = '_'.join(str(player2Id))
                    room_group_name = 'notification_%s' % room_name
                    message = 'Your opponent has disconnected'
                    await channel_layer.group_send(
                        room_group_name,
                        {
                            'type': 'opponent_disconnected_notification',
                            'message': message,
                        }
                    )
                    player1_id = int(player1Id)
                    player2_id = int(player2Id)
                    score1 = int(PrivateGameConsumer.players[str(player1Id)]["score"])
                    score2 = 3
                    await game_save(player1_id, player2_id, score1, score2)
                    del PrivateGameConsumer.players[str(player1_id)]
                    del PrivateGameConsumer.players[str(player2_id)]
                    break

                if (PrivateGameConsumer.players[str(player2Id)]["connected"] == False):
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "game_end",
                        },
                    )
                    channel_layer = get_channel_layer()
                    room_name = '_'.join(str(player1Id))
                    room_group_name = 'notification_%s' % room_name
                    message = 'Your opponent has disconnected'
                    await channel_layer.group_send(
                        room_group_name,
                        {
                            'type': 'opponent_disconnected_notification',
                            'message': message,
                        }
                    )
                    player1_id = int(player1Id)
                    player2_id = int(player2Id)
                    score1 = 3
                    score2 = int(PrivateGameConsumer.players[str(player2Id)]["score"])
                    await game_save(player1_id, player2_id, score1, score2)
                    del PrivateGameConsumer.players[str(player1_id)]
                    del PrivateGameConsumer.players[str(player2_id)]
                    break
                if (PrivateGameConsumer.players[player1Id]["score"] == 3 or PrivateGameConsumer.players[player2Id]["score"] == 3):
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "game_end",
                        },
                    )
                    channel_layer = get_channel_layer()
                    room_name = '_'.join(str(player1Id))
                    room_group_name = 'notification_%s' % room_name
                    result = 'won' if PrivateGameConsumer.players[str(player1_id)]["score"] > PrivateGameConsumer.players[str(player1Id)]["score"] else 'lost'
                    message = 'You %s the game against the opponent' % result
                    await channel_layer.group_send(
                        room_group_name,
                        {
                            'type': 'game_result_notification',
                            'message': message,
                        }
                    )
                    room_name = '_'.join(str(player2Id))
                    room_group_name = 'notification_%s' % room_name
                    result = 'won' if PrivateGameConsumer.players[str(player2Id)]["score"] > PrivateGameConsumer.players[str(player1Id)]["score"] else 'lost'
                    message = 'You %s the game against the opponent' % result
                    await channel_layer.group_send(
                        room_group_name,
                        {
                            'type': 'game_result_notification',
                            'message': message,
                        }
                    )
                    player1_id = int(player1Id)
                    player2_id = int(player2Id)
                    score1 = int(PrivateGameConsumer.players[str(player1Id)]["score"])
                    score2 = int(PrivateGameConsumer.players[str(player2Id)]["score"])
                    await game_save(player1_id, player2_id, score1, score2)
                    del PrivateGameConsumer.players[str(player1_id)]
                    del PrivateGameConsumer.players[str(player2_id)]
                    break
                if PrivateGameConsumer.players[player1Id]["upPressed"] and PrivateGameConsumer.players[player1Id]["paddleY"] > 0:
                    PrivateGameConsumer.players[player1Id]["paddleY"] -= 7
                elif PrivateGameConsumer.players[player1Id]["downPressed"] and PrivateGameConsumer.players[player1Id]["paddleY"] < self.canvas_height - self.paddle_height:
                    PrivateGameConsumer.players[player1Id]["paddleY"] += 7
                if PrivateGameConsumer.players[player2Id]["upPressed"] and PrivateGameConsumer.players[player2Id]["paddleY"] > 0:
                    PrivateGameConsumer.players[player2Id]["paddleY"] -= 7
                elif PrivateGameConsumer.players[player2Id]["downPressed"] and PrivateGameConsumer.players[player2Id]["paddleY"] < self.canvas_height - self.paddle_height:
                    PrivateGameConsumer.players[player2Id]["paddleY"] += 7
                if (y + dy > self.canvas_height - self.ball_radius or y + dy < self.ball_radius):
                    dy = -dy
                if (x + dx < self.ball_radius):
                    if (y > PrivateGameConsumer.players[player1Id]["paddleY"] and y < PrivateGameConsumer.players[player1Id]["paddleY"] + self.paddle_height):
                        dx = -dx * 1.05
                        dy = dy * 1.05
                    else:
                        PrivateGameConsumer.players[player1Id]["score"] += 1
                        x = self.canvas_width / 2
                        y = self.canvas_height / 2
                        angle1 = random.uniform(0.67 * math.pi, 0.8 * math.pi)
                        angle2 = random.uniform(0.2 * math.pi, 0.33 * math.pi)
                        angle = random.choice([angle1, angle2]) + random.choice([0, math.pi])
                        dx = self.speed * math.sin(angle)
                        dy = self.speed * math.cos(angle)  
                        PrivateGameConsumer.players[player1Id]["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                        PrivateGameConsumer.players[player2Id]["paddleY"] = (self.canvas_height - self.paddle_height) / 2

                elif (x + dx > self.canvas_width - self.ball_radius):
                    if (y > PrivateGameConsumer.players[player2Id]["paddleY"] and y < PrivateGameConsumer.players[player2Id]["paddleY"] + self.paddle_height):
                        dx = -dx * 1.05
                        dy = dy * 1.05
                    else:
                        PrivateGameConsumer.players[player2Id]["score"] += 1
                        x = self.canvas_width / 2
                        y = self.canvas_height / 2
                        angle1 = random.uniform(0.67 * math.pi, 0.8 * math.pi)
                        angle2 = random.uniform(0.2 * math.pi, 0.33 * math.pi)
                        angle = random.choice([angle1, angle2]) + random.choice([0, math.pi])
                        dx = self.speed * math.sin(angle)
                        dy = self.speed * math.cos(angle)
                        PrivateGameConsumer.players[player1Id]["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                        PrivateGameConsumer.players[player2Id]["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                x += dx
                y += dy

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "game_update",
                        "x": x,
                        "y": y,
                        "player1_paddleY": PrivateGameConsumer.players[player1Id]["paddleY"],
                        "player2_paddleY": PrivateGameConsumer.players[player2Id]["paddleY"],
                        "player1_score": PrivateGameConsumer.players[player1Id]["score"],
                        "player2_score": PrivateGameConsumer.players[player2Id]["score"],
                    },
                )



class MatchmakingConsumer(AsyncWebsocketConsumer):
    players = {}
    waiting_player = False
    waiting_player_id = None
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
                # playerLen = len(MatchmakingConsumer.players)
                # print(playerLen)
                if (MatchmakingConsumer.waiting_player == False):
                    self.room_group_name = 'matchmaking_%s' % str(self.player.id)
                    await self.channel_layer.group_add(
                        self.room_group_name,
                        self.channel_name
                    )
                    await self.send(
                        text_data=json.dumps({"type": "playerNum", "playerNum": 0})
                    )
                    async with self.update_lock:
                        MatchmakingConsumer.players[str(self.player.id)] = {
                            "room_group_name": self.room_group_name,
                            "connected": True,
                            "playerNum": 0,
                            "paddleY": (self.canvas_height - self.paddle_height) / 2,
                            "upPressed": False,
                            "downPressed": False,
                            "score": 0,
                        }
                    MatchmakingConsumer.waiting_player = True
                    MatchmakingConsumer.waiting_player_id = str(self.player.id)
                elif (MatchmakingConsumer.waiting_player == True):
                    opponent_index = MatchmakingConsumer.waiting_player_id
                    self.room_group_name = 'matchmaking_%s' % opponent_index
                    await self.channel_layer.group_add(
                        self.room_group_name,
                        self.channel_name
                    )
                    await self.send(
                        text_data=json.dumps({"type": "playerNum", "playerNum": 1})
                    )
                    async with self.update_lock:
                        MatchmakingConsumer.players[str(self.player.id)] = {
                            "room_group_name": self.room_group_name,
                            "connected": True,
                            "playerNum": 1,
                            "paddleY": (self.canvas_height - self.paddle_height) / 2,
                            "upPressed": False,
                            "downPressed": False,
                            "score": 0,
                        }
                    await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                "type": "game_start",
                            },
                        )
                    asyncio.create_task(self.game_loop(player1Id=opponent_index, player2Id=str(self.player.id)))
                    MatchmakingConsumer.waiting_player = False
                    MatchmakingConsumer.waiting_player_id = None
                else:
                    await self.close()
            else:
                await self.close()
        else:
            await self.close()
        
    async def disconnect(self, close_code):
        async with self.update_lock:
            if str(self.player.id) in MatchmakingConsumer.players:
                MatchmakingConsumer.players[str(self.player.id)]["connected"] = False
            if (self.waiting_player_id == str(self.player.id)):
                MatchmakingConsumer.waiting_player = False
                MatchmakingConsumer.waiting_player_id = None

        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "")
        if message_type == 'game_update':
            playerNum = text_data_json["playerNum"]
            player_index = next((index for index, player in MatchmakingConsumer.players.items() if player["room_group_name"] == self.room_group_name and player["playerNum"] == playerNum), None)
            MatchmakingConsumer.players[player_index]["upPressed"] = text_data_json["upPressed"]
            MatchmakingConsumer.players[player_index]["downPressed"] = text_data_json["downPressed"]
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
        

    async def game_loop(self, player1Id, player2Id):
        x = self.canvas_width / 2
        y = self.canvas_height / 2
        speed = 1.5
        angle1 = random.uniform(0.67 * math.pi, 0.8 * math.pi)
        angle2 = random.uniform(0.2 * math.pi, 0.33 * math.pi)
        angle = random.choice([angle1, angle2]) + random.choice([0, math.pi])
        dx = self.speed * math.sin(self.angle)
        dy = self.speed * math.cos(self.angle)
        while len(MatchmakingConsumer.players) > 1:
            await asyncio.sleep(0.01)
            async with self.update_lock:
                if (MatchmakingConsumer.players[player1Id]["connected"] == False):
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "game_end",
                        },
                    )
                    channel_layer = get_channel_layer()
                    room_name = '_'.join(str(player2Id))
                    room_group_name = 'notification_%s' % room_name
                    message = 'Your opponent has disconnected'
                    await channel_layer.group_send(
                        room_group_name,
                        {
                            'type': 'opponent_disconnected_notification',
                            'message': message,
                        }
                    )
                    player1_id = int(player1Id)
                    player2_id = int(player2Id)
                    score1 = int(MatchmakingConsumer.players[player1Id]["score"])
                    score2 = 3
                    await game_save(player1_id, player2_id, score1, score2)
                    del MatchmakingConsumer.players[player1Id]
                    del MatchmakingConsumer.players[player2Id]
                    break

                if (MatchmakingConsumer.players[player2Id]["connected"] == False):
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "game_end",
                        },
                    )
                    channel_layer = get_channel_layer()
                    room_name = '_'.join(str(player1Id))
                    room_group_name = 'notification_%s' % room_name
                    message = 'Your opponent has disconnected'
                    await channel_layer.group_send(
                        room_group_name,
                        {
                            'type': 'opponent_disconnected_notification',
                            'message': message,
                        }
                    )
                    player1_id = int(player1Id)
                    player2_id = int(player2Id)
                    score1 = 3
                    score2 = int(MatchmakingConsumer.players[player2Id]["score"])
                    await game_save(player1_id, player2_id, score1, score2)
                    del MatchmakingConsumer.players[player1Id]
                    del MatchmakingConsumer.players[player2Id]
                    break

                if (MatchmakingConsumer.players[player1Id]["score"] == 3 or MatchmakingConsumer.players[player2Id]["score"] == 3):
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "game_end",
                        },
                    )
                    channel_layer = get_channel_layer()
                    room_name = '_'.join(str(player1Id))
                    room_group_name = 'notification_%s' % room_name
                    result = 'won' if MatchmakingConsumer.players[player1Id]["score"] > MatchmakingConsumer.players[player2Id]["score"] else 'lost'
                    message = 'You %s the game against %s' % (result, player2Id)
                    await channel_layer.group_send(
                        room_group_name,
                        {
                            'type': 'game_result_notification',
                            'message': message,
                        }
                    )
                    room_name = '_'.join(str(player2Id))
                    room_group_name = 'notification_%s' % room_name
                    result = 'won' if MatchmakingConsumer.players[player2Id]["score"] > MatchmakingConsumer.players[player1Id]["score"] else 'lost'
                    message = 'You %s the game against %s' % (result, player1Id)
                    await channel_layer.group_send(
                        room_group_name,
                        {
                            'type': 'game_result_notification',
                            'message': message,
                        }
                    )
                    player1_id =int(player1Id)
                    player2_id = int(player2Id)
                    score1 = int(MatchmakingConsumer.players[player1Id]["score"])
                    score2 = int(MatchmakingConsumer.players[player2Id]["score"])
                    await game_save(player1_id, player2_id, score1, score2)
                    del MatchmakingConsumer.players[player1Id]
                    del MatchmakingConsumer.players[player2Id]
                    break

                if MatchmakingConsumer.players[player1Id]["upPressed"] and MatchmakingConsumer.players[player1Id]["paddleY"] > 0:
                    MatchmakingConsumer.players[player1Id]["paddleY"] -= 10
                elif MatchmakingConsumer.players[player1Id]["downPressed"] and MatchmakingConsumer.players[player1Id]["paddleY"] < self.canvas_height - self.paddle_height:
                    MatchmakingConsumer.players[player1Id]["paddleY"] += 10
                if MatchmakingConsumer.players[player2Id]["upPressed"] and MatchmakingConsumer.players[player2Id]["paddleY"] > 0:
                    MatchmakingConsumer.players[player2Id]["paddleY"] -= 10
                elif MatchmakingConsumer.players[player2Id]["downPressed"] and MatchmakingConsumer.players[player2Id]["paddleY"] < self.canvas_height - self.paddle_height:
                    MatchmakingConsumer.players[player2Id]["paddleY"] += 10
                if (y + dy > self.canvas_height - self.ball_radius or y + dy < self.ball_radius):
                    dy = -dy
                if (x + dx < self.ball_radius):
                    if (y > MatchmakingConsumer.players[player1Id]["paddleY"] and y < MatchmakingConsumer.players[player1Id]["paddleY"] + self.paddle_height):
                        dx = -dx * 1.05
                        dy = dy * 1.05
                    else:
                        MatchmakingConsumer.players[player2Id]["score"] += 1
                        x = self.canvas_width / 2
                        y = self.canvas_height / 2
                        angle1 = random.uniform(0.67 * math.pi, 0.8 * math.pi)
                        angle2 = random.uniform(0.2 * math.pi, 0.33 * math.pi)
                        angle = random.choice([angle1, angle2]) + random.choice([0, math.pi])
                        dx = self.speed * math.sin(self.angle)
                        dy = self.speed * math.cos(self.angle)
                        MatchmakingConsumer.players[player1Id]["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                        MatchmakingConsumer.players[player2Id]["paddleY"] = (self.canvas_height - self.paddle_height) / 2

                elif (x + dx > self.canvas_width - self.ball_radius):
                    if (y > MatchmakingConsumer.players[player2Id]["paddleY"] and y < MatchmakingConsumer.players[player2Id]["paddleY"] + self.paddle_height):
                        dx = -dx * 1.05
                        dy = dy * 1.05
                    else:
                        MatchmakingConsumer.players[player1Id]["score"] += 1
                        x = self.canvas_width / 2
                        y = self.canvas_height / 2
                        angle1 = random.uniform(0.67 * math.pi, 0.8 * math.pi)
                        angle2 = random.uniform(0.2 * math.pi, 0.33 * math.pi)
                        angle = random.choice([angle1, angle2]) + random.choice([0, math.pi])
                        dx = self.speed * math.sin(self.angle)
                        dy = self.speed * math.cos(self.angle)
                        MatchmakingConsumer.players[player1Id]["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                        MatchmakingConsumer.players[player2Id]["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                x += dx
                y += dy

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "game_update",
                        "x": x,
                        "y": y,
                        "player1_paddleY": MatchmakingConsumer.players[player1Id]["paddleY"],
                        "player2_paddleY": MatchmakingConsumer.players[player2Id]["paddleY"],
                        "player1_score": MatchmakingConsumer.players[player1Id]["score"],
                        "player2_score": MatchmakingConsumer.players[player2Id]["score"],
                    },
                )
                
class AIConsumer(AsyncWebsocketConsumer):
    player = None
    bot = None
    ball_radius = 10
    paddle_height = 75
    canvas_width = 480
    canvas_height = 480
    x = 0
    y = 0
    speed = 0
    angle = 0

    update_lock = asyncio.Lock()

    async def connect(self):
        query_string = parse_qs(self.scope['query_string'].decode())
        token_key = query_string.get('token')

        if token_key:
            self.user = await get_user(token_key[0])
            if self.user.is_authenticated:
                await self.accept()
                await self.send(
                    text_data=json.dumps({"type": "playerNum", "playerNum": 0})
                )
                async with self.update_lock:
                    self.player = {
                        "playerNum": 0,
                        "connected": True,
                        "paddleY": (self.canvas_height - self.paddle_height) / 2,
                        "upPressed": False,
                        "downPressed": False,
                        "score": 0,
                    }
                async with self.update_lock:
                    self.bot = {
                        "playerNum": 1,
                        "paddleY": (self.canvas_height - self.paddle_height) / 2,
                        "upPressed": False,
                        "downPressed": False,
                        "score": 0,
                    }
                asyncio.create_task(self.game_loop())
                await self.send(
                    text_data=json.dumps({"type": "game_start"})
                )

            else:
                await self.close()
        else:
            await self.close()
        
        

    async def disconnect(self, close_code):
        async with self.update_lock:
            self.player["connected"] = False

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "")
        if message_type == 'game_update':
            
            self.player["upPressed"] = text_data_json["upPressed"]
            self.player["downPressed"] = text_data_json["downPressed"]
        else:
            pass

    bot_error = 0
    calc_y = 0
    calc_dx = 0
    move = False

    async def bot_update(self):
        previous_y = self.y
        previous_x = self.x
        previous_dx = 0
        previous_dy = 0
        # dx = 0
        # dy = 0
        while True:
            await asyncio.sleep(1)
            async with self.update_lock:
                if (self.player["connected"] == False or self.player["score"] == 3 or self.bot["score"] == 3):
                    break
            # if (dx == 0 and dy == 0):
            #     dx = self.x - previous_x
            #     dy = self.y - previous_y
            # dx = self.x - previous_x if dx >= previous_dx else previous_dx
            # dy = self.y - previous_y if dy >= previous_dy else previous_dy
            # previous_dx = dx if dx >= previous_dx else previous_dx
            # previous_dy = dy if dy >= previous_dy else previous_dy
            dx = self.x - previous_x
            if previous_dy > 0 and self.y < previous_dy:
                dy = previous_dy
            elif previous_dy < 0 and self.canvas_height - self.y < abs(previous_dy):
                dy = previous_dy
            else:
                dy = self.y - previous_y
            # previous_dx = dx
            previous_dy = dy
            previous_x = self.x
            previous_y = self.y
            x = self.x
            y = self.y
            if dx > 0:
                distance_x = self.canvas_width - x
                time_x = distance_x / dx
                while True:
                    distance_y = self.canvas_height - y if dy > 0 else y
                    time_y = distance_y / abs(dy)                                             
                    if time_y < time_x:
                        x = x + dx * time_y
                        y = self.canvas_height - self.ball_radius if dy > 0 else self.ball_radius
                        dy = -dy
                        distance_x = self.canvas_width - x
                        time_x = distance_x / dx
                        continue
                    else:
                        y = y + dy * time_x + self.bot_error
                        self.calc_y = y
                        self.move = True
                        # self.bot_error = self.bot_error / 2
                        break
            else:
                self.move = False
                pass
                # self.bot_error = random.uniform(-100, 100)
            
    async def bot_move(self):
        asyncio.create_task(self.bot_update())
        while True:
            await asyncio.sleep(0.01)
            async with self.update_lock:
                if (self.player["connected"] == False or self.player["score"] == 3 or self.bot["score"] == 3):
                    break
                print(self.calc_y)
                if self.move == True:
                    if self.calc_y < self.bot["paddleY"]:
                        self.bot["upPressed"] = True
                        self.bot["downPressed"] = False
                    elif self.calc_y > self.bot["paddleY"] + self.paddle_height / 3 and self.calc_y < self.bot["paddleY"] + self.paddle_height * 2 / 3:
                        self.bot["upPressed"] = False
                        self.bot["downPressed"] = False
                    elif self.calc_y > self.bot["paddleY"] + self.paddle_height :
                        self.bot["upPressed"] = False
                        self.bot["downPressed"] = True
                else:
                    self.bot["upPressed"] = False
                    self.bot["downPressed"] = False


    async def game_loop(self):
        self.x = self.canvas_width / 2
        self.y = self.canvas_height / 2
        self.speed = 1.5
        angle1 = random.uniform(0.67 * math.pi, 0.8 * math.pi)
        angle2 = random.uniform(0.2 * math.pi, 0.33 * math.pi)
        self.angle = random.choice([angle1, angle2]) + random.choice([0, math.pi])
        dx = self.speed * math.sin(self.angle)
        dy = self.speed * math.cos(self.angle)
        asyncio.create_task(self.bot_move())
        while self.player is not None and self.bot is not None:
            await asyncio.sleep(0.01)
            async with self.update_lock:
                if (self.player["connected"] == False):
                    player = None
                    bot = None
                    break
                if (self.player["score"] == 3 or self.bot["score"] == 3):
                    await self.send(
                    text_data=json.dumps(
                        {
                        "type": "game_end",
                        }
                    )
                    )
                    result = 'won' if self.player["score"] > self.bot["score"] else 'lost'
                    channel_layer = get_channel_layer()
                    room_name = '_'.join(str(self.user.id))
                    room_group_name = 'notification_%s' % room_name
                    message = 'You %s the game against AI' % result
                    await channel_layer.group_send(
                        room_group_name,
                        {
                            'type': 'game_result_notification',
                            'message': message,
                        }
                    )
                    await asyncio.sleep(0.01)
                    player = None
                    bot = None
                    break
            if self.player["upPressed"] and self.player["paddleY"] > 0:
                self.player["paddleY"] -= 7
            elif self.player["downPressed"] and self.player["paddleY"] < self.canvas_height - self.paddle_height:
                self.player["paddleY"] += 7
            if self.bot["upPressed"] and self.bot["paddleY"] > 0:
                self.bot["paddleY"] -= 7
            elif self.bot["downPressed"] and self.bot["paddleY"] < self.canvas_height - self.paddle_height:
                self.bot["paddleY"] += 7
            if (self.y + dy > self.canvas_height - self.ball_radius or self.y + dy < self.ball_radius):
                dy = -dy
            if (self.x + dx < self.ball_radius):
                if (self.y > self.player["paddleY"] and self.y < self.player["paddleY"] + self.paddle_height):
                    dx = -dx * 1.05
                    dy = dy * 1.05
                else:
                    self.bot["score"] += 1
                    self.x = self.canvas_width / 2
                    self.y = self.canvas_height / 2
                    angle1 = random.uniform(0.67 * math.pi, 0.8 * math.pi)
                    angle2 = random.uniform(0.2 * math.pi, 0.33 * math.pi)
                    self.angle = random.choice([angle1, angle2]) + random.choice([0, math.pi])
                    dx = self.speed * math.sin(self.angle)
                    dy = self.speed * math.cos(self.angle)
                    self.player["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                    self.bot["paddleY"] = (self.canvas_height - self.paddle_height) / 2

            elif (self.x + dx > self.canvas_width - self.ball_radius):
                if (self.y > self.bot["paddleY"] and self.y < self.bot["paddleY"] + self.paddle_height):
                    dx = -dx * 1.05
                    dy = dy * 1.05
                else:
                    self.player["score"] += 1
                    self.x = self.canvas_width / 2
                    self.y = self.canvas_height / 2
                    angle1 = random.uniform(0.67 * math.pi, 0.8 * math.pi)
                    angle2 = random.uniform(0.2 * math.pi, 0.33 * math.pi)
                    self.angle = random.choice([angle1, angle2]) + random.choice([0, math.pi])
                    dx = self.speed * math.sin(self.angle)
                    dy = self.speed * math.cos(self.angle)
                    self.player["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                    self.bot["paddleY"] = (self.canvas_height - self.paddle_height) / 2
            self.x += dx
            self.y += dy
            await self.send(
                text_data=json.dumps(
                {
                    "type": "game_update",
                    "x": self.x,
                    "y": self.y,
                    "player1_paddleY": self.player["paddleY"],
                    "player2_paddleY": self.bot["paddleY"],
                    "player1_score": self.player["score"],
                    "player2_score": self.bot["score"],
                }
                )
            )
