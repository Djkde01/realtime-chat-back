import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat.models import Chat, Message, ChatParticipant, MessageStatus


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle new WebSocket connection from client"""
        self.user = self.scope["user"]

        # Make sure user is authenticated
        if self.user.is_anonymous:
            await self.close()
            return

        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.chat_group_name = f"chat_{self.chat_id}"
        self.user_group_name = f"user_{self.user.id}"

        # Verify user is participant
        is_participant = await self.is_chat_participant()
        if not is_participant:
            await self.close()
            return

        # Join chat group
        await self.channel_layer.group_add(self.chat_group_name, self.channel_name)

        # Join user-specific group for individual notifications
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)

        await self.accept()

        # Mark messages as delivered when user connects
        await self.mark_messages_as_delivered()

        # Notify other users about this user's online status
        await self.notify_user_online()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave the room group
        if hasattr(self, "chat_group_name"):
            await self.channel_layer.group_discard(
                self.chat_group_name, self.channel_name
            )

        # Leave user-specific group
        if hasattr(self, "user_group_name"):
            await self.channel_layer.group_discard(
                self.user_group_name, self.channel_name
            )

        # Notify others about user going offline
        if (
            hasattr(self, "user")
            and not self.user.is_anonymous
            and hasattr(self, "chat_id")
        ):
            await self.notify_user_offline()

    # Receive message from WebSocket
    async def receive(self, text_data):
        """Process messages received from clients"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type", "chat_message")

            if message_type == "chat_message":
                # Handle new chat message
                content = text_data_json.get("message", "")
                if not content:
                    return

                # Save message to database
                message_obj = await self.save_message(content)

                # Send message to room group
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        "type": "chat.message",
                        "message": {
                            "id": message_obj.id,
                            "content": content,
                            "sender_id": self.user.id,
                            "sender_username": self.user.username,
                            "sender_profile_img": getattr(
                                self.user, "profile_img", None
                            ),
                            "sent_at": message_obj.sent_at.isoformat(),
                            "status": "sent",
                            "chat_id": int(self.chat_id),
                        },
                    },
                )

            elif message_type == "typing":
                # Broadcast typing indicator
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        "type": "chat.event",
                        "event": "typing",
                        "user_id": self.user.id,
                        "username": self.user.username,
                        "chat_id": int(self.chat_id),
                    },
                )

            elif message_type == "read_messages":
                # Mark messages as read
                await self.mark_messages_as_read()

                # Notify others
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        "type": "chat.event",
                        "event": "mensajes_leidos",
                        "user_id": self.user.id,
                        "chat_id": int(self.chat_id),
                    },
                )

            elif message_type == "delivered_messages":
                # Mark messages as delivered
                await self.mark_messages_as_delivered()

                # Notify others
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        "type": "chat.event",
                        "event": "mensajes_entregados",
                        "user_id": self.user.id,
                        "chat_id": int(self.chat_id),
                    },
                )
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Error processing WebSocket message: {e}")

    # Receive message from chat group
    async def chat_message(self, event):
        """Forward chat messages to the WebSocket client"""
        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message": event["message"],
                }
            )
        )

    # Handle chat events
    async def chat_event(self, event):
        """Forward chat events to the WebSocket client"""
        # Forward the event to WebSocket
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def is_chat_participant(self):
        """Check if current user is a participant in the chat"""
        return ChatParticipant.objects.filter(
            chat_id=self.chat_id, user=self.user
        ).exists()

    @database_sync_to_async
    def save_message(self, content):
        """Save a new message to the database"""
        chat = Chat.objects.get(id=self.chat_id)
        message = Message.objects.create(chat=chat, sender=self.user, content=content)

        # Create message status entries for all participants except sender
        participants = ChatParticipant.objects.filter(chat=chat).exclude(user=self.user)
        for participant in participants:
            MessageStatus.objects.create(message=message, receiver=participant.user)

        return message

    @database_sync_to_async
    def mark_messages_as_delivered(self):
        """Mark all messages as delivered for the current user"""
        unread_statuses = MessageStatus.objects.filter(
            message__chat_id=self.chat_id, receiver=self.user, status="sent"
        )

        for status in unread_statuses:
            status.status = "delivered"
            status.save()

            # We'll notify about this status change in a separate task
            from chat.tasks import notify_message_status_change

            notify_message_status_change(status.id)

    @database_sync_to_async
    def mark_messages_as_read(self):
        """Mark all messages as read for the current user"""
        unread_statuses = MessageStatus.objects.filter(
            message__chat_id=self.chat_id,
            receiver=self.user,
            status__in=["sent", "delivered"],
        )

        for status in unread_statuses:
            status.status = "read"
            status.save()

            # We'll notify about this status change in a separate task
            from chat.tasks import notify_message_status_change

            notify_message_status_change(status.id)

    async def notify_user_online(self):
        """Let other users know this user is online in this chat"""
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                "type": "chat.event",
                "event": "user_online",
                "user_id": self.user.id,
                "username": self.user.username,
                "chat_id": int(self.chat_id),
            },
        )

    async def notify_user_offline(self):
        """Let other users know this user went offline"""
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                "type": "chat.event",
                "event": "user_offline",
                "user_id": self.user.id,
                "username": self.user.username,
                "chat_id": int(self.chat_id),
            },
        )


class UserConsumer(AsyncWebsocketConsumer):
    """Consumer for user-specific notifications (new chats, etc)"""

    async def connect(self):
        self.user = self.scope["user"]

        # Make sure user is authenticated
        if self.user.is_anonymous:
            await self.close()
            return

        self.user_group_name = f"user_{self.user.id}"

        # Join user-specific group
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)

        await self.accept()

        # Notify that user is available for notifications
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": "Connected to personal notification channel",
                }
            )
        )

    async def disconnect(self, close_code):
        # Leave user group
        if hasattr(self, "user_group_name"):
            await self.channel_layer.group_discard(
                self.user_group_name, self.channel_name
            )

    # Handle chat events for the user
    async def chat_event(self, event):
        # Forward the event to WebSocket
        await self.send(text_data=json.dumps(event))
