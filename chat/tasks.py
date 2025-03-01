from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import MessageStatus


def notify_message_status_change(status_id):
    """Notify about message status changes"""
    try:
        status_obj = MessageStatus.objects.select_related("message", "receiver").get(
            id=status_id
        )
        channel_layer = get_channel_layer()

        # Notify the chat room
        async_to_sync(channel_layer.group_send)(
            f"chat_{status_obj.message.chat.id}",
            {
                "type": "chat.event",
                "event": "mensaje_estado",
                "message_id": status_obj.message.id,
                "user_id": status_obj.receiver.id,
                "status": status_obj.status,
            },
        )

        # Also notify the message sender specifically
        async_to_sync(channel_layer.group_send)(
            f"user_{status_obj.message.sender.id}",
            {
                "type": "chat.event",
                "event": "mensaje_estado",
                "message_id": status_obj.message.id,
                "chat_id": status_obj.message.chat.id,
                "user_id": status_obj.receiver.id,
                "status": status_obj.status,
            },
        )
    except Exception as e:
        print(f"Error notifying message status change: {e}")
