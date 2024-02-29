from rest_framework import serializers
from games.models import Game
from django.contrib.auth.models import User

class GameSerializer(serializers.ModelSerializer):
    player1 = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    player2 = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = Game
        fields = ['created','id', 'p1_score','p2_score', 'winner', 'player1', 'player2']

