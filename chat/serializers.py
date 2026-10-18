from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'sender', 'message', 'created_at']
        read_only_fields = ['id', 'session', 'sender', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    message_count = serializers.ReadOnlyField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'title', 'created_at', 'updated_at', 'message_count', 'last_message']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        last = obj.messages.last()
        if last:
            return {"sender": last.sender, "message": last.message[:100]}
        return None


class ChatSessionDetailSerializer(ChatSessionSerializer):
    """Session serializer with full message list."""
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta(ChatSessionSerializer.Meta):
        fields = ChatSessionSerializer.Meta.fields + ['messages']
