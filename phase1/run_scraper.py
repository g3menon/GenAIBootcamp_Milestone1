"""
Phase 1 — CLI Entry Point

Run this script to scrape all 5 HDFC Mutual Fund pages from IndMoney.

Usage:
    python -m phase1.run_scraper              # Scrape all funds
    python -m phase1.run_scraper --fund hdfc_pharma_healthcare  # Scrape one fund
    python -m phase1.run_scraper --dry-run    # Show config without scraping
"""

import argparse
import asyncio
import json
import sys
import io
from pathlib import Path

# Fix Windows console encoding for emoji output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from phase1.scraper.config import FUND_URLS, SCRAPER_CONFIG
from phase1.scraper.fund_scraper import FundScraper, run_scraper
from phase1.scraper.utils import logger


def print_config():
    """Print current scraper configuration."""
    print("\n📋 Phase 1 — Scraper Configuration")
    print("=" * 50)
    print(f"  Headless: {SCRAPER_CONFIG['headless']}")
    print(f"  Timeout: {SCRAPER_CONFIG['timeout_ms']}ms")
    print(f"  Retries: {SCRAPER_CONFIG['retry_count']}")
    print(f"  Viewport: {SCRAPER_CONFIG['viewport']}")
    print(f"\n  Target Funds ({len(FUND_URLS)}):")
    for fund_id, info in FUND_URLS.items():
        print(f"    • {info['name']}")
        print(f"      {info['url']}")
    print("=" * 50)


async def scrape_single_fund(fund_id: str):
    """Scrape a single fund by its ID."""
    if fund_id not in FUND_URLS:
        print(f"❌ Unknown fund ID: {fund_id}")
        print(f"   Available: {', '.join(FUND_URLS.keys())}")
        sys.exit(1)

    scraper = FundScraper()
    try:
        await scraper.start()
        fund_info = FUND_URLS[fund_id]
        result = await scraper.scrape_fund(fund_id, fund_info)
        scraper.results[fund_id] = result
        scraper.save_results()
        print(f"\n✅ Successfully scraped: {fund_info['name']}")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
    finally:
        await scraper.stop()


def main():
    parser = argparse.ArgumentParser(
        description="Phase 1 — HDFC Mutual Fund Scraper (Playwright)"
    )
    parser.add_argument(
        "--fund", type=str, default=None,
        help="Scrape a single fund by its ID (e.g., hdfc_pharma_healthcare)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show configuration without scraping"
    )
    parser.add_argument(
        "--list-funds", action="store_true",
        help="List all available fund IDs"
    )

    args = parser.parse_args()

    if args.list_funds:
        print("\n📋 Available Fund IDs:")
        for fund_id, info in FUND_URLS.items():
            print(f"  • {fund_id} → {info['name']}")
        return

    if args.dry_run:
        print_config()
        return

    if args.fund:
        asyncio.run(scrape_single_fund(args.fund))
    else:
        asyncio.run(run_scraper())


if __name__ == "__main__":
    main()
