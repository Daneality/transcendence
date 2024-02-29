from rest_framework import serializers
from django.contrib.auth.models import User
from games.serializers import GameSerializer

class UserSerializer(serializers.ModelSerializer):
    games_as_player1 = GameSerializer(many=True, read_only=True)
    games_as_player2 = GameSerializer(many=True, read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'games_as_player1', 'games_as_player2']