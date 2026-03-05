# 🏦 HDFC Mutual Fund RAG Chatbot

An intelligent **Retrieval-Augmented Generation (RAG)** chatbot that answers user queries about select HDFC Mutual Funds using real-time data from [IndMoney](https://www.indmoney.com/mutual-funds/amc/hdfc-mutual-fund).

## 🎯 Supported Funds

| Fund Name | Risk Level |
|-----------|------------|
| HDFC Banking & Financial Services Fund | Very High |
| HDFC Pharma and Healthcare Fund | Very High |
| HDFC Housing Opportunities Fund | Very High |
| HDFC Manufacturing Fund | Very High |
| HDFC Transportation and Logistics Fund | Very High |

## 💬 Sample Queries

- "What is the expense ratio of HDFC Pharma and Healthcare Fund?"
- "Is there an ELSS lock-in for HDFC Banking Fund?"
- "What is the minimum SIP amount?"
- "What is the exit load?"
- "What is the riskometer/benchmark?"
- "How to download capital-gains statement?"

## 🏗️ Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the complete phase-wise architecture.

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Data Collection (Web Scraping) | 🔲 Not Started |
| Phase 2 | Data Processing & Chunking | 🔲 Not Started |
| Phase 3 | Vector Store & Embedding | 🔲 Not Started |
| Phase 4 | RAG Pipeline & LLM Integration | 🔲 Not Started |
| Phase 5 | Chat UI (Frontend) | 🔲 Not Started |
| Phase 6 | Integration Testing | 🔲 Not Started |

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Chrome (for web scraping)
- Google Gemini API key

### Setup

```bash
# Clone the repository
git clone https://github.com/g3menon/GenAIBootcamp_Milestone1.git
cd GenAIBootcamp_Milestone1

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Run

```bash
# Phase 1: Scrape data
python phase1/run_scraper.py

# Phase 2: Process data
python phase2/run_processor.py

# Phase 3: Build vector store
python phase3/run_vectorstore.py

# Phase 4: Test RAG pipeline
python phase4/run_rag.py "What is the expense ratio of HDFC Pharma Fund?"

# Phase 5: Launch chat UI
streamlit run phase5/app/streamlit_app.py
```

## 📄 License

This project is for educational purposes as part of the GenAI Bootcamp.
