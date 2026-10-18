"""
Document Processing Service — RAG indexing pipeline.

When a document is uploaded, process_document() is called to:
  1. Extract raw text from PDF / DOCX / TXT
  2. Split text into overlapping chunks
  3. Embed chunks and upsert into ChromaDB with metadata

When a document is deleted, delete_document_from_index() removes its
chunks from ChromaDB so they're no longer retrieved.
"""

import logging
import uuid

from documents.models import Document

logger = logging.getLogger(__name__)

# ─── Chunking settings ─────────────────────────────────────────────────────────
CHUNK_SIZE = 500        # characters per chunk
CHUNK_OVERLAP = 50      # overlap between consecutive chunks


# ─── Text Extraction ───────────────────────────────────────────────────────────

def _extract_text_pdf(file_path: str) -> str:
    """Extract full text from a PDF file."""
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _extract_text_docx(file_path: str) -> str:
    """Extract full text from a DOCX file."""
    from docx import Document as DocxDocument
    doc = DocxDocument(file_path)
    return "\n".join(para.text for para in doc.paragraphs)


def _extract_text_txt(file_path: str) -> str:
    """Read a plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _extract_text(document: Document) -> str:
    """Dispatch text extraction based on document file_type."""
    file_path = document.file.path
    file_type = document.file_type.lower()

    if file_type == "pdf":
        return _extract_text_pdf(file_path)
    elif file_type == "docx":
        return _extract_text_docx(file_path)
    elif file_type == "txt":
        return _extract_text_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


# ─── Chunking ──────────────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text:       Full document text.
        chunk_size: Max characters per chunk.
        overlap:    Characters shared between consecutive chunks.

    Returns:
        List of text chunk strings.
    """
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == text_len:
            break
        start = end - overlap  # slide back by overlap

    return chunks


# ─── Public API ────────────────────────────────────────────────────────────────

def process_document(document: Document) -> dict:
    """
    Index a document into ChromaDB for RAG retrieval.

    Steps:
        1. Extract text from the document file
        2. Split text into overlapping chunks
        3. Embed and upsert chunks into ChromaDB
        4. Mark document.is_indexed = True in the DB

    Args:
        document: The Document model instance to process.

    Returns:
        dict with status, chunk count, and message.
    """
    try:
        # Import here to avoid circular imports at module load time
        from chat.services.rag_service import get_vectordb

        # Step 1: Extract text
        logger.info("RAG indexing: extracting text from document '%s' (id=%s)", document.title, document.id)
        text = _extract_text(document)

        if not text.strip():
            document.is_indexed = False
            document.index_error = "No text could be extracted from this file."
            document.save(update_fields=["is_indexed", "index_error"])
            logger.warning("RAG indexing: no text extracted from document id=%s", document.id)
            return {"status": "empty", "message": "No text extracted.", "document_id": document.id}

        # Step 2: Split into chunks
        chunks = _chunk_text(text)
        logger.info("RAG indexing: %d chunks from document id=%s", len(chunks), document.id)

        # Step 3: Build IDs and metadata for ChromaDB
        # Each chunk gets a stable, unique ID: "doc_<id>_chunk_<n>"
        ids = [f"doc_{document.id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "doc_id": str(document.id),
                "title": document.title,
                "category": document.category.name if document.category else "Uncategorized",
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        # Step 4: Upsert into ChromaDB (upsert = insert or update)
        collection = get_vectordb()
        collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)

        # Step 5: Mark as indexed in Django DB
        document.is_indexed = True
        document.index_error = ""
        document.save(update_fields=["is_indexed", "index_error"])

        logger.info("RAG indexing: successfully indexed %d chunks for document id=%s", len(chunks), document.id)
        return {
            "status": "success",
            "chunk_count": len(chunks),
            "document_id": document.id,
            "message": f"Indexed {len(chunks)} chunks successfully.",
        }

    except Exception as exc:
        error_msg = str(exc)
        logger.error("RAG indexing failed for document id=%s: %s", document.id, error_msg, exc_info=True)

        # Record the error on the document
        document.is_indexed = False
        document.index_error = error_msg[:500]  # Truncate to fit the field
        document.save(update_fields=["is_indexed", "index_error"])

        return {
            "status": "error",
            "message": error_msg,
            "document_id": document.id,
        }


def delete_document_from_index(document_id: int) -> None:
    """
    Remove all ChromaDB chunks belonging to a document.
    Called before deleting a Document instance from the DB.

    Args:
        document_id: The Django primary key of the Document being deleted.
    """
    try:
        from chat.services.rag_service import get_vectordb
        collection = get_vectordb()

        # ChromaDB supports filtering by metadata for deletion
        collection.delete(where={"doc_id": str(document_id)})
        logger.info("RAG: removed chunks for document id=%s from vector DB", document_id)

    except Exception as exc:
        logger.error("RAG: failed to remove document id=%s from vector DB: %s", document_id, exc, exc_info=True)
