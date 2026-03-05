"""
Phase 3 — Tests for Embedder, Store, and Retriever

Covers T3.1–T3.10 from the architecture test cases.
"""

import sys
import json
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

# Suppress noisy logs during tests
logging.basicConfig(level=logging.WARNING)


# ─── Embedder Tests ─────────────────────────────────────────────────
class TestEmbedder:
    """Test embedding generation."""

    @pytest.fixture(scope="class")
    def embedder(self):
        from phase3.vectorstore.embedder import Embedder
        return Embedder()

    def test_embed_single_text(self, embedder):
        """Embedding a single text produces a list of floats."""
        vec = embedder.embed_text("What is the expense ratio?")
        assert isinstance(vec, list)
        assert len(vec) > 0
        assert all(isinstance(v, float) for v in vec)

    def test_embed_dimension(self, embedder):
        """Embedding dimension matches expected (384 for MiniLM)."""
        dim = embedder.get_dimension()
        assert dim == 384

    def test_embed_batch(self, embedder):
        """Batch embedding produces correct number of vectors."""
        texts = ["text one", "text two", "text three"]
        vecs = embedder.embed_texts(texts)
        assert len(vecs) == 3
        assert all(len(v) == 384 for v in vecs)

    def test_embed_empty_text(self, embedder):
        """Empty text should not crash."""
        vec = embedder.embed_text("")
        assert isinstance(vec, list)
        assert len(vec) == 384


# ─── Store Tests ─────────────────────────────────────────────────────
class TestStore:
    """Test ChromaDB store operations."""

    @pytest.fixture(scope="class")
    def store(self, tmp_path_factory):
        """Create a temporary store for testing."""
        from phase3.vectorstore.store import VectorStore
        tmp_dir = str(tmp_path_factory.mktemp("test_chroma"))
        return VectorStore(persist_dir=tmp_dir, collection_name="test_collection")

    @pytest.fixture
    def sample_chunks(self):
        return [
            {
                "chunk_id": "test_fund_overview",
                "fund_id": "test_fund",
                "fund_name": "Test Fund",
                "source_url": "https://example.com",
                "chunk_type": "overview",
                "metadata_tags": ["fund_name", "category"],
                "content": "Test Fund is an equity mutual fund.",
                "last_updated": "2026-01-01T00:00:00"
            },
            {
                "chunk_id": "test_fund_costs",
                "fund_id": "test_fund",
                "fund_name": "Test Fund",
                "source_url": "https://example.com",
                "chunk_type": "costs",
                "metadata_tags": ["expense_ratio"],
                "content": "The expense ratio of Test Fund is 0.8%.",
                "last_updated": "2026-01-01T00:00:00"
            },
            {
                "chunk_id": "other_fund_overview",
                "fund_id": "other_fund",
                "fund_name": "Other Fund",
                "source_url": "https://other.com",
                "chunk_type": "overview",
                "metadata_tags": ["fund_name"],
                "content": "Other Fund is a debt mutual fund.",
                "last_updated": "2026-01-01T00:00:00"
            },
        ]

    def test_t3_2_collection_created(self, store):
        """T3.2: ChromaDB collection created."""
        assert store.collection is not None
        assert store.collection_name == "test_collection"

    def test_build_index(self, store, sample_chunks):
        """Building index adds vectors."""
        count = store.build_index(chunks=sample_chunks, force_rebuild=True)
        assert count == 3

    def test_collection_count(self, store, sample_chunks):
        """Collection count matches indexed chunks."""
        store.build_index(chunks=sample_chunks, force_rebuild=True)
        assert store.get_collection_count() == 3

    def test_collection_exists(self, store, sample_chunks):
        """Collection exists check works."""
        store.build_index(chunks=sample_chunks, force_rebuild=True)
        assert store.collection_exists()


