from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserRegisterSerializer, UserProfileSerializer
from .permissions import IsAdminRole, admin_required


# ─── API Views ────────────────────────────────────────────────────────────────

class RegisterAPIView(APIView):
    """POST /api/auth/register/ — Create a new user account."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Registration successful.",
                    "user": UserProfileSerializer(user).data,
                    "tokens": {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """POST /api/auth/login/ — Authenticate and receive JWT tokens."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": "Login successful.",
                "user": UserProfileSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_200_OK,
        )


class ProfileAPIView(APIView):
    """GET /api/auth/profile/ — Return the authenticated user's profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── Template Views ────────────────────────────────────────────────────────────

class HomeView(View):
    """Public landing page."""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        return render(request, 'home/index.html')


class LoginView(View):
    """Template-based login page."""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        return render(request, 'accounts/login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/dashboard/')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'accounts/login.html')


class RegisterView(View):
    """Template-based registration page."""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        return render(request, 'accounts/register.html')

    def post(self, request):
        data = {
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
            'first_name': request.POST.get('first_name', ''),
            'last_name': request.POST.get('last_name', ''),
            'password': request.POST.get('password'),
            'password_confirm': request.POST.get('password_confirm'),
        }
        serializer = UserRegisterSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Welcome, {user.first_name or user.username}! Your account has been created.")
            return redirect('dashboard:index')
        else:
            for field, errors in serializer.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return render(request, 'accounts/register.html', {'form_data': request.POST})


class LogoutView(View):
    """Log out and redirect to login."""
    def post(self, request):
        logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('accounts:login')


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    """Template-based profile page (for students)."""
    def get(self, request):
        # Admins have their own profile page
        if request.user.is_admin_role:
            return redirect('accounts:admin_profile')
        return render(request, 'accounts/profile.html', {'user': request.user})

    def post(self, request):
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.bio = request.POST.get('bio', user.bio)
        if request.FILES.get('avatar'):
            user.avatar = request.FILES['avatar']
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')


# ─── Admin-only Template Views ─────────────────────────────────────────────────

@method_decorator(admin_required, name='dispatch')
class AdminProfileView(View):
    """Admin profile page — view-only with links to edit and change password."""
    def get(self, request):
        return render(request, 'accounts/admin_profile.html', {'profile_user': request.user})


@method_decorator(admin_required, name='dispatch')
class AdminEditProfileView(View):
    """Admin edit profile page — update name, email, avatar."""
    def get(self, request):
        return render(request, 'accounts/admin_edit_profile.html', {'profile_user': request.user})

    def post(self, request):
        user = request.user
        from django.contrib.auth import get_user_model
        User = get_user_model()

        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        # Validate required fields
        if not first_name:
            messages.error(request, 'First name is required.')
            return render(request, 'accounts/admin_edit_profile.html', {'profile_user': user})
        if not email:
            messages.error(request, 'Email is required.')
            return render(request, 'accounts/admin_edit_profile.html', {'profile_user': user})

        # Validate email format
        from django.core.validators import validate_email as django_validate_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            django_validate_email(email)
        except DjangoValidationError:
            messages.error(request, 'Enter a valid email address.')
            return render(request, 'accounts/admin_edit_profile.html', {'profile_user': user})

        # Check email uniqueness (excluding current user)
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            messages.error(request, 'This email address is already in use by another account.')
            return render(request, 'accounts/admin_edit_profile.html', {'profile_user': user})

        # Validate and save avatar
        if request.FILES.get('avatar'):
            avatar = request.FILES['avatar']
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if avatar.content_type not in allowed_types:
                messages.error(request, 'Only JPG, PNG, GIF, and WebP images are allowed.')
                return render(request, 'accounts/admin_edit_profile.html', {'profile_user': user})
            max_size = 5 * 1024 * 1024  # 5 MB
            if avatar.size > max_size:
                messages.error(request, 'Image must be smaller than 5 MB.')
                return render(request, 'accounts/admin_edit_profile.html', {'profile_user': user})
            user.avatar = avatar

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:admin_profile')


@method_decorator(admin_required, name='dispatch')
class AdminChangePasswordView(View):
    """Admin change password page."""
    def get(self, request):
        return render(request, 'accounts/admin_change_password.html')

    def post(self, request):
        user = request.user
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Verify current password
        if not user.check_password(current_password):
            messages.error(request, 'Your current password is incorrect.')
            return render(request, 'accounts/admin_change_password.html')

        # Passwords must match
        if new_password != confirm_password:
            messages.error(request, 'New password and confirmation do not match.')
            return render(request, 'accounts/admin_change_password.html')

        # Run Django password validators
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'accounts/admin_change_password.html')

        user.set_password(new_password)
        user.save()
        # Keep the admin logged in after password change
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed successfully.')
        return redirect('accounts:admin_profile')

# ─── Admin User Management Views ──────────────────────────────────────────────

@method_decorator(admin_required, name='dispatch')
class AdminUserListView(View):
    """
    GET /admin/users/ — List all users with search and role filter.
    Admin-only.
    """
    def get(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        queryset = User.objects.all().order_by('-date_joined')
        search_q = request.GET.get('q', '').strip()
        role_filter = request.GET.get('role', '')

        if search_q:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(username__icontains=search_q) |
                Q(email__icontains=search_q) |
                Q(first_name__icontains=search_q) |
                Q(last_name__icontains=search_q)
            )
        if role_filter in ('student', 'admin'):
            queryset = queryset.filter(role=role_filter)

        context = {
            'users': queryset,
            'search_q': search_q,
            'role_filter': role_filter,
            'total_count': queryset.count(),
        }
        return render(request, 'accounts/admin_users.html', context)


@method_decorator(admin_required, name='dispatch')
class AdminUserDetailView(View):
    """GET /admin/users/<pk>/ — View full details of a user."""
    def get(self, request, pk):
        from django.contrib.auth import get_user_model
        from django.shortcuts import get_object_or_404
        User = get_user_model()
        target_user = get_object_or_404(User, pk=pk)
        return render(request, 'accounts/admin_user_detail.html', {'target_user': target_user})


@method_decorator(admin_required, name='dispatch')
class AdminUserToggleView(View):
    """POST /admin/users/<pk>/toggle/ — Activate or deactivate a user."""
    def post(self, request, pk):
        from django.contrib.auth import get_user_model
        from django.shortcuts import get_object_or_404
        User = get_user_model()
        target_user = get_object_or_404(User, pk=pk)

        # Prevent admin from deactivating themselves
        if target_user.pk == request.user.pk:
            messages.error(request, 'You cannot deactivate your own account.')
            return redirect('accounts:admin_users')

        target_user.is_active = not target_user.is_active
        target_user.save()
        action = 'activated' if target_user.is_active else 'deactivated'
        messages.success(request, f'User "{target_user.username}" has been {action}.')
        return redirect('accounts:admin_users')

