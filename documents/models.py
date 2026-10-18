import os
from django.db import models
from django.conf import settings


def document_upload_path(instance, filename):
    """Store documents in media/documents/<filename>."""
    return f"documents/{filename}"


class DocumentCategory(models.Model):
    """
    Category for classifying documents (e.g. Placement Guidelines, Syllabus).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Document Category'
        verbose_name_plural = 'Document Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def document_count(self):
        return self.documents.count()


class Document(models.Model):
    """
    Represents an uploaded document available to students.
    Text extraction and embedding will be added here in the future RAG layer.
    """

    FILE_TYPE_PDF = 'pdf'
    FILE_TYPE_DOCX = 'docx'
    FILE_TYPE_TXT = 'txt'

    FILE_TYPE_CHOICES = [
        (FILE_TYPE_PDF, 'PDF'),
        (FILE_TYPE_DOCX, 'DOCX'),
        (FILE_TYPE_TXT, 'TXT'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=document_upload_path)
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    is_active = models.BooleanField(default=True, help_text="Inactive documents are hidden from students")

    # ─── RAG indexing status ───────────────────────────────────────────────────
    is_indexed = models.BooleanField(
        default=False,
        help_text="True when this document has been embedded into the vector database for AI search."
    )
    index_error = models.TextField(
        blank=True,
        default="",
        help_text="Error message if indexing failed. Empty when successful."
    )

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

    @property
    def file_size_display(self):
        """Human-readable file size."""
        size = self.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 ** 2:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 ** 2):.1f} MB"

    @property
    def filename(self):
        return os.path.basename(self.file.name)