# ─── Retriever Tests ─────────────────────────────────────────────────
class TestRetriever:
    """Test retrieval functionality."""

    @pytest.fixture(scope="class")
    def retriever(self, tmp_path_factory):
        """Create a retriever with test data."""
        from phase3.vectorstore.store import VectorStore
        from phase3.vectorstore.retriever import Retriever

        tmp_dir = str(tmp_path_factory.mktemp("test_retriever"))
        store = VectorStore(persist_dir=tmp_dir, collection_name="test_retriever")

        # Build with realistic test data
        test_chunks = [
            {
                "chunk_id": "hdfc_pharma_costs",
                "fund_id": "hdfc_pharma_healthcare",
                "fund_name": "HDFC Pharma and Healthcare Fund",
                "source_url": "https://www.indmoney.com/mutual-funds/hdfc-pharma",
                "chunk_type": "costs",
                "metadata_tags": ["expense_ratio", "exit_load"],
                "content": "The HDFC Pharma and Healthcare Fund has an expense ratio of 0.95%. The exit load is 1% if redeemed in 0-30 Days.",
                "last_updated": "2026-03-05T00:00:00"
            },
            {
                "chunk_id": "hdfc_pharma_investment",
                "fund_id": "hdfc_pharma_healthcare",
                "fund_name": "HDFC Pharma and Healthcare Fund",
                "source_url": "https://www.indmoney.com/mutual-funds/hdfc-pharma",
                "chunk_type": "investment",
                "metadata_tags": ["min_sip", "min_lumpsum"],
                "content": "To invest in HDFC Pharma and Healthcare Fund: Minimum SIP amount is ₹100. Minimum lumpsum investment is ₹100.",
                "last_updated": "2026-03-05T00:00:00"
            },
            {
                "chunk_id": "hdfc_banking_costs",
                "fund_id": "hdfc_banking_financial_services",
                "fund_name": "HDFC Banking & Financial Services Fund",
                "source_url": "https://www.indmoney.com/mutual-funds/hdfc-banking",
                "chunk_type": "costs",
                "metadata_tags": ["expense_ratio", "exit_load"],
                "content": "The HDFC Banking & Financial Services Fund has an expense ratio of 0.8%. The exit load is 1% if redeemed in 0-30 Days.",
                "last_updated": "2026-03-05T00:00:00"
            },
            {
                "chunk_id": "static_faq_capital_gains",
                "fund_id": "static",
                "fund_name": "HDFC Mutual Funds (General)",
                "source_url": "manually_curated",
                "chunk_type": "faq",
                "metadata_tags": ["question", "source", "capital_gains"],
                "content": "Q: How to download capital gains statement?\nA: You can download your capital gains statement from the HDFC AMC website by logging into your account and visiting the 'Statements' section.",
                "last_updated": "2026-03-05T00:00:00"
            },
            {
                "chunk_id": "hdfc_pharma_overview",
                "fund_id": "hdfc_pharma_healthcare",
                "fund_name": "HDFC Pharma and Healthcare Fund",
                "source_url": "https://www.indmoney.com/mutual-funds/hdfc-pharma",
                "chunk_type": "overview",
                "metadata_tags": ["fund_name", "category"],
                "content": "HDFC Pharma and Healthcare Fund is an Equity - Sectoral mutual fund offered under the Direct Plan - Growth option.",
                "last_updated": "2026-03-05T00:00:00"
            },
        ]

        store.build_index(chunks=test_chunks, force_rebuild=True)
        return Retriever(store=store)

    def test_t3_3_query_expense_ratio(self, retriever):
        """T3.3: Query 'expense ratio HDFC Pharma' returns Pharma costs chunk."""
        results = retriever.retrieve("expense ratio HDFC Pharma")
        assert len(results) > 0
        top = results[0]
        assert "expense ratio" in top["content"].lower() or "pharma" in top["content"].lower()

    def test_t3_4_query_minimum_sip(self, retriever):
        """T3.4: Query 'minimum SIP' returns investment chunks."""
        results = retriever.retrieve("minimum SIP")
        assert len(results) > 0
        assert any("sip" in r["content"].lower() or "minimum" in r["content"].lower() for r in results)

    def test_t3_5_query_capital_gains(self, retriever):
        """T3.5: Query 'how to download capital gains' returns FAQ chunk."""
        results = retriever.retrieve("how to download capital gains statement")
        assert len(results) > 0
        assert any("capital gains" in r["content"].lower() for r in results)

    def test_t3_6_fund_filter(self, retriever):
        """T3.6: Filter by fund_id works."""
        results = retriever.retrieve(
            "expense ratio",
            fund_filter="hdfc_pharma_healthcare"
        )
        assert len(results) > 0
        for r in results:
            assert r["fund_id"] == "hdfc_pharma_healthcare"

    def test_t3_7_similarity_scores(self, retriever):
        """T3.7: Similarity scores are returned between 0 and 1."""
        results = retriever.retrieve("expense ratio")
        assert len(results) > 0
        for r in results:
            assert 0.0 <= r["similarity_score"] <= 1.0

    def test_t3_8_top_k_parameter(self, retriever):
        """T3.8: top_k parameter works — exactly k results returned."""
        results = retriever.retrieve("fund information", top_k=2)
        assert len(results) == 2

    def test_t3_9_empty_query(self, retriever):
        """T3.9: Empty query returns no crash, empty results."""
        results = retriever.retrieve("")
        assert results == []
        results = retriever.retrieve("   ")
        assert results == []

    def test_results_have_source_url(self, retriever):
        """Every result has a source_url for citation (C6)."""
        results = retriever.retrieve("expense ratio")
        for r in results:
            assert r["source_url"], f"Missing source_url in {r['chunk_id']}"

    def test_chunk_type_filter(self, retriever):
        """Filter by chunk_type works."""
        results = retriever.retrieve(
            "fund information",
            chunk_type_filter="costs"
        )
        assert len(results) > 0
        for r in results:
            assert r["chunk_type"] == "costs"


