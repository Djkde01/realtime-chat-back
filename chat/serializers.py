from rest_framework import serializers
from .models import Chat, ChatParticipant, Message, MessageStatus
from django.contrib.auth import get_user_model

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "profile_img"]


class MessageStatusSerializer(serializers.ModelSerializer):
    receiver = UserMinimalSerializer(read_only=True)

    class Meta:
        model = MessageStatus
        fields = ["id", "receiver", "status", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    sender = UserMinimalSerializer(read_only=True)
    statuses = MessageStatusSerializer(
        source="receiver_statuses", many=True, read_only=True
    )

    class Meta:
        model = Message
        fields = ["id", "chat", "sender", "content", "status", "sent_at", "statuses"]
        read_only_fields = ["sent_at", "status"]


class ChatParticipantSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = ChatParticipant
        fields = ["id", "chat", "user", "joined_at"]


class ChatSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["id", "name", "created_at", "active", "participants", "last_message"]

    def get_participants(self, obj):
        participants = ChatParticipant.objects.filter(chat=obj)
        return ChatParticipantSerializer(participants, many=True).data

    def get_last_message(self, obj):
        message = obj.messages.order_by("-sent_at").first()
        if message:
            return MessageSerializer(message).data
        return None
