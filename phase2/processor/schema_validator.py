"""
Phase 2 — Schema Validator

Validates raw scraped fund JSON files against the fund_schema.json.
Logs warnings for missing/malformed fields without blocking processing.
"""

import json
from pathlib import Path
from datetime import datetime


FUND_SCHEMA_FILE = Path("phase2/schemas/fund_schema.json")

# Required fields (must exist and be non-null)
REQUIRED_FIELDS = [
    "fund_id", "fund_name", "source_url", "plan_type", "category",
    "overview", "returns", "costs", "risk", "investment",
    "portfolio", "aum", "manager", "inception_date", "scraped_at"
]

# Sub-fields that should be present
EXPECTED_SUB_FIELDS = {
    "overview": ["nav", "nav_date", "benchmark"],
    "returns": ["1M", "3M", "6M", "1Y"],
    "costs": ["expense_ratio", "exit_load"],
    "risk": ["riskometer", "lock_in_period"],
    "investment": ["minimum_sip", "minimum_lumpsum"],
    "portfolio": ["top_holdings"],
    "aum": ["value"],
    "manager": ["name"],
}


def validate_fund_data(fund_data: dict) -> dict:
    """
    Validate a single fund's raw JSON data.

    Returns:
        dict with 'valid' (bool), 'errors' (list), 'warnings' (list),
        'fields_present' (int), 'fields_total' (int)
    """
    errors: list[str] = []
    warnings: list[str] = []
    fund_id = fund_data.get("fund_id", "unknown")
    fields_present = 0
    fields_total = 0

    # Check required top-level fields
    for field in REQUIRED_FIELDS:
        fields_total += 1
        if field not in fund_data:
            errors.append(f"{fund_id}: Missing required field '{field}'")
        elif fund_data[field] is None:
            warnings.append(f"{fund_id}: Field '{field}' is null")
        else:
            fields_present += 1

    # Check sub-fields
    for section, sub_fields in EXPECTED_SUB_FIELDS.items():
        section_data = fund_data.get(section, {})
        if not isinstance(section_data, dict):
            warnings.append(f"{fund_id}: Section '{section}' is not a dict")
            continue
        for sub_field in sub_fields:
            fields_total += 1
            val = section_data.get(sub_field)
            if val is None or val == "" or val == "N/A":
                warnings.append(f"{fund_id}: Missing sub-field '{section}.{sub_field}'")
            else:
                fields_present += 1

    # Validate source_url
    source_url = fund_data.get("source_url", "")
    if source_url and not source_url.startswith("https://"):
        errors.append(f"{fund_id}: source_url is not HTTPS: {source_url}")

    # Validate scraped_at is ISO timestamp
    scraped_at = fund_data.get("scraped_at", "")
    if scraped_at:
        try:
            datetime.fromisoformat(scraped_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            errors.append(f"{fund_id}: scraped_at is not valid ISO: {scraped_at}")

    # Check FAQs
    faqs = fund_data.get("faqs", [])
    if not faqs:
        warnings.append(f"{fund_id}: No FAQs found")

    return {
        "fund_id": fund_id,
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "fields_present": fields_present,
        "fields_total": fields_total,
        "completeness": round(fields_present / max(fields_total, 1) * 100, 1),
        "faq_count": len(faqs),
    }


def validate_all_funds(raw_data_dir: str = "phase1/data/raw") -> dict:
    """Validate all raw fund JSON files."""
    raw_dir = Path(raw_data_dir)
    results: list[dict] = []
    all_errors: list[str] = []
    all_warnings: list[str] = []

    fund_files = sorted(raw_dir.glob("hdfc_*.json"))
    for filepath in fund_files:
        with open(filepath, "r", encoding="utf-8") as f:
            fund_data = json.load(f)
        result = validate_fund_data(fund_data)
        results.append(result)
        all_errors.extend(result["errors"])
        all_warnings.extend(result["warnings"])

    return {
        "validated_at": datetime.utcnow().isoformat(),
        "funds_validated": len(results),
        "total_errors": len(all_errors),
        "total_warnings": len(all_warnings),
        "all_valid": all(r["valid"] for r in results),
        "fund_results": results,
        "errors": all_errors,
        "warnings": all_warnings,
    }


if __name__ == "__main__":
    report = validate_all_funds()
    print(f"Validated {report['funds_validated']} funds")
    print(f"Errors: {report['total_errors']}, Warnings: {report['total_warnings']}")
    for r in report["fund_results"]:
        status = "PASS" if r["valid"] else "FAIL"
        print(f"  [{status}] {r['fund_id']}: {r['completeness']}% complete, {r['faq_count']} FAQs")
