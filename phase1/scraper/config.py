"""
Phase 1 Configuration — Fund URLs, CSS selectors, scraper settings.
"""

# ─── Target Fund URLs ───────────────────────────────────────────────
FUND_URLS = {
    "hdfc_banking_financial_services": {
        "name": "HDFC Banking & Financial Services Fund",
        "url": "https://www.indmoney.com/mutual-funds/hdfc-banking-financial-services-fund-direct-growth-1006661",
        "plan": "Direct Plan - Growth",
        "category": "Equity - Sectoral"
    },
    "hdfc_pharma_healthcare": {
        "name": "HDFC Pharma and Healthcare Fund",
        "url": "https://www.indmoney.com/mutual-funds/hdfc-pharma-and-healthcare-fund-direct-growth-1044289",
        "plan": "Direct Plan - Growth",
        "category": "Equity - Sectoral"
    },
    "hdfc_housing_opportunities": {
        "name": "HDFC Housing Opportunities Fund",
        "url": "https://www.indmoney.com/mutual-funds/hdfc-housing-opportunities-fund-direct-growth-9006",
        "plan": "Direct Plan - Growth",
        "category": "Equity - Sectoral"
    },
    "hdfc_manufacturing": {
        "name": "HDFC Manufacturing Fund",
        "url": "https://www.indmoney.com/mutual-funds/hdfc-manufacturing-fund-direct-growth-1045641",
        "plan": "Direct Plan - Growth",
        "category": "Equity - Sectoral"
    },
    "hdfc_transportation_logistics": {
        "name": "HDFC Transportation and Logistics Fund",
        "url": "https://www.indmoney.com/mutual-funds/hdfc-transportation-and-logistics-fund-direct-growth-1044147",
        "plan": "Direct Plan - Growth",
        "category": "Equity - Sectoral"
    }
}

# ─── HDFC AMC Document URLs (SID / KIM / Factsheet) ────────────────
HDFC_AMC_BASE_URL = "https://www.hdfcfund.com"

# ─── Scraper Settings ──────────────────────────────────────────────
SCRAPER_CONFIG = {
    "headless": True,
    "timeout_ms": 30000,
    "retry_count": 3,
    "retry_delay_sec": 5,
    "wait_for_selector_timeout_ms": 15000,
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ─── CSS Selectors for IndMoney Fund Pages ─────────────────────────
# NOTE: These selectors may need to be updated if IndMoney changes their page structure.
# Inspect the page and update as needed.
SELECTORS = {
    # Fund overview / header
    "fund_name": "h1",
    "plan_type": "[data-testid='plan-type'], .plan-type",
    "nav_value": "[data-testid='nav-value'], .nav-value",
    "nav_date": "[data-testid='nav-date'], .nav-date",
    "fund_category": "[data-testid='fund-category'], .fund-category",
    "benchmark": "[data-testid='benchmark'], .benchmark-name",

    # Key stats section
    "expense_ratio": "[data-testid='expense-ratio'], .expense-ratio",
    "exit_load": "[data-testid='exit-load'], .exit-load",
    "aum": "[data-testid='aum'], .aum-value",
    "min_sip": "[data-testid='min-sip'], .min-sip",
    "min_lumpsum": "[data-testid='min-lumpsum'], .min-lumpsum",
    "lock_in": "[data-testid='lock-in'], .lock-in-period",

    # Risk section
    "riskometer": "[data-testid='riskometer'], .riskometer",

    # Returns section
    "returns_table": "[data-testid='returns-table'], .returns-table",
    "returns_row": "tr, .return-row",

    # Portfolio / Holdings section
    "holdings_table": "[data-testid='holdings-table'], .holdings-table",
    "holdings_row": "tr, .holding-row",
    "sector_allocation": "[data-testid='sector-chart'], .sector-allocation",

    # Fund manager section
    "fund_manager": "[data-testid='fund-manager'], .fund-manager-name",
    "inception_date": "[data-testid='inception-date'], .inception-date",

    # FAQ section
    "faq_section": "[data-testid='faq-section'], .faq-section",
    "faq_question": ".faq-question, summary, [data-testid='faq-q']",
    "faq_answer": ".faq-answer, details p, [data-testid='faq-a']"
}

# ─── Output Paths ──────────────────────────────────────────────────
OUTPUT_DIR = "phase1/data/raw"
SCRAPED_AT_FILE = "phase1/data/scraped_at.json"
STATIC_FAQS_FILE = "phase1/data/raw/static_faqs.json"
FUND_DOCUMENTS_FILE = "phase1/data/raw/fund_documents.json"
