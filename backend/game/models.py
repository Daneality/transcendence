from django.db import models

# Create your models here.

class game_result(models.Model):
    player1 = models.CharField(max_length=100)
    player2 = models.CharField(max_length=100)
    score1 = models.IntegerField()
    score2 = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Game between " + self.player1 + " and " + self.player2 + " on " + str(self.date) + " ended with score " + str(self.score1) + " - " + str(self.score2) + ".\n"