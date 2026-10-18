"""
Management command: reindex_all_documents

Re-index all active documents into ChromaDB. Useful when:
  - The chroma_db/ folder was deleted or corrupted
  - You want to rebuild the entire vector index from scratch
  - New documents were added directly to the DB without going through upload

Usage:
  python manage.py reindex_all_documents           # Index all active documents
  python manage.py reindex_all_documents --all      # Index ALL documents (including inactive)
  python manage.py reindex_all_documents --clear    # Clear the entire collection first
"""

from django.core.management.base import BaseCommand
from documents.models import Document
from documents.services.document_service import process_document


class Command(BaseCommand):
    help = 'Re-index all documents into ChromaDB for RAG search'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Index ALL documents, including inactive ones',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear the entire vector collection before re-indexing',
        )

    def handle(self, *args, **options):
        index_all = options['all']
        clear_first = options['clear']

        if clear_first:
            self.stdout.write(self.style.WARNING('Clearing entire vector collection...'))
            try:
                from chat.services.rag_service import get_vectordb
                collection = get_vectordb()
                # Delete all entries
                ids = collection.get()['ids']
                if ids:
                    collection.delete(ids=ids)
                self.stdout.write(self.style.SUCCESS(f'  Cleared {len(ids)} chunks from collection.'))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'  Failed to clear: {exc}'))
                return

        # Select documents to index
        if index_all:
            queryset = Document.objects.all()
            self.stdout.write(f'\nRe-indexing ALL {queryset.count()} documents...\n')
        else:
            queryset = Document.objects.filter(is_active=True)
            self.stdout.write(f'\nRe-indexing {queryset.count()} active documents...\n')

        success_count = 0
        fail_count = 0
        empty_count = 0

        for doc in queryset:
            self.stdout.write(f'  [{doc.id}] {doc.title} ({doc.file_type})... ', ending='')
            result = process_document(doc)

            if result['status'] == 'success':
                success_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'OK ({result["chunk_count"]} chunks)'
                ))
            elif result['status'] == 'empty':
                empty_count += 1
                self.stdout.write(self.style.WARNING('EMPTY (no text extracted)'))
            else:
                fail_count += 1
                self.stdout.write(self.style.ERROR(
                    f'FAILED: {result["message"][:80]}'
                ))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done: {success_count} indexed, {empty_count} empty, {fail_count} failed'))

        # Show final collection stats
        try:
            from chat.services.rag_service import get_vectordb
            collection = get_vectordb()
            self.stdout.write(f'Vector DB now has {collection.count()} total chunks.')
        except Exception:
            pass
