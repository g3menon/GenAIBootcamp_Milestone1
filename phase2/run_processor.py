"""
Phase 2 — CLI Entry Point

Run this script to process raw scraped data into structured chunks.

Usage:
    python -m phase2.run_processor                  # Process all funds
    python -m phase2.run_processor --validate-only   # Only validate, no chunking
    python -m phase2.run_processor --stats           # Show chunk statistics
"""

import argparse
import sys
import io
import json
from pathlib import Path

# Fix Windows console encoding for emoji output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from phase2.processor.chunk_builder import process_all_funds, OUTPUT_FILE, QUALITY_REPORT_FILE
from phase2.processor.schema_validator import validate_all_funds
from phase2.processor.data_cleaner import clean_fund_data
from phase2.processor.utils import logger, load_json


def validate_only():
    """Run schema validation on raw data without chunking."""
    logger.info("🔍 Running schema validation only...")
    report = validate_all_funds()

    print(f"\n{'='*60}")
    print(f"📋 Schema Validation Report")
    print(f"{'='*60}")
    print(f"  Funds validated: {report['funds_validated']}")
    print(f"  All valid: {report['all_valid']}")
    print(f"  Errors: {report['total_errors']}")
    print(f"  Warnings: {report['total_warnings']}")

    for r in report["fund_results"]:
        status = "✅" if r["valid"] else "❌"
        print(f"  {status} {r['fund_id']}: {r['completeness']}% complete, {r['faq_count']} FAQs")
        if r["errors"]:
            for e in r["errors"]:
                print(f"      ❌ {e}")

    print(f"{'='*60}\n")


def show_stats():
    """Show statistics about processed chunks."""
    if not OUTPUT_FILE.exists():
        print("❌ processed_chunks.json not found. Run processing first.")
        return

    chunks = load_json(OUTPUT_FILE)
    print(f"\n{'='*60}")
    print(f"📊 Chunk Statistics")
    print(f"{'='*60}")
    print(f"  Total chunks: {len(chunks)}")

    # Count by type
    type_counts: dict[str, int] = {}
    fund_counts: dict[str, int] = {}
    for chunk in chunks:
        ctype = chunk.get("chunk_type", "unknown")
        type_counts[ctype] = type_counts.get(ctype, 0) + 1
        fund_id = chunk.get("fund_id", "unknown")
        fund_counts[fund_id] = fund_counts.get(fund_id, 0) + 1

    print(f"\n  By chunk type:")
    for ctype, count in sorted(type_counts.items()):
        print(f"    • {ctype}: {count}")

    print(f"\n  By fund:")
    for fund_id, count in sorted(fund_counts.items()):
        print(f"    • {fund_id}: {count} chunks")

    # Check for empty content
    empty_count = sum(1 for c in chunks if not c.get("content", "").strip())
    print(f"\n  Empty content chunks: {empty_count}")
    print(f"{'='*60}\n")


def run_full_pipeline():
    """Run the full processing pipeline: validate → clean → chunk → save."""
    logger.info("🚀 Starting Phase 2 processing pipeline...")

    # Step 1: Validate raw data
    logger.info("Step 1/3: Schema validation...")
    validation = validate_all_funds()
    if validation["total_errors"] > 0:
        logger.warning(f"⚠️  {validation['total_errors']} validation errors found")
        for e in validation["errors"]:
            logger.warning(f"  → {e}")

    for r in validation["fund_results"]:
        status = "✅" if r["valid"] else "⚠️"
        logger.info(f"  {status} {r['fund_id']}: {r['completeness']}% complete")

    # Step 2: Process and chunk
    logger.info("Step 2/3: Building chunks...")
    report = process_all_funds()

    # Step 3: Summary
    logger.info("Step 3/3: Generating summary...")

    print(f"\n{'='*60}")
    print(f"📊 Phase 2 — Processing Summary")
    print(f"{'='*60}")
    print(f"  Funds processed: {report['funds_processed']}")
    print(f"  Total chunks: {report['total_chunks']}")
    print(f"  Static FAQ chunks: {report['static_faq_chunks']}")

    for fund_id, count in report.get("chunks_per_fund", {}).items():
        print(f"    • {fund_id}: {count} chunks")

    if report.get("warnings"):
        print(f"\n  ⚠️  Warnings ({len(report['warnings'])}):")
        for w in report["warnings"]:
            print(f"    - {w}")

    print(f"\n  Output: {OUTPUT_FILE}")
    print(f"  Quality Report: {QUALITY_REPORT_FILE}")
    print(f"{'='*60}\n")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Phase 2 — Data Processing & Chunking Pipeline"
    )
    parser.add_argument(
        "--validate-only", action="store_true",
        help="Only validate raw data, don't process"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show chunk statistics from last processing run"
    )

    args = parser.parse_args()

    if args.validate_only:
        validate_only()
    elif args.stats:
        show_stats()
    else:
        run_full_pipeline()


if __name__ == "__main__":
    main()
