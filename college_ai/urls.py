"""
college_ai URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Template-based views
    path('', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('documents/', include('documents.urls')),
    path('chat/', include('chat.urls')),

    # API endpoints
    path('api/auth/', include('accounts.api_urls')),
    path('api/admin/', include('accounts.admin_api_urls')),
    path('api/documents/', include('documents.api_urls')),
    path('api/chat/', include('chat.api_urls')),

    # Allauth (Google OAuth callback, etc.)
    path('accounts/', include('allauth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

