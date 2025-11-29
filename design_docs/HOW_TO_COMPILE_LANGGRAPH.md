# How to Compile LangGraph Agent - Summary

## 🎯 Quick Answer

The LangGraph agent **compiles automatically** when you initialize it. Here's how:

```python
from src.rag.agents.langgraph_agent import LangGraphRAGAgent

# This single line compiles all three graphs
agent = LangGraphRAGAgent()

# Now you can use it
answer = agent.ask_question("Your question?")
```

---

## 📦 What Gets Compiled

When you initialize `LangGraphRAGAgent()`, three workflow graphs are built:

### 1. **Ingestion Graph** (6 stages)
```
convert_markdown → classify_document → extract_metadata → 
chunk_document → save_vectordb → update_tracking
```
- Converts documents to markdown
- Classifies intent and department
- Extracts semantic metadata
- Splits into semantic chunks
- Generates embeddings
- Logs audit trail

### 2. **Retrieval Graph** (7 stages)
```
retrieve_context → rerank_context → check_optimization → 
optimize_context → answer_question → validate_guardrails → traceability
```
- Retrieves relevant documents
- Reranks by relevance
- Decides if optimization needed (RL agent)
- Optimizes if needed
- Generates answer
- Validates with guardrails
- Logs query

### 3. **Optimization Graph** (2 stages)
```
optimize → apply_config
```
- Analyzes performance
- Applies configuration updates

---

## 🚀 Complete Compilation Process (5 minutes)

### Step 1: Install Dependencies (1 min)
```bash
cd e:\epoch_explorers
pip install -r requirements.txt
```

**Installs:**
- langgraph, langchain, langchain-core
- chromadb (vector database)
- docling (document converter)
- pydantic, numpy, pandas

### Step 2: Create Config (1 min)
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

**Why needed?** LangGraph agent reads this to initialize LLM and embedding services.

### Step 3: Setup Database (2 min)
```bash
python scripts/setup_db.py
```

**Creates:**
- `incident_iq.db` - Main database
- `agent_memory` table - Agent memories
- `rag_history_and_optimization` table - Query logs
- Indexes for fast queries

### Step 4: Compile Agent (1 min)
```bash
python -c "
from src.rag.agents.langgraph_agent import LangGraphRAGAgent
agent = LangGraphRAGAgent()
print('✓ LangGraph agent compiled successfully!')
"
```

---

## ✅ Verification

### Option 1: Run Quick Test
```bash
python scripts/test_langgraph_compilation.py
```

**Tests:**
- [x] All imports resolve
- [x] Config loads correctly
- [x] Agent initializes
- [x] Graphs compile
- [x] Ingestion workflow works
- [x] Retrieval workflow works
- [x] Memory system works
- [x] Response modes work

Expected output: `✅ LangGraph Agent compilation successful!`

### Option 2: Run Demo
```bash
python scripts/demo_langgraph_compilation.py
```

**Shows:**
- [x] Initialize agent
- [x] Ingest document
- [x] Ask question
- [x] Store memory
- [x] Retrieve memory
- [x] Test 3 response modes

---

## 💡 What Happens During Initialization

```python
from src.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()  # Initialization starts here
```

**Sequence:**

1. **Load LLM Config** (from `src/rag/config/llm_config.json`)
   - Reads provider settings (Ollama, Azure, etc.)
   - Validates required fields
   - ⚠️ **FAILS if file not found** - No fallback!

2. **Initialize Services**
   - `LLMService` - For embedding and text generation
   - `VectorDBService` - For semantic search (ChromaDB)
   - `RLHealingAgent` - For optimization decisions

3. **Compile Ingestion Graph**
   - Creates StateGraph with 6 nodes
   - Adds edges: convert → classify → extract → chunk → save → track
   - Compiles using `.compile()`
   - Result: Executable ingestion workflow

4. **Compile Retrieval Graph**
   - Creates StateGraph with 7 nodes
   - Adds conditional edges (optimize if needed)
   - Compiles using `.compile()`
   - Result: Executable retrieval workflow

5. **Compile Optimization Graph**
   - Creates StateGraph with 2 nodes
   - Adds edges: optimize → apply
   - Compiles using `.compile()`
   - Result: Executable optimization workflow

