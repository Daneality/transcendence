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



class GameList(APIView):
    """
    List all snippets, or create a new snippet.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


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

        return Response(self.get_serializer(tournament).data, status=status.HTTP_200_OK)

# class GameList(generics.ListCreateAPIView):
#     queryset = Game.objects.all()
#     serializer_class = GameSerializer


# class GameDetail(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Game.objects.all()
#     serializer_class = GameSerializer