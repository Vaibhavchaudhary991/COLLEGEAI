from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import Http404

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatSessionDetailSerializer, ChatMessageSerializer
from .services.ai_service import generate_response


# ─── API Views ────────────────────────────────────────────────────────────────

class ChatSessionListCreateAPIView(APIView):
    """
    GET  /api/chat/sessions/    — List user's chat sessions
    POST /api/chat/sessions/    — Create a new chat session
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user)
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ChatSessionSerializer(data=request.data)
        if serializer.is_valid():
            session = serializer.save(user=request.user)
            return Response(ChatSessionSerializer(session).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatSessionDetailAPIView(APIView):
    """
    GET    /api/chat/sessions/<id>/ — Session detail with messages
    DELETE /api/chat/sessions/<id>/ — Delete session
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return ChatSession.objects.get(pk=pk, user=user)
        except ChatSession.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        session = self.get_object(pk, request.user)
        serializer = ChatSessionDetailSerializer(session)
        return Response(serializer.data)

    def delete(self, request, pk):
        session = self.get_object(pk, request.user)
        session.delete()
        return Response({"message": "Chat session deleted."}, status=status.HTTP_204_NO_CONTENT)


class ChatMessageListCreateAPIView(APIView):
    """
    GET  /api/chat/sessions/<id>/messages/ — List messages in a session
    POST /api/chat/sessions/<id>/messages/ — Send a message and get AI response
    """
    permission_classes = [IsAuthenticated]

    def get_session(self, pk, user):
        try:
            return ChatSession.objects.get(pk=pk, user=user)
        except ChatSession.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        session = self.get_session(pk, request.user)
        messages_qs = session.messages.all()
        serializer = ChatMessageSerializer(messages_qs, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        session = self.get_session(pk, request.user)

        user_message_text = request.data.get('message', '').strip()
        if not user_message_text:
            return Response({"error": "Message cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Save the user's message
        user_msg = ChatMessage.objects.create(
            session=session,
            sender=ChatMessage.SENDER_USER,
            message=user_message_text,
        )

        # Build chat history context for the AI service
        history = list(
            session.messages.exclude(pk=user_msg.pk).values('sender', 'message')
        )

        # Call AI service — placeholder now, RAG pipeline later
        ai_response_text = generate_response(question=user_message_text, chat_history=history)

        # Save the assistant's response
        assistant_msg = ChatMessage.objects.create(
            session=session,
            sender=ChatMessage.SENDER_ASSISTANT,
            message=ai_response_text,
        )

        # Update session title based on first user message
        if session.messages.filter(sender=ChatMessage.SENDER_USER).count() == 1:
            session.title = user_message_text[:50]
            session.save()

        return Response(
            {
                "user_message": ChatMessageSerializer(user_msg).data,
                "assistant_message": ChatMessageSerializer(assistant_msg).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ─── Template Views ────────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class ChatView(View):
    """Template-based chat interface."""
    def get(self, request, pk=None):
        sessions = ChatSession.objects.filter(user=request.user)
        active_session = None
        messages_qs = []

        if pk:
            try:
                active_session = ChatSession.objects.get(pk=pk, user=request.user)
                messages_qs = active_session.messages.all()
            except ChatSession.DoesNotExist:
                pass

        return render(request, 'chat/chat.html', {
            'sessions': sessions,
            'active_session': active_session,
            'chat_messages': messages_qs,
        })
