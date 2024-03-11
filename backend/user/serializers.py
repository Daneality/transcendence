from rest_framework import serializers
from django.contrib.auth.models import User
from games.serializers import GameSerializer
from .models import Profile
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from . models import FriendRequest
from rest_framework import status

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



class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Profile.objects.all())
    to_user = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Profile.objects.all())
    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'to_user', 'created']
        read_only_fields = ['created', 'id']

    def validate(self, data):
        if 'from_user' in data and data['from_user'] == data['to_user']:
            raise serializers.ValidationError("A user cannot send a friend request to themselves.")
        if 'from_user' in data and FriendRequest.objects.filter(from_user=data['from_user'], to_user=data['to_user']).exists():
            raise serializers.ValidationError("A friend request from this user to the recipient already exists.")
        if 'from_user' in data and 'to_user' in data and data['from_user'].friends.filter(id=data['to_user'].id).exists():
            raise serializers.ValidationError("These users are already friends.")
        return data
    
class ProfileSerializer(serializers.ModelSerializer):
    games = serializers.SerializerMethodField()
    image = serializers.ImageField(max_length=None, use_url=True)
    to_user = FriendRequestSerializer(many=True)
    friends = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        fields = ['games_lost', 'games_won', 'friends', 'blocked_users', 'games', 'image', 'to_user']

    def get_games(self, obj):
        games_as_player1 = GameSerializer(obj.games_as_player1.all(), many=True).data
        games_as_player2 = GameSerializer(obj.games_as_player2.all(), many=True).data
        return sorted(games_as_player1 + games_as_player2, key=lambda game: game['created'], reverse=True)
    
    def get_friends(self, obj):  # Add this method
        return [{'id': friend.id, 'username': friend.username} for friend in obj.friends.all()]
    
class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']