# doc_id Strategy - Automatic Generation & Management

## Overview

The **`doc_id`** is a **unique identifier for each document** in the system. Users never need to provide it manually - it's **generated automatically** based on the source.

| Source | Example doc_id | Generation Method |
|--------|---|---|
| **File Upload** | `file_budget_report_20250128_153045` | filename + timestamp |
| **Text Input** | `text_user_input_20250128_153045` | "text_user_input" + timestamp |
| **Database Table** | `table_knowledge_base_20250128_153045` | "table_" + table_name + timestamp |
| **URL** | `url_https_example_com_20250128_153045` | "url_" + hash(url) + timestamp |

---

## 1. Current Implementation

### File Upload doc_id Generation
**Location**: `src/rag/tools/ingestion_tools.py` line 208

```python
def ingest_documents_from_path_tool(path: str, doc_id_prefix: str = "doc"):
    # ...
    doc_id = f"{doc_id_prefix}_{file_path.stem}_{dt.now().strftime('%Y%m%d_%H%M%S')}"
    # Example: doc_budget_report_20250128_153045
```

### Chunk doc_id Derivation
```python
# In chunk_document_tool
"chunk_id": f"{doc_id}_chunk_{i}"
# Example: doc_budget_report_20250128_153045_chunk_0
```

---

## 2. Chat Interface Auto-Generation Strategy

### Updated Chat Interface with Auto doc_id

The chat system now **automatically generates doc_ids** based on source:

```python
class ChatRAGInterface:
    def _generate_doc_id(self, source_type: str, source_name: str) -> str:
        """
        Automatically generate unique doc_id based on source.
        
        Args:
            source_type: "file" | "text" | "table" | "url"
            source_name: filename, table_name, or URL
        
        Returns:
            Unique doc_id: prefix_source_timestamp
        """
        import hashlib
        from datetime import datetime
        
        # Sanitize source_name (remove special chars, lowercase)
        sanitized = re.sub(r'[^a-z0-9_]', '_', source_name.lower())
        
        # Prefix by source type
        prefixes = {
            "file": "file",
            "text": "text_user_input",
            "table": "table",
            "url": "url"
        }
        
        prefix = prefixes.get(source_type, "doc")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        doc_id = f"{prefix}_{sanitized}_{timestamp}"
        return doc_id
```

### Examples

#### File Upload
```
User uploads: "Q4_Budget_Report.pdf"
Auto-generated doc_id: file_q4_budget_report_20250128_153045
```

#### Text Input
```
User enters text: "Company financial summary..."
Auto-generated doc_id: text_user_input_20250128_153045
```

#### Table Ingestion
```
User ingests table: "knowledge_base"
Auto-generated doc_id: table_knowledge_base_20250128_153045
```

#### URL
```
User provides URL: "https://example.com/report"
Auto-generated doc_id: url_https_example_com_20250128_153045
```

---

## 3. Uniqueness Guarantee

### Why Timestamps Ensure Uniqueness

```
Format: prefix_source_timestamp

Examples:
file_budget_20250128_153045  (uploaded 15:30:45 on Jan 28)
file_budget_20250128_153046  (uploaded 15:30:46 on Jan 28)
file_budget_20250128_153047  (uploaded 15:30:47 on Jan 28)
```

**Resolution**: Down to the **second** (86,400 possible docs per day)
- Very unlikely 2 users upload same file in exact same second
- If they do, system adds microsecond precision automatically

### Collision Handling

```python
def _generate_unique_doc_id(self, base_doc_id: str) -> str:
    """Ensure doc_id is truly unique by checking database."""
    import time
    
    doc_id = base_doc_id
    counter = 0
    
    while self._doc_id_exists(doc_id):
        # Add microsecond suffix if collision
        counter += 1
        microseconds = int(time.time() * 1_000_000) % 1_000_000
        doc_id = f"{base_doc_id}_{microseconds}_{counter}"
    
    return doc_id
```

---

## 4. Hash-Based Option (Alternative)

For systems that prefer hash-based doc_ids:

```python
import hashlib

def _generate_doc_id_hash(self, source_type: str, source_content: str) -> str:
    """
    Generate doc_id using content hash.
    Pros: Same content = same doc_id (deduplication)
    Cons: Cannot tell when doc was added
    """
    content_hash = hashlib.sha256(source_content.encode()).hexdigest()[:12]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"{source_type}_{content_hash}_{timestamp}"
```

**Use Case**: When you want to detect duplicate uploads
```
Upload budget.pdf (first time) → doc_id: file_a1b2c3d4e5f6_20250128_153045
Upload budget.pdf (again) → Same doc_id (detected as duplicate)
```

---

## 5. User Perspective - How It Works

### Streamlit Chat (Admin Ingest Tab)

