from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    """
    Represents a conversation session between a user and the AI assistant.
    Each session groups multiple ChatMessages together.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
    )
    title = models.CharField(max_length=255, default='New Chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} — {self.title}"

    @property
    def message_count(self):
        return self.messages.count()


class ChatMessage(models.Model):
    """
    A single message in a ChatSession.
    sender='user' for user messages, sender='assistant' for AI responses.
    """
    SENDER_USER = 'user'
    SENDER_ASSISTANT = 'assistant'

    SENDER_CHOICES = [
        (SENDER_USER, 'User'),
        (SENDER_ASSISTANT, 'Assistant'),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.get_sender_display()}] {self.message[:50]}"
