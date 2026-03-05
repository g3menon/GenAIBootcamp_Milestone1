# Phase 1 — Data Collection (Web Scraping)

## Overview

Phase 1 scrapes structured mutual fund data from [IndMoney](https://www.indmoney.com) for 5 target HDFC Mutual Funds using **Playwright** (headless Chromium).

## Target Funds

| # | Fund Name | Source URL |
|---|-----------|-----------|
| 1 | HDFC Banking & Financial Services Fund | [Link](https://www.indmoney.com/mutual-funds/hdfc-banking-financial-services-fund-direct-growth-1006661) |
| 2 | HDFC Pharma and Healthcare Fund | [Link](https://www.indmoney.com/mutual-funds/hdfc-pharma-and-healthcare-fund-direct-growth-1044289) |
| 3 | HDFC Housing Opportunities Fund | [Link](https://www.indmoney.com/mutual-funds/hdfc-housing-opportunities-fund-direct-growth-9006) |
| 4 | HDFC Manufacturing Fund | [Link](https://www.indmoney.com/mutual-funds/hdfc-manufacturing-fund-direct-growth-1045641) |
| 5 | HDFC Transportation and Logistics Fund | [Link](https://www.indmoney.com/mutual-funds/hdfc-transportation-and-logistics-fund-direct-growth-1044147) |

## Setup

```bash
# Install Python dependencies
pip install playwright pytest pytest-asyncio

# Install Playwright browsers
playwright install chromium
```

## Usage

```bash
# Scrape all 5 funds
python -m phase1.run_scraper

# Scrape a single fund
python -m phase1.run_scraper --fund hdfc_pharma_healthcare

# List available fund IDs
python -m phase1.run_scraper --list-funds

# Show config without scraping
python -m phase1.run_scraper --dry-run
```

## Run Tests

```bash
# Run all Phase 1 tests
pytest phase1/tests/ -v

# Run only config/static data tests (no scraping needed)
pytest phase1/tests/test_scraper.py -v -k "Config or Utils or StaticData"

# Run data integrity tests (requires scraper to have run)
pytest phase1/tests/test_scraper.py -v -k "ScrapedDataIntegrity"
```

## Data Points Scraped

Each fund's JSON includes:
- **Overview**: Fund name, NAV, NAV date, benchmark, category
- **Returns**: 1M, 3M, 6M, 1Y, 3Y, 5Y, since inception + benchmark comparison
- **Costs**: Expense ratio, exit load, stamp duty
- **Risk**: Riskometer level, lock-in period
- **Investment**: Minimum SIP, lumpsum, SIP frequency
- **Portfolio**: Top 10-15 holdings with %, sector allocation, total holdings
- **AUM**: Current AUM value and date
- **Manager**: Fund manager name, experience, qualification
- **FAQs**: On-page FAQ Q&A pairs
- **Documents**: SID/KIM/Factsheet URL references (no PDF scraping — constraint C1)

## Constraints

- **C1**: No PDF scraping — only web URL data
- **C3**: No personal information collected from users
- **C6**: Every output includes `source_url` for citation

## Output

Each fund generates a JSON file in `phase1/data/raw/`:
```
phase1/data/raw/
├── hdfc_banking_financial_services.json
├── hdfc_pharma_healthcare.json
├── hdfc_housing_opportunities.json
├── hdfc_manufacturing.json
├── hdfc_transportation_logistics.json
├── static_faqs.json        (pre-curated)
└── fund_documents.json     (document URL references)
```
