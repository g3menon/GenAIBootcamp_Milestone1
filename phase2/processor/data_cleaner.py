"""
Phase 2 — Data Cleaner

Cleans and normalizes raw scraped data before chunking:
- Strips HTML tags and extra whitespace
- Normalizes currency values (₹100 → numeric + display)
- Normalizes percentages (0.8% → float + display)
- Standardizes fund names for consistent matching
"""

import re
from typing import Any


def clean_text(text: str | None) -> str:
    """Strip extra whitespace, HTML tags, and normalize Unicode."""
    if not text or not isinstance(text, str):
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove zero-width characters
    text = text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    return text


def normalize_currency(value: str | None) -> dict:
    """
    Normalize currency string.
    '₹100' → {'raw': '₹100', 'numeric': 100.0, 'display': '₹100'}
    '₹4,486 Cr' → {'raw': '₹4,486 Cr', 'numeric': 4486.0, 'display': '₹4,486 Cr', 'unit': 'Cr'}
    """
    if not value or not isinstance(value, str):
        return {"raw": value, "numeric": None, "display": str(value) if value else "N/A"}

    result: dict[str, Any] = {"raw": value, "numeric": None, "display": value}

    # Extract numeric portion
    match = re.search(r'₹?\s*([\d,]+\.?\d*)', value)
    if match:
        num_str = match.group(1).replace(',', '')
        try:
            result["numeric"] = float(num_str)
        except ValueError:
            pass

    # Detect unit (Cr, Lakh, etc.)
    unit_match = re.search(r'(Cr|Crore|Lakh|L)', value, re.IGNORECASE)
    if unit_match:
        result["unit"] = unit_match.group(1)

    return result


def normalize_percentage(value: str | None) -> dict:
    """
    Normalize percentage string.
    '0.8%' → {'raw': '0.8%', 'numeric': 0.008, 'display': '0.8%'}
    '25.28%' → {'raw': '25.28%', 'numeric': 0.2528, 'display': '25.28%'}
    """
    if not value or not isinstance(value, str):
        return {"raw": value, "numeric": None, "display": str(value) if value else "N/A"}

    result: dict[str, Any] = {"raw": value, "numeric": None, "display": value}

    match = re.search(r'([-\d.]+)\s*%', value)
    if match:
        try:
            pct_float = float(match.group(1))
            result["numeric"] = round(pct_float / 100, 6)
            result["display"] = f"{pct_float}%"
        except ValueError:
            pass

    return result


def standardize_fund_name(name: str) -> str:
    """Standardize fund name for consistent matching."""
    if not name:
        return name
    # Remove extra spaces, standardize casing
    name = re.sub(r'\s+', ' ', name).strip()
    # Ensure consistent prefix
    if not name.startswith("HDFC"):
        name = "HDFC " + name
    return name


def clean_exit_load(exit_load: str | None) -> str:
    """Clean exit load string."""
    if not exit_load or not isinstance(exit_load, str):
        return "N/A"
    # Remove FAQ question prefixes
    cleaned = re.sub(r'^.*?(?:exit\s*load\s*is\s*)', '', exit_load, flags=re.IGNORECASE)
    return cleaned.strip() if cleaned.strip() else exit_load


def clean_fund_data(fund_data: dict) -> dict:
    """Apply all cleaning operations to a fund's raw data."""
    cleaned = fund_data.copy()

    # Clean fund name
    if cleaned.get("fund_name"):
        cleaned["fund_name"] = standardize_fund_name(clean_text(cleaned["fund_name"]))

    # Clean overview
    overview = cleaned.get("overview", {})
    if overview:
        if overview.get("nav"):
            overview["nav"] = clean_text(str(overview["nav"]))
        if overview.get("nav_date"):
            overview["nav_date"] = clean_text(overview["nav_date"])
        if overview.get("benchmark"):
            overview["benchmark"] = clean_text(overview["benchmark"])

    # Clean costs
    costs = cleaned.get("costs", {})
    if costs:
        if costs.get("exit_load"):
            costs["exit_load"] = clean_exit_load(costs["exit_load"])

    # Clean FAQs
    faqs = cleaned.get("faqs", [])
    if faqs:
        for faq in faqs:
            faq["question"] = clean_text(faq.get("question", ""))
            faq["answer"] = clean_text(faq.get("answer", ""))

    return cleaned
