from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardIndexView.as_view(), name='index'),
    path('student/', views.StudentDashboardView.as_view(), name='student'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin'),
]