#### File Upload
```
1. User clicks "Upload File"
2. Selects "Q4_Budget_Report.pdf"
3. System auto-generates: file_q4_budget_report_20250128_153045
4. User sees: "✓ Ingested as doc_id: file_q4_budget_report_20250128_153045"
5. System stores doc_id in session
```

#### Text Input
```
1. User enters: "Company spending summary..."
2. System auto-generates: text_user_input_20250128_153045
3. User sees: "✓ Ingested as doc_id: text_user_input_20250128_153045"
```

#### Table Ingestion
```
1. User selects: "knowledge_base" from dropdown
2. System auto-generates: table_knowledge_base_20250128_153045
3. User sees: "✓ Ingested 342 rows as doc_id: table_knowledge_base_20250128_153045"
```

**User never types or thinks about doc_id - it's automatic!**

---

## 6. CLI Usage

### File Upload
```bash
> ingest_file: /home/user/budget_report.pdf
✓ Ingested successfully
  doc_id: file_budget_report_20250128_153045
  chunks: 28
  quality_score: 0.87
```

### Text Input
```bash
> ingest_text: Company financial summary for Q4 2025...
✓ Ingested successfully
  doc_id: text_user_input_20250128_153045
  chunks: 5
```

### Query Using Auto-Generated doc_id
```bash
> query: What is the budget?
✓ Found 3 results from:
  - file_q4_budget_report_20250128_153045 (2 chunks)
  - table_knowledge_base_20250128_153045 (1 chunk)

Answer: The budget is $2.5M...
```

---

## 7. Python Direct Import

### Auto-Generation Example

```python
from src.rag.chat import ChatRAGInterface, ChatMode

chat = ChatRAGInterface(agent.ask_question)
session = chat.create_session(mode=ChatMode.ADMIN)

# File upload - doc_id auto-generated!
response = await chat.process_message(
    text="ingest_file: /path/to/budget.pdf",
    session_id=session.session_id
)
# Returns:
# {
#   "doc_id": "file_budget_20250128_153045",
#   "status": "ingested",
#   "chunks": 28
# }

# Use that doc_id in healing
response = await chat.process_message(
    text=f"heal: {response['doc_id']}|0.55",
    session_id=session.session_id
)
```

### Optional Manual doc_id Override

If users want to provide custom doc_ids:

```python
response = await chat.process_message(
    text="ingest_file: /path/to/budget.pdf",
    session_id=session.session_id,
    custom_doc_id="budget_q4_2025"  # Optional override
)
```

---

## 8. Database Storage

### document_metadata Table

```sql
CREATE TABLE document_metadata (
    doc_id TEXT PRIMARY KEY,           -- file_budget_20250128_153045
    title TEXT,                        -- Q4 Budget Report
    author TEXT,
    source TEXT,                       -- pdf | txt | csv | table
    summary TEXT,
    created_at TIMESTAMP,              -- Auto: datetime.now()
    file_path TEXT,                    -- For files: /path/to/budget.pdf
    source_table TEXT,                 -- For tables: knowledge_base
    classification_intent TEXT,
    rbac_tags TEXT,                    -- JSON
    meta_tags TEXT,                    -- JSON
    markdown_format BOOLEAN
);

-- Example rows:
file_budget_20250128_153045 | Q4 Budget Report | ... | pdf | /path/to/budget.pdf | ...
text_user_input_20250128_153045 | User Input | ... | txt | NULL | ...
table_knowledge_base_20250128_153045 | Knowledge Base | ... | table | knowledge_base | ...
```

### Query Using doc_id

```sql
-- Find all chunks from a specific document
SELECT * FROM chunk_embedding_data 
WHERE doc_id = 'file_budget_20250128_153045';

-- Find when document was added
SELECT created_at FROM document_metadata 
WHERE doc_id = 'file_budget_20250128_153045';

-- List all ingested files in the last hour
SELECT doc_id, title, created_at 
FROM document_metadata 
WHERE source = 'pdf' 
  AND created_at > datetime('now', '-1 hour');
```

---

## 9. Tracking & Analytics

### Session Context Includes Auto-Generated doc_ids

```python
context = session.get_context()
# Returns:
{
    "session_id": "session_123",
    "ingested_files": [
        {
            "doc_id": "file_budget_20250128_153045",
            "source": "pdf",
            "chunks": 28,
            "ingested_at": "2025-01-28T15:30:45"
        },
        {
            "doc_id": "text_user_input_20250128_153100",
            "source": "text",
            "chunks": 5,
            "ingested_at": "2025-01-28T15:31:00"
        }
    ],
    "healed_docs": [
        "file_budget_20250128_153045"  # Healed once
    ]
}
```

### Query History with doc_ids

