"""API URL routes for the documents app."""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.DocumentListCreateAPIView.as_view(), name='api-document-list'),
    path('<int:pk>/', views.DocumentDetailAPIView.as_view(), name='api-document-detail'),
    path('<int:pk>/toggle/', views.DocumentToggleActiveAPIView.as_view(), name='api-document-toggle'),
]
