# LangGraph Agent - Compilation & Testing Guide

## Quick Start - 3 Steps

### Step 1: Setup Environment
```bash
cd e:\epoch_explorers

# Install dependencies
pip install -r requirements.txt

# Setup database
python scripts/setup_db.py
```

### Step 2: Create Config Files
```bash
# Create LLM config
mkdir -p src/rag/config

# Create llm_config.json
cat > src/rag/config/llm_config.json << 'EOF'
{
  "default_provider": "ollama",
  "llm_providers": {
    "ollama": {
      "type": "ollama",
      "enabled": true,
      "model": "llama3.1:latest",
      "api_endpoint": "http://localhost:11434",
      "temperature": 0.3,
      "max_tokens": 2000
    }
  },
  "embedding_providers": {
    "ollama_embedding": {
      "type": "ollama",
      "enabled": true,
      "model": "nomic-embed-text",
      "api_endpoint": "http://localhost:11434"
    }
  },
  "default_embedding_provider": "ollama_embedding"
}
EOF
```

### Step 3: Run Agent
```bash
python -c "
from src.rag.agents.langgraph_agent import LangGraphRAGAgent

# Initialize agent
agent = LangGraphRAGAgent()
print('[✓] LangGraph agent compiled successfully!')

# Test ingestion
result = agent.ingest_document(
    text='This is a test document about Python.',
    doc_id='test_doc_20250129_001'
)
print(f'Ingestion result: {result}')

# Test retrieval
answer = agent.ask_question(
    question='What is this document about?',
    response_mode='concise'
)
print(f'Answer: {answer[\"answer\"]}'
)
"
```

---

## Full Compilation Process

### 1. **Install Requirements**

```bash
# Navigate to project root
cd e:\epoch_explorers

# Install all dependencies
pip install -r requirements.txt

# Verify installations
python -c "import langgraph; import langchain; print('✓ LangChain & LangGraph installed')"
```

**Required packages:**
- `langgraph>=0.1.0` - Workflow orchestration
- `langchain>=0.2.14` - LLM framework
- `chromadb>=0.3.0` - Vector database
- `docling>=1.0.0` - Document conversion
- `pydantic>=2.0.0` - Data validation

---

### 2. **Setup Configuration Files**

**Location**: `src/rag/config/`

**Create llm_config.json**:
```json
{
  "default_provider": "ollama",
  "llm_providers": {
    "ollama": {
      "type": "ollama",
      "enabled": true,
      "model": "llama3.1:latest",
      "api_endpoint": "http://localhost:11434",
      "temperature": 0.3,
      "max_tokens": 2000
    }
  },
  "embedding_providers": {
    "ollama_embedding": {
      "type": "ollama",
      "enabled": true,
      "model": "nomic-embed-text",
      "api_endpoint": "http://localhost:11434"
    }
  },
  "default_embedding_provider": "ollama_embedding"
}
```

**Create data_sources.json** (for web APIs):
```json
{
  "data_sources": [
    {
      "name": "budget_api",
      "type": "rest_api",
      "url": "https://api.example.com/budgets",
      "method": "GET",
      "headers": {"Authorization": "Bearer token"},
      "enabled": true
    }
  ]
}
```

---

### 3. **Setup Database**

```bash
# Run migrations
python scripts/setup_db.py

# Verify database
sqlite3 src/database/data/incident_iq.db ".tables"
```

Expected tables:
- `rag_history_and_optimization` - Query/healing logs
- `agent_memory` - Agent memory storage
- `chunk_embedding_data` - Embedding metadata
- `document_metadata` - Document metadata

---

### 4. **Verify LangGraph Graphs**

```python
from src.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()

# Check ingestion graph
print("=== INGESTION GRAPH ===")
print(agent.ingestion_graph.get_graph())

# Check retrieval graph
print("\n=== RETRIEVAL GRAPH ===")
print(agent.retrieval_graph.get_graph())

# Check optimization graph
print("\n=== OPTIMIZATION GRAPH ===")
print(agent.optimization_graph.get_graph())
```

---

### 5. **Test Each Workflow**

#### A. **Test Ingestion Workflow**

```python
from src.rag.agents.langgraph_agent import LangGraphRAGAgent
import json

agent = LangGraphRAGAgent()

# Test document ingestion
text = """
# Budget Report 2025

This document outlines the budget allocation for 2025:

## Revenue
- Product Sales: $2M
- Services: $1M
- Consulting: $500K

## Expenses
- Operations: $1.5M
- R&D: $1M
- Marketing: $500K
"""

result = agent.ingest_document(
    text=text,
    doc_id="file_budget_report_20250129_001"
)

print(json.dumps(result, indent=2))
```

**Expected output**:
```json
{
  "success": true,
  "doc_id": "file_budget_report_20250129_001",
  "chunks_count": 5,
  "chunks_saved": 5,
  "metadata": {
    "title": "Budget Report 2025",
    "keywords": ["budget", "revenue", "expenses"]
  },
  "errors": []
}
```

#### B. **Test Retrieval Workflow**

```python
from src.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()

# Answer question
response = agent.ask_question(
    question="What are the revenue sources?",
    response_mode="concise"
)

print(f"Answer: {response['answer']}")
print(f"Sources: {response.get('source_docs', [])}")
print(f"Quality Score: {response.get('quality_score', 'N/A')}")
```

**Expected output**:
```
Answer: The revenue sources are: Product Sales ($2M), Services ($1M), and Consulting ($500K).
Sources: [{'doc_id': 'file_budget_report_20250129_001', 'chunk_id': '...'}]
Quality Score: 0.85
```

