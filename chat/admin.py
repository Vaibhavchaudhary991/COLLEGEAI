from django.contrib import admin
from .models import ChatSession, ChatMessage


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'message_count', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'user__username', 'user__email']
    ordering = ['-updated_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'sender', 'short_message', 'created_at']
    list_filter = ['sender', 'created_at']
    search_fields = ['message', 'session__user__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at']

    def short_message(self, obj):
        return obj.message[:80]
    short_message.short_description = 'Message'
