"""API URL routes for the chat app."""

from django.urls import path
from . import views

urlpatterns = [
    path('sessions/', views.ChatSessionListCreateAPIView.as_view(), name='api-session-list'),
    path('sessions/<int:pk>/', views.ChatSessionDetailAPIView.as_view(), name='api-session-detail'),
    path('sessions/<int:pk>/messages/', views.ChatMessageListCreateAPIView.as_view(), name='api-session-messages'),
]
