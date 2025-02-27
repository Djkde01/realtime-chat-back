from django.db import models
from django.conf import settings
from django.utils import timezone


class Chat(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ChatParticipant(models.Model):
    chat = models.ForeignKey(
        Chat, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_participants",
    )
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("chat", "user")

    def __str__(self):
        return f"{self.user.username} in {self.chat.name}"


class Message(models.Model):
    STATUS_CHOICES = (
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("read", "Read"),
    )

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="sent")
    sent_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"

    class Meta:
        ordering = ["sent_at"]


class MessageStatus(models.Model):
    STATUS_CHOICES = (
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("read", "Read"),
    )

    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="receiver_statuses"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_statuses",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="sent")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("message", "receiver")

    def __str__(self):
        return f"{self.receiver.username}: {self.status} - {self.message.content[:20]}"
