from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Chat, ChatParticipant, Message, MessageStatus
from .serializers import (
    ChatSerializer,
    MessageSerializer,
    ChatParticipantSerializer,
    MessageStatusSerializer,
)


class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(participants__user=user, active=True)

    def perform_create(self, serializer):
        chat = serializer.save()
        # Add the creator as a participant
        ChatParticipant.objects.create(chat=chat, user=self.request.user)

    @action(detail=True, methods=["post"])
    def add_participant(self, request, pk=None):
        chat = self.get_object()
        user_id = request.data.get("user_id")
        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.get(pk=user_id)

            # Check if user is already a participant
            if ChatParticipant.objects.filter(chat=chat, user=user).exists():
                return Response(
                    {"error": "User is already a participant"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ChatParticipant.objects.create(chat=chat, user=user)
            return Response({"status": "participant added"})
        except User.DoesNotExist:
            return Response(
                {"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND
            )


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        chat_id = self.request.query_params.get("chat_id", None)

        if chat_id:
            return Message.objects.filter(
                chat_id=chat_id, chat__participants__user=user
            )

        return Message.objects.filter(chat__participants__user=user)

    def perform_create(self, serializer):
        message = serializer.save(sender=self.request.user)

        # Create message status entries for all participants except sender
        chat = message.chat
        participants = ChatParticipant.objects.filter(chat=chat).exclude(
            user=self.request.user
        )

        for participant in participants:
            MessageStatus.objects.create(message=message, receiver=participant.user)

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        message = self.get_object()
        new_status = request.data.get("status")

        if new_status not in dict(MessageStatus.STATUS_CHOICES):
            return Response(
                {
                    "error": f"Invalid status. Choose from {dict(MessageStatus.STATUS_CHOICES).keys()}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update status for this user
        status_obj, created = MessageStatus.objects.get_or_create(
            message=message, receiver=request.user, defaults={"status": new_status}
        )

        if not created:
            status_obj.status = new_status
            status_obj.save()

        return Response({"status": "message status updated"})