# ─── Integration Tests (require Phase 2 data) ──────────────────────
class TestFullBuild:
    """Integration tests that build from actual Phase 2 chunks."""

    @pytest.fixture(autouse=True)
    def check_phase2_data(self):
        """Skip if Phase 2 processed chunks don't exist."""
        from phase3.vectorstore.config import PROCESSED_CHUNKS_FILE
        if not PROCESSED_CHUNKS_FILE.exists():
            pytest.skip("Phase 2 processed chunks not available")

    def test_t3_1_embeddings_for_all_chunks(self, tmp_path):
        """T3.1: Embeddings generated for all chunks."""
        from phase3.vectorstore.store import VectorStore
        from phase3.vectorstore.config import PROCESSED_CHUNKS_FILE

        chunks = json.load(open(PROCESSED_CHUNKS_FILE, "r", encoding="utf-8"))
        store = VectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test_full")
        count = store.build_index(chunks=chunks, force_rebuild=True)
        assert count == len(chunks), f"Expected {len(chunks)} vectors, got {count}"

    def test_t3_10_persistence(self, tmp_path):
        """T3.10: Vector store is persistent — survives 'process restart'."""
        from phase3.vectorstore.store import VectorStore
        from phase3.vectorstore.config import PROCESSED_CHUNKS_FILE

        persist_dir = str(tmp_path / "persist_test")
        chunks = json.load(open(PROCESSED_CHUNKS_FILE, "r", encoding="utf-8"))

        # Build store
        store1 = VectorStore(persist_dir=persist_dir, collection_name="persist_test")
        count1 = store1.build_index(chunks=chunks, force_rebuild=True)

        # "Restart" — create a new store instance pointing to same dir
        store2 = VectorStore(persist_dir=persist_dir, collection_name="persist_test")
        count2 = store2.get_collection_count()

        assert count2 == count1, f"Persistence failed: built {count1}, loaded {count2}"
