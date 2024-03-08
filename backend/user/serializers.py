from rest_framework import serializers
from django.contrib.auth.models import User
from games.serializers import GameSerializer
from .models import Profile
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=get_user_model().objects.all())]
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=get_user_model().objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True},
            'password2': {'write_only': True},
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords must match")
        return data

    def create(self, validated_data):
        validated_data.pop('password2', None) # Remove the password2 field
        user = get_user_model().objects.create_user(**validated_data)
        Profile.objects.create(user=user, games_lost=0, games_won=0)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    games = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['games_lost', 'games_won', 'friends', 'blocked_users', 'games']

    def get_games(self, obj):
        games_as_player1 = GameSerializer(obj.games_as_player1.all(), many=True).data
        games_as_player2 = GameSerializer(obj.games_as_player2.all(), many=True).data
        return sorted(games_as_player1 + games_as_player2, key=lambda game: game['created'], reverse=True)

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']