"""
Phase 2 — Schema Validator Tests

Tests for T2.1: Schema validation catches missing fields.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from phase2.processor.schema_validator import validate_fund_data, validate_all_funds


class TestSchemaValidation:
    """T2.1: Schema validation catches missing fields."""

    def test_t2_1_missing_field_triggers_error(self):
        """Missing required field should trigger an error."""
        incomplete = {"fund_id": "test_fund"}
        result = validate_fund_data(incomplete)
        assert not result["valid"]
        assert len(result["errors"]) > 0

    def test_complete_fund_passes(self):
        """Complete fund data should pass validation."""
        complete = {
            "fund_id": "hdfc_test",
            "fund_name": "HDFC Test Fund",
            "source_url": "https://www.indmoney.com/test",
            "plan_type": "Direct Plan - Growth",
            "category": "Equity - Sectoral",
            "overview": {"nav": "₹10.00", "nav_date": "01 Jan 2026", "benchmark": "Nifty"},
            "returns": {"1M": "1.5%", "3M": "3%", "6M": "5%", "1Y": "10%"},
            "costs": {"expense_ratio": "0.8%", "exit_load": "1%"},
            "risk": {"riskometer": "Very High", "lock_in_period": "None"},
            "investment": {"minimum_sip": "₹100", "minimum_lumpsum": "₹100"},
            "portfolio": {"top_holdings": [{"name": "Test", "pct": "10%"}]},
            "aum": {"value": "₹1000 Cr"},
            "manager": {"name": "Manager Name"},
            "inception_date": "01-Jan-2013",
            "scraped_at": "2026-03-05T00:00:00+00:00",
            "faqs": [{"question": "Test?", "answer": "Yes."}]
        }
        result = validate_fund_data(complete)
        assert result["valid"]
        assert result["completeness"] == 100.0

    def test_null_field_triggers_warning(self):
        """Null field values should trigger warnings."""
        data = {
            "fund_id": "hdfc_test",
            "fund_name": None,  # null
            "source_url": "https://test.com",
            "plan_type": "Direct Plan - Growth",
            "category": "Equity",
            "overview": {"nav": None, "nav_date": None, "benchmark": None},
            "returns": {"1M": None, "3M": None, "6M": None, "1Y": None},
            "costs": {"expense_ratio": None, "exit_load": None},
            "risk": {"riskometer": None, "lock_in_period": None},
            "investment": {"minimum_sip": None, "minimum_lumpsum": None},
            "portfolio": {"top_holdings": []},
            "aum": {"value": None},
            "manager": {"name": None},
            "inception_date": None,
            "scraped_at": "2026-01-01T00:00:00",
        }
        result = validate_fund_data(data)
        assert len(result["warnings"]) > 0

    def test_invalid_source_url(self):
        """Non-HTTPS source URL should trigger error."""
        data = {
            "fund_id": "hdfc_test",
            "fund_name": "Test",
            "source_url": "http://insecure.com",
            "plan_type": "Direct",
            "category": "Equity",
            "overview": {},
            "returns": {},
            "costs": {},
            "risk": {},
            "investment": {},
            "portfolio": {},
            "aum": {},
            "manager": {},
            "inception_date": "N/A",
            "scraped_at": "2026-01-01T00:00:00",
        }
        result = validate_fund_data(data)
        assert any("not HTTPS" in e for e in result["errors"])

    def test_completeness_percentage(self):
        """Completeness should reflect filled vs total fields."""
        data = {
            "fund_id": "hdfc_test",
            "fund_name": "Test Fund With Name",
            "source_url": "https://test.com",
            "plan_type": "Direct Plan - Growth",
            "category": "Equity",
            "overview": {"nav": "₹10", "nav_date": "01 Jan", "benchmark": "Nifty"},
            "returns": {"1M": "1%", "3M": "2%", "6M": "3%", "1Y": "4%"},
            "costs": {"expense_ratio": "0.5%", "exit_load": "1%"},
            "risk": {"riskometer": "High", "lock_in_period": "None"},
            "investment": {"minimum_sip": "₹100", "minimum_lumpsum": "₹500"},
            "portfolio": {"top_holdings": [{"name": "A", "pct": "10%"}]},
            "aum": {"value": "₹500 Cr"},
            "manager": {"name": "Manager"},
            "inception_date": "2020-01-01",
            "scraped_at": "2026-01-01T00:00:00",
        }
        result = validate_fund_data(data)
        assert result["completeness"] == 100.0


class TestValidateAllFunds:
    """Integration tests for validate_all_funds."""

    @pytest.fixture(autouse=True)
    def check_raw_data(self):
        """Skip if Phase 1 data doesn't exist."""
        raw_dir = Path("phase1/data/raw")
        if not raw_dir.exists() or not list(raw_dir.glob("hdfc_*.json")):
            pytest.skip("Phase 1 data not available")

    def test_all_funds_validated(self):
        report = validate_all_funds()
        assert report["funds_validated"] == 5

    def test_all_funds_are_valid(self):
        report = validate_all_funds()
        assert report["all_valid"], f"Errors: {report['errors']}"
