"""API URL routes for the accounts app."""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterAPIView.as_view(), name='api-register'),
    path('login/', views.LoginAPIView.as_view(), name='api-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('profile/', views.ProfileAPIView.as_view(), name='api-profile'),
]
