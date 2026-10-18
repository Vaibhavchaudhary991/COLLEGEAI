"""
RAG Service — Core retrieval-augmented generation engine.

Responsibilities:
  1. Maintain a single ChromaDB client instance (get_vectordb)
  2. Embed a question and fetch top-k matching document chunks (search_documents)
  3. Build a structured prompt for the LLM (build_prompt)

Called by:
  - chat/services/ai_service.py  → generate_response()
  - documents/services/document_service.py → process_document() / delete_document_from_index()
"""

import logging
from functools import lru_cache

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from django.conf import settings

logger = logging.getLogger(__name__)

# ─── ChromaDB collection name ──────────────────────────────────────────────────
COLLECTION_NAME = "college_documents"

# ─── Embedding model (free, runs locally, no API key needed) ───────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_embedding_function():
    """Return a cached SentenceTransformer embedding function."""
    return SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)


def get_vectordb() -> chromadb.Collection:
    """
    Return the ChromaDB collection, creating it if it doesn't exist.
    The database is persisted at settings.CHROMA_DB_PATH.
    """
    client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def search_documents(question: str, k: int = 3) -> list[dict]:
    """
    Embed the question and retrieve the top-k most relevant document chunks.

    Args:
        question: The user's question string.
        k:        Number of chunks to retrieve.

    Returns:
        List of dicts, each with:
          - text      (str)  : The chunk content
          - source    (str)  : Document title
          - doc_id    (int)  : Document primary key in Django DB
          - distance  (float): Cosine distance (lower = more relevant)
    """
    try:
        collection = get_vectordb()
        count = collection.count()
        if count == 0:
            logger.info("RAG: Vector DB is empty — no documents indexed yet.")
            return []

        results = collection.query(
            query_texts=[question],
            n_results=min(k, count),
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for text, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append({
                "text": text,
                "source": meta.get("title", "Unknown"),
                "doc_id": meta.get("doc_id", ""),
                "distance": dist,
            })

        return chunks

    except Exception as exc:
        logger.error("RAG search_documents error: %s", exc, exc_info=True)
        return []


def build_prompt(question: str, chunks: list[dict], chat_history: list = None) -> str:
    """
    Build a structured prompt combining:
      - System role instruction
      - Retrieved document context
      - Optional conversation history
      - The user's question

    Args:
        question:     The user's latest question.
        chunks:       Retrieved document chunks from search_documents().
        chat_history: List of previous messages [{sender, message}, ...].

    Returns:
        A single prompt string ready to send to the LLM.
    """
    # System instruction
    system = (
        "You are the official College AI Student Assistant, dedicated to helping students with "
        "their academic policies, exam rules, placement procedures, hostel regulations, campus facilities, "
        "and general student life questions.\n\n"
        "Instructions:\n"
        "1. Prioritize and base your answers on the relevant college documents provided below whenever applicable.\n"
        "2. Provide clear, empathetic, and accurate responses formatted with clean Markdown (use bullet points, bold key terms/dates, and concise paragraphs).\n"
        "3. If specific details (like a particular date or fee) are not covered in the documents, state that clearly and advise the student which office to contact (e.g. Dean of Academics, Placement Cell, Warden, or Exam Section).\n"
        "4. Keep your tone encouraging, professional, and student-focused."
    )

    # Build context block from retrieved chunks
    if chunks:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i}: {chunk['source']}]\n{chunk['text']}"
            )
        context_block = "\n\n".join(context_parts)
        context_section = f"\n\n--- Relevant College Documents ---\n{context_block}\n---"
    else:
        context_section = "\n\n[No relevant documents found in the knowledge base.]"

    # Build conversation history block
    history_section = ""
    if chat_history:
        history_lines = []
        for msg in chat_history[-6:]:  # Last 6 messages for context window efficiency
            role = "Student" if msg["sender"] == "user" else "Assistant"
            history_lines.append(f"{role}: {msg['message']}")
        if history_lines:
            history_section = "\n\nConversation History:\n" + "\n".join(history_lines)

    prompt = (
        f"{system}"
        f"{context_section}"
        f"{history_section}"
        f"\n\nStudent Question: {question}"
        f"\n\nAnswer:"
    )
    return prompt
