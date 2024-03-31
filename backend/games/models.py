from django.db import models
from django.contrib.auth.models import User
from user.models import Profile

# Create your models here.

class Game(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    p1_score = models.PositiveIntegerField()
    p2_score = models.PositiveIntegerField()
    winner = models.PositiveIntegerField()
    player1 = models.ForeignKey(Profile, related_name='games_as_player1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(Profile, related_name='games_as_player2', on_delete=models.CASCADE)
    
    def __str__(self):
        return f'{self.player1.user.username} vs {self.player2.user.username}, score: {self.p1_score} - {self.p2_score}, winner: player {self.winner}, played - {self.created}'

    class Meta:
        ordering = ['created']


class Tournament(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    game1 = models.ForeignKey(Game, related_name='game1', on_delete=models.CASCADE, null=True, blank=True)
    game2 = models.ForeignKey(Game, related_name='game2', on_delete=models.CASCADE, null=True, blank=True)
    game3 = models.ForeignKey(Game, related_name='game3', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['created']