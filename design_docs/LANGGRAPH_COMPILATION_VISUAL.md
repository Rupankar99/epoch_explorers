# LangGraph Agent Compilation - Visual Guide

## 📋 Timeline: Compilation in 5 Minutes

```
┌─────────────────────────────────────────────────────────────┐
│                  LANGGRAPH COMPILATION                      │
│                    (5-Minute Process)                       │
└─────────────────────────────────────────────────────────────┘

MINUTE 1️⃣: INSTALL
├─ Command: pip install -r requirements.txt
├─ Installs: langgraph, langchain, chromadb, docling
└─ Status: ✅ Done

MINUTE 2️⃣: CONFIG
├─ Create: src/rag/config/llm_config.json
├─ Content: LLM provider settings (Ollama/Azure/OpenAI)
└─ Status: ✅ Done

MINUTE 3️⃣: DATABASE
├─ Command: python scripts/setup_db.py
├─ Creates: agent_memory, rag_history tables
└─ Status: ✅ Done

MINUTE 4️⃣: COMPILE
├─ Command: python -c "from src.rag.agents.langgraph_agent import LangGraphRAGAgent; agent = LangGraphRAGAgent()"
├─ Action: Initializes all 3 graphs
└─ Status: ✅ Done

MINUTE 5️⃣: TEST
├─ Command: python scripts/test_langgraph_compilation.py
├─ Result: 7/7 tests pass
└─ Status: ✅ Ready to Use!
```

---

## 🏗️ Initialization Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              LangGraphRAGAgent.__init__()                   │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌─────────────┐ ┌────────────┐ ┌──────────────┐
    │   SERVICES  │ │  RL AGENT  │ │  GUARDRAILS  │
    └─────────────┘ └────────────┘ └──────────────┘
          │               │               │
    ┌─────┴─────┐         │               │
    ▼           ▼         ▼               ▼
┌────────┐ ┌──────────┐ ┌─────────┐ ┌──────────────┐
│LLMServ │ │VectorDB  │ │RLHealing│ │CustomGuardrails
└────────┘ └──────────┘ └─────────┘ └──────────────┘
    │           │            │            │
    └─────────────────────────┴────────────┘
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
    ┌──────────┬──────────┬──────────┐
    │Ingestion │Retrieval │Optimizat │
    │ Graph    │ Graph    │ Graph    │
    └──────────┴──────────┴──────────┘
        (StateGraph Compilation)
```

---

## 🔄 Ingestion Graph Compilation

```
┌─────────────────────────────────────────────────────────────┐
│            INGESTION WORKFLOW COMPILATION                   │
│                 (6 Nodes, 6 Edges)                          │
└─────────────────────────────────────────────────────────────┘

    START
      │
      ▼
    ┌─────────────────────────────────┐
    │ 1. CONVERT_MARKDOWN             │
    │    • Input: Raw document        │
    │    • Process: Normalize format  │
    │    • Output: Markdown text      │
    └─────────────────────────────────┘
      │
      ▼
    ┌─────────────────────────────────┐
    │ 2. CLASSIFY_DOCUMENT            │
    │    • Input: Markdown text       │
    │    • Process: Extract metadata  │
    │    • Output: Classification     │
    └─────────────────────────────────┘
      │
      ▼
    ┌─────────────────────────────────┐
    │ 3. EXTRACT_METADATA             │
    │    • Input: Document content    │
    │    • Process: LLM analysis      │
    │    • Output: Keywords, summary  │
    └─────────────────────────────────┘
      │
      ▼
    ┌─────────────────────────────────┐
    │ 4. CHUNK_DOCUMENT               │
    │    • Input: Normalized text     │
    │    • Process: Split semantic    │
    │    • Output: Chunk list         │
    └─────────────────────────────────┘
      │
      ▼
    ┌─────────────────────────────────┐
    │ 5. SAVE_VECTORDB                │
    │    • Input: Chunks              │
    │    • Process: Generate embed    │
    │    • Output: Stored in ChromaDB │
    └─────────────────────────────────┘
      │
      ▼
    ┌─────────────────────────────────┐
    │ 6. UPDATE_TRACKING              │
    │    • Input: Save result         │
    │    • Process: Audit trail       │
    │    • Output: Logging complete   │
    └─────────────────────────────────┘
      │
      ▼
     END
     
