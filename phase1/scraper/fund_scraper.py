"""
Phase 1 — Fund Scraper

Main scraper class that uses Playwright to navigate to each fund's IndMoney page,
extract all data points using the data_extractor module, and save structured JSON.
"""

import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from phase1.scraper.config import FUND_URLS, SCRAPER_CONFIG, OUTPUT_DIR, SCRAPED_AT_FILE, FUND_DOCUMENTS_FILE
from phase1.scraper.data_extractor import (
    extract_fund_name, extract_overview, extract_returns, extract_costs,
    extract_risk, extract_investment, extract_portfolio, extract_manager,
    extract_aum, extract_faqs, extract_inception_date
)
from phase1.scraper.utils import logger, retry, ensure_dir


class FundScraper:
    """Scrapes fund data from IndMoney using Playwright."""

    def __init__(self):
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.results: dict[str, dict] = {}
        self.errors: list[str] = []

    async def start(self):
        """Launch Playwright browser."""
        logger.info("🚀 Starting Playwright browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=SCRAPER_CONFIG["headless"]
        )
        self.context = await self.browser.new_context(
            viewport=SCRAPER_CONFIG["viewport"],
            user_agent=SCRAPER_CONFIG["user_agent"],
        )
        logger.info("✅ Browser started successfully")

    async def stop(self):
        """Close browser and Playwright."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        logger.info("🛑 Browser closed")

    @retry(max_attempts=SCRAPER_CONFIG["retry_count"], delay_sec=SCRAPER_CONFIG["retry_delay_sec"])
    async def scrape_fund(self, fund_id: str, fund_info: dict) -> dict:
        """Scrape all data for a single fund."""
        url = fund_info["url"]
        fund_name_config = fund_info["name"]
        logger.info(f"📄 Scraping: {fund_name_config}")
        logger.info(f"   URL: {url}")

        page: Page = await self.context.new_page()  # type: ignore
        try:
            # Navigate to the fund page
            await page.goto(url, wait_until="domcontentloaded",
                          timeout=SCRAPER_CONFIG["timeout_ms"])
            # Wait for main content to render
            await page.wait_for_timeout(3000)

            # Wait for h1 (fund name) to appear
            try:
                await page.wait_for_selector("h1", timeout=SCRAPER_CONFIG["wait_for_selector_timeout_ms"])
            except Exception:
                logger.warning(f"   ⚠️  h1 not found, page may not have loaded fully")

            # Extract all data points
            logger.info(f"   📊 Extracting data points...")

            fund_name = await extract_fund_name(page) or fund_name_config
            overview = await extract_overview(page)
            returns = await extract_returns(page)
            costs = await extract_costs(page)
            risk = await extract_risk(page)
            investment = await extract_investment(page)
            portfolio = await extract_portfolio(page)
            manager = await extract_manager(page)
            aum = await extract_aum(page)
            faqs = await extract_faqs(page)
            inception_date = await extract_inception_date(page)

            # Load document links from fund_documents.json
            documents = self._get_document_links(fund_id)

            # Build the structured output
            fund_data = {
                "fund_id": fund_id,
                "fund_name": fund_name,
                "source_url": url,
                "plan_type": fund_info.get("plan", "Direct Plan - Growth"),
                "category": fund_info.get("category", "Equity - Sectoral"),
                "overview": overview,
                "returns": returns,
                "costs": costs,
                "risk": risk,
                "investment": investment,
                "portfolio": portfolio,
                "aum": aum,
                "manager": manager,
                "inception_date": inception_date or "N/A",
                "faqs": faqs,
                "documents": documents,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }

            # Post-process to fix known extraction issues
            self._postprocess_data(fund_data)

            # Log summary of what was extracted
            self._log_extraction_summary(fund_id, fund_data)

            return fund_data

        finally:
            await page.close()

    def _get_document_links(self, fund_id: str) -> dict:
        """Load SID/KIM/Factsheet URLs from fund_documents.json."""
        try:
            with open(FUND_DOCUMENTS_FILE, "r", encoding="utf-8") as f:
                docs = json.load(f)
            fund_docs = docs.get("funds", {}).get(fund_id, {}).get("documents", {})
            return {
                "sid_link": fund_docs.get("sid", {}).get("url"),
                "kim_link": fund_docs.get("kim", {}).get("url"),
                "factsheet_link": fund_docs.get("factsheet", {}).get("url"),
            }
        except Exception as e:
            logger.warning(f"   ⚠️  Could not load fund documents: {e}")
            return {"sid_link": None, "kim_link": None, "factsheet_link": None}

    def _postprocess_data(self, data: dict):
        """Clean up extracted data — fix known issues."""
        import re

        # 1. Clean exit_load: strip FAQ question text prefix
        exit_load = data.get("costs", {}).get("exit_load")
        if exit_load and isinstance(exit_load, str):
            # Remove common prefixes like "of the fund?The exit load is "
            cleaned = re.sub(r'^.*?(?:exit\s*load\s*is\s*)', '', exit_load, flags=re.IGNORECASE)
            if cleaned:
                data["costs"]["exit_load"] = cleaned.strip()
            else:
                data["costs"]["exit_load"] = exit_load

        # 2. Fill empty top_holdings from FAQ answers
        holdings = data.get("portfolio", {}).get("top_holdings", [])
        if not holdings:
            for faq in data.get("faqs", []):
                if "top" in faq["question"].lower() and "holding" in faq["question"].lower():
                    answer = faq["answer"]
                    # Trim to text after "are " to avoid capturing prefix words
                    are_idx = answer.lower().find(" are ")
                    if are_idx >= 0:
                        answer = answer[are_idx + 5:]
                    # Parse "HDFC Bank Ltd(18.85%), ICICI Bank Ltd(15.1%)"
                    pairs = re.findall(r'([A-Za-z][A-Za-z\s&\'\.]+?)\s*\(\s*([\d.]+)\s*%\s*\)', answer)
                    if pairs:
                        data["portfolio"]["top_holdings"] = [
                            {"name": name.strip(), "pct": f"{pct}%"}
                            for name, pct in pairs
                        ]
                    break


        # 3. Clean benchmark: remove noise like risk/probability text
        benchmark = data.get("overview", {}).get("benchmark")
        if benchmark and ("probab" in benchmark.lower() or
                          "risk" in benchmark.lower() and "nifty" not in benchmark.lower()):
            data["overview"]["benchmark"] = None

        # 4. Clean total_holdings: the "3" is from FAQ ("top 3 holdings"), not actual count
        if data.get("portfolio", {}).get("total_holdings") == 3:
            # Only trust if it came from a "XX stocks" pattern, not FAQ
            data["portfolio"]["total_holdings"] = None


    def _log_extraction_summary(self, fund_id: str, data: dict):
        """Log a summary of what was extracted."""
        filled = 0
        total = 0
        sections = ["overview", "returns", "costs", "risk", "investment", "portfolio", "aum", "manager"]
        for section in sections:
            section_data = data.get(section, {})
            if isinstance(section_data, dict):
                for key, val in section_data.items():
                    total += 1
                    if val is not None and val != "" and val != [] and val != {}:
                        filled += 1

        faq_count = len(data.get("faqs", []))
        logger.info(f"   ✅ {fund_id}: {filled}/{total} fields filled, {faq_count} FAQs extracted")

    async def scrape_all_funds(self) -> dict[str, dict]:
        """Scrape all 5 target funds."""
        logger.info(f"🏦 Starting scrape of {len(FUND_URLS)} funds...")
        start_time = datetime.now(timezone.utc)

        for fund_id, fund_info in FUND_URLS.items():
            try:
                fund_data = await self.scrape_fund(fund_id, fund_info)
                self.results[fund_id] = fund_data
            except Exception as e:
                error_msg = f"❌ Failed to scrape {fund_id}: {e}"
                logger.error(error_msg)
                self.errors.append(error_msg)

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(f"🏁 Scraping complete: {len(self.results)}/{len(FUND_URLS)} funds in {elapsed:.1f}s")
        if self.errors:
            logger.warning(f"⚠️  {len(self.errors)} errors occurred")

        return self.results

    def save_results(self):
        """Save all scraped data to individual JSON files."""
        output_dir = ensure_dir(OUTPUT_DIR)

        for fund_id, fund_data in self.results.items():
            filepath = output_dir / f"{fund_id}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(fund_data, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved: {filepath}")

        # Save scrape timestamp
        timestamp_data = {
            "last_scraped": datetime.now(timezone.utc).isoformat(),
            "funds_scraped": list(self.results.keys()),
            "funds_failed": [e.split(":")[0] for e in self.errors] if self.errors else [],
            "total_funds": len(FUND_URLS),
            "success_count": len(self.results),
            "error_count": len(self.errors),
        }
        scraped_at_path = Path(SCRAPED_AT_FILE)
        scraped_at_path.parent.mkdir(parents=True, exist_ok=True)
        with open(scraped_at_path, "w", encoding="utf-8") as f:
            json.dump(timestamp_data, f, indent=2, ensure_ascii=False)
        logger.info(f"⏱️  Timestamp saved: {SCRAPED_AT_FILE}")


async def run_scraper():
    """Main entry point for running the scraper."""
    scraper = FundScraper()
    try:
        await scraper.start()
        results = await scraper.scrape_all_funds()
        scraper.save_results()

        # Print summary
        print(f"\n{'='*60}")
        print(f"📊 Scraping Summary")
        print(f"{'='*60}")
        print(f"  Funds scraped: {len(results)}/{len(FUND_URLS)}")
        print(f"  Errors: {len(scraper.errors)}")
        for fund_id, data in results.items():
            nav = data.get("overview", {}).get("nav", "N/A")
            er = data.get("costs", {}).get("expense_ratio", "N/A")
            print(f"  • {data['fund_name']}: NAV={nav}, ER={er}")
        print(f"{'='*60}\n")

        return results
    finally:
        await scraper.stop()


if __name__ == "__main__":
    asyncio.run(run_scraper())
