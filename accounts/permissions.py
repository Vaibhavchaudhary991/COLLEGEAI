from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """
    Allows access only to users with role='admin'.
    This is separate from Django's is_staff — it uses the custom role field.
    """
    message = "Only administrators are allowed to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_admin_role
        )


class IsStudentRole(BasePermission):
    """Allows access only to users with role='student'."""
    message = "This endpoint is for students only."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_student
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Admins can perform any action.
    Authenticated students can only perform safe (read) methods.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_admin_role


# ─── Template-view decorator ──────────────────────────────────────────────────

def admin_required(view_func):
    """
    Decorator for template-based views.
    - Unauthenticated users are redirected to the login page.
    - Authenticated students receive a 403 Access Denied page.
    - Admins pass through normally.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        if not request.user.is_admin_role:
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

