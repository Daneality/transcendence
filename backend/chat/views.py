from django.shortcuts import render
from user.models import User
from .models import Chat
from .serializers import ChatSerializerList, ChatSerializer
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated



# Create your views here.
class ChatListView(generics.ListAPIView):
    serializer_class = ChatSerializerList
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(participant1=user) | Chat.objects.filter(participant2=user)
    
class ChatDetailView(generics.RetrieveAPIView):
    serializer_class = ChatSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user1 = self.request.user
        user2 = User.objects.get(pk=self.kwargs['pk'])
        return (Chat.objects.filter(participant1=user1, participant2=user2) | Chat.objects.filter(participant1=user2, participant2=user1)).first()