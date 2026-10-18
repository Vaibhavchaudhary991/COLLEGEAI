"""Template-based URL routes for the accounts app."""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Public
    path('', views.HomeView.as_view(), name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # Student profile
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # Admin profile
    path('admin-profile/', views.AdminProfileView.as_view(), name='admin_profile'),
    path('admin-profile/edit/', views.AdminEditProfileView.as_view(), name='admin_edit_profile'),
    path('admin-profile/change-password/', views.AdminChangePasswordView.as_view(), name='admin_change_password'),

    # User management (admin only) — using /manage/ prefix to avoid conflict with Django's /admin/
    path('manage/users/', views.AdminUserListView.as_view(), name='admin_users'),
    path('manage/users/<int:pk>/', views.AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('manage/users/<int:pk>/toggle/', views.AdminUserToggleView.as_view(), name='admin_user_toggle'),
]

