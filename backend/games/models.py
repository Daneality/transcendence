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



    def save(self, *args, **kwargs):
        # Call the "real" save() method.
        super().save(*args, **kwargs)

        # Update stats for the winner and loser.
        if self.winner == 1:
            winner = self.player1
            loser = self.player2
        else:
            winner = self.player2
            loser = self.player1
        winner.games_won += 1
        loser.games_lost += 1
        winner.save()
        loser.save()


class Tournament(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    game1 = models.ForeignKey(Game, related_name='game1', on_delete=models.CASCADE, null=True, blank=True)
    game2 = models.ForeignKey(Game, related_name='game2', on_delete=models.CASCADE, null=True, blank=True)
    game3 = models.ForeignKey(Game, related_name='game3', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['created']