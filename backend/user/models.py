from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add additional fields here
    games_lost = models.PositiveIntegerField(default=0)
    games_won = models.PositiveIntegerField(default=0)
    friends = models.ManyToManyField(User, related_name='friends')
    blocked_users = models.ManyToManyField(User, related_name='blocked_users')
    #image = models.ImageField(upload_to='images/')
    #tournament = models.ForeignKey(Tournament, on_delete=models.SET_NULL, null=True, blank=True, related_name='players')
