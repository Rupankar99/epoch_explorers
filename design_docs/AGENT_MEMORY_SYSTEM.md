# Agent Memory Storage Implementation

## Overview

Agent memory storage provides **self-reflection and learning capabilities** for the RAG system using a **hybrid approach**:

1. **In-Memory Cache (LRU + TTL)**: Fast access during active sessions
2. **SQLite Database**: Persistent storage for learning across sessions

---

## Architecture

### Component 1: AgentMemoryModel (SQLite)

**Location**: `src/database/models/agent_memory_model.py`

**Purpose**: Persistent storage for agent memories in SQLite

**Table Schema**:
```sql
CREATE TABLE agent_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,                    -- Agent identifier
    memory_type TEXT CHECK(...IN ('context', 'log', 'decision', 'performance')),
    memory_key TEXT NOT NULL,                  -- Unique key for memory
    content TEXT NOT NULL,                     -- JSON content
    importance_score REAL DEFAULT 0.5,         -- 0-1 (higher = keep longer)
    access_count INTEGER DEFAULT 0,            -- Track usage frequency
    created_at TEXT NOT NULL,                  -- Timestamp
    updated_at TEXT NOT NULL,                  -- Last update
    expires_at TEXT,                           -- TTL expiration (optional)
    UNIQUE(agent_id, memory_type, memory_key)
);
```

**Indexes**:
- `idx_agent_memory_agent_id`: Fast lookup by agent
- `idx_agent_memory_type`: Fast lookup by type
- `idx_agent_memory_expires`: Fast expiration cleanup

**Key Methods**:

```python
# Record new or update existing memory
memory_id = mem_model.record_memory(
    agent_id="langgraph_agent",
    memory_type="decision",
    memory_key="healing_strategy_re_embed",
    content=json.dumps({"strategy": "RE_EMBED", "success_rate": 0.85}),
    importance_score=0.9,
    ttl_hours=24  # Keep for 24 hours
)

# Retrieve memories
memories = mem_model.retrieve_memory(
    agent_id="langgraph_agent",
    memory_type="decision",
    limit=10
)

# Get statistics
stats = mem_model.get_memory_stats("langgraph_agent")
# Returns: {'total_memories': 42, 'by_type': {...}, 'avg_importance': 0.75, ...}

# Cleanup expired
deleted = mem_model.cleanup_expired_memories()

# Delete specific memory
mem_model.delete_memory(agent_id, memory_type, memory_key)

# Clear all memories for agent
count = mem_model.clear_agent_memories(agent_id)
```

---

### Component 2: AgentMemoryCache (In-Memory)

**Location**: `src/database/cache/agent_memory_cache.py`

**Purpose**: Fast, thread-safe LRU cache with TTL support

**Features**:
- **LRU Eviction**: Oldest entries removed when cache fills
- **TTL Support**: Auto-expire entries after timeout
- **Thread-Safe**: RLock for concurrent access from multiple agents
- **Hit Rate Tracking**: Monitor cache efficiency

**Key Methods**:

```python
from src.database.cache import get_agent_memory_cache

cache = get_agent_memory_cache(max_size=1000, ttl_seconds=3600)

# Write to cache (fast)
cache.put(
    agent_id="langgraph_agent",
    memory_type="decision",
    memory_key="healing_strategy_re_embed",
    data={"strategy": "RE_EMBED", "success_rate": 0.85},
    ttl_seconds=3600  # 1 hour
)

# Read from cache (super fast if hit)
memory = cache.get(
    agent_id="langgraph_agent",
    memory_type="decision",
    memory_key="healing_strategy_re_embed"
)

# Cache statistics
stats = cache.get_stats()
# Returns: {'size': 42, 'hits': 1000, 'misses': 150, 'hit_rate_percent': 87.0}

# Cleanup expired entries
expired_count = cache.cleanup_expired()

# Remove specific entry
cache.remove(agent_id, memory_type, memory_key)

# Clear all entries for agent
count = cache.clear_agent(agent_id)
```

---

## Usage Patterns

### Pattern 1: Record Memory During Execution