#### C. **Test Response Modes**

```python
# CONCISE - User friendly
response_concise = agent.ask_question(
    question="What is the budget?",
    response_mode="concise"
)
print("CONCISE:", response_concise['answer'])

# INTERNAL - System integration
response_internal = agent.ask_question(
    question="What is the budget?",
    response_mode="internal"
)
print("INTERNAL:", response_internal)

# VERBOSE - Full debug info
response_verbose = agent.ask_question(
    question="What is the budget?",
    response_mode="verbose"
)
print("VERBOSE:", json.dumps(response_verbose, indent=2))
```

---

### 6. **Test Agent Memory**

```python
from src.rag.tools.ingestion_tools import (
    record_agent_memory_tool,
    retrieve_agent_memory_tool
)
import json

# Record memory
mem_result = record_agent_memory_tool.invoke({
    "agent_name": "langgraph_agent",
    "memory_type": "decision",
    "memory_key": "healing_strategy_re_embed",
    "memory_value": json.dumps({
        "strategy": "RE_EMBED",
        "success_rate": 0.85,
        "best_for": "low_quality_retrieval"
    }),
    "importance_score": 0.9,
    "ttl_hours": 72
})
print("Memory recorded:", mem_result)

# Retrieve memory
retrieve_result = retrieve_agent_memory_tool.invoke({
    "agent_name": "langgraph_agent",
    "memory_type": "decision",
    "limit": 5
})
mem_dict = json.loads(retrieve_result)
print("Memories found:", len(mem_dict['memories']))
for mem in mem_dict['memories']:
    print(f"  - {mem['memory_key']}: {mem['importance_score']}")
```

---

### 7. **Test with Interactive Chat**

```python
from src.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()

# Start interactive chat
result = agent.invoke_chat(response_mode="concise", show_history=True)

print(f"Total messages: {result['message_count']}")
print(f"Session stats: {result['session_stats']}")
```

---

## Compilation Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with paths
- [ ] `llm_config.json` created in `src/rag/config/`
- [ ] Database migrations run (`python scripts/setup_db.py`)
- [ ] ChromaDB directory created
- [ ] Ollama service running (or other LLM backend)
- [ ] All imports resolve (no ImportError)
- [ ] LangGraph graphs compile (no StateGraph errors)
- [ ] Ingestion workflow tested
- [ ] Retrieval workflow tested
- [ ] Agent memory tested
- [ ] Response modes tested

---

## Common Issues & Fixes

### Issue 1: "FileNotFoundError: llm_config.json not found"

**Fix:**
```bash
# Create config file
mkdir -p src/rag/config
cat > src/rag/config/llm_config.json << 'EOF'
{
  "default_provider": "ollama",
  "llm_providers": {
    "ollama": {
      "type": "ollama",
      "enabled": true,
      "model": "llama3.1:latest",
      "api_endpoint": "http://localhost:11434",
      "temperature": 0.3,
      "max_tokens": 2000
    }
  },
  "embedding_providers": {
    "ollama_embedding": {
      "type": "ollama",
      "enabled": true,
      "model": "nomic-embed-text",
      "api_endpoint": "http://localhost:11434"
    }
  },
  "default_embedding_provider": "ollama_embedding"
}
EOF
```

### Issue 2: "ModuleNotFoundError: No module named 'langgraph'"

**Fix:**
```bash
pip install langgraph langchain langchain-core langchain-text-splitters
```

### Issue 3: "Connection refused" (Ollama not running)

**Fix:**
```bash
# Start Ollama
ollama serve

# In another terminal, verify
ollama list
ollama pull llama3.1:latest
ollama pull nomic-embed-text
```

### Issue 4: "AgentMemoryModel not found"

**Fix:**
```bash
# Run migrations
python scripts/setup_db.py

# Verify table created
sqlite3 src/database/data/incident_iq.db "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_memory';"
```

### Issue 5: "VectorDB connection error"

**Fix:**
```bash
# Check ChromaDB path in .env
cat .env | grep CHROMA

# Create directory if missing
mkdir -p src/database/data/chroma_db

# Reset ChromaDB (if needed)
rm -rf src/database/data/chroma_db
```

---

## Docker Compilation (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Setup database
RUN python scripts/setup_db.py

# Run agent
CMD ["python", "-m", "src.rag.agents.langgraph_agent"]
```

**Build and run:**
```bash
docker build -t langgraph-rag .
docker run -it langgraph-rag
```

---

## Performance Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Agent initialization | ~2-3s | Loads graphs, services |
| Document ingestion (5KB) | ~5-10s | Embedding generation |
| Query retrieval | ~2-5s | Vector search + reranking |
| Answer generation | ~3-8s | LLM inference |
| Total Q&A cycle | ~10-25s | End-to-end |
| Memory recording | ~50-100ms | Cache + SQLite |
| Memory retrieval | ~10-20ms | Cache hit, ~100-200ms miss |

---

## Debugging Tips

### Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run agent
agent = LangGraphRAGAgent()
```

### Check graph structure:
```python
from langgraph.graph import visualize_graph

# Visualize ingestion workflow
graph_image = visualize_graph(agent.ingestion_graph)
graph_image.write_png("ingestion_graph.png")
```

### Monitor performance:
```python
import time
start = time.time()
result = agent.ask_question("What is the budget?", response_mode="verbose")
elapsed = time.time() - start
print(f"Query took {elapsed:.2f} seconds")
```

---

## Next Steps

1. ✅ Compile agent (this guide)
2. Test end-to-end workflow
3. Deploy to production
4. Monitor performance & quality
5. Tune parameters based on metrics

