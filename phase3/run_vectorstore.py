"""
Phase 3 — CLI Entry Point

Build, query, and manage the vector store.

Usage:
    python -m phase3.run_vectorstore              # Build/rebuild the vector store
    python -m phase3.run_vectorstore --rebuild     # Force rebuild from scratch
    python -m phase3.run_vectorstore --query "What is the expense ratio?"
    python -m phase3.run_vectorstore --stats       # Show vector store stats
"""

import argparse
import sys
import io
import logging
from pathlib import Path

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("phase3")

from phase3.vectorstore.store import VectorStore
from phase3.vectorstore.retriever import Retriever
from phase3.vectorstore.config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME


def build_store(force_rebuild: bool = False):
    """Build or update the vector store."""
    logger.info("🚀 Building vector store...")
    store = VectorStore()
    count = store.build_index(force_rebuild=force_rebuild)

    print(f"\n{'='*60}")
    print(f"📊 Vector Store Build Complete")
    print(f"{'='*60}")
    print(f"  Collection: {CHROMA_COLLECTION_NAME}")
    print(f"  Vectors: {count}")
    print(f"  Persist Dir: {CHROMA_PERSIST_DIR}")
    print(f"{'='*60}\n")


def query_store(query: str, top_k: int = 3, fund_filter: str = None):
    """Query the vector store."""
    retriever = Retriever()
    results = retriever.retrieve(query, top_k=top_k, fund_filter=fund_filter)

    print(f"\n{'='*60}")
    print(f"🔍 Query: \"{query}\"")
    if fund_filter:
        print(f"   Fund Filter: {fund_filter}")
    print(f"   Top-K: {top_k}")
    print(f"{'='*60}")

    if not results:
        print("  No results found.")
    else:
        for i, r in enumerate(results):
            print(f"\n  [{i+1}] Score: {r['similarity_score']:.4f} | Type: {r['chunk_type']}")
            print(f"      Fund: {r['fund_name']}")
            print(f"      ID: {r['chunk_id']}")
            print(f"      Content: {r['content'][:200]}...")
            print(f"      Source: {r['source_url']}")

    print(f"\n{'='*60}\n")


def show_stats():
    """Show vector store statistics."""
    retriever = Retriever()
    stats = retriever.get_store_stats()

    print(f"\n{'='*60}")
    print(f"📊 Vector Store Statistics")
    print(f"{'='*60}")
    for key, val in stats.items():
        print(f"  {key}: {val}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3 — Vector Store & Embedding Management"
    )
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild the vector store")
    parser.add_argument("--query", type=str, help="Query the vector store")
    parser.add_argument("--top-k", type=int, default=3, help="Number of results to return")
    parser.add_argument("--fund", type=str, default=None, help="Filter by fund_id")
    parser.add_argument("--stats", action="store_true", help="Show vector store statistics")

    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.query:
        query_store(args.query, top_k=args.top_k, fund_filter=args.fund)
    else:
        build_store(force_rebuild=args.rebuild)


if __name__ == "__main__":
    main()
