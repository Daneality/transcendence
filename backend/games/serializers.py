from rest_framework import serializers
from games.models import Game
from django.contrib.auth.models import User
from user.models import Profile
from django.apps import apps

Tournament = apps.get_model('games', 'Tournament')

class GameSerializer(serializers.ModelSerializer):
    player1 = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all(), read_only=False, write_only=True)
    player2 = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all(), read_only=False, write_only=True)
    winner = serializers.IntegerField(write_only=True)
    is_winner = serializers.SerializerMethodField()
    opponent_id = serializers.SerializerMethodField()
    opponent_username = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ['player1', 'player2', 'winner', 'created','id', 'p1_score','p2_score', 'is_winner', 'opponent_id', 'opponent_username']

    def get_is_winner(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if obj.winner == 1 and obj.player1.user == request.user:
                return True
            elif obj.winner == 2 and obj.player2.user == request.user:
                return True
        return False
    
    def get_opponent_id(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if obj.player1.user == request.user:
                return obj.player2.user.id
            elif obj.player2.user == request.user:
                return obj.player1.user.id
        return None

    def get_opponent_username(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if obj.player1.user == request.user:
                return obj.player2.user.username
            elif obj.player2.user == request.user:
                return obj.player1.user.username
        return None
    


class TournamentSerializer(serializers.ModelSerializer):
    game1 = GameSerializer(read_only=True)
    game2 = GameSerializer(read_only=True)
    game3 = GameSerializer(read_only=True)

    class Meta:
        model = Tournament
        fields = ['id', 'created', 'name', 'game1', 'game2', 'game3']
        read_only_fields = ['name']