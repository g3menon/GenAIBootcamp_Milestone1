"""
Phase 3 — Embedder

Generates vector embeddings for text chunks using sentence-transformers.
Uses all-MiniLM-L6-v2 (384-dimension, free, fast).
"""

import logging
from sentence_transformers import SentenceTransformer
from phase3.vectorstore.config import EMBEDDING_MODEL

logger = logging.getLogger("phase3")


class Embedder:
    """Generates embeddings using a sentence-transformer model."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the model on first use."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded — dimension: {self._model.get_sentence_embedding_dimension()}")
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text string."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        embeddings = self.model.encode(texts, batch_size=batch_size, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()

    def get_dimension(self) -> int:
        """Return embedding dimension of the loaded model."""
        return self.model.get_sentence_embedding_dimension()
