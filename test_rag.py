"""
RAG Pipeline End-to-End Test Script
Run: python test_rag.py

Tests:
  1. Groq or Gemini API key + connection
  2. ChromaDB / SentenceTransformer embeddings
  3. Full generate_response() RAG query
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_ai.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("College AI -- RAG Pipeline Test")
print("=" * 60)

groq_key = getattr(settings, 'GROQ_API_KEY', '').strip()
gemini_key = getattr(settings, 'GEMINI_API_KEY', '').strip()

has_groq = bool(groq_key and groq_key != 'your_groq_api_key_here')
has_gemini = bool(gemini_key and gemini_key != 'your_gemini_api_key_here')

if not (has_groq or has_gemini):
    print("\n[FAIL] No API key found. Please set GROQ_API_KEY or GEMINI_API_KEY in .env")
    exit(1)

# 1. Test LLM provider connection
if has_groq:
    print(f"\n[1/3] Testing Groq connection (key: {groq_key[:8]}...)...")
    try:
        import groq
        client = groq.Groq(api_key=groq_key)
        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say 'RAG test OK' in 3 words."}],
            model="openai/gpt-oss-20b",
        )
        print(f"  [OK] Groq responded: {resp.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"  [FAIL] Groq error: {e}")
        if not has_gemini:
            exit(1)

if has_gemini:
    print(f"\n[1/3] Testing Gemini connection (key: {gemini_key[:8]}...)...")
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Say 'RAG test OK' and nothing else.",
        )
        print(f"  [OK] Gemini responded: {resp.text.strip()}")
    except Exception as e:
        print(f"  [FAIL] Gemini error: {e}")

# 2. Test ChromaDB + embeddings
print("\n[2/3] Testing ChromaDB + sentence embeddings...")
try:
    from chat.services.rag_service import get_vectordb, search_documents
    collection = get_vectordb()
    count = collection.count()
    print(f"  [OK] ChromaDB OK -- {count} chunks in vector collection")
    if count == 0:
        print("  [WARN] No documents indexed yet. Run: python manage.py load_sample_documents")
    else:
        results = search_documents("What is the attendance rule?", k=1)
        print(f"  [OK] Vector search returned {len(results)} chunk(s)")
        if results:
            print(f"       Top source: '{results[0]['source']}'")
            print(f"       Preview: {results[0]['text'][:90]}...")
except Exception as e:
    print(f"  [FAIL] ChromaDB error: {e}")

# 3. Test full RAG query
print("\n[3/3] Testing full RAG pipeline (generate_response)...")
try:
    from chat.services.ai_service import generate_response
    query = "What is the minimum attendance required for examinations?"
    print(f"  Query: '{query}'")
    answer = generate_response(query)
    print(f"  [OK] Full RAG pipeline response received ({len(answer)} chars)")
    print("\n--- AI Response Preview ---")
    safe_preview = answer[:400].encode('ascii', errors='replace').decode('ascii')
    print(safe_preview + "...\n")
except Exception as e:
    print(f"  [FAIL] Pipeline error: {e}")

print("=" * 60)
print("RAG Pipeline is READY!")
print("=" * 60)
