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
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json


class ChatViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing chats
    """

    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        """Get chats where the current user is a participant"""
        user = self.request.user
        # Only return active chats
        return Chat.objects.filter(participants__user=user, active=True).distinct()

    def perform_create(self, serializer):
        """Create a new chat and add participants"""
        # Create the chat
        chat = serializer.save()

        # Add the creator as participant first
        ChatParticipant.objects.create(chat=chat, user=self.request.user)

        # Get participants IDs from request data
        participants_ids = self.request.data.get("participants_ids", [])
        if isinstance(participants_ids, str):
            # Handle string format (from frontend form data)
            import ast

            try:
                participants_ids = ast.literal_eval(participants_ids)
            except (ValueError, SyntaxError):
                participants_ids = []

        # Add other participants
        from django.contrib.auth import get_user_model

        User = get_user_model()

        for user_id in participants_ids:
            try:
                user = User.objects.get(id=user_id)
                if user.id != self.request.user.id:  # Don't add creator twice
                    ChatParticipant.objects.create(chat=chat, user=user)

                    # Notify the user about the new chat via WebSocket
                    self.notify_new_chat(chat.id, user.id)
            except User.DoesNotExist:
                continue  # Skip invalid user IDs

    @action(detail=True, methods=["post"])
    def add_participants(self, request, pk=None):
        """Add new participants to an existing chat"""
        chat = self.get_object()

        # Check if the current user is a participant
        if not ChatParticipant.objects.filter(chat=chat, user=request.user).exists():
            return Response(
                {"detail": "You are not a participant in this chat."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get user IDs to add
        users_ids = request.data.get("users_ids", [])
        if isinstance(users_ids, str):
            import ast

            try:
                users_ids = ast.literal_eval(users_ids)
            except (ValueError, SyntaxError):
                users_ids = []

        # Add new participants
        from django.contrib.auth import get_user_model

        User = get_user_model()

        added_count = 0
        for user_id in users_ids:
            try:
                user = User.objects.get(id=user_id)

                # Skip if already a participant
                if ChatParticipant.objects.filter(chat=chat, user=user).exists():
                    continue

                # Add as participant
                ChatParticipant.objects.create(chat=chat, user=user)
                added_count += 1

                # Notify the user about being added to the chat
                self.notify_new_chat(chat.id, user.id)
            except User.DoesNotExist:
                continue

        # Notify all participants about the updated participant list
        updated_participants = ChatParticipantSerializer(
            ChatParticipant.objects.filter(chat=chat), many=True
        ).data

        self.notify_participants_updated(chat.id, updated_participants)

        return Response(
            {
                "detail": f"Added {added_count} participants to the chat.",
                "participants": updated_participants,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        """Get paginated messages for a specific chat"""
        chat = self.get_object()

        # Check if the current user is a participant
        if not ChatParticipant.objects.filter(chat=chat, user=request.user).exists():
            return Response(
                {"detail": "You are not a participant in this chat."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Pagination parameters
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        start = (page - 1) * page_size
        end = start + page_size

        # Get messages, newest first
        messages = (
            Message.objects.filter(chat=chat)
            .select_related("sender")
            .prefetch_related("receiver_statuses", "receiver_statuses__receiver")
            .order_by("-sent_at")[start:end]
        )

        serializer = MessageSerializer(messages, many=True)

        # Mark messages as delivered when history is viewed
        self.mark_messages_as_delivered(chat.id, request.user)

        return Response(serializer.data)

    def notify_new_chat(self, chat_id, user_id):
        """Notify a user about a new chat via WebSocket"""
        channel_layer = get_channel_layer()

        try:
            # Get chat data to include in notification
            chat = Chat.objects.get(id=chat_id)
            chat_data = ChatSerializer(chat).data

            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}",
                {
                    "type": "chat.event",
                    "event": "nuevo_chat",
                    "chat": chat_data,
                },
            )
        except Exception as e:
            print(f"WebSocket notification error: {e}")

    def notify_participants_updated(self, chat_id, participants_data):
        """Notify chat participants about updated participant list"""
        channel_layer = get_channel_layer()

        try:
            async_to_sync(channel_layer.group_send)(
                f"chat_{chat_id}",
                {
                    "type": "chat.event",
                    "event": "participantes_actualizados",
                    "participants": participants_data,
                },
            )
        except Exception as e:
            print(f"WebSocket notification error: {e}")

    def mark_messages_as_delivered(self, chat_id, user):
        """Mark unread messages as delivered"""
        unread_statuses = MessageStatus.objects.filter(
            message__chat_id=chat_id, receiver=user, status="sent"
        )

        for status in unread_statuses:
            status.status = "delivered"
            status.save()

            # Notify the sender about message being delivered
            self.notify_message_status_change(status)

    def notify_message_status_change(self, message_status):
        """Notify about message status changes"""
        channel_layer = get_channel_layer()

        try:
            # Notify the chat room
            async_to_sync(channel_layer.group_send)(
                f"chat_{message_status.message.chat.id}",
                {
                    "type": "chat.event",
                    "event": "mensaje_estado",
                    "message_id": message_status.message.id,
                    "user_id": message_status.receiver.id,
                    "status": message_status.status,
                },
            )

            # Notify the message sender specifically
            async_to_sync(channel_layer.group_send)(
                f"user_{message_status.message.sender.id}",
                {
                    "type": "chat.event",
                    "event": "mensaje_estado",
                    "message_id": message_status.message.id,
                    "chat_id": message_status.message.chat.id,
                    "user_id": message_status.receiver.id,
                    "status": message_status.status,
                },
            )
        except Exception as e:
            print(f"WebSocket notification error: {e}")


class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing messages with complete sequence diagram flow
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Get messages for chats where the current user is a participant"""
        user = self.request.user
        chat_id = self.request.query_params.get("chat_id")

        if chat_id:
            # Check if user is a participant in this chat
            if not ChatParticipant.objects.filter(chat_id=chat_id, user=user).exists():
                return Message.objects.none()

            messages = Message.objects.filter(chat_id=chat_id)

            # Optimize query with select_related and prefetch_related
            return (
                messages.select_related("sender")
                .prefetch_related("receiver_statuses", "receiver_statuses__receiver")
                .order_by("-sent_at")
            )

        # Return messages from all chats where user is a participant
        return (
            Message.objects.filter(chat__participants__user=user)
            .select_related("sender", "chat")
            .order_by("-sent_at")
        )

    def create(self, request, *args, **kwargs):
        """Create a message following the sequence diagram flow"""
        # Extract the chat ID from either the URL or request data
        chat_id = request.data.get("chat")
        content = request.data.get("content")

        if not chat_id or not content:
            return Response(
                {"detail": "Chat ID and message content are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user is a participant
        user = request.user
        if not ChatParticipant.objects.filter(chat_id=chat_id, user=user).exists():
            return Response(
                {"detail": "You are not a participant in this chat."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Create the message in database
        chat = Chat.objects.get(id=chat_id)
        message = Message.objects.create(chat=chat, sender=user, content=content)

        # Create message status entries for all participants except sender
        participants = ChatParticipant.objects.filter(chat=chat).exclude(user=user)
        for participant in participants:
            MessageStatus.objects.create(
                message=message, receiver=participant.user, status="sent"
            )

        # Serialize and return the created message
        serializer = self.get_serializer(message)

        # Notify participants via WebSocket - this matches the sequence diagram's
        # "par" section showing REST API and WebSocket in parallel
        self.notify_new_message(message)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["put"])
    def update_all_status(self, request, chat_id=None):
        """Mark all messages in a chat as read for the current user"""

        # Debug the parameters we're receiving
        print(f"Request user: {request.user.username}, chat_id param: {chat_id}")

        # If chat_id is None, try to get it from query_params
        if chat_id is None:
            chat_id = request.query_params.get("chat_id")

        if not chat_id:
            return Response(
                {"detail": "Chat ID is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if chat exists
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return Response(
                {"detail": f"Chat with ID {chat_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if user is a participant
        if not ChatParticipant.objects.filter(
            chat_id=chat_id, user=request.user
        ).exists():
            return Response(
                {"detail": "You are not a participant in this chat."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Update status for all unread messages
        statuses = MessageStatus.objects.filter(
            message__chat_id=chat_id,
            receiver=request.user,
            status__in=["sent", "delivered"],
        )

        updated_count = 0
        for status_obj in statuses:
            status_obj.status = "read"
            status_obj.save()
            updated_count += 1

            # Notify about status change
            try:
                # When tasks module is implemented
                from .tasks import notify_message_status_change

                notify_message_status_change(status_obj.id)
            except ImportError:
                pass

        # Notify via WebSocket
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{chat_id}",
                {
                    "type": "chat.event",
                    "event": "mensajes_leidos",
                    "user_id": request.user.id,
                    "chat_id": int(chat_id),
                },
            )
        except Exception as e:
            print(f"WebSocket notification error: {e}")

        return Response(
            {"detail": f"Marked {updated_count} messages as read."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["put"])
    def status(self, request, pk=None):
        """Update the status of a specific message"""
        message = self.get_object()
        new_status = request.data.get("status")

        if new_status not in dict(MessageStatus.STATUS_CHOICES):
            return Response(
                {
                    "detail": f"Invalid status. Choose from {[s[0] for s in MessageStatus.STATUS_CHOICES]}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user is a receiver of this message
        if message.sender == request.user:
            return Response(
                {"detail": "Cannot update status for your own message."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update or create status
        status_obj, created = MessageStatus.objects.update_or_create(
            message=message, receiver=request.user, defaults={"status": new_status}
        )

        # Notify about status change
        from .tasks import notify_message_status_change

        notify_message_status_change(status_obj.id)

        return Response(
            MessageStatusSerializer(status_obj).data, status=status.HTTP_200_OK
        )

    def notify_new_message(self, message):
        """Notify participants about a new message via WebSocket"""
        channel_layer = get_channel_layer()
        message_data = MessageSerializer(message).data

        try:
            # Broadcast to the chat room
            async_to_sync(channel_layer.group_send)(
                f"chat_{message.chat.id}",
                {
                    "type": "chat.message",
                    "message": message_data,
                },
            )
        except Exception as e:
            print(f"WebSocket notification error: {e}")
