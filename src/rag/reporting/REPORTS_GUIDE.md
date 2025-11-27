# RAG Analytics Reports - Complete Guide

## Overview

The RAG system uses **three main metadata tables** to track system performance and generate comprehensive analytics reports:

### Metadata Tables

1. **`document_metadata`** - Stores document-level information
2. **`chunk_embedding_data`** - Tracks individual chunk embeddings quality
3. **`rag_history_and_optimization`** - Complete audit trail of all RAG operations

---

## Reports Generated

### 1. **Document Ingestion Report**
**Purpose**: Track document ingestion pipeline health and document diversity

**Key Metrics**:
- Total documents ingested (last N days)
- Documents by RBAC namespace (access control)
- Average chunks per document
- Chunking strategy distribution (how documents are split)
- Document ingestion timeline
- Documents by source (CSV, PDF, Database, etc.)

**Use Cases**:
- Identify ingestion bottlenecks
- Monitor document distribution across namespaces
- Optimize chunking strategies by document type
- Track document source effectiveness

**SQL Foundation**: Queries from `document_metadata` table joined with chunk counts

---

### 2. **Query Performance Report**
**Purpose**: Analyze query execution quality and user behavior patterns

**Key Metrics**:
- Total queries executed
- Average query accuracy
- Average query latency (response time)
- Average cost per query
- Query frequency timeline (daily breakdown)
- Top 10 performing queries (most frequent)
- Performance by user/session
- Average reward signal (RL agent evaluation)

**Use Cases**:
- Identify slow queries for optimization
- Track user query patterns
- Measure system accuracy improvements over time
- Cost analysis per query
- Session-based user analytics

**SQL Foundation**: Queries from `rag_history_and_optimization` where `event_type='QUERY'`

---

### 3. **Healing & Optimization Report**
**Purpose**: Monitor RAG self-optimization through the Healing Agent

**Key Metrics**:
- Total healing events performed
- Distribution of healing actions:
  - OPTIMIZE - Improve existing chunks
  - REINDEX - Re-embed chunks with new strategy
  - RE_EMBED - Re-generate embeddings for chunks
  - SKIP - No action needed
- Average improvement per action type
- Documents most frequently healed
- Healing effectiveness (reward signal)
- Before/after metrics comparison

**Use Cases**:
- Measure RL agent effectiveness
- Identify problematic documents needing healing
- Optimize system parameters based on success rates
- Track cost vs benefit of healing actions
- Plan re-indexing schedules

**SQL Foundation**: Queries from `rag_history_and_optimization` where `event_type='HEAL'`

---

### 4. **Embedding Health Report**
**Purpose**: Monitor vector embedding quality and identify degradation

**Key Metrics**:
- Total chunks tracked
- Average quality score (0-1 scale)
- Quality score distribution (Excellent/Good/Fair/Poor)
- Chunks needing re-indexing (quality < 0.7)
- Average re-index count per chunk
- Embedding models in use
- Poor quality chunks (top 20 for review)

**Quality Score Breakdown**:
- **EXCELLENT** (0.9+): High-quality embeddings, no action needed
- **GOOD** (0.8-0.89): Acceptable, monitor for degradation
- **FAIR** (0.7-0.79): Needs attention, consider re-embedding
- **POOR** (<0.7): Immediate re-indexing recommended

**Use Cases**:
- Prevent "embedding collapse" (poor vector quality)
- Plan re-embedding campaigns
- Validate embedding model effectiveness
- Identify chunks with quality issues
- Monitor degradation over time

**SQL Foundation**: Queries from `chunk_embedding_data` table

---

### 5. **Cost & Token Analysis Report**
**Purpose**: Monitor operational costs and token usage

**Key Metrics**:
- Total tokens consumed (last N days)
- Total estimated cost
- Cost breakdown by event type:
  - QUERY events
  - HEAL events
  - SYNTHETIC_TEST events
- Cost per query
- Top 10 most expensive queries
- Daily cost trend
- Cost efficiency metrics

**Cost Calculation**:
- Tracks tokens used per event
- Multiplies by model pricing
- Identifies cost optimization opportunities
- Shows ROI of healing actions

**Use Cases**:
- Budget tracking and forecasting
- Identify cost optimization opportunities
- Prioritize queries by cost/accuracy ratio
- Justify healing investments (cost vs improvement)
- Plan capacity and resource allocation

**SQL Foundation**: Parses JSON `metrics_json` field from `rag_history_and_optimization`

---

### 6. **System Health Dashboard**
**Purpose**: Quick executive summary of RAG system health

**Composite Metrics**:
- **Health Score** (0-100): Weighted average of:
  - Query accuracy (50% weight)
  - Embedding quality (30% weight)
  - Healing effectiveness (20% weight)

- Documents ingested (last 7 days)
- Queries processed (last 7 days)
- Average query accuracy
- Healing actions taken
- Embedding health score
- System cost summary

**Health Score Interpretation**:
- **90-100**: Excellent - System operating optimally
- **75-89**: Good - Minor issues, monitor closely
- **60-74**: Fair - Action recommended
- **<60**: Poor - Immediate intervention needed

