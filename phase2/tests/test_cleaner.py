"""
Phase 2 — Data Cleaner Tests

Tests for currency normalization, percentage normalization, text cleaning,
and fund name standardization.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from phase2.processor.data_cleaner import (
    clean_text, normalize_currency, normalize_percentage,
    standardize_fund_name, clean_exit_load, clean_fund_data
)


class TestCleanText:
    """Test text cleaning functions."""

    def test_removes_extra_whitespace(self):
        assert clean_text("  hello   world  ") == "hello world"

    def test_removes_html_tags(self):
        assert clean_text("<b>bold</b> text") == "bold text"

    def test_handles_none(self):
        assert clean_text(None) == ""

    def test_handles_empty(self):
        assert clean_text("") == ""

    def test_removes_zero_width_chars(self):
        assert clean_text("hello\u200bworld") == "helloworld"


class TestNormalizeCurrency:
    """T2.2: Currency normalization works."""

    def test_rupee_100(self):
        result = normalize_currency("₹100")
        assert result["numeric"] == 100.0
        assert "₹100" in result["display"]

    def test_rupee_with_commas(self):
        result = normalize_currency("₹4,486 Cr")
        assert result["numeric"] == 4486.0
        assert result.get("unit") == "Cr"

    def test_none_input(self):
        result = normalize_currency(None)
        assert result["numeric"] is None

    def test_simple_number(self):
        result = normalize_currency("₹100")
        assert result["numeric"] == 100.0


class TestNormalizePercentage:
    """T2.3: Percentage normalization works."""

    def test_expense_ratio(self):
        result = normalize_percentage("0.8%")
        assert result["numeric"] == 0.008
        assert result["display"] == "0.8%"

    def test_return_percentage(self):
        result = normalize_percentage("25.28%")
        assert result["numeric"] == 0.2528
        assert result["display"] == "25.28%"

    def test_negative_percentage(self):
        result = normalize_percentage("-3.5%")
        assert result["numeric"] == -0.035
        assert result["display"] == "-3.5%"

    def test_none_input(self):
        result = normalize_percentage(None)
        assert result["numeric"] is None


class TestFundNameStandardization:
    """Test fund name standardization."""

    def test_already_standard(self):
        name = "HDFC Banking & Financial Services Fund"
        assert standardize_fund_name(name) == name

    def test_extra_spaces(self):
        assert standardize_fund_name("HDFC  Banking   Fund") == "HDFC Banking Fund"


class TestCleanExitLoad:
    """Test exit load cleaning."""

    def test_clean_normal(self):
        result = clean_exit_load("1% if redeemed in 0-30 Days")
        assert "1%" in result

    def test_clean_with_prefix(self):
        result = clean_exit_load("of the fund?The exit load is 1% if redeemed in 0-30 Days")
        assert result.startswith("1%")

    def test_none_input(self):
        assert clean_exit_load(None) == "N/A"
