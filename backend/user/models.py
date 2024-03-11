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
    image = models.ImageField(upload_to='images/')
    #tournament = models.ForeignKey(Tournament, on_delete=models.SET_NULL, null=True, blank=True, related_name='players')


class FriendRequest(models.Model):
    from_user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='from_user')
    to_user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='to_user')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created']
        constraints = [
            models.UniqueConstraint(fields=['from_user', 'to_user'], name='unique_friend_request')
        ]
    
    def __str__(self):
        return f'{self.from_user.username} to {self.to_user.username}'