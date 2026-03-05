"""
Phase 2 — Chunker Tests

Tests for chunk creation, validation, and data integrity.
Covers T2.4–T2.12 from the architecture test cases.
"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from phase2.processor.chunk_builder import (
    build_overview_chunk, build_nav_chunk, build_returns_chunk,
    build_costs_chunk, build_risk_chunk, build_investment_chunk,
    build_portfolio_chunk, build_aum_chunk, build_manager_chunk,
    build_documents_chunk, build_faq_chunks, build_static_faq_chunks,
    build_all_chunks_for_fund, process_all_funds,
    OUTPUT_FILE, QUALITY_REPORT_FILE
)

# ─── Test Data ──────────────────────────────────────────────────────
SAMPLE_FUND = {
    "fund_id": "hdfc_banking_financial_services",
    "fund_name": "HDFC Banking & Financial Services Fund",
    "source_url": "https://www.indmoney.com/mutual-funds/hdfc-banking-financial-services-fund-direct-growth-1006661",
    "plan_type": "Direct Plan - Growth",
    "category": "Equity - Sectoral",
    "overview": {"nav": "₹18.82", "nav_date": "04 Mar 2026", "benchmark": "Nifty Financial Services TR INR"},
    "returns": {
        "1M": "3.31%", "3M": "1.45%", "6M": "8.07%",
        "1Y": "23.66%", "3Y": "17.87%", "5Y": "--",
        "since_inception": None,
        "benchmark_returns": {"1M": "1.56%", "3M": "2.42%", "6M": "1.52%", "1Y": "16.31%", "3Y": "16.18%", "5Y": "12.79%"}
    },
    "costs": {"expense_ratio": "0.8%", "exit_load": "1% if redeemed in 0-30 Days", "stamp_duty": None, "transaction_charges": None},
    "risk": {"riskometer": "Very High", "risk_category": None, "lock_in_period": "None", "suitable_for": None},
    "investment": {"minimum_sip": "₹100", "minimum_lumpsum": "₹100", "sip_frequency": None, "additional_purchase_min": None},
    "portfolio": {
        "top_holdings": [
            {"name": "HDFC Bank Ltd", "pct": "18.85%"},
            {"name": "ICICI Bank Ltd", "pct": "15.1%"},
            {"name": "Axis Bank Ltd", "pct": "8.67%"}
        ],
        "sector_allocation": None, "total_holdings": None, "portfolio_turnover": None
    },
    "aum": {"value": "₹4486 Cr", "date": None, "trend": None},
    "manager": {"name": "Anand Laddha", "experience": None, "qualification": None, "other_funds_managed": None},
    "inception_date": "N/A",
    "faqs": [
        {"question": "What is the current NAV?", "answer": "The NAV is ₹18.82."},
        {"question": "What is the expense ratio?", "answer": "The expense ratio is 0.80%."}
    ],
    "documents": {"sid_link": None, "kim_link": None, "factsheet_link": None},
    "scraped_at": "2026-03-05T05:32:56.524367+00:00"
}

SAMPLE_FUND_DOCS = {
    "funds": {
        "hdfc_banking_financial_services": {
            "source_url": "https://www.indmoney.com/mutual-funds/hdfc-banking-financial-services-fund-direct-growth-1006661",
            "documents": {
                "sid": {"url": "https://www.hdfcfund.com/doc/sid.pdf"},
                "kim": {"url": "https://www.hdfcfund.com/doc/kim.pdf"}
            }
        }
    }
}

SOURCE_URL = SAMPLE_FUND["source_url"]


# ─── Individual Chunk Tests ─────────────────────────────────────────
class TestChunkBuilders:
    """Test individual chunk builder functions."""

    def test_overview_chunk_has_fund_name(self):
        chunk = build_overview_chunk(SAMPLE_FUND, SOURCE_URL)
        assert SAMPLE_FUND["fund_name"] in chunk["content"]
        assert chunk["chunk_type"] == "overview"

    def test_nav_chunk_has_nav_value(self):
        chunk = build_nav_chunk(SAMPLE_FUND, SOURCE_URL)
        assert "18.82" in chunk["content"]
        assert chunk["chunk_type"] == "nav"

    def test_returns_chunk_has_periods(self):
        """T2.11: Returns chunk has all periods."""
        chunk = build_returns_chunk(SAMPLE_FUND, SOURCE_URL)
        content = chunk["content"]
        for period in ["1M", "3M", "6M", "1Y", "3Y"]:
            assert period in content, f"Missing period {period}"

    def test_costs_chunk_has_expense_ratio(self):
        chunk = build_costs_chunk(SAMPLE_FUND, SOURCE_URL)
        assert "0.8%" in chunk["content"]

    def test_risk_chunk_has_riskometer(self):
        chunk = build_risk_chunk(SAMPLE_FUND, SOURCE_URL)
        assert "Very High" in chunk["content"]

    def test_investment_chunk_has_min_sip(self):
        chunk = build_investment_chunk(SAMPLE_FUND, SOURCE_URL)
        assert "100" in chunk["content"]

    def test_portfolio_chunk_has_holdings(self):
        chunk = build_portfolio_chunk(SAMPLE_FUND, SOURCE_URL)
        assert "HDFC Bank" in chunk["content"]

    def test_aum_chunk_has_value(self):
        chunk = build_aum_chunk(SAMPLE_FUND, SOURCE_URL)
        assert "4486" in chunk["content"]

    def test_manager_chunk_has_name(self):
        chunk = build_manager_chunk(SAMPLE_FUND, SOURCE_URL)
        assert "Anand Laddha" in chunk["content"]

    def test_documents_chunk_has_links(self):
        """T2.12: Document links chunk created with SID/KIM links."""
        chunk = build_documents_chunk(SAMPLE_FUND, SOURCE_URL, SAMPLE_FUND_DOCS)
        assert "SID" in chunk["content"]
        assert "KIM" in chunk["content"]

    def test_faq_chunks_created(self):
        """T2.6: FAQ chunks are created."""
        chunks = build_faq_chunks(SAMPLE_FUND, SOURCE_URL)
        assert len(chunks) >= 1
        assert chunks[0]["chunk_type"] == "faq"
        assert "?" in chunks[0]["content"]


class TestChunkMetadata:
    """T2.5: Chunk metadata tags are present."""

    def test_all_chunks_have_required_fields(self):
        chunks = build_all_chunks_for_fund(SAMPLE_FUND, SAMPLE_FUND_DOCS)
        required = ["chunk_id", "fund_id", "fund_name", "source_url",
                     "chunk_type", "metadata_tags", "content", "last_updated"]
        for chunk in chunks:
            for field in required:
                assert field in chunk, f"Missing field '{field}' in {chunk.get('chunk_id')}"

    def test_all_chunks_have_metadata_tags(self):
        chunks = build_all_chunks_for_fund(SAMPLE_FUND, SAMPLE_FUND_DOCS)
        for chunk in chunks:
            assert len(chunk["metadata_tags"]) >= 1, f"Empty tags in {chunk['chunk_id']}"

    def test_all_chunks_have_source_url(self):
        chunks = build_all_chunks_for_fund(SAMPLE_FUND, SAMPLE_FUND_DOCS)
        for chunk in chunks:
            assert chunk["source_url"], f"Missing source_url in {chunk['chunk_id']}"


class TestChunkCounts:
    """T2.4 & T2.7: Chunk count validation."""

    def test_t2_4_each_fund_produces_10_plus_chunks(self):
        """T2.4: Each fund produces 10+ chunks (10 standard + FAQs)."""
        chunks = build_all_chunks_for_fund(SAMPLE_FUND, SAMPLE_FUND_DOCS)
        assert len(chunks) >= 10, f"Expected ≥10 chunks, got {len(chunks)}"

    def test_t2_8_no_empty_content(self):
        """T2.8: No empty content in any chunk."""
        chunks = build_all_chunks_for_fund(SAMPLE_FUND, SAMPLE_FUND_DOCS)
        for chunk in chunks:
            assert chunk["content"].strip(), f"Empty content in {chunk['chunk_id']}"

    def test_chunk_types_complete(self):
        """Verify all 10 standard chunk types are produced."""
        chunks = build_all_chunks_for_fund(SAMPLE_FUND, SAMPLE_FUND_DOCS)
        expected_types = {"overview", "nav", "returns", "costs", "risk",
                         "investment", "portfolio", "aum", "manager", "documents"}
        actual_types = {c["chunk_type"] for c in chunks if c["chunk_type"] != "faq"}
        assert expected_types.issubset(actual_types), f"Missing types: {expected_types - actual_types}"


class TestStaticFaqs:
    """Test static FAQ chunk generation."""

    def test_static_faqs_created(self):
        static_faqs = [
            {"faq_id": "test_faq_1", "question": "Test Q?", "answer": "Test A.", "category": "general"}
        ]
        chunks = build_static_faq_chunks(static_faqs)
        assert len(chunks) == 1
        assert chunks[0]["fund_id"] == "static"
        assert chunks[0]["chunk_type"] == "faq"


# ─── Integration Tests (require Phase 1 data) ──────────────────────
class TestFullPipeline:
    """Integration tests that require Phase 1 scraped data."""

    @pytest.fixture(autouse=True)
    def check_raw_data(self):
        """Skip if Phase 1 data doesn't exist."""
        raw_dir = Path("phase1/data/raw")
        if not raw_dir.exists() or not list(raw_dir.glob("hdfc_*.json")):
            pytest.skip("Phase 1 data not available — run scraper first")

    def test_t2_7_total_chunk_count(self):
        """T2.7: Total chunk count matches expected."""
        report = process_all_funds()
        # 5 funds × 10 types + FAQ chunks (8 per fund) + static FAQs ≈ 90+
        assert report["total_chunks"] >= 50, f"Too few chunks: {report['total_chunks']}"

    def test_t2_9_data_quality_report_generated(self):
        """T2.9: Data quality report is generated."""
        process_all_funds()
        assert QUALITY_REPORT_FILE.exists(), "Quality report not generated"
        report = json.load(open(QUALITY_REPORT_FILE, "r", encoding="utf-8"))
        assert "funds_processed" in report
        assert "total_chunks" in report

    def test_t2_10_re_processing_idempotent(self):
        """T2.10: Re-processing is idempotent — same input → same output."""
        report1 = process_all_funds()
        report2 = process_all_funds()
        assert report1["total_chunks"] == report2["total_chunks"]
        assert report1["funds_processed"] == report2["funds_processed"]

    def test_processed_chunks_file_created(self):
        """Verify processed_chunks.json exists after processing."""
        process_all_funds()
        assert OUTPUT_FILE.exists()
        chunks = json.load(open(OUTPUT_FILE, "r", encoding="utf-8"))
        assert isinstance(chunks, list)
        assert len(chunks) > 0

    def test_every_chunk_has_source_url(self):
        """C6: Every chunk has a source_url for citation."""
        process_all_funds()
        chunks = json.load(open(OUTPUT_FILE, "r", encoding="utf-8"))
        for chunk in chunks:
            assert chunk.get("source_url"), f"Missing source_url in {chunk.get('chunk_id')}"
