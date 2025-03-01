from django.contrib import admin
from .models import Chat, ChatParticipant, Message, MessageStatus


class ChatParticipantInline(admin.TabularInline):
    model = ChatParticipant
    extra = 0


class MessageStatusInline(admin.TabularInline):
    model = MessageStatus
    extra = 0


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "active")
    list_filter = ("active", "created_at")
    search_fields = ("name",)
    inlines = [ChatParticipantInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "sender", "content", "status", "sent_at")
    list_filter = ("status", "sent_at")
    search_fields = ("content",)
    inlines = [MessageStatusInline]


@admin.register(MessageStatus)
class MessageStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "receiver", "status", "updated_at")
    list_filter = ("status", "updated_at")


@admin.register(ChatParticipant)
class ChatParticipantAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "user", "joined_at")
    list_filter = ("joined_at",)
