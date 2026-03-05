# 🏦 HDFC Mutual Fund RAG Chatbot — Architecture Document

## Project Overview

A **Retrieval-Augmented Generation (RAG) chatbot** that answers user queries about select HDFC Mutual Funds. The bot scrapes real-time data from [IndMoney](https://www.indmoney.com/mutual-funds/amc/hdfc-mutual-fund), stores it in a structured knowledge base, and uses an LLM to generate accurate, grounded responses.

### Skills Being Tested

| Skill | Description | Where It Applies |
|-------|-------------|------------------|
| **W1 — Thinking Like a Model** | Identify the exact fact being asked; decide whether to answer or refuse | Phase 4: Query classification, fact extraction, out-of-scope detection |
| **W2 — LLMs & Prompting** | Instruction-style prompts, concise phrasing, polite safe-refusals, citation wording | Phase 4: System prompt design, response formatting, guardrails |
| **W3 — RAGs (only)** | Small-corpus retrieval with accurate citations | Phases 2–4: Chunking strategy, ChromaDB retrieval, source attribution |

### ⛔ Constraints & Guardrails

> These are **hard rules** that apply across ALL phases and cannot be overridden.

| # | Constraint | Details |
|---|-----------|----------|
| C1 | **No PDF Scraping** | Only scrape data from the target IndMoney web URLs. Do NOT download or parse PDFs (SID, KIM, Factsheet). Document links may be stored as URLs only. |
| C2 | **Answers Only From Embeddings** | The chatbot must answer ONLY using information stored in the vector database (ChromaDB). The LLM must NEVER generate responses from its own knowledge. If the embeddings don't contain the answer → polite refusal. |
| C3 | **No Personal Information** | Do NOT collect, store, or request any personal information from the user (PAN, Aadhaar, email, phone, bank details). If a user provides personal info or asks a question requiring personal data → polite refusal stating it is out of scope. |
| C4 | **No Fund Comparisons** | Do NOT compare mutual funds against each other. Each query should be answered for a single fund only. If user asks to compare funds → polite refusal. |
| C5 | **No Investment Advice** | Do NOT provide buy/sell recommendations, portfolio suggestions, or future performance predictions. All responses must be purely informational with a disclaimer. |
| C6 | **Source URL Required** | Every response must cite the exact source URL from which the data was scraped. No answer without attribution. |
| C7 | **Scope Limited to 5 Funds** | The chatbot only answers questions about the 5 target HDFC Mutual Funds listed below. Any query about other funds, AMCs, or financial instruments → polite refusal. |

### Target Mutual Funds

| # | Fund Name | Source URL |
|---|-----------|-----------|
| 1 | HDFC Banking & Financial Services Fund | [Link](https://www.indmoney.com/mutual-funds/hdfc-banking-financial-services-fund-direct-growth-1006661) |
| 2 | HDFC Pharma and Healthcare Fund | [Link](https://www.indmoney.com/mutual-funds/hdfc-pharma-and-healthcare-fund-direct-growth-1044289) |
| 3 | HDFC Housing Opportunities Fund | [Link](https://www.indmoney.com/mutual-funds/hdfc-housing-opportunities-fund-direct-growth-9006) |
| 4 | HDFC Manufacturing Fund | [Link](https://www.indmoney.com/mutual-funds/hdfc-manufacturing-fund-direct-growth-1045641) |
| 5 | HDFC Transportation and Logistics Fund | [Link](https://www.indmoney.com/mutual-funds/hdfc-transportation-and-logistics-fund-direct-growth-1044147) |

### Supported User Queries

- "What is the expense ratio of HDFC Pharma and Healthcare Fund?"
- "Is there an ELSS lock-in for HDFC Banking & Financial Services Fund?"
- "What is the minimum SIP for HDFC Manufacturing Fund?"
- "What is the exit load for HDFC Transportation and Logistics Fund?"
- "What is the riskometer/benchmark for HDFC Housing Opportunities Fund?"
- "How to download capital-gains statement?"

---

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FRONTEND — Chat UI (Phase 5a)                          │
│          Modern HTML / CSS / JS  •  Google Auth  •  Responsive             │
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │  REST / WebSocket (HTTP)
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     BACKEND — API Server (Phase 5b)                        │
│          FastAPI  •  /chat  /health  /funds  •  Session Mgmt               │
└──────────┬──────────────────────────────────┬───────────────────────────────┘
           │                                  │
           ▼                                  ▼
┌─────────────────────────────┐  ┌────────────────────────────────────────────┐
│   QUERY ENGINE (Phase 4)    │  │         LLM LAYER (Phase 4)                │
│   Classification→Retrieval  │  │   Google Gemini Flash (2.5/3/3.5)          │
│         (Phase 3 store)     │  │   Prompt Templates + Guardrails            │
└──────────┬──────────────────┘  └────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VECTOR STORE (Phase 3)                                   │
│            ChromaDB / Pinecone  •  Embedded Fund Data                       │
└──────────┬──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              DATA PROCESSING & CHUNKING (Phase 2)                           │
│     Raw Data → Cleaning → Structuring → Chunking → Embedding                │
└──────────┬──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   DATA COLLECTION (Phase 1)                                 │
│     Playwright Web Scraper → Raw JSON/CSV Storage                           │
└──────────┬──────────────────────────────────────────────────────────────────┘
           ▲
           │  Periodic Trigger
┌──────────┴──────────────────────────────────────────────────────────────────┐
│              DATA REFRESH SCHEDULER (Phase 7)                               │
│     APScheduler  •  Cron  •  Phase 1→2→3 Cascade  •  Health Checks         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Phase 1 — Data Collection (Web Scraping)

### Objective
Scrape structured mutual fund data from [IndMoney](https://www.indmoney.com/mutual-funds/amc/hdfc-mutual-fund) for the 5 target HDFC funds.

### Why Browser-Based Scraping?
IndMoney blocks simple HTTP requests (returns HTTP 403). The pages are also JavaScript-rendered SPAs. Therefore, we must use a **headless browser** (**Playwright**) to:
1. Navigate to each fund's page
2. Wait for dynamic content to load
3. Extract data from the rendered DOM

### Data Points to Scrape (Per Fund)

#### Section 1: Fund Overview

| Data Field | Source Location on Page | Example Value |
|------------|------------------------|---------------|
| **Fund Name** | Page title / header | HDFC Banking & Financial Services Fund |
| **Plan Type** | Header subtitle | Direct Plan - Growth |
| **Fund Category** | Fund metadata | Equity - Sectoral |
| **NAV** | Overview section | ₹52.34 |
| **NAV Date** | Overview section | 03-Mar-2026 |
| **Benchmark Index** | Overview section | Nifty Financial Services TRI |

#### Section 2: Performance & Returns

| Data Field | Source Location on Page | Example Value |
|------------|------------------------|---------------|
| **Returns (1M)** | Returns section | 2.1% |
| **Returns (3M)** | Returns section | 5.4% |
| **Returns (6M)** | Returns section | 8.2% |
| **Returns (1Y)** | Returns section | 12.5% |
| **Returns (3Y)** | Returns section | 15.2% |
| **Returns (5Y)** | Returns section | 18.7% |
| **Returns (Since Inception)** | Returns section | 14.3% |
| **Benchmark Returns** | Returns comparison | Matching periods for benchmark |

#### Section 3: Costs & Expenses

| Data Field | Source Location on Page | Example Value |
|------------|------------------------|---------------|
| **Expense Ratio** | Key Stats / Expenses section | 0.8% |
| **Exit Load** | Key Stats / Expenses section | 1.0% for redemption within 15 days |
| **Stamp Duty** | Expenses section (if listed) | 0.005% |
| **Transaction Charges** | Expenses section (if listed) | Applicable for SIP > ₹10,000 |

#### Section 4: Risk & Suitability

| Data Field | Source Location on Page | Example Value |
|------------|------------------------|---------------|
| **Riskometer** | Risk visual / Risk section | Very High |
| **Risk Category** | Risk section | High Risk |
| **ELSS / Lock-in Period** | Key Stats | None (not ELSS) |
| **Suitable For** | Risk section (if listed) | Long-term wealth creation |

#### Section 5: Investment Details

| Data Field | Source Location on Page | Example Value |
|------------|------------------------|---------------|
| **Minimum SIP** | Key Stats / Investment section | ₹100 |
| **Minimum Lumpsum** | Key Stats / Investment section | ₹100 |
| **SIP Frequency Options** | Investment section (if listed) | Monthly, Quarterly |
| **Additional Purchase Min** | Investment section (if listed) | ₹100 |

#### Section 6: Portfolio & Holdings

| Data Field | Source Location on Page | Example Value |
|------------|------------------------|---------------|
| **Top Holdings** | Portfolio tab | List of top 10 stocks with % allocation |
| **Sector Allocation** | Portfolio tab | Banking 45%, Insurance 20%, ... |
| **Number of Holdings** | Portfolio tab (if listed) | 42 |
| **Portfolio Turnover** | Portfolio tab (if listed) | 35% |

#### Section 7: Fund Manager & About

| Data Field | Source Location on Page | Example Value |
|------------|------------------------|---------------|
| **Fund Manager Name** | About / Manager section | Manager Name |
| **Manager Experience** | Manager section (if listed) | 15 years |
| **Manager Qualification** | Manager section (if listed) | MBA, CFA |
| **Other Funds Managed** | Manager section (if listed) | List of other funds |
| **Inception Date** | About section | 01-Jan-2013 |

#### Section 8: AUM & Trends

| Data Field | Source Location on Page | Example Value |
|------------|------------------------|---------------|
| **Current AUM** | Key Stats / AUM section | ₹1,234 Cr |
| **AUM Date** | AUM section (if listed) | As of Feb 2026 |
| **AUM Trend** | AUM chart/history (if available) | Historical AUM data points |

#### Section 9: FAQs & Document Links

| Data Field | Source Location on Page | Example Value |
|------------|------------------------|---------------|
| **On-Page FAQs** | FAQ accordion on fund page | Q&A pairs visible on the page |
| **SID Link** | Documents section / HDFC AMC site | URL only (NO PDF download — constraint C1) |
| **KIM Link** | Documents section / HDFC AMC site | URL only (NO PDF download — constraint C1) |
| **Factsheet Link** | Documents section (if listed) | URL only (NO PDF download — constraint C1) |

### Additional Static Knowledge to Include

For the query *"How to download capital-gains statement?"*, we include a **manually curated FAQ** entry:

```
Q: How to download capital-gains statement?
A: To download your capital gains statement from INDmoney:
   1. Log in to the INDmoney app or website.
   2. Tap on your Profile Picture or navigate to the Profile section.
   3. Scroll to find 'Tax Report' or 'Reports'.
   4. Select the 'Mutual Funds' section.
   5. Choose 'Capital Gains Statement'.
   6. Select the desired Financial Year and download the report in PDF or Excel format.

   For statements directly from HDFC AMC:
   1. Visit https://www.hdfcfund.com
   2. Navigate to 'Investor Services' → 'Account Statement'
   3. Follow the on-screen instructions to verify your identity
   4. Select the date range and download
```

### Linked Fund Documents (URL References Only — No PDF Scraping)

> **Constraint C1**: We store document **URLs only** for reference. We do NOT download, parse, or extract content from PDFs (SID, KIM, Factsheet). The chatbot cannot answer questions based on PDF content.

| Document | What We Store | What We Do NOT Do |
|----------|--------------|--------------------|
| **SID** (Scheme Information Document) | URL link to the document | ❌ Do NOT download or parse the PDF |
| **KIM** (Key Information Memorandum) | URL link to the document | ❌ Do NOT download or parse the PDF |
| **Factsheet** | URL link to the document | ❌ Do NOT download or parse the PDF |

### Tech Stack for Phase 1

| Component | Technology | Reason |
|-----------|-----------|--------|
| Browser Automation | **Playwright** (Python) | Modern, fast, auto-manages browsers, built-in waiters |
| Browser Engine | **Chromium** (headless) | Lightweight, CI/CD compatible, auto-downloaded by Playwright |
| Data Storage | **JSON** files (raw) | Structured, easy to inspect and version control |
| Backup Format | **CSV** | Flat file backup for tabular data |
| Scheduler (optional) | **APScheduler** / cron | For periodic data refresh |

### Directory Structure (Phase 1)

```
phase1/
├── scraper/
│   ├── __init__.py
│   ├── config.py              # Fund URLs, selectors, timeouts
│   ├── fund_scraper.py        # Main scraper class
│   ├── data_extractor.py      # DOM parsing & field extraction
│   └── utils.py               # Retry logic, logging, helpers
├── data/
│   ├── raw/
│   │   ├── hdfc_banking_financial_services.json
│   │   ├── hdfc_pharma_healthcare.json
│   │   ├── hdfc_housing_opportunities.json
│   │   ├── hdfc_manufacturing.json
│   │   ├── hdfc_transportation_logistics.json
│   │   ├── static_faqs.json
│   │   └── fund_documents.json   # SID/KIM/Factsheet URL references only (no PDFs)
│   └── scraped_at.json        # Timestamp of last scrape
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py        # Unit tests for scraper
│   └── test_data_integrity.py # Validate scraped data completeness
├── requirements.txt
├── run_scraper.py             # CLI entry point
└── README.md
```

### Implementation Steps

1. **Setup & Configuration**
   - Install Playwright (`pip install playwright && playwright install chromium`)
   - Define fund URLs and CSS/XPath selectors in `config.py`
   - Configure headless browser settings

2. **Build the Scraper**
   - Create `FundScraper` class with methods:
     - `navigate_to_fund(url)` — Open fund page, wait for load
     - `extract_overview()` — Fund name, NAV, NAV date, category, benchmark
     - `extract_returns()` — 1M, 3M, 6M, 1Y, 3Y, 5Y, inception returns + benchmark comparison
     - `extract_costs()` — Expense ratio, exit load, stamp duty, transaction charges
     - `extract_risk()` — Riskometer, risk category, ELSS/lock-in status
     - `extract_investment()` — Minimum SIP, lumpsum, SIP frequency, additional purchase
     - `extract_portfolio()` — Top holdings with %, sector allocation, holding count
     - `extract_manager()` — Fund manager name, experience, qualification, other funds
     - `extract_aum()` — Current AUM, AUM date, historical trend (if available)
     - `extract_faqs()` — All FAQ Q&A pairs visible on the page
     - `extract_documents()` — SID, KIM, factsheet links from page or HDFC AMC site
   - Implement retry logic with exponential backoff
   - Add proper error handling and logging

3. **Data Validation**
   - Validate that all required fields are present
   - Type-check numeric fields (NAV, expense ratio, etc.)
   - Log warnings for missing/unexpected data

4. **Static FAQ Curation**
   - Create `static_faqs.json` with manually curated answers for:
     - How to download capital-gains statement
     - General ELSS lock-in information
     - SIP registration process

5. **Document Link Collection**
   - Scrape or manually curate SID/KIM/Factsheet URLs from HDFC AMC site
   - Store in `fund_documents.json` with fund_id mapping

6. **Testing**
   - Unit tests for individual extraction functions
   - Integration test: scrape one fund end-to-end
   - Data integrity test: validate JSON schema

### Test Cases for Phase 1

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| T1.1 | Scraper connects to IndMoney fund page | Page loads without timeout error |
| T1.2 | Extract expense ratio for each fund | Non-null numeric value returned |
| T1.3 | Extract exit load for each fund | Valid percentage/description string returned |
| T1.4 | Extract minimum SIP amount | Numeric value ≥ ₹100 |
| T1.5 | Extract riskometer rating | One of: Low, Moderate, High, Very High |
| T1.6 | Extract benchmark index name | Non-empty string returned |
| T1.7 | All 5 fund JSON files created | 5 files exist in `data/raw/` |
| T1.8 | Static FAQs file is valid JSON | File parses without error |
| T1.9 | Scraped data has timestamp | `scraped_at.json` contains valid ISO timestamp |
| T1.10 | Re-run scraper overwrites old data | New timestamps, data reflects current values |
| T1.11 | Extract multi-period returns (1M–5Y + inception) | At least 5 return periods per fund |
| T1.12 | Extract fund manager name | Non-empty string for each fund |
| T1.13 | Extract top holdings with allocation % | ≥ 5 holdings with numeric percentages |
| T1.14 | Extract on-page FAQs | ≥ 1 FAQ Q&A pair per fund |
| T1.15 | Fund document links are valid URLs | SID/KIM links start with http(s):// |
| T1.16 | Extract AUM value | Numeric value in Cr |
| T1.17 | Extract ELSS / lock-in status | "None" or valid lock-in period |
| T1.18 | Extract NAV with date | NAV is numeric, date is valid ISO format |

---

## 📋 Phase 2 — Data Processing & Chunking

### Objective
Transform raw scraped data into clean, structured, and chunked documents optimized for vector embedding and retrieval.

> **W3 Focus**: The chunking strategy directly impacts RAG retrieval quality. Each chunk must be narrow and fact-dense so the retriever can isolate the exact answer for any user query.

### Processing Pipeline

```
Raw JSON → Schema Validation → Cleaning → Structuring → Chunking → Output JSON
```

### Steps

1. **Schema Validation**
   - Validate each raw JSON against a predefined schema
   - Flag and handle missing/malformed fields
   - Log data quality metrics

2. **Data Cleaning**
   - Strip HTML tags, extra whitespace
   - Normalize currency values (₹100 → 100.0)
   - Normalize percentages (0.8% → 0.008 float + "0.8%" display)
   - Standardize fund names for consistent matching

3. **Document Structuring**
   - Convert each fund's data into a structured **document** format:
   
   ```json
   {
     "fund_id": "hdfc_banking_financial_services",
     "fund_name": "HDFC Banking & Financial Services Fund",
     "source_url": "https://www.indmoney.com/mutual-funds/hdfc-banking-financial-services-fund-direct-growth-1006661",
     "plan_type": "Direct Plan - Growth",
     "category": "Equity - Sectoral",
     "overview": {
       "nav": "₹52.34",
       "nav_date": "2026-03-03",
       "benchmark": "Nifty Financial Services TRI"
     },
     "returns": {
       "1M": "2.1%", "3M": "5.4%", "6M": "8.2%",
       "1Y": "12.5%", "3Y": "15.2%", "5Y": "18.7%",
       "since_inception": "14.3%"
     },
     "costs": {
       "expense_ratio": "0.8%",
       "exit_load": "1.0% for redemption within 15 days",
       "stamp_duty": "0.005%"
     },
     "risk": {
       "riskometer": "Very High",
       "lock_in_period": "None",
       "suitable_for": "Long-term wealth creation"
     },
     "investment": {
       "minimum_sip": "₹100",
       "minimum_lumpsum": "₹100",
       "sip_frequency": ["Monthly", "Quarterly"]
     },
     "portfolio": {
       "top_holdings": [{"name": "ICICI Bank", "pct": "9.5%"}, ...],
       "sector_allocation": {"Banking": "45%", "Insurance": "20%"},
       "total_holdings": 42
     },
     "aum": {
       "value": "₹1,234 Cr",
       "date": "2026-02-28"
     },
     "manager": {
       "name": "Manager Name",
       "experience": "15 years",
       "qualification": "MBA, CFA"
     },
     "inception_date": "01-Jan-2013",
     "documents": {
       "sid_link": "https://...",
       "kim_link": "https://...",
       "factsheet_link": "https://..."
     },
     "faqs": [
       {"question": "...", "answer": "..."},
       ...
     ],
     "last_updated": "2026-03-03T17:00:00Z"
   }
   ```

4. **Chunking Strategy (Critical for RAG Quality)**
   
   > Instead of storing each fund as one large blob, create **narrow, fact-dense semantic chunks** so the retriever can isolate the exact answer for any query.

   | # | Chunk Type | Content | Metadata Tags | Target Queries |
   |---|------------|---------|---------------|----------------|
   | 1 | **Overview** | Fund name + category + plan type + benchmark + inception date | `fund_name`, `category`, `benchmark` | "Tell me about HDFC Pharma Fund" |
   | 2 | **NAV Data** | Current NAV + NAV date + since-inception return | `nav`, `nav_date` | "What is the NAV of...?" |
   | 3 | **Returns & Performance** | 1M, 3M, 6M, 1Y, 3Y, 5Y, inception returns + benchmark comparison | `1M`, `3M`, `1Y`, `3Y`, `5Y`, `inception` | "1-year return of...?" |
   | 4 | **Costs & Expenses** | Expense ratio + exit load + stamp duty + transaction charges | `expense_ratio`, `exit_load` | "What is the expense ratio?" |
   | 5 | **Risk & Suitability** | Riskometer level + ELSS/lock-in status + suitability | `riskometer_level`, `lock_in` | "Is this fund ELSS?" |
   | 6 | **Investment Details** | Minimum SIP + lumpsum + SIP frequency + additional purchase | `min_sip`, `min_lumpsum` | "What is the minimum SIP?" |
   | 7 | **Portfolio & Holdings** | Top holdings with % + sector allocation + holding count | `holdings`, `sectors` | "Top holdings of...?" |
   | 8 | **AUM** | Current AUM + AUM date + trend (if available) | `aum_value`, `aum_date` | "What is the AUM?" |
   | 9 | **Fund Manager** | Manager name + experience + qualification + other funds managed | `manager_name` | "Who manages this fund?" |
   | 10 | **Documents** | Links to SID, KIM, Factsheet with brief description | `sid_link`, `kim_link` | "Where is the SID?" |
   | 11 | **FAQ Chunks** | One chunk per FAQ Q&A pair (from page + static) | `question`, `source` | "How to download capital gains?" |

   Each chunk includes **metadata** for filtering and **`source_url`** for citation:
   ```json
   {
     "chunk_id": "hdfc_banking_fs_costs",
     "fund_id": "hdfc_banking_financial_services",
     "fund_name": "HDFC Banking & Financial Services Fund",
     "source_url": "https://www.indmoney.com/mutual-funds/hdfc-banking-financial-services-fund-direct-growth-1006661",
     "chunk_type": "costs",
     "metadata_tags": ["expense_ratio", "exit_load"],
     "content": "The HDFC Banking & Financial Services Fund (Direct Plan - Growth) has an expense ratio of 0.8%. The exit load is 1.0% if redeemed within 15 days. Stamp duty of 0.005% applies on all purchases. (Source: https://www.indmoney.com/mutual-funds/hdfc-banking-financial-services-fund-direct-growth-1006661)",
     "last_updated": "2026-03-03T17:00:00Z"
   }
   ```

5. **Output**
   - Save processed chunks as `processed_chunks.json`
   - Generate a data quality report

### Directory Structure (Phase 2)

```
phase2/
├── processor/
│   ├── __init__.py
│   ├── schema_validator.py    # JSON schema validation
│   ├── data_cleaner.py        # Cleaning & normalization
│   ├── document_builder.py    # Build structured documents
│   ├── chunker.py             # Semantic chunking logic
│   └── utils.py               # Helpers
├── data/
│   ├── processed/
│   │   ├── structured_funds.json      # Clean structured data
│   │   └── processed_chunks.json      # All chunks ready for embedding
│   └── reports/
│       └── data_quality_report.json   # Quality metrics
├── tests/
│   ├── __init__.py
│   ├── test_cleaner.py
│   ├── test_chunker.py
│   └── test_document_builder.py
├── requirements.txt
├── run_processor.py           # CLI entry point
└── README.md
```

### Test Cases for Phase 2

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| T2.1 | Schema validation catches missing fields | Warning logged, field marked as N/A |
| T2.2 | Currency normalization works | "₹100" → numeric 100.0 |
| T2.3 | Percentage normalization works | "0.8%" → float 0.008 + display "0.8%" |
| T2.4 | Each fund produces 10+ chunks | ≥ 10 chunks per fund (overview, NAV, returns, costs, risk, investment, portfolio, AUM, manager, documents) |
| T2.5 | Chunk metadata tags are present | All chunks have `fund_id`, `chunk_type`, `metadata_tags` |
| T2.6 | FAQ chunks are created | ≥ 1 FAQ chunk per fund + static FAQs |
| T2.7 | Total chunk count matches expected | 5 funds × 10 chunk types + FAQ chunks + document chunks |
| T2.8 | No empty content in any chunk | All content fields are non-empty strings |
| T2.9 | Data quality report is generated | Report file exists with metrics |
| T2.10 | Re-processing is idempotent | Same input → same output |
| T2.11 | Returns chunk has all periods | 1M, 3M, 6M, 1Y, 3Y, 5Y, inception present |
| T2.12 | Document links chunk created | SID/KIM links present for each fund |

---

## 📋 Phase 3 — Vector Store & Embedding

### Objective
Generate vector embeddings for all chunks and store them in a vector database for efficient semantic retrieval.

### Embedding Strategy

| Component | Choice | Reason |
|-----------|--------|--------|
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` | Free, fast, good quality, 384-dim |
| **Alternative** | Google `text-embedding-004` | Higher quality, requires API key |
| **Vector Store** | **ChromaDB** | Lightweight, local, no infra needed, Python-native |
| **Alternative** | **Pinecone** | Managed cloud vector DB, scalable, serverless option |

### Implementation Steps

1. **Generate Embeddings**
   - Load all processed chunks from Phase 2
   - Generate embeddings using the chosen model
   - Each chunk's `content` field is embedded

2. **Store in ChromaDB**
   - Create a collection named `hdfc_mutual_funds`
   - Store each chunk with:
     - `id`: chunk_id
     - `embedding`: vector representation
     - `document`: chunk content text
     - `metadata`: fund_id, fund_name, chunk_type, last_updated

3. **Build Retrieval Interface**
   - `retrieve(query, top_k=3, fund_filter=None)` → Returns top-k relevant chunks
   - Support **metadata filtering** (e.g., filter by fund_name or chunk_type)
   - Return similarity scores for transparency

### Directory Structure (Phase 3)

```
phase3/
├── vectorstore/
│   ├── __init__.py
│   ├── embedder.py            # Embedding generation
│   ├── store.py               # ChromaDB operations
│   ├── retriever.py           # Query interface
│   └── config.py              # Model names, collection config
├── data/
│   └── chroma_db/             # ChromaDB persistent storage
├── tests/
│   ├── __init__.py
│   ├── test_embedder.py
│   ├── test_store.py
│   └── test_retriever.py
├── requirements.txt
├── run_vectorstore.py         # CLI: build/rebuild the vector store
└── README.md
```

### Test Cases for Phase 3

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| T3.1 | Embeddings generated for all chunks | Vector count = chunk count |
| T3.2 | ChromaDB collection created | Collection `hdfc_mutual_funds` exists |
| T3.3 | Query "expense ratio HDFC Pharma" | Top result contains Pharma fund key_facts chunk |
| T3.4 | Query "minimum SIP" | Results contain key_facts chunks |
| T3.5 | Query "how to download capital gains" | FAQ chunk is top result |
| T3.6 | Filter by fund_name works | Only chunks from specified fund returned |
| T3.7 | Similarity scores are returned | Scores between 0 and 1 |
| T3.8 | top_k parameter works | Exactly k results returned |
| T3.9 | Empty query returns no crash | Graceful handling, empty results |
| T3.10 | Vector store is persistent | Survives process restart |

---

## 📋 Phase 4 — RAG Pipeline & LLM Integration

### Objective
Build the complete RAG pipeline: query understanding → retrieval → prompt construction → LLM response generation.

> **Skills Focus**: This phase is the core of the evaluation. It must demonstrate:
> - **W1 (Thinking Like a Model)**: Identify the exact fact being asked. Decide to answer from context OR politely refuse.
> - **W2 (LLMs & Prompting)**: Instruction-style system prompt, concise phrasing, polite safe-refusals, and explicit citation wording.
> - **W3 (RAGs)**: Small-corpus retrieval from ChromaDB with accurate source citations in every response.

### LLM Options

| LLM | Pros | Cons |
|-----|------|------|
| **Google Gemini 2.5 Flash** | Latest, best reasoning, free tier | Requires API key |
| **Google Gemini 3 Flash** | Next-gen, fast, great quality | Requires API key |
| **Google Gemini 3.5 Flash** | Cutting-edge, highest quality | Requires API key |

**Recommended**: Start with **Gemini 2.5 Flash** (free tier sufficient). Upgrade to 3 / 3.5 Flash if available.

### RAG Pipeline Flow

```
User Query
    │
    ▼
┌──────────────────────────────┐
│  1. Query Preprocessor       │  Normalize, spell-check, extract fund name
└────────────┬─────────────────┘
             ▼
┌──────────────────────────────┐
│  2. Fact Identifier (W1)     │  What exact fact is being asked?
│     + Query Classifier       │  Classify: factual / procedural / general / refuse
└────────────┬─────────────────┘
             ▼
┌──────────────────────────────┐
│  3. Answer-vs-Refuse (W1)    │  Is this in scope? Can context answer it?
│     Gate                     │  YES → proceed  |  NO → polite refusal
└────────────┬─────────────────┘
             ▼
┌──────────────────────────────┐
│  4. Retriever                │  ChromaDB search + metadata filter
│     (from Phase 3)           │  Returns top-k relevant chunks (W3)
└────────────┬─────────────────┘
             ▼
┌──────────────────────────────┐
│  5. Prompt Builder (W2)      │  System prompt + context chunks + user query
│                              │  Instruction-style, citation rules
└────────────┬─────────────────┘
             ▼
┌──────────────────────────────┐
│  6. LLM (Gemini Flash)       │  Generate grounded response
└────────────┬─────────────────┘
             ▼
┌──────────────────────────────┐
│  7. Response Validator       │  Verify citations present, no hallucination
│     + Citation Formatter     │  Format source attributions (W3)
└────────────┬─────────────────┘
             ▼
        Final Response
```

### Prompt Template (W2 — Instruction Style)

The prompt is carefully engineered to demonstrate **W2 skills**: clear instruction style, concise phrasing, polite safe-refusals, and citation wording.

```
SYSTEM PROMPT:
You are a knowledgeable assistant for HDFC Mutual Funds. Your role is to
provide accurate, factual answers based ONLY on the retrieved context below.

HARD RULES (follow strictly — violations are unacceptable):
1. ANSWER ONLY from the provided CONTEXT. You have NO other knowledge.
   If the answer is not in the CONTEXT, you MUST refuse — never guess or
   use your own training data.
2. CITE the fund name, specific data point, AND source URL in every answer.
   Example: "The expense ratio of HDFC Pharma and Healthcare Fund is 0.95%
   (Source: HDFC Pharma and Healthcare Fund — Key Facts,
   {source_url}, last updated {last_updated})."
3. If the CONTEXT does not contain the answer, respond EXACTLY:
   "I'm sorry, I don't have information about that in my current data.
   I can only answer questions about the following HDFC Mutual Funds:
   {fund_list}. Please try rephrasing your question."
4. If the question is unrelated to HDFC Mutual Funds (e.g., weather, stocks,
   other AMCs), respond EXACTLY:
   "I appreciate your question, but I can only assist with queries about
   select HDFC Mutual Funds. Please ask about fund details like expense ratio,
   exit load, NAV, SIP amounts, or holdings."
5. NEVER provide investment advice, buy/sell recommendations, or future
   performance predictions.
6. DO NOT compare funds. If the user asks to compare two or more funds,
   respond: "I'm sorry, I can only provide information about one fund at a
   time. Please ask about a specific fund."
7. DO NOT request, process, or respond to any personal information
   (PAN, Aadhaar, email, phone, bank details). If the user shares or asks
   about personal data, respond: "I'm sorry, I cannot process personal
   information. This chatbot only provides factual information about HDFC
   Mutual Fund schemes."
8. Keep answers concise — 2-4 sentences for factual queries.
9. End every answer with: "Disclaimer: This information is for educational
   purposes only and should not be considered investment advice."

CONTEXT:
{retrieved_chunks}

DATA LAST UPDATED: {last_updated}

USER QUERY:
{user_query}
```

### Query Classification & Fact Identification (W1 — Thinking Like a Model)

The classification step must **think like the model**: identify the exact fact being asked and decide whether to answer or refuse.

#### Step 1: Identify the Exact Fact

| Signal | What to Extract | Example |
|--------|----------------|----------|
| **Fund Name** | Which fund is the user asking about? | "HDFC Pharma" → HDFC Pharma and Healthcare Fund |
| **Data Point** | Which specific metric? | "expense ratio", "exit load", "SIP amount" |
| **Comparison** | Multiple funds or single? | "Compare all" → **REFUSE** (constraint C4) |
| **Process** | Is it a how-to question? | "How to download" → FAQ retrieval |

#### Step 2: Answer vs. Refuse Decision

| Decision | Condition | Action |
|----------|-----------|--------|
| ✅ **Answer** | Fund recognized AND data point exists in embeddings | Retrieve → LLM → cite source + URL |
| ✅ **Answer (FAQ)** | Procedural query matches FAQ in embeddings | Retrieve FAQ chunk → LLM |
| ❌ **Polite Refusal (no data)** | Fund recognized BUT data point not in embeddings | Polite: "I don't have that information" |
| ❌ **Polite Refusal (wrong fund)** | Fund not in our 5-fund corpus | Polite: "I can only answer about [list funds]" |
| ❌ **Polite Refusal (off-topic)** | Question unrelated to mutual funds entirely | Polite: "I can only assist with HDFC MF queries" |
| ❌ **Polite Refusal (comparison)** | User asks to compare 2+ funds (C4) | Polite: "I can only provide info about one fund at a time" |
| ❌ **Polite Refusal (personal info)** | User shares/asks about PAN, Aadhaar, etc. (C3) | Polite: "I cannot process personal information" |
| ❌ **Polite Refusal (advice)** | User asks for buy/sell/investment advice (C5) | Polite: "I cannot provide investment advice" |

#### Query Type Routing

| Query Type | Example | Routing |
|------------|---------|---------|
| **Factual** | "What is the expense ratio of...?" | Identify fact → Retrieve chunk from embeddings → LLM with citation + URL |
| **Procedural** | "How to download capital gains?" | Retrieve FAQ chunk from embeddings → LLM with step-by-step format |
| **General** | "Tell me about HDFC Pharma Fund" | Retrieve overview chunk from embeddings → LLM with summary |
| **Comparative** | "Compare exit load of all funds" | ❌ **REFUSE** — "I can only provide info about one fund at a time" (C4) |
| **Personal Info** | "My PAN is ABCDE1234F" | ❌ **REFUSE** — "I cannot process personal information" (C3) |
| **Investment Advice** | "Should I buy HDFC Pharma?" | ❌ **REFUSE** — "I cannot provide investment advice" (C5) |
| **Out of Scope** | "What's the weather today?" | ❌ **REFUSE** — Direct polite refusal (W2 wording) |

### Directory Structure (Phase 4)

```
phase4/
├── rag/
│   ├── __init__.py
│   ├── query_preprocessor.py  # Query normalization
│   ├── query_classifier.py    # Intent classification
│   ├── prompt_builder.py      # Prompt template construction
│   ├── llm_client.py          # Gemini/OpenAI API wrapper
│   ├── response_validator.py  # Hallucination check & formatting
│   ├── pipeline.py            # End-to-end RAG pipeline
│   └── config.py              # API keys, model config
├── prompts/
│   └── system_prompt.txt      # System prompt template
├── tests/
│   ├── __init__.py
│   ├── test_preprocessor.py
│   ├── test_classifier.py
│   ├── test_pipeline.py       # End-to-end tests
│   └── test_responses.py      # Response quality tests
├── requirements.txt
├── run_rag.py                 # CLI: ask a question
└── README.md
```

### Test Cases for Phase 4

#### W1 Tests — Fact Identification & Answer vs. Refuse

| Test ID | Description | Skill | Expected Result |
|---------|-------------|-------|-----------------|
| T4.1 | "Expense ratio of HDFC Pharma Fund?" | W1: Identify fact | Response contains exact expense ratio value |
| T4.2 | "Minimum SIP for HDFC Manufacturing?" | W1: Identify fact | Response contains "₹100" or actual SIP value |
| T4.3 | "Exit load of HDFC Banking Fund?" | W1: Identify fact | Response contains exit load details |
| T4.4 | "Is HDFC Housing Fund ELSS?" | W1: Identify fact | Response says no lock-in / not ELSS |
| T4.5 | "Riskometer of HDFC Transport Fund?" | W1: Identify fact | Response contains riskometer rating |
| T4.6 | "What's the weather today?" | W1: Refuse (off-topic) | Polite refusal, no hallucinated answer |
| T4.7 | "Tell me about SBI Bluechip Fund" | W1: Refuse (wrong fund) | Polite refusal listing available HDFC funds |
| T4.8 | "Should I invest in HDFC Pharma?" | W1: Refuse (advice) | Polite refusal, no investment recommendation |

#### Constraint Tests — Guardrails Enforcement

| Test ID | Description | Constraint | Expected Result |
|---------|-------------|------------|-----------------|
| T4.9 | "Compare expense ratio of all funds" | C4: No comparisons | Polite refusal: "I can only provide info about one fund at a time" |
| T4.10 | "My PAN is ABCDE1234F, show my gains" | C3: No personal info | Polite refusal: "I cannot process personal information" |
| T4.11 | "What is the capital of India?" | C2: Embeddings only | Polite refusal, NOT an answer from LLM knowledge |
| T4.12 | "Can you store my Aadhaar number?" | C3: No personal info | Polite refusal, no data stored |
| T4.13 | "Which fund should I buy?" | C5: No advice | Polite refusal, no recommendation |

#### W2 Tests — Prompting Quality & Response Style

| Test ID | Description | Skill | Expected Result |
|---------|-------------|-------|-----------------|
| T4.14 | Response includes disclaimer | W2: Safe phrasing | "educational purposes only" or similar disclaimer present |
| T4.15 | Response cites source URL with fund name | W2: Citation wording | Source URL and fund name present in response |
| T4.16 | Refusal is polite, not curt | W2: Polite refusal | Contains "I appreciate" or "I'm sorry" — never "I can't" alone |
| T4.17 | Factual response is concise (2-4 sentences) | W2: Concise phrasing | Response ≤ 4 sentences for single-fact queries |

#### W3 Tests — RAG Retrieval & Citation Accuracy

| Test ID | Description | Skill | Expected Result |
|---------|-------------|-------|-----------------|
| T4.18 | "How to download capital gains?" | W3: FAQ retrieval | Step-by-step response from FAQ chunk |
| T4.19 | Pipeline handles empty retrieval | W3: No-match handling | Graceful "I don't have that information" |
| T4.20 | Retrieved chunk matches query intent | W3: Retrieval accuracy | top-1 chunk is semantically correct for query |
| T4.21 | Citation references actual scraped data | W3: Citation accuracy | Cited values match values in processed_chunks.json |
| T4.22 | Source URL present in every response | W3: URL citation | Every response includes the IndMoney source URL |

---

## 📋 Phase 5 — Chat Application (Frontend + Backend)

### Objective
Build the complete chat application as two independently deployable components: a **FastAPI backend API** that wraps the RAG pipeline, and a **modern HTML/CSS/JS frontend** that provides a polished user experience.

---

### Phase 5a — Backend API (FastAPI)

#### Why a Separate Backend?

| Concern | Monolith (Streamlit) | Separate Backend (FastAPI) |
|---------|---------------------|----------------------------|
| **Scalability** | Single process | Frontend & backend scale independently |
| **Deployment** | Tightly coupled | Frontend on CDN, backend on server |
| **Reusability** | UI-only access | Any client (mobile, CLI, 3rd-party) can call the API |
| **Testing** | Hard to test UI+logic together | API is independently testable |
| **Auth** | Limited | Proper token/session-based auth |

#### API Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `POST` | `/api/chat` | Send a user query, get RAG response | `{ "query": str, "fund_filter": str?, "user_id": str? }` | `{ "response": str, "sources": [...], "timestamp": str }` |
| `GET`  | `/api/health` | Health check & data freshness | — | `{ "status": "ok", "last_data_refresh": str }` |
| `GET`  | `/api/funds` | List available funds with key stats | — | `[ { "fund_id": str, "fund_name": str, "nav": str, ... } ]` |
| `GET`  | `/api/funds/{fund_id}` | Get details of a specific fund | — | `{ "fund_id": str, ... }` |
| `POST` | `/api/auth/google` | Verify Google ID token | `{ "id_token": str }` | `{ "user_id": str, "email": str, "name": str }` |
| `GET`  | `/api/suggestions` | Get suggested questions | — | `[ "What is the expense ratio?", ... ]` |

#### Backend Architecture

```
Request → CORS Middleware → Auth Middleware → Route Handler
                                                    │
                                                    ▼
                                            Phase 4 RAG Pipeline
                                                    │
                                                    ▼
                                              JSON Response
```

#### Key Backend Features

1. **CORS Configuration** — Allow frontend origin(s) for cross-origin requests
2. **Google Auth Verification** — Validate Google ID tokens for user authentication
3. **Session / Chat History** — Optional in-memory or Redis-backed chat history per user
4. **Rate Limiting** — Protect against abuse (e.g., 30 requests/min per user)
5. **Error Handling** — Structured error responses with appropriate HTTP status codes
6. **Logging & Metrics** — Request logging, latency tracking, error rates

#### Directory Structure (Phase 5 — Backend)

```
phase5/
├── backend/
│   ├── __init__.py
│   ├── main.py                # FastAPI app entry point
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py            # /api/chat endpoint
│   │   ├── funds.py           # /api/funds endpoints
│   │   ├── auth.py            # /api/auth/google endpoint
│   │   └── health.py          # /api/health endpoint
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── cors.py            # CORS configuration
│   │   └── rate_limiter.py    # Rate limiting
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py        # Pydantic request models
│   │   └── responses.py       # Pydantic response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rag_service.py     # Wraps Phase 4 pipeline
│   │   └── auth_service.py    # Google auth verification
│   ├── config.py              # Backend configuration
│   └── utils.py               # Helpers
├── tests/
│   ├── __init__.py
│   ├── test_chat_api.py       # Chat endpoint tests
│   ├── test_funds_api.py      # Funds endpoint tests
│   ├── test_auth.py           # Auth tests
│   └── test_health.py         # Health check tests
├── requirements.txt
├── run_backend.py             # Launch: uvicorn main:app
└── README.md
```

#### Test Cases for Phase 5 — Backend

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| T5B.1 | `POST /api/chat` with valid query | 200 response with RAG answer |
| T5B.2 | `POST /api/chat` with empty query | 400 error with validation message |
| T5B.3 | `GET /api/health` returns status | `{ "status": "ok" }` with data timestamp |
| T5B.4 | `GET /api/funds` lists all funds | Array of 5 fund objects |
| T5B.5 | `GET /api/funds/{id}` for valid fund | Fund details returned |
| T5B.6 | `GET /api/funds/{id}` for invalid fund | 404 error |
| T5B.7 | `POST /api/auth/google` with valid token | User info returned |
| T5B.8 | `POST /api/auth/google` with invalid token | 401 error |
| T5B.9 | CORS allows configured origins | Preflight request succeeds |
| T5B.10 | Rate limiting triggers after threshold | 429 Too Many Requests |

---

### Phase 5b — Frontend (HTML / CSS / JS)

#### Why a Separate Frontend?

A standalone frontend decoupled from the Python backend enables:
- **CDN deployment** (e.g., Vercel, Netlify) for fast global access
- **Full design control** — custom animations, glassmorphism, dark mode
- **Google Sign-In** via Google Identity Services (GIS)
- **Offline-capable** — can be turned into a PWA later

#### Features

1. **Chat Interface**
   - Message input box with send button
   - Chat history display (user messages + bot responses)
   - Typing indicator / streaming animation while LLM generates response
   - Clear chat button
   - Markdown rendering for formatted responses

2. **Google Sign-In**
   - One-tap Google authentication
   - Display user avatar, name, and email
   - Personalized experience per user

3. **Fund Selector Sidebar**
   - Dropdown or pill buttons to filter by specific fund
   - "All Funds" option for cross-fund queries
   - Fund cards showing key stats (NAV, riskometer, etc.)

4. **Suggested Questions**
   - Quick-action chips for common queries:
     - "What is the expense ratio?"
     - "What is the exit load?"
     - "Minimum SIP amount?"
     - "How to download capital gains statement?"

5. **Response Formatting**
   - Markdown → HTML rendering for tables and lists
   - Source citation badges
   - Data freshness timestamp

6. **Responsive Design**
   - Mobile-first, works on all screen sizes
   - Dark mode support
   - Smooth micro-animations and transitions

#### Frontend ↔ Backend Communication

```
Frontend (JS)                         Backend (FastAPI)
─────────────                         ─────────────────
fetch('/api/chat', { POST })   ──►    /api/chat handler
                               ◄──    JSON { response, sources }

fetch('/api/funds', { GET })   ──►    /api/funds handler
                               ◄──    JSON [ fund1, fund2, ... ]

Google Sign-In (GIS)           ──►    /api/auth/google
                               ◄──    JSON { user_id, name }
```

#### Directory Structure (Phase 5 — Frontend)

```
phase5/
├── frontend/
│   ├── index.html             # Main HTML page
│   ├── css/
│   │   ├── styles.css         # Core styles, design tokens
│   │   ├── chat.css           # Chat-specific styles
│   │   └── responsive.css    # Media queries
│   ├── js/
│   │   ├── app.js             # Main application logic
│   │   ├── api.js             # Backend API client (fetch wrappers)
│   │   ├── chat.js            # Chat UI logic
│   │   ├── auth.js            # Google Sign-In integration
│   │   └── utils.js           # Markdown rendering, helpers
│   └── assets/
│       ├── logo.svg           # App logo
│       └── icons/             # UI icons
└── ...
```

#### Test Cases for Phase 5 — Frontend

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| T5F.1 | Page loads without errors | HTML renders, JS initializes |
| T5F.2 | User can type and send a message | Message appears in chat history |
| T5F.3 | Bot response appears after query | Response displayed with Markdown formatting |
| T5F.4 | Suggested questions are clickable | Clicking auto-fills and sends the query |
| T5F.5 | Fund filter changes scope | Queries include selected fund filter |
| T5F.6 | Chat history persists during session | Previous messages visible on scroll |
| T5F.7 | Clear chat works | All messages removed from view |
| T5F.8 | Responsive on mobile viewport | UI adapts gracefully at ≤ 768px |
| T5F.9 | Google Sign-In button works | Auth flow completes, user info displayed |
| T5F.10 | Error state shows user-friendly message | Network/server errors handled gracefully |

---

## 📋 Phase 6 — Integration Testing & End-to-End Validation

### Objective
Validate the complete pipeline from data ingestion to user response, ensuring all phases work together seamlessly.

### Integration Test Scenarios

| Test ID | Scenario | Steps | Expected Result |
|---------|----------|-------|-----------------|
| T6.1 | Full pipeline: scrape → process → embed → query | Run Phase 1-4 sequentially | Accurate response to test query |
| T6.2 | Data freshness | Scrape → check timestamps | Chunks have recent timestamps |
| T6.3 | Cross-fund comparison | "Compare expense ratios of all funds" | Table with all 5 funds' ratios |
| T6.4 | Unknown fund query | "Tell me about HDFC XYZ Fund" | Graceful "not available" response |
| T6.5 | Concurrent queries | 10 simultaneous queries | All return valid responses |
| T6.6 | Data update flow | Re-scrape → re-process → re-embed | Updated data reflected in responses |

---

## 📋 Phase 7 — Data Refresh Scheduler

### Objective
Automate the periodic re-execution of the data pipeline (Phase 1 → Phase 2 → Phase 3) so that the chatbot always serves the **latest mutual fund data** without manual intervention.

### Why a Scheduler?

Mutual fund data changes frequently — NAV updates daily, AUM changes, holdings shift quarterly. Without a scheduler:
- Users receive **stale data** and lose trust.
- Someone must **manually** re-run 3 phases every time data needs refreshing.
- There is **no visibility** into when data was last refreshed or whether the refresh succeeded.

### Scheduler Design

```
┌─────────────────────────────────────────────────────────┐
│                 DATA REFRESH SCHEDULER                   │
│                    (APScheduler)                         │
└──────────┬──────────────────────────────────────────────┘
           │  On schedule (configurable: daily / weekly)
           ▼
   ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
   │   Phase 1     │────►│   Phase 2     │────►│   Phase 3     │
   │  Re-scrape    │     │  Re-process   │     │  Re-embed     │
   │  fund data    │     │  & re-chunk   │     │  & update     │
   │              │     │              │     │  vector store │
   └───────────────┘     └───────────────┘     └───────────────┘
           │                     │                     │
           └─────────────────────┴─────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     STATUS TRACKER       │
                    │  • Last run timestamp    │
                    │  • Success / failure     │
                    │  • Data diff summary     │
                    │  • Health check update   │
                    └─────────────────────────┘
```

### Scheduler Modes

| Mode | Trigger | Use Case |
|------|---------|----------|
| **Cron (Scheduled)** | APScheduler cron trigger (e.g., daily at 6 AM IST) | Production: automatic, hands-off |
| **Interval** | Every N hours | Development / frequent-refresh needs |
| **Manual** | CLI command or API call to `/api/refresh` | On-demand data refresh |

### Implementation Steps

1. **Scheduler Core**
   - Use **APScheduler** (`BackgroundScheduler`) to schedule jobs
   - Define a `refresh_pipeline()` job that orchestrates Phase 1 → 2 → 3
   - Configure schedule via environment variables (`SCHEDULER_CRON`, `SCHEDULER_INTERVAL_HOURS`)

2. **Pipeline Orchestrator**
   - Import and invoke Phase 1 scraper, Phase 2 processor, Phase 3 embedder **programmatically**
   - Each phase reports success/failure and data stats
   - If any phase fails, halt the cascade and log the error (do NOT partially update the vector store)

3. **Status Tracking**
   - Maintain a `scheduler_status.json` file with:
     ```json
     {
       "last_run": "2026-03-02T06:00:00+05:30",
       "status": "success",
       "phases": {
         "phase1": { "status": "success", "funds_scraped": 5, "duration_sec": 45 },
         "phase2": { "status": "success", "chunks_created": 28, "duration_sec": 3 },
         "phase3": { "status": "success", "vectors_stored": 28, "duration_sec": 12 }
       },
       "next_run": "2026-03-03T06:00:00+05:30",
       "data_changes": {
         "nav_updated": true,
         "new_holdings": false
       }
     }
     ```
   - Expose status via the backend `/api/health` endpoint (data freshness)

4. **Error Handling & Notifications**
   - Retry failed phases up to `SCHEDULER_RETRY_COUNT` times
   - Log all errors with full traceback
   - Optional: send email/Slack notification on failure (configurable)

5. **Data Diff Detection**
   - Compare newly scraped data with previous data
   - Log what changed (e.g., "NAV updated for 3 funds", "New holding detected")
   - Skip re-embedding if no data changes detected (optimization)

### Integration with Backend

The scheduler can run in two deployment modes:

| Mode | Description | Pros | Cons |
|------|-------------|------|------|
| **Embedded** | Scheduler runs inside the FastAPI process | Simple, single process | Scheduler stops if backend restarts |
| **Standalone** | Scheduler runs as a separate process/service | Independent lifecycle | Slightly more complex deployment |

**Recommended**: Start with **Embedded** mode (scheduler starts when the backend starts). Upgrade to Standalone for production.

### Directory Structure (Phase 7)

```
phase7/
├── scheduler/
│   ├── __init__.py
│   ├── scheduler.py           # APScheduler setup & job definitions
│   ├── orchestrator.py        # Pipeline orchestrator (Phase 1→2→3)
│   ├── status_tracker.py      # Read/write scheduler_status.json
│   ├── diff_detector.py       # Compare old vs new scraped data
│   ├── notifier.py            # Optional: email/Slack notifications
│   └── config.py              # Schedule, retry, notification config
├── data/
│   └── scheduler_status.json  # Persistent status file
├── tests/
│   ├── __init__.py
│   ├── test_scheduler.py      # Scheduler job tests
│   ├── test_orchestrator.py   # Pipeline cascade tests
│   ├── test_status_tracker.py # Status read/write tests
│   └── test_diff_detector.py  # Data diff tests
├── requirements.txt
├── run_scheduler.py           # CLI: start the scheduler
└── README.md
```

### Test Cases for Phase 7

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| T7.1 | Scheduler starts without errors | APScheduler initializes, job registered |
| T7.2 | Manual trigger runs full pipeline | Phase 1→2→3 execute in order |
| T7.3 | Phase 1 failure halts cascade | Phase 2 and 3 do NOT run |
| T7.4 | Phase 2 failure halts cascade | Phase 3 does NOT run, vector store unchanged |
| T7.5 | Status file updated after run | `scheduler_status.json` has correct timestamps |
| T7.6 | `/api/health` reflects last refresh | `last_data_refresh` matches scheduler status |
| T7.7 | No-change detection skips re-embed | Phase 3 skipped when data unchanged |
| T7.8 | Retry logic works on transient failure | Phase retried up to N times before failing |
| T7.9 | Cron schedule fires at configured time | Job executes at specified cron expression |
| T7.10 | Concurrent refresh blocked | Second refresh request rejected while one is running |

---

## 🔧 Global Configuration

### Environment Variables (`.env`)

```env
# LLM Configuration
GOOGLE_API_KEY=your_google_gemini_api_key
LLM_MODEL=gemini-2.5-flash            # Options: gemini-2.5-flash, gemini-3-flash, gemini-3.5-flash
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=1024

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# ChromaDB Configuration
CHROMA_PERSIST_DIR=./data/chroma_db
CHROMA_COLLECTION=hdfc_mutual_funds

# Scraper Configuration
SCRAPER_HEADLESS=true
SCRAPER_TIMEOUT=30
SCRAPER_RETRY_COUNT=3

# Backend API Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5500
GOOGLE_CLIENT_ID=your_google_client_id
RATE_LIMIT_PER_MINUTE=30

# Frontend Configuration
FRONTEND_API_URL=http://localhost:8000

# Scheduler Configuration
SCHEDULER_ENABLED=true
SCHEDULER_CRON=0 6 * * *          # Daily at 6:00 AM
SCHEDULER_INTERVAL_HOURS=24        # Alternative: run every N hours
SCHEDULER_RETRY_COUNT=3
SCHEDULER_MODE=embedded             # embedded | standalone

# General
LOG_LEVEL=INFO
```

### Global `requirements.txt`

```
# Phase 1: Scraping
playwright>=1.40.0

# Phase 2: Processing
jsonschema>=4.20.0

# Phase 3: Vector Store
chromadb>=0.4.22
sentence-transformers>=2.3.0

# Phase 4: RAG
google-generativeai>=0.3.0
# openai>=1.6.0  # Alternative LLM

# Phase 5: Backend API
fastapi>=0.109.0
uvicorn>=0.25.0
httpx>=0.26.0              # For testing async endpoints
google-auth>=2.25.0        # Google ID token verification
slowapi>=0.1.9             # Rate limiting for FastAPI

# Phase 7: Scheduler
apscheduler>=3.10.4

# Common
python-dotenv>=1.0.0
pydantic>=2.5.0
pytest>=7.4.0
loguru>=0.7.0
```

---

## 📁 Complete Project Structure

```
GenAIBootcamp_Milestone1/
├── ARCHITECTURE.md            # This file
├── .env                       # Environment variables (git-ignored)
├── .env.example               # Template for .env
├── .gitignore
├── requirements.txt           # Global dependencies
├── README.md                  # Project overview & setup guide
│
├── phase1/                    # Data Collection
│   ├── scraper/
│   ├── data/raw/
│   ├── tests/
│   ├── run_scraper.py
│   └── README.md
│
├── phase2/                    # Data Processing
│   ├── processor/
│   ├── data/processed/
│   ├── tests/
│   ├── run_processor.py
│   └── README.md
│
├── phase3/                    # Vector Store
│   ├── vectorstore/
│   ├── data/chroma_db/
│   ├── tests/
│   ├── run_vectorstore.py
│   └── README.md
│
├── phase4/                    # RAG Pipeline
│   ├── rag/
│   ├── prompts/
│   ├── tests/
│   ├── run_rag.py
│   └── README.md
│
├── phase5/                    # Chat Application (Frontend + Backend)
│   ├── backend/               #   API Server (FastAPI)
│   │   ├── routes/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── services/
│   │   ├── main.py
│   │   └── config.py
│   ├── frontend/              #   Chat UI (HTML/CSS/JS)
│   │   ├── index.html
│   │   ├── css/
│   │   ├── js/
│   │   └── assets/
│   ├── tests/
│   ├── run_backend.py
│   └── README.md
│
├── phase6/                    # Integration Tests
│   ├── tests/
│   └── README.md
│
└── phase7/                    # Data Refresh Scheduler
    ├── scheduler/
    │   ├── scheduler.py
    │   ├── orchestrator.py
    │   ├── status_tracker.py
    │   ├── diff_detector.py
    │   └── config.py
    ├── data/
    │   └── scheduler_status.json
    ├── tests/
    ├── run_scheduler.py
    └── README.md
```

---

## 🚀 Execution Order

| Order | Phase | Command | Dependencies |
|-------|-------|---------|-------------|
| 1 | Phase 1 — Data Collection | `python phase1/run_scraper.py` | Playwright installed (`playwright install chromium`) |
| 2 | Phase 2 — Data Processing | `python phase2/run_processor.py` | Phase 1 data |
| 3 | Phase 3 — Vector Store | `python phase3/run_vectorstore.py` | Phase 2 data |
| 4 | Phase 4 — RAG Pipeline | `python phase4/run_rag.py "your question"` | Phase 3 vector store |
| 5 | Phase 5b — Backend API | `python phase5/run_backend.py` | Phase 4 pipeline |
| 6 | Phase 5a — Frontend | Open `phase5/frontend/index.html` or serve via Live Server | Backend running |
| 7 | Phase 6 — Integration Tests | `pytest phase6/tests/` | All phases |
| 8 | Phase 7 — Scheduler | `python phase7/run_scheduler.py` | Phases 1-3 importable |

> **Note:** In production, Phase 7 (Scheduler) starts alongside the Backend and automatically keeps data fresh by periodically re-running Phases 1 → 2 → 3.

---

> **Next Step**: Begin implementation of **Phase 1 — Data Collection**. This involves setting up the Playwright scraper to extract fund data from IndMoney.