6. **Initialize Custom Guardrails**
   - Pattern-based safety checks
   - No external dependencies

**Total time:** 2-3 seconds

---

## 🔧 Using Compiled Agent

### Pattern 1: Ingest Documents
```python
result = agent.ingest_document(
    text="Your document content",
    doc_id="my_doc_20250129_001"
)
# Returns: {success, doc_id, chunks_count, chunks_saved, errors}
```

### Pattern 2: Ask Questions
```python
# User-friendly
response = agent.ask_question("What's in the doc?", response_mode="concise")
print(response['answer'])  # Just the answer

# System integration
response = agent.ask_question("What's in the doc?", response_mode="internal")
print(response['quality_score'])  # Answer + metrics

# Full debug
response = agent.ask_question("What's in the doc?", response_mode="verbose")
print(response['execution_time_ms'])  # Everything
```

### Pattern 3: Store/Retrieve Memory
```python
from src.rag.tools.ingestion_tools import (
    record_agent_memory_tool,
    retrieve_agent_memory_tool
)

# Store memory
record_agent_memory_tool.invoke({
    "agent_name": "langgraph_agent",
    "memory_type": "decision",
    "memory_key": "my_key",
    "memory_value": json.dumps({"data": "value"}),
    "importance_score": 0.9,
    "ttl_hours": 72
})

# Retrieve memory
retrieve_agent_memory_tool.invoke({
    "agent_name": "langgraph_agent",
    "memory_type": "decision"
})
```

---

## 🐛 Troubleshooting Compilation Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `FileNotFoundError: llm_config.json` | Config missing | Create file (see Step 2 above) |
| `ModuleNotFoundError: langgraph` | langgraph not installed | `pip install langgraph` |
| `Connection refused` | LLM not running | `ollama serve` in another terminal |
| `AgentMemoryModel not found` | Migrations not run | `python scripts/setup_db.py` |
| `ChromaDB error` | Dir doesn't exist | `mkdir -p src/database/data/chroma_db` |

---

## 📊 Compilation Performance

| Step | Time | Notes |
|------|------|-------|
| Import modules | ~1s | First-time cached after |
| Load config | ~100ms | JSON parsing |
| Init LLM service | ~500ms | Loads embedding model |
| Init VectorDB | ~200ms | Connects to ChromaDB |
| Compile ingestion graph | ~50ms | StateGraph compilation |
| Compile retrieval graph | ~50ms | StateGraph compilation |
| Compile optimization graph | ~30ms | StateGraph compilation |
| **Total** | **~2-3s** | Ready to use |

---

## 📚 Related Documentation

1. **LANGGRAPH_COMPILATION_GUIDE.md** - Detailed comprehensive guide
2. **LANGGRAPH_QUICK_REFERENCE.md** - Quick usage examples
3. **RAG_AGENTIC_WORKFLOW_COMPLETE.md** - Full architecture details
4. **AGENT_MEMORY_SYSTEM.md** - Memory storage deep dive

---

## ✨ Key Points

✅ **Compilation is automatic** - Just initialize the agent
✅ **No fallback configs** - Config must exist, fails if missing
✅ **Three workflows** - Ingestion, retrieval, optimization
✅ **Fully typed** - Type hints throughout for IDE support
✅ **Production ready** - Error handling, logging, traceability
✅ **Memory enabled** - Cache + SQLite for agent learning
✅ **Three output modes** - Concise, internal, verbose
✅ **Testable** - Includes test suite and demo scripts

---

## 🎓 Learning Path

1. ✅ Read this document (compilation overview)
2. ✅ Read LANGGRAPH_QUICK_REFERENCE.md (usage examples)
3. ✅ Run `demo_langgraph_compilation.py` (see it work)
4. ✅ Run your own queries
5. ✅ Read LANGGRAPH_COMPILATION_GUIDE.md (deep dive)
6. ✅ Explore source code

---

## 🎯 Next Steps

1. Complete the compilation process (see "Complete Compilation Process" above)
2. Verify with `python scripts/test_langgraph_compilation.py`
3. Run demo with `python scripts/demo_langgraph_compilation.py`
4. Start using: `agent = LangGraphRAGAgent()`

You're now ready to build agentic RAG systems! 🚀