COMPILATION RESULT: StateGraph.compile()
├─ Nodes: 6 functional nodes
├─ Edges: 6 sequential edges
└─ Status: ✅ Executable workflow
```

---

## 🔄 Retrieval Graph Compilation

```
┌─────────────────────────────────────────────────────────────┐
│            RETRIEVAL WORKFLOW COMPILATION                   │
│            (7 Nodes, 8 Edges, 1 Conditional)               │
└─────────────────────────────────────────────────────────────┘

    START
      │
      ▼
    ┌──────────────────────────────────────┐
    │ 1. RETRIEVE_CONTEXT                  │
    │    • Input: User question            │
    │    • Process: Semantic search        │
    │    • Output: Top-5 documents         │
    └──────────────────────────────────────┘
      │
      ▼
    ┌──────────────────────────────────────┐
    │ 2. RERANK_CONTEXT                    │
    │    • Input: Retrieved docs           │
    │    • Process: LLM re-evaluate        │
    │    • Output: Sorted by relevance     │
    └──────────────────────────────────────┘
      │
      ▼
    ┌──────────────────────────────────────┐
    │ 3. CHECK_OPTIMIZATION                │
    │    • Input: Reranked context         │
    │    • Process: RL decision (heal?)    │
    │    • Output: should_optimize flag    │
    └──────────────────────────────────────┘
      │
      ├─ YES ──────────────────────┐
      │                           │
      ▼                           ▼
    ┌──────────────────┐    ┌──────────────────┐
    │ 4. OPTIMIZE      │    │ (Skip to answer) │
    │    • Cost/quality│    │                  │
    │    • Healing     │    │                  │
    └──────────────────┘    └──────────────────┘
      │                           │
      └─────────────┬─────────────┘
                    │
                    ▼
    ┌──────────────────────────────────────┐
    │ 5. ANSWER_QUESTION                   │
    │    • Input: Reranked context         │
    │    • Process: Generate answer        │
    │    • Output: LLM response            │
    └──────────────────────────────────────┘
      │
      ▼
    ┌──────────────────────────────────────┐
    │ 6. VALIDATE_GUARDRAILS               │
    │    • Input: Generated answer         │
    │    • Process: Safety checks          │
    │    • Output: Validated answer        │
    └──────────────────────────────────────┘
      │
      ▼
    ┌──────────────────────────────────────┐
    │ 7. TRACEABILITY                      │
    │    • Input: Answer + metadata        │
    │    • Process: Log to database        │
    │    • Output: Audit trail             │
    └──────────────────────────────────────┘
      │
      ▼
     END

COMPILATION RESULT: StateGraph.compile()
├─ Nodes: 7 functional nodes
├─ Edges: 8 sequential edges
├─ Conditional: 1 routing decision
└─ Status: ✅ Executable workflow
```

---

## 💾 State Flow During Compilation

```
┌──────────────────────────────────────────────────────────┐
│          STATE DICT (Flows through graphs)               │
└──────────────────────────────────────────────────────────┘

INGESTION:
{
  "doc_id": "doc_123",              ← Created by system
  "text": "raw content",            ← Input by user
  "markdown_text": "# Markdown",    ← Updated by convert_markdown
  "metadata": {...},                ← Updated by extract_metadata
  "chunks": [...],                  ← Updated by chunk_document
  "save_result": {...},             ← Updated by save_vectordb
  "tracking_result": {...},         ← Updated by update_tracking
  "errors": []                       ← Filled by any node
}

RETRIEVAL:
{
  "question": "What is...",         ← Input by user
  "session_id": "uuid",             ← Auto-generated
  "response_mode": "concise",       ← Input by user
  "context": {...},                 ← Updated by retrieve_context
  "reranked_context": {...},        ← Updated by rerank_context
  "retrieval_quality": 0.85,        ← Updated by check_optimization
  "should_optimize": false,         ← Set by check_optimization
  "answer": "answer text",          ← Updated by answer_question
  "guardrail_checks": {...},        ← Updated by validate_guardrails
  "traceability": {...},            ← Updated by traceability
  "errors": []                       ← Filled by any node
}
```

---

## 🔌 Service Integration

```
┌──────────────────────────────────────────────────────────┐
│        SERVICES INITIALIZED DURING COMPILATION           │
└──────────────────────────────────────────────────────────┘

