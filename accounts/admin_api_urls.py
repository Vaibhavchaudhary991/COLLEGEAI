from django.urls import path
from . import admin_api_views

urlpatterns = [
    path('profile/', admin_api_views.AdminProfileAPIView.as_view(), name='api-admin-profile'),
    path('change-password/', admin_api_views.AdminChangePasswordAPIView.as_view(), name='api-admin-change-password'),
    path('users/', admin_api_views.AdminUserListAPIView.as_view(), name='api-admin-users'),
    path('users/<int:pk>/', admin_api_views.AdminUserDetailAPIView.as_view(), name='api-admin-user-detail'),
    path('statistics/', admin_api_views.AdminStatisticsAPIView.as_view(), name='api-admin-statistics'),
]