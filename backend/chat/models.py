from django.db import models
from django.contrib.auth.models import User

class Chat(models.Model):
    id = models.CharField(primary_key=True, max_length=255, editable=False)
    participant1 = models.ForeignKey(User, related_name='chats1', on_delete=models.CASCADE)
    participant2 = models.ForeignKey(User, related_name='chats2', on_delete=models.CASCADE)
    def save(self, *args, **kwargs):
        self.id = '_'.join(sorted([str(self.participant1_id), str(self.participant2_id)]))
        super().save(*args, **kwargs)

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)