```python
# In langgraph_rag_agent.py - optimize_context_node

if state.get("should_optimize") and state.get("rl_action"):
    # Record healing action as memory
    result = record_agent_memory_tool(
        agent_name="langgraph_agent",
        memory_type="decision",
        memory_key=f"healing_action_{state['rl_action'].lower()}",
        memory_value=json.dumps({
            "action": state["rl_action"],
            "reason": state["optimization_reason"],
            "before_quality": state["retrieval_quality"],
            "expected_improvement": 0.15,
            "timestamp": time.time()
        }),
        importance_score=0.9,
        ttl_hours=72  # Keep for 3 days
    )
    print(f"[✓] Healing memory recorded: {result}")
```

### Pattern 2: Query Memory for Learning

```python
# At agent startup or decision point

memories = retrieve_agent_memory_tool(
    agent_name="langgraph_agent",
    memory_type="decision",
    limit=5
)

result_dict = json.loads(memories)
if result_dict["success"]:
    for mem in result_dict["memories"]:
        print(f"Strategy: {mem['memory_key']}")
        print(f"Importance: {mem['importance_score']}")
        print(f"Used {mem['access_count']} times")
```

### Pattern 3: Context Memory for Session State

```python
# Store query patterns for semantic understanding

record_agent_memory_tool(
    agent_name="langgraph_agent",
    memory_type="context",
    memory_key="query_pattern_budget_analysis",
    memory_value=json.dumps({
        "pattern": "budget or financial analysis",
        "department": "finance",
        "frequency": 15,
        "last_seen": time.time()
    }),
    importance_score=0.7,
    ttl_hours=168  # Keep for 1 week
)
```

### Pattern 4: Performance Metrics Recording

```python
# Log performance data for optimization

record_agent_memory_tool(
    agent_name="langgraph_agent",
    memory_type="performance",
    memory_key="chunk_size_512_quality",
    memory_value=json.dumps({
        "chunk_size": 512,
        "avg_quality_score": 0.82,
        "avg_cost_tokens": 1500,
        "avg_latency_ms": 1200,
        "total_trials": 42
    }),
    importance_score=0.8,
    ttl_hours=None  # Keep forever
)
```

---

## Memory Types

### 1. **Context** (`memory_type="context"`)
**Purpose**: Contextual information about users, documents, patterns

**Examples**:
- Query patterns by department
- User role profiles
- Document summaries and keywords
- Semantic understanding of domains

**TTL**: 1-4 weeks (relevant for mid-term patterns)

```json
{
  "pattern": "budget or financial analysis",
  "department": "finance",
  "frequency": 15,
  "required_roles": ["analyst", "manager"],
  "last_seen": 1706456789.123
}
```

---

### 2. **Log** (`memory_type="log"`)
**Purpose**: Execution logs and status reports

**Examples**:
- Ingestion status reports
- Retrieval attempts and failures
- Healing action attempts
- Error logs with context

**TTL**: 3-7 days (transient diagnostic info)

```json
{
  "event": "ingestion_completed",
  "doc_id": "file_budget_20250129_143022",
  "chunks_created": 42,
  "chunks_saved": 40,
  "errors": [],
  "duration_ms": 2300
}
```

---

### 3. **Decision** (`memory_type="decision"`)
**Purpose**: Strategic decisions that should influence future behavior

**Examples**:
- Which healing strategies worked best
- Parameter tuning decisions
- Successful vs failed approaches
- Trade-off evaluations

**TTL**: 30-90 days (learning data)

```json
{
  "strategy": "RE_EMBED",
  "success_rate": 0.85,
  "avg_improvement": 0.18,
  "cost_increase_percent": 12,
  "recommendation": "Use when quality < 0.5",
  "trials": 24
}
```

---

### 4. **Performance** (`memory_type="performance"`)
**Purpose**: Performance metrics for system optimization

**Examples**:
- Quality scores by configuration
- Cost analysis across chunk sizes
- Latency trends
- Resource utilization patterns

**TTL**: None / Forever (historical baseline)

```json
{
  "config": "chunk_size_512",
  "avg_quality_score": 0.82,
  "avg_cost_tokens": 1500,
  "avg_latency_ms": 1200,
  "total_trials": 42,
  "trend": "stable"
}
```

