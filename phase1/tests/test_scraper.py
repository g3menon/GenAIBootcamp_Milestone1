"""
Phase 1 — Tests for Scraper and Data Integrity

Tests cover:
  - Config validation (T1.1-T1.3)
  - Scraper functionality (T1.4-T1.9)
  - Data integrity checks (T1.10-T1.18)
"""

import json
import os
import sys
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from phase1.scraper.config import FUND_URLS, SCRAPER_CONFIG, OUTPUT_DIR, FUND_DOCUMENTS_FILE
from phase1.scraper.utils import (
    clean_text, clean_percentage, parse_nav, extract_number
)


# ═══════════════════════════════════════════════════════════════════
# T1.1 — T1.3: Configuration Tests
# ═══════════════════════════════════════════════════════════════════

class TestConfig:
    """Tests for scraper configuration."""

    def test_t1_1_all_five_fund_urls_defined(self):
        """T1.1: All 5 target fund URLs are defined."""
        assert len(FUND_URLS) == 5, f"Expected 5 funds, got {len(FUND_URLS)}"
        expected_ids = [
            "hdfc_banking_financial_services",
            "hdfc_pharma_healthcare",
            "hdfc_housing_opportunities",
            "hdfc_manufacturing",
            "hdfc_transportation_logistics",
        ]
        for fund_id in expected_ids:
            assert fund_id in FUND_URLS, f"Missing fund: {fund_id}"

    def test_t1_2_fund_urls_are_valid_indmoney_urls(self):
        """T1.2: All fund URLs point to IndMoney."""
        for fund_id, info in FUND_URLS.items():
            assert "url" in info, f"{fund_id} missing 'url'"
            assert info["url"].startswith("https://www.indmoney.com/"), \
                f"{fund_id} URL is not IndMoney: {info['url']}"

    def test_t1_3_scraper_config_has_required_keys(self):
        """T1.3: Scraper config has all required settings."""
        required_keys = ["headless", "timeout_ms", "retry_count", "viewport"]
        for key in required_keys:
            assert key in SCRAPER_CONFIG, f"Missing config key: {key}"

    def test_fund_info_has_name_and_plan(self):
        """Each fund entry has name, url, plan, and category."""
        for fund_id, info in FUND_URLS.items():
            assert "name" in info, f"{fund_id} missing 'name'"
            assert "url" in info, f"{fund_id} missing 'url'"
            assert "plan" in info, f"{fund_id} missing 'plan'"
            assert "category" in info, f"{fund_id} missing 'category'"


# ═══════════════════════════════════════════════════════════════════
# T1.4 — T1.6: Utility Function Tests
# ═══════════════════════════════════════════════════════════════════

class TestUtils:
    """Tests for utility functions."""

    def test_t1_4_clean_text_removes_whitespace(self):
        """T1.4: clean_text normalizes whitespace."""
        assert clean_text("  HDFC   Fund  ") == "HDFC Fund"
        assert clean_text(None) == ""
        assert clean_text("") == ""

    def test_t1_5_clean_percentage(self):
        """T1.5: clean_percentage extracts percentage values."""
        assert clean_percentage("0.8%") == "0.8%"
        assert clean_percentage("0.8 %") == "0.8%"
        assert clean_percentage("Expense ratio 1.2%") == "1.2%"
        assert clean_percentage(None) is None

    def test_t1_6_parse_nav(self):
        """T1.6: parse_nav extracts NAV value."""
        assert parse_nav("₹19.18") == "₹19.18"
        assert parse_nav("₹ 52.34") == "₹52.34"
        assert parse_nav(None) is None

    def test_extract_number(self):
        """extract_number gets numeric value from text."""
        assert extract_number("₹4,486 Cr") == 4486.0
        assert extract_number("0.8%") == 0.8
        assert extract_number(None) is None


# ═══════════════════════════════════════════════════════════════════
# T1.7 — T1.10: Static Data Tests
# ═══════════════════════════════════════════════════════════════════

