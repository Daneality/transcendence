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
        elif (tournament.game2 is None):
            tournament.game2 = result
            winner1 = tournament.game1.player1 if tournament.game1.winner == 1 else tournament.game1.player2
            winner2 = tournament.game2.player1 if tournament.game2.winner == 1 else tournament.game2.player2
            GameInvite.objects.create(from_user = "tournament", to_user = winner1, from_user_id = winner2)
            GameInvite.objects.create(from_user = "tournament", to_user = winner2, from_user_id = winner1)
            channel_layer = get_channel_layer()
            room_name = '_'.join(str(players1.id))
            room_group_name = 'notification_%s' % room_name
            message = 'You have an invitation to join tournament final game against %s, check your dashboard' % players2.user.username
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'tournament_game_notification',
                    'message': message,
                }
            )
            room_name = '_'.join(str(players2.id))
            room_group_name = 'notification_%s' % room_name
            message = 'You have an invitation to join tournament final game against %s, check your dashboard' % players1.user.username
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
                del PrivateGameConsumer.players[str(self.player.id)]
            # print(PrivateGameConsumer.players)

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
        angle = random.uniform(0, 2 * math.pi)
        dx = speed * math.cos(angle)
        dy = speed * math.sin(angle)
        if abs(dx) < abs(dy):
            dx, dy = dy, dx
        while len(PrivateGameConsumer.players) > 1:
            await asyncio.sleep(0.01)
            async with self.update_lock:
                if (PrivateGameConsumer.players[player1Id]["score"] == 1 or PrivateGameConsumer.players[player2Id]["score"] == 1):
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "game_end",
                        },
                    )
                    player1_id = int(player1Id)
                    player2_id = int(player2Id)
                    score1 = int(PrivateGameConsumer.players[player1Id]["score"])
                    score2 = int(PrivateGameConsumer.players[player2Id]["score"])
                    await game_save(player1_id, player2_id, score1, score2)
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
                        PrivateGameConsumer.players[player2Id]["score"] += 1
                        x = self.canvas_width / 2
                        y = self.canvas_height / 2
                        angle = random.uniform(0, 2 * math.pi)
                        dx = speed * math.cos(angle)
                        dy = speed * math.sin(angle)
                        if abs(dx) < abs(dy):
                            dx, dy = dy, dx
                        PrivateGameConsumer.players[player1Id]["paddleY"] = (self.canvas_height - self.paddle_height) / 2
                        PrivateGameConsumer.players[player2Id]["paddleY"] = (self.canvas_height - self.paddle_height) / 2

                elif (x + dx > self.canvas_width - self.ball_radius):
                    if (y > PrivateGameConsumer.players[player2Id]["paddleY"] and y < PrivateGameConsumer.players[player2Id]["paddleY"] + self.paddle_height):
                        dx = -dx * 1.05
                        dy = dy * 1.05
                    else:
                        PrivateGameConsumer.players[player1Id]["score"] += 1
                        x = self.canvas_width / 2
                        y = self.canvas_height / 2
                        angle = random.uniform(0, 2 * math.pi)
                        dx = speed * math.cos(angle)
                        dy = speed * math.sin(angle)
                        if abs(dx) < abs(dy):
                            dx, dy = dy, dx
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
    playerLen = 0
    waiting_player = False
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
                if (MatchmakingConsumer.playerLen == 0 or MatchmakingConsumer.waiting_player == False):
                    self.room_group_name = 'matchmaking_%s' % str(self.player.id)
                    await self.channel_layer.group_add(
                        self.room_group_name,
                        self.channel_name
                    )
                    await self.send(
                        text_data=json.dumps({"type": "playerNum", "playerNum": 0})
                    )
                    async with self.update_lock:
                        MatchmakingConsumer.players[MatchmakingConsumer.playerLen] = {
                            "userId": str(self.player.id),
                            "room_group_name": self.room_group_name,
                            "playerNum": 0,
                            "paddleY": (self.canvas_height - self.paddle_height) / 2,
                            "upPressed": False,
                            "downPressed": False,
                            "score": 0,
                        }
                    MatchmakingConsumer.playerLen += 1
                    MatchmakingConsumer.waiting_player = True
                elif (MatchmakingConsumer.playerLen > 0 and MatchmakingConsumer.waiting_player == True):
                    opponent_index = MatchmakingConsumer.playerLen - 1
                    self.room_group_name = 'matchmaking_%s' % MatchmakingConsumer.players[opponent_index]["userId"]
                    await self.channel_layer.group_add(
                        self.room_group_name,
                        self.channel_name
                    )
                    await self.send(
                        text_data=json.dumps({"type": "playerNum", "playerNum": 1})
                    )
                    async with self.update_lock:
                        MatchmakingConsumer.players[MatchmakingConsumer.playerLen] = {
                            "userId": str(self.player.id),
                            "room_group_name": self.room_group_name,
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
                    asyncio.create_task(self.game_loop(player1Id=opponent_index, player2Id=MatchmakingConsumer.playerLen))
                    MatchmakingConsumer.playerLen += 1
                    MatchmakingConsumer.waiting_player = False
                else:
                    await self.close()
            else:
                await self.close()
        else:
            await self.close()
        
    async def disconnect(self, close_code):
        async with self.update_lock:
            for player_id, player in MatchmakingConsumer.players.items():
                if player["userId"] == str(self.player.id):
                    del MatchmakingConsumer.players[player_id]
                    break

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
        angle = random.uniform(0, 2 * math.pi)
        dx = speed * math.cos(angle)
        dy = speed * math.sin(angle)
        if abs(dx) < abs(dy):
            dx, dy = dy, dx
        while len(MatchmakingConsumer.players) > 1:
            await asyncio.sleep(0.01)
            async with self.update_lock:
                if (MatchmakingConsumer.players[player1Id]["score"] == 3 or MatchmakingConsumer.players[player2Id]["score"] == 3):
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "game_end",
                        },
                    )
                    # print("Game Ended")
                    player1_id =int(MatchmakingConsumer.players[player1Id]["userId"])
                    player2_id = int(MatchmakingConsumer.players[player2Id]["userId"])
                    score1 = int(MatchmakingConsumer.players[player1Id]["score"])
                    score2 = int(MatchmakingConsumer.players[player2Id]["score"])
                    await game_save(player1_id, player2_id, score1, score2)
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
                        angle = random.uniform(0, 2 * math.pi)
                        dx = speed * math.cos(angle)
                        dy = speed * math.sin(angle)
                        if abs(dx) < abs(dy):
                            dx, dy = dy, dx
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
                        angle = random.uniform(0, 2 * math.pi)
                        dx = speed * math.cos(angle)
                        dy = speed * math.sin(angle)
                        if abs(dx) < abs(dy):
                            dx, dy = dy, dx
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