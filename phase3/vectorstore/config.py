"""
Phase 3 — Configuration

Model names, collection config, paths for vector store.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root .env
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# ─── Embedding Model ───────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 produces 384-dim vectors

# ─── ChromaDB ──────────────────────────────────────────────────────
CHROMA_PERSIST_DIR = str(Path(__file__).resolve().parent.parent / "data" / "chroma_db")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "hdfc_mutual_funds")

# ─── Paths ─────────────────────────────────────────────────────────
PROCESSED_CHUNKS_FILE = Path(__file__).resolve().parent.parent.parent / "phase2" / "data" / "processed" / "processed_chunks.json"

# ─── Retrieval Defaults ────────────────────────────────────────────
DEFAULT_TOP_K = 3
MAX_TOP_K = 10

# ─── Gemini Model (for reference by other phases) ─────────────────
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
