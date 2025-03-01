from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, MessageViewSet

router = DefaultRouter()
router.register("chats", ChatViewSet, basename="chat")
router.register("messages", MessageViewSet, basename="message")

urlpatterns = [
    path("", include(router.urls)),
    # Modified patterns for better compatibility
    path(
        "chats/<int:chat_id>/messages/",
        MessageViewSet.as_view({"get": "list", "post": "create"}),
        name="chat-messages",
    ),
    # Fix for update_all_status - make it simpler
    path(
        "messages/read/<int:chat_id>/",
        MessageViewSet.as_view({"put": "update_all_status"}),
        name="update-all-message-status",
    ),
    # Keep the old URL pattern for backward compatibility
    path(
        "messages/status/update-all/<int:chat_id>/",
        MessageViewSet.as_view({"put": "update_all_status"}),
        name="update-all-message-status-old",
    ),
    path(
        "messages/<int:pk>/status/",
        MessageViewSet.as_view({"put": "status"}),
        name="message-status",
    ),
]
