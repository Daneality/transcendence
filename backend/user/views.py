from django.shortcuts import render
from django.contrib.auth.models import User
from user.serializers import UserSerializer, GameInviteSerializer
from rest_framework import generics
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer
from django.shortcuts import get_object_or_404
from .serializers import ProfileSerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from . models import FriendRequest, GameInvite
from . serializers import FriendRequestSerializer
from chat.models import Chat
from rest_framework.exceptions import ValidationError


# Create your views here.
class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs.get('pk'))

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if (request.user.id != user.id):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if serializer.is_valid():
            serializer.save()
            if 'image' in request.FILES:
                profile_serializer = ProfileSerializer(user.profile, data={'image': request.FILES['image']}, partial=True)
                if profile_serializer.is_valid():
                    profile_serializer.save()
                else:
                    return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            if user:
                token = Token.objects.create(user=user)
                return Response({'token': str(token), 'user' : UserSerializer(user).data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': str(token), 'user' : UserSerializer(user).data}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid username or password'}, status=status.HTTP_400_BAD_REQUEST)

class FriendRequestListCreate(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer

    def create(self, request, *args, **kwargs):
        if 'from_user' in request.data and request.data['from_user'] != request.user.id:
            return Response({"message": "You do not have permission to create this friend request."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

class FriendRequestAcceptView(generics.UpdateAPIView):
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


    def update(self, request, *args, **kwargs):
        friend_request = self.get_object()
        if friend_request.to_user.id != request.user.id:
            return Response({"message": "You do not have permission to accept this friend request."}, status=status.HTTP_403_FORBIDDEN)
        friend_request.from_user.friends.add(friend_request.to_user.user)
        friend_request.to_user.friends.add(friend_request.from_user.user)
        chat = Chat.objects.create(participant1=friend_request.from_user.user, participant2=friend_request.to_user.user)
        reverse_friend_request = FriendRequest.objects.filter(from_user=friend_request.to_user, to_user=friend_request.from_user)
        if reverse_friend_request.exists():
            reverse_friend_request.delete()
        friend_request.delete()
        return Response({"message": f"You have successfully accepted request."},status=status.HTTP_200_OK)
    
class UserBlockView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


    def update(self, request, *args, **kwargs):
        user_to_block = self.get_object()
        if request.user == user_to_block:
            return Response({"message": "You cannot block yourself."}, status=status.HTTP_400_BAD_REQUEST)

        # Add the user to the blocked_users of the authenticated user
        request.user.profile.blocked_users.add(user_to_block)

        return Response({"message": f"You have successfully blocked {user_to_block.username}."}, status=status.HTTP_200_OK)
    
class UserUnblockView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user_to_unblock = self.get_object()

        # Check if the user is in the blocked_users of the authenticated user
        if user_to_unblock not in request.user.profile.blocked_users.all():
            return Response({"message": "This user is not in your blocked users list."}, status=status.HTTP_400_BAD_REQUEST)

        # Remove the user from the blocked_users of the authenticated user
        request.user.profile.blocked_users.remove(user_to_unblock)

        return Response({"message": f"You have successfully unblocked {user_to_unblock.username}."}, status=status.HTTP_200_OK)
    
class GameInviteCreateView(generics.CreateAPIView):
    queryset = GameInvite.objects.all()
    serializer_class = GameInviteSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        from_user = self.request.user.profile
        to_user = serializer.validated_data['to_user']

        if from_user == to_user:
            raise ValidationError('You cannot invite yourself')

        if GameInvite.objects.filter(from_user=from_user, to_user=to_user).exists():
            raise ValidationError('You have already sent an invite to this user')

        serializer.save(from_user=from_user.user.username, from_user_id=from_user, to_user=to_user)