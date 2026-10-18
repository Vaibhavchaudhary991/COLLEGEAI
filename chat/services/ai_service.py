"""
AI Service — RAG-powered response generation for College AI Assistant.

Supports both Groq (Llama / GPT-OSS / Qwen) and Google Gemini LLMs.
If GROQ_API_KEY is configured in .env, Groq is used for ultra-fast responses.
If GEMINI_API_KEY is configured in .env, Gemini is used.

Pipeline:
  1. Embed the question and search ChromaDB for top relevant college document chunks
  2. Build a structured prompt with system instructions + retrieved context + history
  3. Send prompt to LLM (Groq or Gemini)
  4. Return the generated answer with clear source citations
"""

import logging
from django.conf import settings
from .rag_service import search_documents, build_prompt

logger = logging.getLogger(__name__)


def _call_groq(prompt: str) -> str:
    """Call Groq API using available chat completion models."""
    import groq
    api_key = getattr(settings, 'GROQ_API_KEY', '').strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured")

    client = groq.Groq(api_key=api_key)
    # Available models in priority order
    candidate_models = [
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]

    last_exc = None
    for model_name in candidate_models:
        try:
            logger.info("Calling Groq model '%s'...", model_name)
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model_name,
                temperature=0.3,
                max_tokens=1024,
            )
            answer = response.choices[0].message.content
            if answer:
                return answer.strip()
        except Exception as e:
            last_exc = e
            # If model not found or error, continue to next candidate
            logger.warning("Groq model %s failed: %s, trying next...", model_name, e)
            continue

    raise last_exc or RuntimeError("All Groq candidate models failed.")


def _call_gemini(prompt: str) -> str:
    """Call Google Gemini using the google-genai SDK."""
    from google import genai
    api_key = getattr(settings, 'GEMINI_API_KEY', '').strip()
    if not api_key or api_key == 'your_gemini_api_key_here':
        raise ValueError("GEMINI_API_KEY is not set in .env")

    client = genai.Client(api_key=api_key)
    for model_name in ["gemini-2.0-flash", "gemini-1.5-flash"]:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            logger.warning("Gemini model %s failed: %s", model_name, e)
            continue
    raise RuntimeError("Gemini API call failed.")


def generate_response(question: str, chat_history: list = None) -> str:
    """
    Generate an AI response using the full RAG pipeline.

    Args:
        question:     The student's question/query.
        chat_history: Optional list of previous messages [{sender, message}, ...].

    Returns:
        str: Clean markdown response answering the query with source references.
    """
    try:
        # Step 1: Retrieve relevant college document chunks
        chunks = search_documents(question, k=3)
        logger.info("RAG: Retrieved %d chunks for student question: '%s'", len(chunks), question[:80])

        # Step 2: Build structured prompt
        prompt = build_prompt(question, chunks, chat_history)

        # Step 3: Dispatch to LLM (Groq first if available, then Gemini)
        groq_key = getattr(settings, 'GROQ_API_KEY', '').strip()
        gemini_key = getattr(settings, 'GEMINI_API_KEY', '').strip()

        answer = None
        if groq_key and groq_key != 'your_groq_api_key_here':
            try:
                answer = _call_groq(prompt)
            except Exception as e:
                logger.error("Groq generation failed: %s", e)
                if gemini_key and gemini_key != 'your_gemini_api_key_here':
                    logger.info("Falling back to Gemini...")
                    answer = _call_gemini(prompt)
                else:
                    raise

        elif gemini_key and gemini_key != 'your_gemini_api_key_here':
            answer = _call_gemini(prompt)

        else:
            return (
                "⚠️ **AI Assistant Configuration Needed**\n\n"
                "Please add an API key in your `.env` file to enable responses:\n"
                "- **GROQ_API_KEY** (from [console.groq.com](https://console.groq.com/keys))\n"
                "- OR **GEMINI_API_KEY** (from [aistudio.google.com](https://aistudio.google.com/app/apikey))"
            )

        # Step 4: Append clean citation badges if sources were retrieved
        if chunks:
            sources = list(dict.fromkeys(c["source"] for c in chunks if c.get("source")))
            if sources:
                sources_text = "\n\n---\n📚 **Relevant Documents Consulted:** " + " • ".join(f"`{s}`" for s in sources)
                answer = answer + sources_text

        return answer

    except Exception as exc:
        logger.error("RAG generate_response error: %s", exc, exc_info=True)
        return (
            "I encountered an issue retrieving the information right now. "
            "Please try again in a moment.\n\n"
            f"*Technical details: {str(exc)}*"
        )
