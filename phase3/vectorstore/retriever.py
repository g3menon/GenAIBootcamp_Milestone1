"""
Phase 3 — Retriever

Query interface for retrieving relevant chunks from the vector store.
Supports semantic search, metadata filtering, and similarity scores.
"""

import logging
from typing import Optional

from phase3.vectorstore.store import VectorStore
from phase3.vectorstore.embedder import Embedder
from phase3.vectorstore.config import DEFAULT_TOP_K, MAX_TOP_K

logger = logging.getLogger("phase3")


class Retriever:
    """
    Retrieves relevant chunks from ChromaDB using semantic search.

    Usage:
        retriever = Retriever()
        results = retriever.retrieve("What is the expense ratio of HDFC Pharma Fund?")
    """

    def __init__(self, store: Optional[VectorStore] = None):
        self.store = store or VectorStore()
        self._embedder = None

    @property
    def embedder(self) -> Embedder:
        """Lazy-init the embedder."""
        if self._embedder is None:
            self._embedder = Embedder()
        return self._embedder

    def retrieve(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        fund_filter: Optional[str] = None,
        chunk_type_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Retrieve top-k relevant chunks for a query.

        Args:
            query: User's natural language question
            top_k: Number of results to return (default: 3, max: 10)
            fund_filter: Optional fund_id to filter results (e.g., "hdfc_pharma_healthcare")
            chunk_type_filter: Optional chunk_type to filter (e.g., "costs")

        Returns:
            List of dicts with keys: chunk_id, content, fund_name, source_url,
            chunk_type, metadata, distance, similarity_score
        """
        if not query or not query.strip():
            logger.warning("Empty query received")
            return []

        # Clamp top_k
        top_k = max(1, min(top_k, MAX_TOP_K))

        # Build where filter
        where_filter = self._build_where_filter(fund_filter, chunk_type_filter)

        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)

        # Query ChromaDB
        try:
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"],
            }
            if where_filter:
                query_params["where"] = where_filter

            results = self.store.collection.query(**query_params)
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return []

        # Parse results
        return self._parse_results(results)

    def _build_where_filter(
        self,
        fund_filter: Optional[str],
        chunk_type_filter: Optional[str],
    ) -> Optional[dict]:
        """Build ChromaDB where filter from optional parameters."""
        conditions = []

        if fund_filter:
            conditions.append({"fund_id": {"$eq": fund_filter}})
        if chunk_type_filter:
            conditions.append({"chunk_type": {"$eq": chunk_type_filter}})

        if len(conditions) == 0:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}

    def _parse_results(self, raw_results: dict) -> list[dict]:
        """Parse ChromaDB results into a clean list of dicts."""
        parsed = []

        if not raw_results or not raw_results.get("ids"):
            return parsed

        ids = raw_results["ids"][0]
        documents = raw_results["documents"][0] if raw_results.get("documents") else [None] * len(ids)
        metadatas = raw_results["metadatas"][0] if raw_results.get("metadatas") else [{}] * len(ids)
        distances = raw_results["distances"][0] if raw_results.get("distances") else [0.0] * len(ids)

        for i, chunk_id in enumerate(ids):
            metadata = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else 0.0

            # Convert distance to similarity score (ChromaDB uses L2 distance by default)
            # Lower distance = more similar; we convert to 0-1 score
            similarity = max(0.0, 1.0 - (distance / 2.0))

            parsed.append({
                "chunk_id": chunk_id,
                "content": documents[i] if i < len(documents) else "",
                "fund_id": metadata.get("fund_id", ""),
                "fund_name": metadata.get("fund_name", ""),
                "source_url": metadata.get("source_url", ""),
                "chunk_type": metadata.get("chunk_type", ""),
                "metadata_tags": metadata.get("metadata_tags", ""),
                "last_updated": metadata.get("last_updated", ""),
                "distance": round(distance, 4),
                "similarity_score": round(similarity, 4),
            })

        return parsed

    def get_store_stats(self) -> dict:
        """Get vector store statistics."""
        count = self.store.get_collection_count()
        return {
            "collection_name": self.store.collection_name,
            "vector_count": count,
            "embedding_model": self.embedder.model_name,
            "embedding_dimension": self.embedder.get_dimension(),
        }
