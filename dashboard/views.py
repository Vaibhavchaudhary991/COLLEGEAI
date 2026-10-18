from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views import View

from documents.models import Document, DocumentCategory
from chat.models import ChatSession, ChatMessage

User = get_user_model()


@method_decorator(login_required, name='dispatch')
class DashboardIndexView(View):
    """
    Routes users to the appropriate dashboard based on their role.
    Students → StudentDashboardView
    Admins   → AdminDashboardView
    """
    def get(self, request):
        if request.user.is_admin_role:
            return redirect('dashboard:admin')
        return redirect('dashboard:student')


@method_decorator(login_required, name='dispatch')
class StudentDashboardView(View):
    """Student dashboard with personal stats and recent activity."""
    def get(self, request):
        if request.user.is_admin_role:
            return redirect('dashboard:admin')

        available_documents = Document.objects.filter(is_active=True)
        user_sessions = ChatSession.objects.filter(user=request.user)

        context = {
            'document_count': available_documents.count(),
            'chat_session_count': user_sessions.count(),
            'recent_sessions': user_sessions[:5],
            'recent_documents': available_documents[:6],
        }
        return render(request, 'dashboard/student_dashboard.html', context)


@method_decorator(login_required, name='dispatch')
class AdminDashboardView(View):
    """Admin dashboard with system-wide statistics."""
    def get(self, request):
        if not request.user.is_admin_role:
            return redirect('dashboard:student')

        context = {
            'total_users': User.objects.count(),
            'total_students': User.objects.filter(role='student').count(),
            'total_admins': User.objects.filter(role='admin').count(),
            'total_documents': Document.objects.count(),
            'active_documents': Document.objects.filter(is_active=True).count(),
            'total_categories': DocumentCategory.objects.count(),
            'total_sessions': ChatSession.objects.count(),
            'total_messages': ChatMessage.objects.count(),
            'recent_documents': Document.objects.select_related('uploaded_by', 'category').order_by('-uploaded_at')[:5],
            'recent_users': User.objects.order_by('-date_joined')[:5],
        }
        return render(request, 'dashboard/admin_dashboard.html', context)

