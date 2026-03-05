# Phase 3 — Vector Store & Embedding

## Objective

Generate vector embeddings for all Phase 2 chunks and store them in ChromaDB for efficient semantic retrieval.

## Technology Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| **Embedding Model** | `all-MiniLM-L6-v2` | Free, fast, 384-dim, good quality |
| **Vector Store** | ChromaDB (persistent) | Local, no infra, Python-native |
| **Gemini Model** | `gemini-2.5-flash` | Set in `.env`, used in Phase 4 |

## Setup

```bash
pip install -r phase3/requirements.txt

# Build the vector store (first time)
python -m phase3.run_vectorstore
```

## Usage

```bash
# Build vector store from Phase 2 chunks
python -m phase3.run_vectorstore

# Force rebuild (delete + recreate)
python -m phase3.run_vectorstore --rebuild

# Query the vector store
python -m phase3.run_vectorstore --query "What is the expense ratio of HDFC Pharma?"

# Query with fund filter
python -m phase3.run_vectorstore --query "minimum SIP" --fund hdfc_pharma_healthcare

# Show statistics
python -m phase3.run_vectorstore --stats
```

## Testing

```bash
python -m pytest phase3/tests/ -v
```

## Architecture

```
User Query → Embedder (MiniLM) → ChromaDB Search → Top-K Chunks
                                                        ↓
                                               Metadata Filtering
                                               (fund_id, chunk_type)
                                                        ↓
                                               Ranked Results with
                                               similarity scores
```

## Output

- **ChromaDB**: Persistent storage in `phase3/data/chroma_db/`
- **96 vectors** from Phase 2 chunks
- Each vector stores: content, fund_id, fund_name, chunk_type, source_url, last_updated
