# LangGraph Agent - Quick Reference

## 🚀 One-Liner Compilation

```bash
# From project root
cd e:\epoch_explorers && pip install -r requirements.txt && python scripts/setup_db.py && python scripts/test_langgraph_compilation.py
```

---

## 📋 Step-by-Step Compilation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Config
```bash
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

### 3. Setup Database
```bash
python scripts/setup_db.py
```

### 4. Test Compilation
```bash
python scripts/test_langgraph_compilation.py
```

---

## 💻 Quick Usage Examples

### Initialize Agent
```python
from src.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()
```

### Ingest Document
```python
result = agent.ingest_document(
    text="Your document text here",
    doc_id="doc_id_20250129_001"
)
print(result['chunks_saved'])  # Number of chunks created
```

### Ask Question
```python
# User-friendly
response = agent.ask_question("Your question?", response_mode="concise")
print(response['answer'])

# Full debug info
debug_response = agent.ask_question("Your question?", response_mode="verbose")
print(json.dumps(debug_response, indent=2))
```

### Record Memory
```python
from src.rag.tools.ingestion_tools import record_agent_memory_tool
import json

record_agent_memory_tool.invoke({
    "agent_name": "langgraph_agent",
    "memory_type": "decision",
    "memory_key": "my_strategy",
    "memory_value": json.dumps({"key": "value"}),
    "importance_score": 0.9,
    "ttl_hours": 72
})
```

---

## 🔧 LangGraph Graph Compilation

### Ingestion Graph Structure
```
START 
  ↓
convert_markdown      (Normalize document format)
  ↓
classify_document     (Extract intent, department, roles)
  ↓
extract_metadata      (LLM semantic analysis)
  ↓
chunk_document        (Split into semantic chunks)
  ↓
save_vectordb         (Generate embeddings + store)
  ↓
update_tracking       (Audit trail)
  ↓
END
```

### Retrieval Graph Structure
```
START
  ↓
retrieve_context      (Semantic similarity search)
  ↓
rerank_context        (LLM-based relevance reranking)
  ↓
check_optimization    (RL agent decides if healing needed)
  ↓
optimize_context      (If needed: improve quality/reduce tokens)
  ↓
answer_question       (Generate answer from context)
  ↓
validate_guardrails   (Safety checks)
  ↓
traceability          (Audit logging)
  ↓
END
```

---

## ✅ Verification Checklist

- [ ] All imports resolve
- [ ] LangGraph StateGraph compiles
- [ ] llm_config.json created
- [ ] Database migrations complete
- [ ] ChromaDB directory exists
- [ ] Agent initializes without errors
- [ ] Ingestion workflow runs
- [ ] Retrieval workflow returns answers
- [ ] Memory recording works
- [ ] Response modes all function

---

## 🐛 Common Errors & Fixes

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: langgraph` | `pip install langgraph` |
| `FileNotFoundError: llm_config.json` | Create config file (see above) |
| `Connection refused (Ollama)` | Start Ollama: `ollama serve` |
| `agent_memory table not found` | Run: `python scripts/setup_db.py` |
| `ChromaDB connection error` | Create dir: `mkdir -p src/database/data/chroma_db` |

---

## 📊 Performance Baseline

| Operation | Time | Notes |
|-----------|------|-------|
| Agent init | 2-3s | Load services + graphs |
| Ingest (5KB) | 5-10s | With embedding |
| Query | 2-5s | Retrieval + rerank |
| Answer | 3-8s | LLM inference |
| **Total Q&A** | **10-25s** | End-to-end |

---

## 🎯 Response Modes

### Concise (User)
- Best for: End users
- Output: Answer only
- Guardrails: Full validation

### Internal (System)
- Best for: System integration
- Output: Answer + metadata
- Guardrails: Hallucination check

### Verbose (Engineer)
- Best for: Debugging
- Output: All debug info
- Guardrails: None (engineers need raw data)

---

## 📁 Project Structure

```
src/rag/agents/langgraph_agent/
├── langgraph_rag_agent.py         # Main agent class
├── __main__.py                     # CLI entry point
└── __init__.py

src/rag/tools/
├── ingestion_tools.py             # Document processing
├── retrieval_tools.py             # Context retrieval
├── healing_tools.py               # Optimization
└── __init__.py

src/database/
├── models/
│   ├── agent_memory_model.py      # Memory storage
│   └── rag_history_model.py       # Query/healing logs
├── cache/
│   └── agent_memory_cache.py      # LRU cache
└── migrations/
    └── 012_create_agent_memory_table.py

src/rag/config/
├── llm_config.json                # LLM configuration
├── data_sources.json              # API data sources
└── env_config.py
```

---

## 🔗 Key Files to Check

1. **Agent**: `src/rag/agents/langgraph_agent/langgraph_rag_agent.py`
2. **Config**: `src/rag/config/llm_config.json`
3. **Database**: `src/database/data/incident_iq.db`
4. **Logs**: `logs/` (session visualizations)
5. **Memory**: SQLite `agent_memory` table

---

## 🎓 Learning Resources

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangChain Docs](https://python.langchain.com/)
- [Design Docs](./design_docs/)
  - `LANGGRAPH_COMPILATION_GUIDE.md` - Detailed guide
  - `AGENT_MEMORY_SYSTEM.md` - Memory storage
  - `RAG_AGENTIC_WORKFLOW_COMPLETE.md` - Full architecture

---

## 💡 Pro Tips

1. **Monitor cache hit rate**:
   ```python
   cache = get_agent_memory_cache()
   print(cache.get_stats()['hit_rate_percent'])
   ```

2. **Profile performance**:
   ```python
   import time
   start = time.time()
   result = agent.ask_question("Q?", response_mode="verbose")
   print(f"Took {time.time()-start:.2f}s")
   print(f"Execution: {result['execution_time_ms']}ms")
   ```

3. **Debug graphs**:
   ```python
   print(agent.ingestion_graph.get_graph().draw_ascii())
   ```

4. **Check memory stats**:
   ```python
   mem_model = AgentMemoryModel()
   stats = mem_model.get_memory_stats("langgraph_agent")
   print(f"Total memories: {stats['total_memories']}")
   ```

