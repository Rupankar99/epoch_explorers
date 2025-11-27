# Chat-Enhanced RAG - Quick Reference

## 🚀 Quick Start

### 1. Streamlit Web UI (Easiest)
```bash
cd src
streamlit run app.py
```
- **User Chat**: Simple query interface
- **Admin Chat**: Full ingestion & healing

### 2. FastAPI REST API
```bash
python -m uvicorn src.api:app --reload --port 8000
# Test: curl http://localhost:8000/chat/query -d '{"question":"..."}'
```

### 3. CLI Interactive
```bash
python -m src.rag.agents.langgraph_agent.langgraph_rag_agent --chat
```

### 4. Python Direct
```python
from src.rag.agents.langgraph_agent import LangGraphRAGAgent
from src.rag.chat import ChatRAGInterface, ChatMode

agent = LangGraphRAGAgent()
chat = ChatRAGInterface(agent.ask_question)
session = chat.create_session(mode=ChatMode.ADMIN)
# Now use: await chat.process_message(text, session_id)
```

---

## 📝 Command Syntax

### User Commands
```
query: what is budget?              # Ask question
rag_query: what are causes?         # RAG query
set_mode: concise                   # Change response style
help                                # Show help
```

### Admin Commands (User commands + these)
```
ingest_file: /path/to/file.pdf      # Upload file
ingest_text: document content...    # Paste text
ingest_table: table_name            # Ingest database table
heal: doc_001|0.55                  # Heal document
optimize: doc_001                   # Optimize
check_health: doc_001               # Check status
set_chat_mode: admin                # Switch mode
status                              # System status
clear                               # Clear session
```

---

## 🎯 Response Modes

| Mode | Best For | Format | Guardrails |
|------|----------|--------|-----------|
| **Concise** | End-users | 1-2 sentences | Hallucination + Security |
| **Verbose** | Engineers | Full details + metadata | None (debug data) |
| **Internal** | System integration | Structured JSON | Hallucination only |

---

## 🔗 API Endpoints

```bash
# Query
POST /chat/query
  {"question": "...?", "response_mode": "concise"}

# Ingest text
POST /chat/ingest
  {"text": "...", "doc_id": "optional_id"}

# Ingest file
POST /chat/ingest-file
  (multipart: file=@document.pdf)

# Ingest table
POST /chat/ingest-table?table_name=knowledge_base

# Heal document
POST /chat/heal
  {"doc_id": "doc_001", "current_quality": 0.55}

# Universal chat
POST /chat
  {"content": "query: what?", "response_mode": "concise"}

# System status
GET /chat/status
```

---

## 📊 Session Management

```python
# Create session
session = chat.create_session(
    user_id="emp_123",
    department="finance",
    role="analyst",
    mode=ChatMode.USER  # or ADMIN
)

# Get session
session = chat.get_session(session_id)

# Change response mode
session.set_response_mode(ResponseMode.VERBOSE)

# Get context
context = session.get_context()
# {session_id, user_id, department, role, mode, ...}
```

---

## ✅ Features Checklist

- ✅ Chat-first interface (all platforms)
- ✅ Dual modes (User + Admin)
- ✅ 3 response modes
- ✅ File uploads (PDF, DOCX, TXT, CSV, XLSX)
- ✅ Document ingestion via chat
- ✅ RL-based healing
- ✅ Session management
- ✅ Backward compatible (old code still works)
- ✅ No breaking changes

---

## 🔄 Access Methods

| Method | Status | Commands | File Upload | Healing |
|--------|--------|----------|------------|---------|
| Streamlit UI | ✅ Ready | All | ✅ Yes | ✅ Yes |
| FastAPI | ✅ Ready | All | ✅ Yes | ✅ Yes |
| CLI | ✅ Ready | All | ✅ Yes | ✅ Yes |
| Python | ✅ Ready | All | Via API | Via API |

---

## 🎓 Examples

### Query (All Platforms)
```
query: What is the main incident cause?
```

### Ingest File (Admin Mode)
```
ingest_file: /home/user/incidents.pdf
```

### Heal Document (Admin Mode)
```
heal: doc_incidents|0.55
```

### Change Response Style
```
set_mode: verbose
```

### Get Help
```
help
```

---

## 📈 Performance

| Operation | Overhead | Total Time |
|-----------|----------|-----------|
| Query parse | ~5ms | Query time (250-500ms) |
| File upload | ~50ms | Ingestion time (5-30s) |
| Mode switch | ~1ms | Instant |
| Session create | ~2ms | Instant |

---

## 🛡️ Security Features

✅ **User roles** - Department + role-based access
✅ **Response filtering** - Mode-based data filtering
✅ **Guardrails** - Hallucination + PII detection
✅ **Session isolation** - Per-user contexts
✅ **Admin restrictions** - Only admins can ingest/heal

---

## 📚 File Formats Supported

- ✅ PDF (via docling-parse)
- ✅ DOCX (via docling-parse)
- ✅ XLSX (via docling-parse)
- ✅ CSV (via docling-parse)
- ✅ TXT (plain text)
- ✅ JSON (structured data)
- ✅ Database tables (SQLite)

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Permission denied" | Not in admin mode - use `set_chat_mode: admin` |
| "File too large" | Max 100MB - adjust FileUploadHandler |
| "Module not found" | Install: `pip install -r requirements.txt` |
| "DB connection error" | Check `EnvConfig.get_db_path()` |
| "No answer found" | Try `set_mode: verbose` for more details |

---

## 📖 Full Documentation

See: `CHAT_ENHANCED_RAG_COMPLETE.md` for comprehensive guide