class TestStaticData:
    """Tests for static FAQs and fund documents."""

    def test_t1_7_static_faqs_exist(self):
        """T1.7: static_faqs.json exists and is valid JSON."""
        faq_path = Path("phase1/data/raw/static_faqs.json")
        assert faq_path.exists(), "static_faqs.json not found"
        with open(faq_path, "r", encoding="utf-8") as f:
            faqs = json.load(f)
        assert isinstance(faqs, list), "FAQs should be a list"
        assert len(faqs) >= 3, f"Expected at least 3 FAQs, got {len(faqs)}"

    def test_t1_8_faqs_have_required_fields(self):
        """T1.8: Each FAQ has question, answer, and faq_id."""
        faq_path = Path("phase1/data/raw/static_faqs.json")
        with open(faq_path, "r", encoding="utf-8") as f:
            faqs = json.load(f)
        for faq in faqs:
            assert "question" in faq, f"FAQ missing 'question': {faq}"
            assert "answer" in faq, f"FAQ missing 'answer': {faq}"
            assert "faq_id" in faq, f"FAQ missing 'faq_id': {faq}"
            assert len(faq["question"]) > 5, "Question too short"
            assert len(faq["answer"]) > 10, "Answer too short"

    def test_t1_9_fund_documents_exist(self):
        """T1.9: fund_documents.json exists and has all 5 funds."""
        doc_path = Path(FUND_DOCUMENTS_FILE)
        assert doc_path.exists(), "fund_documents.json not found"
        with open(doc_path, "r", encoding="utf-8") as f:
            docs = json.load(f)
        assert "funds" in docs, "Missing 'funds' key"
        assert len(docs["funds"]) == 5, f"Expected 5 funds, got {len(docs['funds'])}"

    def test_t1_10_fund_documents_have_source_urls(self):
        """T1.10: Each fund in fund_documents.json has a source_url."""
        doc_path = Path(FUND_DOCUMENTS_FILE)
        with open(doc_path, "r", encoding="utf-8") as f:
            docs = json.load(f)
        for fund_id, fund_info in docs["funds"].items():
            assert "source_url" in fund_info, f"{fund_id} missing 'source_url'"
            assert fund_info["source_url"].startswith("https://"), \
                f"{fund_id} source_url is not a URL: {fund_info['source_url']}"

    def test_faqs_no_personal_info(self):
        """Constraint C3: FAQs should NOT contain PAN, Aadhaar references."""
        faq_path = Path("phase1/data/raw/static_faqs.json")
        with open(faq_path, "r", encoding="utf-8") as f:
            faqs = json.load(f)
        for faq in faqs:
            answer = faq["answer"].lower()
            assert "pan" not in answer.split(), \
                f"FAQ '{faq['faq_id']}' references PAN (constraint C3)"
            assert "aadhaar" not in answer, \
                f"FAQ '{faq['faq_id']}' references Aadhaar (constraint C3)"


# ═══════════════════════════════════════════════════════════════════
# T1.11 — T1.18: Scraped Data Integrity Tests
# These tests only run if scraped data files exist
# ═══════════════════════════════════════════════════════════════════

class TestScrapedDataIntegrity:
    """Tests for scraped data quality — only run after scraper has been executed."""

    def _get_scraped_files(self) -> list[Path]:
        """Get list of scraped fund JSON files."""
        raw_dir = Path(OUTPUT_DIR)
        if not raw_dir.exists():
            return []
        return [
            f for f in raw_dir.glob("hdfc_*.json")
            if f.stem in FUND_URLS
        ]

    def test_t1_11_scraped_files_exist(self):
        """T1.11: At least one scraped fund JSON file exists."""
        files = self._get_scraped_files()
        if not files:
            pytest.skip("No scraped data files found — run the scraper first")
        assert len(files) > 0

    def test_t1_12_scraped_data_has_required_fields(self):
        """T1.12: Each scraped file has all required top-level fields."""
        files = self._get_scraped_files()
        if not files:
            pytest.skip("No scraped data files found")

        required = [
            "fund_id", "fund_name", "source_url", "plan_type", "category",
            "overview", "returns", "costs", "risk", "investment",
            "portfolio", "aum", "manager", "inception_date", "scraped_at"
        ]
        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for field in required:
                assert field in data, f"{filepath.stem} missing field: {field}"

    def test_t1_13_source_url_is_indmoney(self):
        """T1.13: Constraint C6 — source_url is an IndMoney URL."""
        files = self._get_scraped_files()
        if not files:
            pytest.skip("No scraped data files found")

        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["source_url"].startswith("https://www.indmoney.com/"), \
                f"{filepath.stem} source_url is wrong: {data['source_url']}"

    def test_t1_14_overview_has_nav(self):
        """T1.14: Overview section contains NAV value."""
        files = self._get_scraped_files()
        if not files:
            pytest.skip("No scraped data files found")

        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            overview = data.get("overview", {})
            assert overview.get("nav") is not None, \
                f"{filepath.stem} missing NAV value"

    def test_t1_15_costs_has_expense_ratio(self):
        """T1.15: Costs section contains expense ratio."""
        files = self._get_scraped_files()
        if not files:
            pytest.skip("No scraped data files found")

        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            costs = data.get("costs", {})
            assert costs.get("expense_ratio") is not None, \
                f"{filepath.stem} missing expense_ratio"

    def test_t1_16_risk_has_riskometer(self):
        """T1.16: Risk section contains riskometer value."""
        files = self._get_scraped_files()
        if not files:
            pytest.skip("No scraped data files found")

        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            risk = data.get("risk", {})
            assert risk.get("riskometer") is not None, \
                f"{filepath.stem} missing riskometer"

    def test_t1_17_investment_has_min_sip(self):
        """T1.17: Investment section contains minimum SIP."""
        files = self._get_scraped_files()
        if not files:
            pytest.skip("No scraped data files found")

        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            inv = data.get("investment", {})
            assert inv.get("minimum_sip") is not None, \
                f"{filepath.stem} missing minimum_sip"

    def test_t1_18_scraped_at_is_iso_timestamp(self):
        """T1.18: scraped_at is a valid ISO timestamp."""
        files = self._get_scraped_files()
        if not files:
            pytest.skip("No scraped data files found")

        from datetime import datetime
        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            try:
                datetime.fromisoformat(data["scraped_at"].replace("Z", "+00:00"))
            except ValueError:
                pytest.fail(f"{filepath.stem} scraped_at is not ISO: {data['scraped_at']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