---

## Tools API

### Tool 1: record_agent_memory_tool

**Purpose**: Write memory to both cache and database

```python
@tool
def record_agent_memory_tool(
    agent_name: str,              # "langgraph_agent"
    memory_key: str,              # "healing_strategy_re_embed"
    memory_value: str,            # JSON string
    memory_type: str = "context", # "context"|"log"|"decision"|"performance"
    importance_score: float = 0.8,# 0-1 (higher = priority)
    ttl_hours: int = None         # None = forever
) -> str:  # JSON response
```

**Example**:
```python
result = record_agent_memory_tool.invoke({
    "agent_name": "langgraph_agent",
    "memory_type": "decision",
    "memory_key": "healing_action_re_embed",
    "memory_value": json.dumps({"strategy": "RE_EMBED", "success": True}),
    "importance_score": 0.9,
    "ttl_hours": 72
})
# {"success": true, "memory_id": 42, "storage": "hybrid (cache + sqlite)", ...}
```

---

### Tool 2: retrieve_agent_memory_tool

**Purpose**: Query memories (cache-first, then database)

```python
@tool
def retrieve_agent_memory_tool(
    agent_name: str,              # "langgraph_agent"
    memory_type: str = None,      # None = all types
    memory_key: str = None,       # None = all keys
    limit: int = 10               # Max results
) -> str:  # JSON response
```

**Example**:
```python
result = retrieve_agent_memory_tool.invoke({
    "agent_name": "langgraph_agent",
    "memory_type": "decision",
    "limit": 5
})
# {
#   "success": true,
#   "memories": [
#     {"memory_id": 42, "memory_key": "...", "content": {...}, ...},
#     ...
#   ],
#   "agent_stats": {"total_memories": 42, "by_type": {...}, ...},
#   "cache_stats": {"hits": 1000, "misses": 150, "hit_rate_percent": 87.0}
# }
```

---

### Tool 3: clear_agent_memory_tool

**Purpose**: Clear all memories for an agent (both cache and DB)

```python
@tool
def clear_agent_memory_tool(agent_name: str) -> str:  # JSON response
```

**Example**:
```python
result = clear_agent_memory_tool.invoke({
    "agent_name": "langgraph_agent"
})
# {
#   "success": true,
#   "cache_entries_cleared": 42,
#   "db_entries_cleared": 85,
#   "total_cleared": 127
# }
```

---

## Integration with LangGraph Agent

### In `langgraph_rag_agent.py`:

```python
# Add to imports
from ...tools.ingestion_tools import (
    record_agent_memory_tool,
    retrieve_agent_memory_tool,
    clear_agent_memory_tool
)

# In optimize_context_node
def optimize_context_node(state):
    try:
        # ... existing optimization code ...
        
        # NEW: Log healing action as memory
        if state.get("rl_action") and state.get("rl_action") != "SKIP":
            mem_result = record_agent_memory_tool(
                agent_name="langgraph_agent",
                memory_type="decision",
                memory_key=f"healing_{state['rl_action'].lower()}",
                memory_value=json.dumps({
                    "action": state["rl_action"],
                    "before_quality": state.get("retrieval_quality", 0.0),
                    "reason": state.get("optimization_reason", ""),
                    "timestamp": time.time()
                }),
                importance_score=0.9,
                ttl_hours=72
            )
            print(f"[✓] Memory recorded: {mem_result}")
    
    except Exception as e:
        # ... error handling ...

# In answer_question_node
def answer_question_node(state):
    try:
        # NEW: Check prior successful query patterns
        prior_queries = retrieve_agent_memory_tool(
            agent_name="langgraph_agent",
            memory_type="context",
            memory_key=None,
            limit=3
        )
        
        query_dict = json.loads(prior_queries)
        if query_dict["success"]:
            print(f"[ℹ] Found {len(query_dict['memories'])} prior patterns")
        
        # ... rest of answer generation ...
```

---

## Performance Characteristics

### Cache Performance
- **Hit**: ~0.1ms (in-memory lookup)
- **Miss**: ~1-5ms (SQLite lookup)
- **TTL Cleanup**: Automatic on read
- **Thread Safety**: Full RLock protection

