from django.db import models
from django.conf import settings
from chat.models import Message
from django.utils import timezone


class Reaction(models.Model):
    REACTION_TYPES = (
        ("like", "Like"),
        ("love", "Love"),
        ("haha", "Haha"),
        ("wow", "Wow"),
        ("sad", "Sad"),
        ("angry", "Angry"),
    )

    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="reactions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reactions"
    )
    type = models.CharField(max_length=10, choices=REACTION_TYPES, default="like")
    reacted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("message", "user")

    def __str__(self):
        return f"{self.user.username} {self.type} on message {self.message.id}"
