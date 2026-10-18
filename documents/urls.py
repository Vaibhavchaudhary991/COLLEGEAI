"""Template-based URL routes for the documents app."""

from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Student views
    path('', views.DocumentListView.as_view(), name='list'),
    path('<int:pk>/', views.DocumentDetailView.as_view(), name='detail'),
    path('<int:pk>/download/', views.DocumentDownloadView.as_view(), name='download'),

    # Admin document management
    path('upload/', views.DocumentUploadView.as_view(), name='upload'),
    path('admin/', views.AdminDocumentListView.as_view(), name='admin_list'),
    path('<int:pk>/edit/', views.AdminDocumentEditView.as_view(), name='admin_edit'),

    # Admin category management
    path('admin/categories/', views.AdminCategoryListView.as_view(), name='admin_categories'),
    path('admin/categories/add/', views.AdminCategoryCreateView.as_view(), name='admin_category_add'),
    path('admin/categories/<int:pk>/edit/', views.AdminCategoryEditView.as_view(), name='admin_category_edit'),
    path('admin/categories/<int:pk>/toggle/', views.AdminCategoryToggleView.as_view(), name='admin_category_toggle'),
]

