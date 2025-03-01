from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # Chat specific WebSocket
    path("ws/chat/<int:chat_id>/", consumers.ChatConsumer.as_asgi()),
    # User specific notification WebSocket (for new chats)
    path("ws/user/", consumers.UserConsumer.as_asgi()),
]
