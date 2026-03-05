# Phase 2 — Data Processing & Chunking

## Objective

Transform raw scraped data from Phase 1 into clean, structured, and chunked documents optimized for vector embedding and retrieval (Phase 3).

## Key Concept

Instead of storing each fund as one large document, Phase 2 creates **narrow, fact-dense semantic chunks** so the retriever can isolate the exact answer for any query.

## Setup

```bash
# Ensure Phase 1 data exists
ls phase1/data/raw/hdfc_*.json

# Run the processor
python -m phase2.run_processor
```

## Usage

```bash
# Full pipeline: validate → clean → chunk → save
python -m phase2.run_processor

# Validate raw data only (no chunking)
python -m phase2.run_processor --validate-only

# Show chunk statistics
python -m phase2.run_processor --stats
```

## Testing

```bash
python -m pytest phase2/tests/ -v
```

## Chunk Types (11 per fund)

| # | Chunk Type | Content | Target Queries |
|---|------------|---------|----------------|
| 1 | **Overview** | Fund name + category + plan + benchmark | "Tell me about HDFC Pharma Fund" |
| 2 | **NAV Data** | Current NAV + NAV date + since-inception | "What is the NAV?" |
| 3 | **Returns** | 1M, 3M, 6M, 1Y, 3Y, 5Y + benchmark | "1-year return?" |
| 4 | **Costs** | Expense ratio + exit load | "What is the expense ratio?" |
| 5 | **Risk** | Riskometer + ELSS/lock-in | "Is this fund ELSS?" |
| 6 | **Investment** | Min SIP + lumpsum | "What is the minimum SIP?" |
| 7 | **Portfolio** | Top holdings + sectors | "Top holdings?" |
| 8 | **AUM** | Current AUM value | "What is the AUM?" |
| 9 | **Manager** | Manager name + details | "Who manages this fund?" |
| 10 | **Documents** | SID/KIM/Factsheet links | "Where is the SID?" |
| 11 | **FAQ** | One chunk per FAQ Q&A pair | "How to download capital gains?" |

## Output Files

```
phase2/data/processed/
├── processed_chunks.json       # All chunks ready for embedding
└── quality_report.json         # Data quality metrics
```

## Chunk Schema

Every chunk contains:
- `chunk_id` — Unique identifier
- `fund_id` — Source fund
- `fund_name` — Human-readable name
- `source_url` — Citation URL (Constraint C6)
- `chunk_type` — Category of information
- `metadata_tags` — Searchable tags for filtering
- `content` — Natural language text for embedding
- `last_updated` — ISO timestamp

## Constraints Applied

- **C1**: No PDF content — only web-scraped data
- **C6**: Every chunk carries `source_url` for citation
