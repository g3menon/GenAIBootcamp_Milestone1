"""
Phase 2 — Chunk Builder

Reads raw scraped fund JSON files + fund_documents.json + static_faqs.json
and produces processed_chunks.json with source_url in every chunk.

Each chunk carries:
  - chunk_id: unique identifier
  - fund_id: which fund this belongs to
  - fund_name: human-readable name for citations
  - source_url: the IndMoney URL where the data was scraped from
  - chunk_type: one of the 11 types (overview, nav, returns, costs, risk, investment, portfolio, aum, manager, documents, faq)
  - metadata_tags: searchable tags for filtered retrieval
  - content: natural language text optimized for embedding
  - last_updated: ISO timestamp of when the data was scraped
"""

import json
import os
from pathlib import Path
from datetime import datetime


# ─── Paths ──────────────────────────────────────────────────────────
RAW_DATA_DIR = Path("phase1/data/raw")
FUND_DOCUMENTS_FILE = RAW_DATA_DIR / "fund_documents.json"
STATIC_FAQS_FILE = RAW_DATA_DIR / "static_faqs.json"
OUTPUT_FILE = Path("phase2/data/processed/processed_chunks.json")
QUALITY_REPORT_FILE = Path("phase2/data/processed/quality_report.json")


def load_fund_documents():
    """Load fund_documents.json to get source_url and document links for each fund."""
    with open(FUND_DOCUMENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_static_faqs():
    """Load static_faqs.json for curated FAQ chunks."""
    with open(STATIC_FAQS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_raw_fund_data(fund_id: str) -> dict:
    """Load raw scraped JSON for a specific fund."""
    filepath = RAW_DATA_DIR / f"{fund_id}.json"
    if not filepath.exists():
        raise FileNotFoundError(f"Raw data not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def build_overview_chunk(fund: dict, source_url: str) -> dict:
    """Chunk 1: Fund Overview — name, category, plan, benchmark, inception."""
    overview = fund.get("overview", {})
    content = (
        f"{fund['fund_name']} is a {fund.get('category', 'N/A')} mutual fund "
        f"offered under the {fund.get('plan_type', 'N/A')} option. "
        f"The fund's benchmark index is {overview.get('benchmark', 'N/A')}. "
        f"It was launched on {fund.get('inception_date', 'N/A')}. "
        f"(Source: {source_url})"
    )
    return {
        "chunk_id": f"{fund['fund_id']}_overview",
        "fund_id": fund["fund_id"],
        "fund_name": fund["fund_name"],
        "source_url": source_url,
        "chunk_type": "overview",
        "metadata_tags": ["fund_name", "category", "benchmark", "inception_date"],
        "content": content,
        "last_updated": fund.get("scraped_at", datetime.utcnow().isoformat())
    }


def build_nav_chunk(fund: dict, source_url: str) -> dict:
    """Chunk 2: NAV Data — current NAV, NAV date, since-inception return."""
    overview = fund.get("overview", {})
    returns = fund.get("returns", {})
    content = (
        f"The current NAV of {fund['fund_name']} is {overview.get('nav', 'N/A')} "
        f"as of {overview.get('nav_date', 'N/A')}. "
        f"The fund has returned {returns.get('since_inception', 'N/A')} since inception. "
        f"(Source: {source_url})"
    )
    return {
        "chunk_id": f"{fund['fund_id']}_nav",
        "fund_id": fund["fund_id"],
        "fund_name": fund["fund_name"],
        "source_url": source_url,
        "chunk_type": "nav",
        "metadata_tags": ["nav", "nav_date", "since_inception"],
        "content": content,
        "last_updated": fund.get("scraped_at", datetime.utcnow().isoformat())
    }


def build_returns_chunk(fund: dict, source_url: str) -> dict:
    """Chunk 3: Returns & Performance — multi-period returns."""
    returns = fund.get("returns", {})
    periods = ["1M", "3M", "6M", "1Y", "3Y", "5Y", "since_inception"]
    parts = [f"{fund['fund_name']} performance:"]
    for p in periods:
        val = returns.get(p)
        if val:
            label = p if p != "since_inception" else "Since Inception"
            parts.append(f"  {label}: {val}")

    benchmark = returns.get("benchmark_returns")
    if benchmark:
        parts.append("Benchmark comparison:")
        for p in ["1M", "3M", "6M", "1Y", "3Y", "5Y"]:
            bval = benchmark.get(p)
            if bval:
                parts.append(f"  {p}: {bval}")

    parts.append(f"(Source: {source_url})")
    content = "\n".join(parts)

    return {
        "chunk_id": f"{fund['fund_id']}_returns",
        "fund_id": fund["fund_id"],
        "fund_name": fund["fund_name"],
        "source_url": source_url,
        "chunk_type": "returns",
        "metadata_tags": ["1M", "3M", "6M", "1Y", "3Y", "5Y", "inception"],
        "content": content,
        "last_updated": fund.get("scraped_at", datetime.utcnow().isoformat())
    }


def build_costs_chunk(fund: dict, source_url: str) -> dict:
    """Chunk 4: Costs & Expenses — expense ratio, exit load, etc."""
    costs = fund.get("costs", {})
    content = (
        f"The {fund['fund_name']} has an expense ratio of {costs.get('expense_ratio', 'N/A')}. "
        f"The exit load is {costs.get('exit_load', 'N/A')}. "
    )
    if costs.get("stamp_duty"):
        content += f"Stamp duty of {costs['stamp_duty']} applies on all purchases. "
    if costs.get("transaction_charges"):
        content += f"Transaction charges: {costs['transaction_charges']}. "
    content += f"(Source: {source_url})"

    return {
        "chunk_id": f"{fund['fund_id']}_costs",
        "fund_id": fund["fund_id"],
        "fund_name": fund["fund_name"],
        "source_url": source_url,
        "chunk_type": "costs",
        "metadata_tags": ["expense_ratio", "exit_load", "stamp_duty"],
        "content": content,
        "last_updated": fund.get("scraped_at", datetime.utcnow().isoformat())
    }


def build_risk_chunk(fund: dict, source_url: str) -> dict:
    """Chunk 5: Risk & Suitability — riskometer, ELSS/lock-in."""
    risk = fund.get("risk", {})
    content = (
        f"The riskometer rating for {fund['fund_name']} is {risk.get('riskometer', 'N/A')}. "
        f"Lock-in period: {risk.get('lock_in_period', 'None (not an ELSS fund)')}. "
    )
    if risk.get("suitable_for"):
        content += f"This fund is suitable for {risk['suitable_for']}. "
    content += f"(Source: {source_url})"

    return {
        "chunk_id": f"{fund['fund_id']}_risk",
        "fund_id": fund["fund_id"],
        "fund_name": fund["fund_name"],
        "source_url": source_url,
        "chunk_type": "risk",
        "metadata_tags": ["riskometer_level", "lock_in", "suitable_for"],
        "content": content,
        "last_updated": fund.get("scraped_at", datetime.utcnow().isoformat())
    }


def build_investment_chunk(fund: dict, source_url: str) -> dict:
    """Chunk 6: Investment Details — SIP, lumpsum, frequency."""
    inv = fund.get("investment", {})
    content = (
        f"To invest in {fund['fund_name']}: "
        f"Minimum SIP amount is {inv.get('minimum_sip', 'N/A')}. "
        f"Minimum lumpsum investment is {inv.get('minimum_lumpsum', 'N/A')}. "
    )
    if inv.get("sip_frequency"):
        content += f"SIP frequency options: {', '.join(inv['sip_frequency'])}. "
    if inv.get("additional_purchase_min"):
        content += f"Minimum additional purchase: {inv['additional_purchase_min']}. "
    content += f"(Source: {source_url})"

    return {
        "chunk_id": f"{fund['fund_id']}_investment",
        "fund_id": fund["fund_id"],
        "fund_name": fund["fund_name"],
        "source_url": source_url,
        "chunk_type": "investment",
        "metadata_tags": ["min_sip", "min_lumpsum", "sip_frequency"],
        "content": content,
        "last_updated": fund.get("scraped_at", datetime.utcnow().isoformat())
    }


def build_portfolio_chunk(fund: dict, source_url: str) -> dict:
    """Chunk 7: Portfolio & Holdings — top stocks, sectors."""
    portfolio = fund.get("portfolio", {})
    parts = [f"Portfolio of {fund['fund_name']}:"]

    holdings = portfolio.get("top_holdings", [])
    if holdings:
        parts.append("Top Holdings:")
        for h in holdings[:10]:
            parts.append(f"  - {h.get('name', '?')}: {h.get('pct', '?')}")

    sectors = portfolio.get("sector_allocation")
    if sectors:
        parts.append("Sector Allocation:")
        for sector, pct in sectors.items():
            parts.append(f"  - {sector}: {pct}")

    total = portfolio.get("total_holdings")
    if total:
        parts.append(f"Total holdings: {total}")

    parts.append(f"(Source: {source_url})")
    content = "\n".join(parts)

    return {
        "chunk_id": f"{fund['fund_id']}_portfolio",
        "fund_id": fund["fund_id"],
        "fund_name": fund["fund_name"],
        "source_url": source_url,
        "chunk_type": "portfolio",
        "metadata_tags": ["holdings", "sectors", "total_holdings"],
        "content": content,
        "last_updated": fund.get("scraped_at", datetime.utcnow().isoformat())
    }


def build_aum_chunk(fund: dict, source_url: str) -> dict:
    """Chunk 8: AUM — current value, date, trend."""
    aum = fund.get("aum", {})
    content = (
        f"The Assets Under Management (AUM) of {fund['fund_name']} is {aum.get('value', 'N/A')}"
    )
    if aum.get("date"):
        content += f" as of {aum['date']}"
    content += f". (Source: {source_url})"

    return {
        "chunk_id": f"{fund['fund_id']}_aum",
        "fund_id": fund["fund_id"],
        "fund_name": fund["fund_name"],
        "source_url": source_url,
        "chunk_type": "aum",
        "metadata_tags": ["aum_value", "aum_date"],
        "content": content,
        "last_updated": fund.get("scraped_at", datetime.utcnow().isoformat())
    }


def build_manager_chunk(fund: dict, source_url: str) -> dict:
    """Chunk 9: Fund Manager — name, experience, qualifications."""
    mgr = fund.get("manager", {})
    content = f"{fund['fund_name']} is managed by {mgr.get('name', 'N/A')}. "
    if mgr.get("experience"):
        content += f"Experience: {mgr['experience']}. "
    if mgr.get("qualification"):
        content += f"Qualifications: {mgr['qualification']}. "
    if mgr.get("other_funds_managed"):
        content += f"Also manages: {', '.join(mgr['other_funds_managed'])}. "
    content += f"(Source: {source_url})"

    return {
        "chunk_id": f"{fund['fund_id']}_manager",
        "fund_id": fund["fund_id"],
        "fund_name": fund["fund_name"],
        "source_url": source_url,
        "chunk_type": "manager",
        "metadata_tags": ["manager_name", "experience", "qualification"],
        "content": content,
        "last_updated": fund.get("scraped_at", datetime.utcnow().isoformat())
    }


def build_documents_chunk(fund: dict, source_url: str, fund_docs: dict) -> dict:
    """Chunk 10: Documents — SID, KIM, Factsheet links from fund_documents.json."""
    docs = fund.get("documents", {})

    # Merge with fund_documents.json if available
    fund_doc_entry = fund_docs.get("funds", {}).get(fund["fund_id"], {})
    doc_links = fund_doc_entry.get("documents", {})
    hdfc_amc_url = fund_doc_entry.get("hdfc_amc_url", "N/A")

    sid_url = docs.get("sid_link") or (doc_links.get("sid", {}).get("url")) or "Not available"
    kim_url = docs.get("kim_link") or (doc_links.get("kim", {}).get("url")) or "Not available"
    factsheet_url = docs.get("factsheet_link") or (doc_links.get("factsheet", {}).get("url")) or "Not available"

    content = (
        f"Official documents for {fund['fund_name']}:\n"
        f"  - SID (Scheme Information Document): {sid_url}\n"
        f"  - KIM (Key Information Memorandum): {kim_url}\n"
        f"  - Monthly Factsheet: {factsheet_url}\n"
        f"  - HDFC AMC Official Page: {hdfc_amc_url}\n"
        f"(Source: {source_url})"
    )

    return {
        "chunk_id": f"{fund['fund_id']}_documents",
        "fund_id": fund["fund_id"],
        "fund_name": fund["fund_name"],
        "source_url": source_url,
        "chunk_type": "documents",
        "metadata_tags": ["sid_link", "kim_link", "factsheet_link", "hdfc_amc_url"],
        "content": content,
        "last_updated": fund.get("scraped_at", datetime.utcnow().isoformat())
    }


def build_faq_chunks(fund: dict, source_url: str) -> list:
    """Chunk 11: FAQ chunks — one per FAQ Q&A pair from the fund page."""
    faqs = fund.get("faqs", []) or []
    chunks = []
    for i, faq in enumerate(faqs):
        faq_id = f"faq_{i+1:02d}"
        content = (
            f"Q: {faq['question']}\n"
            f"A: {faq['answer']}\n"
            f"(Source: {source_url})"
        )
        chunks.append({
            "chunk_id": f"{fund['fund_id']}_{faq_id}",
            "fund_id": fund["fund_id"],
            "fund_name": fund["fund_name"],
            "source_url": source_url,
            "chunk_type": "faq",
            "metadata_tags": ["question", "answer", "faq"],
            "content": content,
            "last_updated": fund.get("scraped_at", datetime.utcnow().isoformat())
        })
    return chunks


def build_static_faq_chunks(static_faqs: list) -> list:
    """Build chunks from static_faqs.json — manually curated FAQs."""
    chunks = []
    for faq in static_faqs:
        faq_id = faq.get("faq_id", f"faq_{len(chunks)+1}")
        content = (
            f"Q: {faq['question']}\n"
            f"A: {faq['answer']}"
        )
        chunks.append({
            "chunk_id": f"static_{faq_id}",
            "fund_id": "static",
            "fund_name": "HDFC Mutual Funds (General)",
            "source_url": "manually_curated",
            "chunk_type": "faq",
            "metadata_tags": ["question", "source", faq.get("category", "general")],
            "content": content,
            "last_updated": datetime.utcnow().isoformat()
        })
    return chunks


def build_all_chunks_for_fund(fund: dict, fund_docs: dict) -> list:
    """Build all 10 standard chunks + FAQ chunks for a single fund."""
    # Get source_url from fund_documents.json
    fund_doc_entry = fund_docs.get("funds", {}).get(fund["fund_id"], {})
    source_url = fund.get("source_url") or fund_doc_entry.get("source_url", "unknown")

    chunks = [
        build_overview_chunk(fund, source_url),
        build_nav_chunk(fund, source_url),
        build_returns_chunk(fund, source_url),
        build_costs_chunk(fund, source_url),
        build_risk_chunk(fund, source_url),
        build_investment_chunk(fund, source_url),
        build_portfolio_chunk(fund, source_url),
        build_aum_chunk(fund, source_url),
        build_manager_chunk(fund, source_url),
        build_documents_chunk(fund, source_url, fund_docs),
    ]

    # Add per-fund FAQ chunks
    chunks.extend(build_faq_chunks(fund, source_url))

    return chunks


def process_all_funds() -> dict:
    """Main processing pipeline: load all raw data, build all chunks, save output."""
    fund_docs = load_fund_documents()
    static_faqs = load_static_faqs()

    all_chunks: list[dict] = []
    funds_processed = 0
    chunks_per_fund: dict[str, int] = {}
    warnings: list[str] = []

    # Get fund IDs from fund_documents.json
    fund_ids = list(fund_docs.get("funds", {}).keys())

    for fund_id in fund_ids:
        try:
            fund_data = load_raw_fund_data(fund_id)
            chunks = build_all_chunks_for_fund(fund_data, fund_docs)
            all_chunks.extend(chunks)
            funds_processed += 1
            chunks_per_fund[fund_id] = len(chunks)
        except FileNotFoundError as e:
            warnings.append(f"Skipped {fund_id}: {str(e)}")
        except Exception as e:
            warnings.append(f"Error processing {fund_id}: {str(e)}")

    # Add static FAQ chunks
    static_chunks = build_static_faq_chunks(static_faqs)
    all_chunks.extend(static_chunks)

    quality_report = {
        "processed_at": datetime.utcnow().isoformat(),
        "funds_processed": funds_processed,
        "total_chunks": len(all_chunks),
        "chunks_per_fund": chunks_per_fund,
        "static_faq_chunks": len(static_chunks),
        "warnings": warnings
    }

    # Save output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    with open(QUALITY_REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2, ensure_ascii=False)

    return quality_report



if __name__ == "__main__":
    report = process_all_funds()
    print(f"✅ Processed {report['funds_processed']} funds → {report['total_chunks']} chunks")
    if report["warnings"]:
        print(f"⚠️  Warnings: {len(report['warnings'])}")
        for w in report["warnings"]:
            print(f"   - {w}")
