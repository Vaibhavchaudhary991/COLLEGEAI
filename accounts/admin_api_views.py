from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import IsAdminRole
from .serializers import UserProfileSerializer, UserListSerializer
from documents.models import Document, DocumentCategory
from chat.models import ChatSession, ChatMessage

User = get_user_model()


class AdminProfileAPIView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.validated_data.pop('role', None)
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminChangePasswordAPIView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password', '')
        new_password = request.data.get('new_password', '')
        if not user.check_password(current_password):
            return Response({'error': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password changed successfully.'})


class AdminUserListAPIView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        queryset = User.objects.all().order_by('-date_joined')
        role = request.query_params.get('role', '')
        if role in ('student', 'admin'):
            queryset = queryset.filter(role=role)
        serializer = UserListSerializer(queryset, many=True)
        return Response(serializer.data)


class AdminUserDetailAPIView(APIView):
    permission_classes = [IsAdminRole]

    def get_user(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        user = self.get_user(pk)
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    def patch(self, request, pk):
        user = self.get_user(pk)
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        if 'is_active' in request.data:
            if user.pk == request.user.pk:
                return Response({'error': 'You cannot deactivate your own account.'}, status=status.HTTP_400_BAD_REQUEST)
            user.is_active = bool(request.data['is_active'])
            user.save()
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


class AdminStatisticsAPIView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response({
            'total_users': User.objects.count(),
            'total_students': User.objects.filter(role='student').count(),
            'total_admins': User.objects.filter(role='admin').count(),
            'total_documents': Document.objects.count(),
            'active_documents': Document.objects.filter(is_active=True).count(),
            'total_categories': DocumentCategory.objects.count(),
            'total_chat_sessions': ChatSession.objects.count(),
            'total_chat_messages': ChatMessage.objects.count(),
        })