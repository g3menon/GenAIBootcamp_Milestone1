# 🏦 HDFC Mutual Fund RAG Chatbot

An intelligent **Retrieval-Augmented Generation (RAG)** chatbot designed to provide accurate, grounded answers to user queries about select HDFC Mutual Funds. The bot leverages real-time data scraped from [IndMoney](https://www.indmoney.com/mutual-funds/amc/hdfc-mutual-fund), processed into a vector store, and served via a modern web interface.

## 🎯 Project Overview

This project is a multi-phase implementation of a production-ready AI application. It demonstrates core skills in web scraping, data engineering, vector databases, LLM orchestration (RAG), and web development.

### Supported Funds
- HDFC Banking & Financial Services Fund
- HDFC Pharma and Healthcare Fund
- HDFC Housing Opportunities Fund
- HDFC Manufacturing Fund
- HDFC Transportation and Logistics Fund

---

## 🏗️ Phase-wise Architecture

The project is divided into 7 distinct phases, each responsible for a critical part of the system:

| Phase | Module | Description | Key Tech |
| :--- | :--- | :--- | :--- |
| **Phase 1** | [Data Collection](file:///c:/Users/Gayathri/.gemini/antigravity/scratch/GenAIBootcamp_Milestone1/phase1) | Browser-based scraping of fund data from IndMoney. | Playwright, Python |
| **Phase 2** | [Data Processing](file:///c:/Users/Gayathri/.gemini/antigravity/scratch/GenAIBootcamp_Milestone1/phase2) | Cleaning, normalization, and semantic chunking of raw data. | JSON Schema, Pandas |
| **Phase 3** | [Vector Store](file:///c:/Users/Gayathri/.gemini/antigravity/scratch/GenAIBootcamp_Milestone1/phase3) | Embedding generation and storage in a vector database. | Pinecone, Sentence-Transformers |
| **Phase 4** | [RAG Pipeline](file:///c:/Users/Gayathri/.gemini/antigravity/scratch/GenAIBootcamp_Milestone1/phase4) | Intent classification and LLM response generation with citations. | Google Gemini, RAG |
| **Phase 5** | [API & UI](file:///c:/Users/Gayathri/.gemini/antigravity/scratch/GenAIBootcamp_Milestone1/phase5) | FastAPI backend and a premium Material Design frontend. | FastAPI, HTML/CSS/JS |
| **Phase 6** | [Testing](file:///c:/Users/Gayathri/.gemini/antigravity/scratch/GenAIBootcamp_Milestone1/phase6) | Comprehensive integration and guardrail testing. | Pytest |
| **Phase 7** | [Scheduler](file:///c:/Users/Gayathri/.gemini/antigravity/scratch/GenAIBootcamp_Milestone1/phase7) | Automated data refresh and pipeline orchestration. | Vercel Cron, Python |

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Google Gemini API Key** (for response generation)
- **Pinecone API Key** (for vector storage)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/g3menon/GenAIBootcamp_Milestone1.git
   cd GenAIBootcamp_Milestone1
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Environment Variables**:
   Create a `.env` file in the root directory based on `.env.example`:
   ```env
   GOOGLE_API_KEY=your_gemini_key
   PINECONE_API_KEY=your_pinecone_key
   PINECONE_ENVIRONMENT=your_env
   PINECONE_INDEX_NAME=hdfc-funds
   ```

---

## 🛠️ How to Run

### 1. Run the Web Application (Local)
This hosts both the backend API and the frontend UI:
```bash
uvicorn phase5.backend.main:app --reload
```
Access the UI at: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

### 2. Run Individual Phases (Development)

- **Scrape Data (Phase 1)**:
  ```bash
  python -m phase1.run_scraper
  ```

- **Process & Chunk Data (Phase 2)**:
  ```bash
  python -m phase2.run_processor
  ```

- **Update Vector Store (Phase 3)**:
  ```bash
  python -m phase3.run_vectorstore --rebuild
  ```

- **Test RAG Pipeline (Phase 4)**:
  ```bash
  python run_rag.py "What is the expense ratio of HDFC Manufacturing Fund?"
  ```

- **Run Scheduler (Phase 7)**:
  ```bash
  python -m phase7.run_scheduler
  ```

---

## 🛡️ Guardrails & Constraints

To ensure financial accuracy and safety, the chatbot follows strict rules:
- **Groundedness**: Answers only using the provided vector context.
- **No Advice**: Never provides investment recommendations.
- **Privacy**: Refuses to handle personal information (PAN, Aadhaar).
- **Citations**: Every answer includes a direct source URL from IndMoney.
- **Limited Scope**: Only answers for the 5 supported HDFC funds.

## 📄 License
Educational project developed for the GenAI Bootcamp. Data ownership belongs to the respective providers.
