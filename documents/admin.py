from django.contrib import admin
from .models import Document, DocumentCategory
from .services.document_service import process_document


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'document_count', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'file_type', 'file_size_display', 'uploaded_by', 'uploaded_at', 'is_active', 'is_indexed']
    list_filter = ['file_type', 'is_active', 'is_indexed', 'uploaded_at', 'category']
    search_fields = ['title', 'description', 'uploaded_by__username']
    ordering = ['-uploaded_at']
    readonly_fields = ['uploaded_at', 'updated_at', 'file_size', 'file_type', 'is_indexed', 'index_error']
    list_editable = ['is_active']

    actions = ['activate_documents', 'deactivate_documents', 'reindex_documents']

    def activate_documents(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} document(s) activated.")
    activate_documents.short_description = "Activate selected documents"

    def deactivate_documents(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} document(s) deactivated.")
    deactivate_documents.short_description = "Deactivate selected documents"

    def reindex_documents(self, request, queryset):
        """Re-index selected documents into ChromaDB (runs synchronously in admin)."""
        success, failed = 0, 0
        for document in queryset:
            result = process_document(document)
            if result["status"] == "success":
                success += 1
            else:
                failed += 1
        if success:
            self.message_user(request, f"{success} document(s) re-indexed successfully.")
        if failed:
            self.message_user(request, f"{failed} document(s) failed to index. Check index_error field.", level='WARNING')
    reindex_documents.short_description = "Re-index selected documents for AI search"


