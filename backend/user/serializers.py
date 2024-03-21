from rest_framework import serializers
from django.contrib.auth.models import User
from games.serializers import GameSerializer
from .models import Profile
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from . models import FriendRequest
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

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
        fields = ['username', 'email', 'password', 'password2',]
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
        request = self.context.get('request')
        user = get_user_model().objects.create_user(**validated_data)
        Profile.objects.create(user=user, image="images/default.jpg", games_lost=0, games_won=0)
        return user



class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Profile.objects.all())
    to_user = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Profile.objects.all())
    from_user_username = serializers.SerializerMethodField()

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user' ,'from_user_username', 'to_user', 'created']
        read_only_fields = ['created', 'id']

    def validate(self, data):
        if 'from_user' in data and data['from_user'] == data['to_user']:
            raise serializers.ValidationError("A user cannot send a friend request to themselves.")
        if 'from_user' in data and FriendRequest.objects.filter(from_user=data['from_user'], to_user=data['to_user']).exists():
            raise serializers.ValidationError("A friend request from this user to the recipient already exists.")
        if 'from_user' in data and 'to_user' in data and data['from_user'].friends.filter(id=data['to_user'].id).exists():
            raise serializers.ValidationError("These users are already friends.")
        return data
    
    def get_from_user_username(self, obj):
        return obj.from_user.user.username
    
class ProfileSerializer(serializers.ModelSerializer):
    games = serializers.SerializerMethodField()
    image = serializers.ImageField(max_length=None, use_url=True)
    to_user = FriendRequestSerializer(many=True)
    friends = serializers.SerializerMethodField()
    is_current_user = serializers.SerializerMethodField()
    already_sent_request = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()


    class Meta:
        model = Profile
        fields = ['games_lost', 'games_won', 'friends', 'blocked_users', 'games', 'image', 'to_user', 'is_current_user', 'already_sent_request', 'is_online']

    def get_games(self, obj):
        games_as_player1 = GameSerializer(obj.games_as_player1.all(), many=True, context=self.context).data
        games_as_player2 = GameSerializer(obj.games_as_player2.all(), many=True, context=self.context).data
        return sorted(games_as_player1 + games_as_player2, key=lambda game: game['created'], reverse=True)
    
    def get_friends(self, obj):  # Add this method
        return [{'id': friend.id, 'username': friend.username} for friend in obj.friends.all()]

    def get_is_current_user(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.user == request.user
        return False
    
    def get_already_sent_request(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if obj.user in request.user.profile.friends.all():
                return True
            return FriendRequest.objects.filter(from_user=request.user.profile, to_user=obj.user.profile).exists()
        return False

    def get_is_online(self, obj):
        if obj.last_activity:
            return timezone.now() - obj.last_activity < timedelta(minutes=1)
        return False

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False)


    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile', ]

    
    def validate_password(self, value):
        validate_password(value)
        return value

    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password is not None:
            user.set_password(password)
            user.save()

        return user