### Database Performance
- **Insert/Update**: ~5-10ms (indexed)
- **Retrieve**: ~2-8ms (indexed by agent_id + type)
- **Cleanup**: ~20-50ms (batch delete)
- **UNIQUE Constraint**: Prevents duplicates

### Typical Cache Hit Rate
- **Session Start**: 0% (cold)
- **After 10 queries**: 60-70%
- **Steady State**: 80-90% (depends on TTL)

---

## Cleanup & Maintenance

### Automatic Cleanup
```python
# On agent startup or periodically
mem_model = AgentMemoryModel()
deleted = mem_model.cleanup_expired_memories()
print(f"Cleaned up {deleted} expired memories")

# Also automatic in cache
cache = get_agent_memory_cache()
cache.cleanup_expired()
```

### Manual Cleanup
```python
# Clear specific agent
mem_model.clear_agent_memories("langgraph_agent")

# Clear specific memory
mem_model.delete_memory("langgraph_agent", "decision", "old_key")
```

---

## Monitoring & Analytics

### Cache Health
```python
cache = get_agent_memory_cache()
stats = cache.get_stats()
print(f"Hit Rate: {stats['hit_rate_percent']}%")
print(f"Memory Usage: {stats['size']}/{stats['max_size']}")
```

### Agent Memory Statistics
```python
mem_model = AgentMemoryModel()
stats = mem_model.get_memory_stats("langgraph_agent")
print(f"Total Memories: {stats['total_memories']}")
print(f"By Type: {stats['by_type']}")
print(f"Avg Importance: {stats['avg_importance']}")
print(f"Most Accessed: {stats['most_accessed']}")
```

---

## Configuration

### Environment Variables
```dotenv
# In .env (optional, uses defaults if not set)
AGENT_MEMORY_CACHE_SIZE=1000
AGENT_MEMORY_TTL_SECONDS=3600
AGENT_MEMORY_DB_PATH="src/database/data/incident_iq.db"
```

### Defaults
- Cache max size: 1000 entries
- Default TTL: 3600 seconds (1 hour)
- Database: incident_iq.db (shared with RAG data)

---

## Migration

### Create Table
```bash
# Run migration 012
python scripts/setup_db.py  # Automatically runs all migrations

# Or manually
from src.database.migrations.migrate import migrate_012
migrate_012(conn)
```

### Verify Table
```sql
.schema agent_memory
SELECT COUNT(*) FROM agent_memory;
```

---

## Troubleshooting

### Memory Not Persisting
```python
# Check SQLite table exists
mem_model = AgentMemoryModel()
result = mem_model.retrieve_memory("langgraph_agent", limit=1)
print(result)  # If empty, migration may not have run
```

### Cache Not Working
```python
# Check cache stats
cache = get_agent_memory_cache()
stats = cache.get_stats()
print(f"Size: {stats['size']}, Hits: {stats['hits']}, Misses: {stats['misses']}")
# If hit_rate is 0%, cache may not be in use
```

### Expired Entries Not Cleaning
```python
# Manual cleanup
mem_model = AgentMemoryModel()
cleaned = mem_model.cleanup_expired_memories()
print(f"Cleaned {cleaned} expired entries")
```

---

## Future Enhancements

1. **Semantic Search**: Find similar memories by embedding
2. **Memory Summarization**: Compress old memories while keeping patterns
3. **Cross-Agent Learning**: Share useful memories between agents
4. **Memory Replay**: Re-execute past decisions for feedback learning
5. **Importance Decay**: Lower importance over time (forgetting curve)
6. **Neo4j Integration**: Store as MEMORY nodes with relationships
7. **Analytics Dashboard**: Visualize memory usage patterns

---

## Summary

The **hybrid memory system** provides:

✅ **Fast access** via in-memory cache  
✅ **Persistence** via SQLite database  
✅ **Self-reflection** through memory retrieval  
✅ **Learning** from past decisions  
✅ **Debugging** via comprehensive logging  
✅ **Cleanup** via TTL and expiration  
✅ **Monitoring** via statistics and analytics  
