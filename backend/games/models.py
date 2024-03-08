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
    

    class Meta:
        ordering = ['created']