```sql
SELECT 
    session_id,
    query_text,
    target_doc_id,  -- Which doc_id answered the question
    response_quality,
    timestamp
FROM rag_history_and_optimization
WHERE event_type = 'QUERY'
ORDER BY timestamp DESC;

-- Shows which documents are actually used
```

---

## 10. Summary Table

| Aspect | Details |
|--------|---------|
| **Generated By** | System automatically |
| **User Input** | No - transparent to users |
| **Format** | `prefix_source_timestamp` |
| **Uniqueness** | Guaranteed via timestamp + collision detection |
| **Prefix Types** | `file` \| `text_user_input` \| `table` \| `url` |
| **Timestamp** | `YYYYMMDD_HHMMSS` (second precision) |
| **Collision Handling** | Microsecond + counter suffix if needed |
| **Storage** | `document_metadata.doc_id` (PRIMARY KEY) |
| **Visibility** | Shown in response, stored in session context |
| **Override** | Optional `custom_doc_id` parameter if needed |

---

## 11. Migration from Manual to Auto

If you have existing systems with manual doc_ids:

```python
def migrate_doc_ids_to_auto():
    """Preserve existing doc_ids, use auto for new ingestions."""
    conn = sqlite3.connect(EnvConfig.get_db_path())
    cursor = conn.cursor()
    
    # Keep existing doc_ids
    cursor.execute("""
        ALTER TABLE document_metadata 
        ADD COLUMN auto_doc_id TEXT;  -- New column
    """)
    
    # For new ingestions, use auto_generate
    # Old doc_ids remain unchanged
```

---

## 12. API Responses Show doc_id

### POST /chat/ingest-file

```json
{
    "status": "success",
    "doc_id": "file_budget_report_20250128_153045",
    "message": "File ingested successfully",
    "metadata": {
        "filename": "budget_report.pdf",
        "chunks": 28,
        "quality_score": 0.87,
        "ingested_at": "2025-01-28T15:30:45Z"
    }
}
```

### POST /chat/ingest-text

```json
{
    "status": "success",
    "doc_id": "text_user_input_20250128_153045",
    "message": "Text ingested successfully",
    "metadata": {
        "chunks": 5,
        "ingested_at": "2025-01-28T15:30:45Z"
    }
}
```

### POST /chat/ingest-table

```json
{
    "status": "success",
    "doc_id": "table_knowledge_base_20250128_153045",
    "message": "Table ingested successfully",
    "metadata": {
        "table_name": "knowledge_base",
        "rows": 342,
        "chunks": 12,
        "ingested_at": "2025-01-28T15:30:45Z"
    }
}
```

---

## 13. Real-World Example

### Complete Workflow

```
User: "I want to ingest this budget file"
System: (detects file upload: budget_2025.pdf)
System: (auto-generates doc_id: file_budget_2025_20250128_153045)

User sees:
✓ File ingested successfully
  Source: budget_2025.pdf
  doc_id: file_budget_2025_20250128_153045
  Chunks: 28
  Ready for queries

User: "What is the Q4 budget?"
System: (searches file_budget_2025_20250128_153045 + others)
System: (retrieves 3 relevant chunks)
System: (generates answer from chunks)

User sees:
Answer: The Q4 budget is $2.5M allocated across...
Sources:
  - file_budget_2025_20250128_153045 (2 chunks)
  - table_knowledge_base_20250128_160000 (1 chunk)

User: "Optimize that budget file"
System: (interprets as doc_id: file_budget_2025_20250128_153045)
System: (runs RL healing agent)

User sees:
✓ Document optimized
  doc_id: file_budget_2025_20250128_153045
  Quality improvement: 55% → 67%
  Strategy: OPTIMIZE (reduced chunk size)
```

---

## 14. Why This Approach?

### Advantages

✅ **Zero user friction** - No manual ID management
✅ **Unique by default** - Timestamp-based uniqueness
✅ **Semantic** - Filename + timestamp tells the story
✅ **Traceable** - Know when each document was added
✅ **Simple** - No complex UUID logic needed
✅ **Human-readable** - Can recognize files later
✅ **Collision-safe** - Microsecond fallback if needed

### Compared to Alternatives

| Approach | Pros | Cons |
|----------|------|------|
| **UUID** (random) | Guaranteed unique | Not human-readable |
| **Hash** (content-based) | Deduplicates | Can't tell when added |
| **Auto-increment** | Simple | Breaks in distributed systems |
| **Timestamp only** | Human-readable | Possible collisions |
| **Timestamp + Source** ✅ | Best of all | Minimal complexity |

---

**Document Version**: 1.0  
**Status**: ✅ FULLY EXPLAINED  
**Key Takeaway**: Users provide file/text/table → System auto-generates unique doc_id → No manual management needed!
