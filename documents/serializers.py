import os
from django.conf import settings
from rest_framework import serializers
from .models import Document, DocumentCategory


class DocumentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentCategory
        fields = ['id', 'name', 'description', 'is_active']


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for creating and listing documents."""
    uploaded_by_username = serializers.ReadOnlyField(source='uploaded_by.username')
    file_size_display = serializers.ReadOnlyField()
    filename = serializers.ReadOnlyField()
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'file', 'file_type', 'file_size',
            'file_size_display', 'filename', 'category', 'category_name',
            'uploaded_by', 'uploaded_by_username',
            'uploaded_at', 'updated_at', 'is_active',
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at', 'updated_at', 'file_type', 'file_size']

    def validate_file(self, value):
        # Validate file extension
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext}'. Allowed: {', '.join(settings.ALLOWED_DOCUMENT_EXTENSIONS)}"
            )

        # Validate file size
        max_size = settings.MAX_UPLOAD_SIZE_BYTES
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit."
            )

        return value

    def create(self, validated_data):
        file = validated_data['file']
        ext = os.path.splitext(file.name)[1].lower().lstrip('.')
        validated_data['file_type'] = ext
        validated_data['file_size'] = file.size
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class DocumentDetailSerializer(DocumentSerializer):
    """Extended serializer for document detail view."""
    uploaded_by_email = serializers.ReadOnlyField(source='uploaded_by.email')

    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + ['uploaded_by_email']