1. LLMService
   │
   ├─ Reads: src/rag/config/llm_config.json
   ├─ Supports: Ollama, Azure, OpenAI, etc.
   └─ Provides: .generate_text() & .generate_embedding()
   
2. VectorDBService (ChromaDB)
   │
   ├─ Path: src/database/data/chroma_db
   ├─ Collections: rag_embeddings, agent_memory
   └─ Provides: .add() & .query()
   
3. RLHealingAgent
   │
   ├─ Database: src/database/data/incident_iq.db
   ├─ Learns: Which healing strategies work
   └─ Provides: .recommend_healing()
   
4. CustomGuardrails
   │
   ├─ Type: Pattern-based (no external deps)
   ├─ Checks: PII, hallucination, safety
   └─ Provides: .process_request()

These 4 services work together during compiled workflows.
```

---

## ⚙️ Compilation Dependency Tree

```
LangGraphRAGAgent.__init__()
│
├─ _init_services()
│  ├─ EnvConfig.get_rag_config_path()
│  ├─ EnvConfig.get_db_path()
│  ├─ EnvConfig.get_chroma_db_path()
│  ├─ LLMService(llm_config) ← Requires llm_config.json ✅
│  └─ VectorDBService() ← Requires chroma dir ✅
│
├─ _init_rl_agent()
│  └─ RLHealingAgent(db_path) ← Requires database ✅
│
├─ _build_ingestion_graph()
│  ├─ StateGraph(dict)
│  ├─ add_node(convert_markdown_node)
│  ├─ add_node(classify_document_node)
│  ├─ add_node(extract_metadata_node)
│  ├─ add_node(chunk_document_node)
│  ├─ add_node(save_vectordb_node)
│  ├─ add_node(update_tracking_node)
│  ├─ add_edge(...) [6 edges]
│  └─ compile() ✅
│
├─ _build_retrieval_graph()
│  ├─ StateGraph(dict)
│  ├─ add_node(...) [7 nodes]
│  ├─ add_edge(...) [8 edges]
│  ├─ add_conditional_edges(...) [1 conditional]
│  └─ compile() ✅
│
├─ _build_optimization_graph()
│  ├─ StateGraph(dict)
│  ├─ add_node(...) [2 nodes]
│  ├─ add_edge(...) [2 edges]
│  └─ compile() ✅
│
└─ CustomGuardrails() ✅

All dependencies → Agent ready to use! ✅
```

---

## 📊 Compilation Checklist

```
PREREQUISITES:
☐ Python 3.10+ installed
☐ pip working
☐ Network access (for pip install)

INSTALLATION (Minute 1):
☐ pip install -r requirements.txt
☐ Verify: python -c "import langgraph; print('✓')"

CONFIGURATION (Minute 2):
☐ mkdir -p src/rag/config
☐ Create llm_config.json
☐ Verify: cat src/rag/config/llm_config.json

DATABASE (Minute 3):
☐ python scripts/setup_db.py
☐ Verify: sqlite3 src/database/data/incident_iq.db ".tables"

COMPILATION (Minute 4):
☐ python -c "from src.rag.agents.langgraph_agent import LangGraphRAGAgent; agent = LangGraphRAGAgent()"
☐ No errors?

TESTING (Minute 5):
☐ python scripts/test_langgraph_compilation.py
☐ All 7 tests pass?

READY TO USE:
☐ Run your first query!
```

---

## 🎯 Key Compilation Facts

| Fact | Details |
|------|---------|
| **Compilation Trigger** | Agent initialization only (automatic) |
| **Compilation Time** | 2-3 seconds per initialization |
| **Number of Graphs** | 3 (ingestion, retrieval, optimization) |
| **Total Nodes** | 15 nodes across 3 graphs |
| **Total Edges** | 16 edges across 3 graphs |
| **Conditional Routing** | 1 (optimize or skip) |
| **State Type** | Python dict (flexible) |
| **Dependencies** | 4 services + config files |
| **Error Recovery** | Fail-fast (no fallbacks) |
| **Memory System** | LRU cache + SQLite persistence |

---

## ✨ Now You Know How to Compile LangGraph Agent!

Continue with:
1. **HOW_TO_COMPILE_LANGGRAPH.md** - Complete guide
2. **LANGGRAPH_QUICK_REFERENCE.md** - Usage examples
3. Run the test/demo scripts to see it in action

You're ready to build agentic RAG systems! 🚀
