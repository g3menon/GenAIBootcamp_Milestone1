"""
Phase 3 — ChromaDB Store

Handles creating, populating, and querying the ChromaDB collection.
Persists data to disk so it survives process restarts.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings

from phase3.vectorstore.config import (
    CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME, PROCESSED_CHUNKS_FILE
)
from phase3.vectorstore.embedder import Embedder

logger = logging.getLogger("phase3")


class VectorStore:
    """Manages ChromaDB collection for HDFC Mutual Fund chunks."""

    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR,
                 collection_name: str = CHROMA_COLLECTION_NAME):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._embedder = None

    @property
    def client(self) -> chromadb.ClientAPI:
        """Lazy-init ChromaDB persistent client."""
        if self._client is None:
            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.persist_dir)
            logger.info(f"ChromaDB client initialized at: {self.persist_dir}")
        return self._client

    @property
    def collection(self):
        """Get or create the collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "HDFC Mutual Fund chunks for RAG retrieval"}
            )
            logger.info(f"Collection '{self.collection_name}' ready — {self._collection.count()} vectors")
        return self._collection

    @property
    def embedder(self) -> Embedder:
        """Lazy-init embedder."""
        if self._embedder is None:
            self._embedder = Embedder()
        return self._embedder

    def load_chunks(self, chunks_file: str | Path = PROCESSED_CHUNKS_FILE) -> list[dict]:
        """Load processed chunks from Phase 2 output."""
        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        logger.info(f"Loaded {len(chunks)} chunks from {chunks_file}")
        return chunks

    def build_index(self, chunks: Optional[list[dict]] = None, force_rebuild: bool = False):
        """
        Build the vector store index from processed chunks.
        
        Args:
            chunks: List of chunk dicts. If None, loads from PROCESSED_CHUNKS_FILE.
            force_rebuild: If True, deletes existing collection and rebuilds.
        """
        if chunks is None:
            chunks = self.load_chunks()

        # Force rebuild: delete and recreate collection
        if force_rebuild:
            try:
                self.client.delete_collection(self.collection_name)
                self._collection = None
                logger.info(f"Deleted existing collection '{self.collection_name}'")
            except Exception:
                pass

        # Check if already populated
        current_count = self.collection.count()
        if current_count > 0 and not force_rebuild:
            logger.info(f"Collection already has {current_count} vectors. Use force_rebuild=True to rebuild.")
            return current_count

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_id = chunk["chunk_id"]
            content = chunk["content"]
            metadata = {
                "fund_id": chunk.get("fund_id", ""),
                "fund_name": chunk.get("fund_name", ""),
                "chunk_type": chunk.get("chunk_type", ""),
                "source_url": chunk.get("source_url", ""),
                "last_updated": chunk.get("last_updated", ""),
            }
            # Add metadata_tags as comma-separated string (ChromaDB doesn't support list metadata)
            tags = chunk.get("metadata_tags", [])
            if tags:
                metadata["metadata_tags"] = ",".join(tags)

            ids.append(chunk_id)
            documents.append(content)
            metadatas.append(metadata)

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(documents)} chunks...")
        embeddings = self.embedder.embed_texts(documents)

        # Add to ChromaDB in batches (ChromaDB supports up to 41666 per batch)
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            end = min(i + batch_size, len(ids))
            self.collection.add(
                ids=ids[i:end],
                embeddings=embeddings[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end],
            )

        total = self.collection.count()
        logger.info(f"✅ Indexed {total} vectors in '{self.collection_name}'")
        return total

    def get_collection_count(self) -> int:
        """Get the number of vectors in the collection."""
        return self.collection.count()

    def collection_exists(self) -> bool:
        """Check if the collection exists and has data."""
        try:
            return self.collection.count() > 0
        except Exception:
            return False

    def delete_collection(self):
        """Delete the entire collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self._collection = None
            logger.info(f"Collection '{self.collection_name}' deleted")
        except Exception as e:
            logger.warning(f"Could not delete collection: {e}")
