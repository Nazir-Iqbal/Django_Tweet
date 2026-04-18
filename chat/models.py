from django.db import models
from django.conf import settings


class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).first()

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class AIAssist(models.Model):
    """Stores AI-generated suggestions for a user within a conversation."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='ai_assists')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    model_used = models.CharField(max_length=50)
    sentiment = models.CharField(max_length=30, blank=True)
    suggestion = models.TextField()
    context_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
