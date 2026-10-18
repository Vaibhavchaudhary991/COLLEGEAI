from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from django.http import FileResponse, Http404
from django.db.models import Q
import threading

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Document, DocumentCategory
from .serializers import DocumentSerializer, DocumentDetailSerializer
from .permissions import CanUploadDocument, CanDeleteDocument
from accounts.permissions import IsAdminRole, admin_required
from .services.document_service import process_document, delete_document_from_index


# ─── API Views ────────────────────────────────────────────────────────────────

class DocumentListCreateAPIView(APIView):
    """
    GET  /api/documents/ — List documents (students see active only)
    POST /api/documents/ — Upload document (admins only)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_admin_role:
            queryset = Document.objects.all()
        else:
            queryset = Document.objects.filter(is_active=True)
        serializer = DocumentSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_admin_role:
            return Response(
                {"error": "Only administrators can upload documents."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = DocumentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            document = serializer.save()
            # Kick off RAG indexing in a background thread so the API responds immediately
            threading.Thread(target=process_document, args=(document,), daemon=True).start()
            return Response(
                DocumentDetailSerializer(document, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentDetailAPIView(APIView):
    """
    GET    /api/documents/<id>/ — Document detail
    DELETE /api/documents/<id>/ — Delete document (admins only)
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            doc = Document.objects.get(pk=pk)
            if not user.is_admin_role and not doc.is_active:
                raise Http404
            return doc
        except Document.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        document = self.get_object(pk, request.user)
        serializer = DocumentDetailSerializer(document, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, pk):
        if not request.user.is_admin_role:
            return Response(
                {"error": "Only administrators can delete documents."},
                status=status.HTTP_403_FORBIDDEN,
            )
        document = self.get_object(pk, request.user)
        # Remove from vector DB before deleting the file/record
        delete_document_from_index(document.id)
        document.file.delete(save=False)  # Delete file from storage
        document.delete()
        return Response({"message": "Document deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class DocumentToggleActiveAPIView(APIView):
    """PATCH /api/documents/<id>/toggle/ — Activate or deactivate a document."""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not request.user.is_admin_role:
            return Response({"error": "Admins only."}, status=status.HTTP_403_FORBIDDEN)
        document = get_object_or_404(Document, pk=pk)
        document.is_active = not document.is_active
        document.save()
        return Response({"is_active": document.is_active, "message": f"Document {'activated' if document.is_active else 'deactivated'}."})


# ─── Template Views ────────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class DocumentListView(View):
    """Student/Admin document list page."""
    def get(self, request):
        if request.user.is_admin_role:
            documents = Document.objects.all()
        else:
            documents = Document.objects.filter(is_active=True)
        return render(request, 'documents/list.html', {'documents': documents})


@method_decorator(login_required, name='dispatch')
class DocumentDetailView(View):
    """Document detail page."""
    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        if not request.user.is_admin_role and not document.is_active:
            raise Http404
        return render(request, 'documents/detail.html', {'document': document})


@method_decorator(login_required, name='dispatch')
class DocumentUploadView(View):
    """Admin-only document upload page."""
    def get(self, request):
        if not request.user.is_admin_role:
            messages.error(request, 'Access denied. Admins only.')
            return redirect('documents:list')
        categories = DocumentCategory.objects.filter(is_active=True)
        return render(request, 'documents/upload.html', {'categories': categories})

    def post(self, request):
        if not request.user.is_admin_role:
            messages.error(request, 'Access denied. Admins only.')
            return redirect('documents:list')

        serializer = DocumentSerializer(data=request.POST | request.FILES, context={'request': request})
        if serializer.is_valid():
            document = serializer.save()
            # Kick off RAG indexing in a background thread
            threading.Thread(target=process_document, args=(document,), daemon=True).start()
            messages.success(request, 'Document uploaded and queued for AI indexing.')
            return redirect('documents:admin_list')
        else:
            categories = DocumentCategory.objects.filter(is_active=True)
            for field, errors in serializer.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return render(request, 'documents/upload.html', {'categories': categories})


@method_decorator(login_required, name='dispatch')
class AdminDocumentListView(View):
    """Admin document management page with search and category filter."""
    def get(self, request):
        if not request.user.is_admin_role:
            messages.error(request, 'Access denied.')
            return redirect('documents:list')

        documents = Document.objects.all().select_related('uploaded_by', 'category')
        search_q = request.GET.get('q', '').strip()
        cat_filter = request.GET.get('category', '')

        if search_q:
            documents = documents.filter(
                Q(title__icontains=search_q) | Q(description__icontains=search_q)
            )
        if cat_filter:
            documents = documents.filter(category__pk=cat_filter)

        categories = DocumentCategory.objects.all()
        context = {
            'documents': documents,
            'categories': categories,
            'search_q': search_q,
            'cat_filter': cat_filter,
        }
        return render(request, 'documents/admin_list.html', context)

    def post(self, request):
        """Handle delete/toggle actions from the admin list page."""
        if not request.user.is_admin_role:
            return redirect('documents:list')

        action = request.POST.get('action')
        doc_id = request.POST.get('document_id')
        document = get_object_or_404(Document, pk=doc_id)

        if action == 'delete':
            delete_document_from_index(document.id)  # Remove from vector DB first
            document.file.delete(save=False)
            document.delete()
            messages.success(request, f'Document "{document.title}" deleted.')

        elif action == 'toggle':
            document.is_active = not document.is_active
            document.save()
            status_text = 'activated' if document.is_active else 'deactivated'
            messages.success(request, f'Document "{document.title}" {status_text}.')

        elif action == 'reindex':
            threading.Thread(target=process_document, args=(document,), daemon=True).start()
            messages.success(request, f'Re-indexing queued for "{document.title}".')

        elif action == 'reindex_all':
            active_docs = list(Document.objects.filter(is_active=True))
            def _reindex_all_worker(doc_list):
                for d in doc_list:
                    try:
                        process_document(d)
                    except Exception as exc:
                        pass
            threading.Thread(target=_reindex_all_worker, args=(active_docs,), daemon=True).start()
            messages.success(request, f'Re-indexing queued for {len(active_docs)} documents in background.')

        return redirect('documents:admin_list')


@method_decorator(login_required, name='dispatch')
class DocumentDownloadView(View):
    """Serve document file for download."""
    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        if not request.user.is_admin_role and not document.is_active:
            raise Http404
        try:
            return FileResponse(document.file.open(), as_attachment=True, filename=document.filename)
        except FileNotFoundError:
            raise Http404


@method_decorator(admin_required, name='dispatch')
class AdminDocumentEditView(View):
    """Edit document title, description, category, and active status."""
    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        categories = DocumentCategory.objects.filter(is_active=True)
        return render(request, 'documents/admin_document_edit.html', {
            'document': document,
            'categories': categories,
        })

    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category', '')
        is_active = request.POST.get('is_active') == 'on'

        if not title:
            messages.error(request, 'Title is required.')
            categories = DocumentCategory.objects.filter(is_active=True)
            return render(request, 'documents/admin_document_edit.html', {
                'document': document, 'categories': categories,
            })

        document.title = title
        document.description = description
        document.is_active = is_active
        if category_id:
            document.category = get_object_or_404(DocumentCategory, pk=category_id)
        else:
            document.category = None
        document.save()
        messages.success(request, f'Document "{document.title}" updated successfully.')
        return redirect('documents:admin_list')


# ─── Category Management Views ────────────────────────────────────────────────

@method_decorator(admin_required, name='dispatch')
class AdminCategoryListView(View):
    """List all document categories."""
    def get(self, request):
        categories = DocumentCategory.objects.all()
        return render(request, 'documents/admin_categories.html', {'categories': categories})


@method_decorator(admin_required, name='dispatch')
class AdminCategoryCreateView(View):
    """Create a new document category."""
    def post(self, request):
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if not name:
            messages.error(request, 'Category name is required.')
            return redirect('documents:admin_categories')
        if DocumentCategory.objects.filter(name__iexact=name).exists():
            messages.error(request, f'A category named "{name}" already exists.')
            return redirect('documents:admin_categories')
        DocumentCategory.objects.create(name=name, description=description, is_active=True)
        messages.success(request, f'Category "{name}" created successfully.')
        return redirect('documents:admin_categories')


@method_decorator(admin_required, name='dispatch')
class AdminCategoryEditView(View):
    """Edit an existing category."""
    def get(self, request, pk):
        category = get_object_or_404(DocumentCategory, pk=pk)
        return render(request, 'documents/admin_category_edit.html', {'category': category})

    def post(self, request, pk):
        category = get_object_or_404(DocumentCategory, pk=pk)
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if not name:
            messages.error(request, 'Category name is required.')
            return render(request, 'documents/admin_category_edit.html', {'category': category})
        if DocumentCategory.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, f'A category named "{name}" already exists.')
            return render(request, 'documents/admin_category_edit.html', {'category': category})
        category.name = name
        category.description = description
        category.save()
        messages.success(request, f'Category "{name}" updated.')
        return redirect('documents:admin_categories')


@method_decorator(admin_required, name='dispatch')
class AdminCategoryToggleView(View):
    """Toggle a category active/inactive."""
    def post(self, request, pk):
        category = get_object_or_404(DocumentCategory, pk=pk)
        category.is_active = not category.is_active
        category.save()
        action = 'activated' if category.is_active else 'deactivated'
        messages.success(request, f'Category "{category.name}" {action}.')
        return redirect('documents:admin_categories')