**Use Cases**:
- Executive reporting
- System status monitoring
- SLA compliance tracking
- Incident investigation starting point
- Performance trend analysis

**SQL Foundation**: Aggregates data from all metadata tables

---

## Metadata Table Schema

### `document_metadata`
```sql
doc_id (TEXT PRIMARY KEY)
title (TEXT)
author (TEXT)
source (TEXT)  -- CSV, PDF, Database, etc.
summary (TEXT)
rbac_namespace (TEXT)  -- Access control namespace
chunk_strategy (TEXT)  -- "recursive_splitter", "semantic", etc.
chunk_size_char (INTEGER)
overlap_char (INTEGER)
metadata_json (TEXT)  -- Additional fields as JSON
last_ingested (TIMESTAMP)
```

**Used For**:
- Tracking what documents are in the system
- Understanding chunking strategies per document
- RBAC-aware access control
- Ingestion audit trail

### `chunk_embedding_data`
```sql
chunk_id (TEXT PRIMARY KEY)
doc_id (TEXT FOREIGN KEY)
embedding_model (TEXT)
embedding_version (TEXT)
quality_score (FLOAT 0-1)  -- Health metric
reindex_count (INTEGER)  -- Times re-embedded
healing_suggestions (TEXT)  -- JSON with RL recommendations
created_at (TIMESTAMP)
last_healed (TIMESTAMP)
```

**Used For**:
- Tracking individual chunk quality
- Identifying poor performing embeddings
- RL agent decision making
- Healing action tracking

### `rag_history_and_optimization`
```sql
history_id (INTEGER PRIMARY KEY)
event_type (TEXT)  -- QUERY, HEAL, SYNTHETIC_TEST
timestamp (TIMESTAMP)
query_text (TEXT)  -- For QUERY events
target_doc_id (TEXT)  -- For HEAL events
target_chunk_id (TEXT)
metrics_json (TEXT)  -- {accuracy, latency_ms, cost, tokens, etc.}
context_json (TEXT)  -- Additional context as JSON
reward_signal (FLOAT 0-1)  -- RL agent reward
action_taken (TEXT)  -- OPTIMIZE, REINDEX, RE_EMBED, SKIP
state_before (TEXT)  -- System state JSON
state_after (TEXT)  -- System state JSON
agent_id (TEXT)  -- langgraph_agent, deepagents, etc.
user_id (TEXT)
session_id (TEXT)
```

**Used For**:
- Complete audit trail of all operations
- RL learning (reward signals)
- Performance tracking
- Cost analysis
- User behavior analysis

---

## How to Use RAG Analytics

### Python Usage

```python
from src.rag.reporting.rag_analytics_report import RAGAnalyticsReport

# Initialize with database path
analytics = RAGAnalyticsReport("path/to/database.db")

# Generate individual reports
ingestion = analytics.generate_ingestion_report(days=30)
queries = analytics.generate_query_performance_report(days=30)
healing = analytics.generate_healing_report(days=30)
embedding = analytics.generate_embedding_health_report()
costs = analytics.generate_cost_analysis_report(days=30)
health = analytics.generate_health_dashboard(days=7)

# Export reports
analytics.export_report_json(ingestion, "ingestion_report.json")
analytics.export_report_csv(queries, "queries.csv")
```

### Key Insights from Reports

**From Ingestion Report**:
- Monitor document diversity
- Identify namespace usage patterns
- Optimize chunking parameters

**From Query Report**:
- Track accuracy trends
- Identify slow/expensive queries
- Monitor user engagement

**From Healing Report**:
- Measure RL agent effectiveness
- Prioritize re-indexing efforts
- Calculate ROI on healing

**From Embedding Health**:
- Prevent quality degradation
- Plan re-embedding campaigns
- Validate embedding models

**From Cost Report**:
- Budget forecasting
- Cost optimization opportunities
- ROI analysis

**From Health Dashboard**:
- Executive reporting
- SLA tracking
- Incident identification

---

## Integration with RAG Agents

### LangGraph Agent Integration
The LangGraph agent logs:
- Query events to `rag_history_and_optimization`
- Document metadata to `document_metadata`
- Chunk embedding data to `chunk_embedding_data`

### DeepAgents Integration
The DeepAgents agent logs:
- Task execution results as QUERY events
- Healing actions as HEAL events
- Agent decisions with reward signals

### RL Healing Agent Integration
The RL agent:
- Reads state from metadata tables
- Logs decisions to `rag_history_and_optimization`
- Updates healing suggestions in `chunk_embedding_data`
- Generates reward signals for learning

---

## Best Practices

1. **Regular Monitoring**: Run health dashboard daily
2. **Weekly Reviews**: Analyze query and healing reports
3. **Monthly Planning**: Review cost and embedding health reports
4. **Ad-Hoc Analysis**: Query specific periods for investigation
5. **Alert Thresholds**: Set alerts for health score < 60
6. **Archive Reports**: Keep historical reports for trend analysis
