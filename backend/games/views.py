from games.models import Game, Tournament
from games.serializers import GameSerializer, TournamentSerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import NotFound
from user.models import GameInvite
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class GameList(APIView):
    """
    List all snippets, or create a new snippet.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        snippets = Game.objects.all()
        serializer = GameSerializer(snippets, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = GameSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class GameDetail(APIView):
    """
    Retrieve, update or delete a snippet instance.
    """
    permission_classes = [permissions.IsAuthenticated]


    def get_object(self, pk):
        try:
            return Game.objects.get(pk=pk)
        except Game.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = GameSerializer(snippet)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = GameSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        snippet = self.get_object(pk)
        snippet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class TournamentCreateView(generics.ListCreateAPIView, generics.DestroyAPIView):
    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile = self.request.user.profile
        if profile.tournament is None:
            raise NotFound('You are not registered in a tournament')
        return profile.tournament

    def perform_create(self, serializer):
        profile = self.request.user.profile
        if profile.tournament is not None:
            raise ValidationError('You are already registered in a tournament')

        tournament = serializer.save(name=self.request.user.username)
        profile.tournament = tournament
        profile.save()
    
    def destroy(self, request, *args, **kwargs):
        profile = self.request.user.profile
        tournament = self.get_object()
        profile.tournament = None
        profile.save()
        if not tournament.players.exists():
            tournament.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TournamentRegisterView(generics.UpdateAPIView):
    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        profile = self.request.user.profile

        if profile.tournament is not None:
            raise ValidationError('You are already registered in a tournament')

        tournament = self.get_object()
        if tournament.players.count() >= 4:
            raise ValidationError('This tournament has already started')
        profile.tournament = tournament
        profile.save()

        channel_layer = get_channel_layer()

        if tournament.players.count() == 4:
            
            players = list(tournament.players.all())
            GameInvite.objects.filter(to_user__in=players).delete()
            GameInvite.objects.create(to_user=players[1], from_user = "Tournament", from_user_id = players[0])
            GameInvite.objects.create(to_user=players[0], from_user = "Tournament", from_user_id = players[1])
            GameInvite.objects.create(to_user=players[3], from_user = "Tournament", from_user_id = players[2])
            GameInvite.objects.create(to_user=players[2], from_user = "Tournament", from_user_id = players[3])
            channel_layer = get_channel_layer()
            room_name = '_'.join(str(players[0].id))
            room_group_name = 'notification_%s' % room_name
            message = 'You have an invitation to join tournament game against %s, check your dashboard' % players[1].user.username
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'tournament_game_notification',
                    'message': message,
                }
            )
            room_name = '_'.join(str(players[1].id))
            room_group_name = 'notification_%s' % room_name
            message = 'You have an invitation to join tournament game against %s, check your dashboard' % players[0].user.username
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'tournament_game_notification',
                    'message': message,
                }
            )
            room_name = '_'.join(str(players[2].id))
            room_group_name = 'notification_%s' % room_name
            message = 'You have an invitation to join tournament game against %s, check your dashboard' % players[3].user.username
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'tournament_game_notification',
                    'message': message,
                }
            )
            room_name = '_'.join(str(players[3].id))
            room_group_name = 'notification_%s' % room_name
            message = 'You have an invitation to join tournament game against %s, check your dashboard' % players[2].user.username
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'tournament_game_notification',
                    'message': message,
                }
            )
        return Response(self.get_serializer(tournament).data, status=status.HTTP_200_OK)

# class GameList(generics.ListCreateAPIView):
#     queryset = Game.objects.all()
#     serializer_class = GameSerializer


# class GameDetail(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Game.objects.all()
#     serializer_class = GameSerializer