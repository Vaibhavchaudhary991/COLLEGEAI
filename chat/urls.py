"""Template-based URL routes for the chat app."""

from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.ChatView.as_view(), name='index'),
    path('<int:pk>/', views.ChatView.as_view(), name='session'),
]
