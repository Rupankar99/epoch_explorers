# Agentic Clustering Orchestrator - Complete Setup

## ✅ Architecture Overview

Your clustering system now uses a **complete agentic workflow** with **multi-provider LLM support**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                      │
│         (UI-Only, No Business Logic Hardcoded)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         AgenticClusteringOrchestrator (LangGraph)           │
│         ┌────────────────────────────────────────────────┐  │
│         │  Multi-Provider LLM Service Integration        │  │
│         │  - Ollama (local, default)                    │  │
│         │  - Azure OpenAI                               │  │
│         │  - OpenAI GPT-4                               │  │
│         │  - Anthropic Claude                           │  │
│         │  - HuggingFace Models                         │  │
│         └────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─► Initialize ─► Optimize Params ─► Cluster ─► Assess ──┐ │
│  │                                                           │ │
│  └─ Make Decision ─► Prepare Approval ─► Save ─► END ──────┘ │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            Orchestrator (Business Logic)                    │
│  - Data Ingestion & Cleaning                               │
│  - KMeans & DBSCAN Clustering                              │
│  - Metadata Management                                      │
│  - Cluster Labeling & Final Table Creation                 │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              SQLite Database                                │
│  - Metadata Table (clustering_metadata)                    │
│  - Staged Tables ({table}_{algo}_{param}_staged)          │
│  - Final Tables ({table}_{algo}_{param}_final)            │
└─────────────────────────────────────────────────────────────┘
```

## 📁 File Structure

```
src/clusterer/
├── agentic_orchestrator.py      # LangGraph workflow (NEW - Multi-provider LLM)
├── orchestrator.py               # Business logic (DB, clustering, approval)
├── dashboard_enhanced.py          # Streamlit UI (UI-only)
├── llm_service.py               # Multi-provider LLM wrapper (NEW - Local)
├── llm_config.json              # LLM configuration (NEW - Local)
├── cluster_data.db              # SQLite database (auto-created)
├── config.yaml                  # Data ingestion config
├── data_allocator.py            # Data loading utilities
└── ... (other files)
```

## 🔧 Key Components

### 1. **llm_service.py** (Multi-Provider LLM Wrapper)
- Supports: Ollama, Azure, OpenAI, Anthropic, HuggingFace
- SSL bypass for corporate networks
- Token counting with tiktoken
- Cost estimation
- Embedding support

### 2. **llm_config.json** (Configuration File)
```json
{
  "llm_providers": {
    "ollama": {
      "enabled": true,
      "base_url": "http://localhost:11434",
      "model": "qwen2.5:0.5b"
    }
  },
  "default_provider": "ollama"
}
```

### 3. **agentic_orchestrator.py** (LangGraph Workflow)
```python
# Initialization
agentic = AgenticClusteringOrchestrator()

# Step 1: Run ingestion
state = agentic.run_autonomous_clustering(
    table_name='transactions',
    custom_k_values=[2, 3, 5, 7],
    custom_eps_values=[0.3, 0.5, 0.7]
)

# Step 2: Get AI recommendations
recs = agentic.get_recommendations(state)
print(f"Best variant: {recs['best_variant']}")
print(f"Quality score: {recs['best_quality']}")

# Step 3: Approve with cluster labels
cluster_labels = {
    0: "High Risk",
    1: "Medium Risk",
    2: "Low Risk"
}
final = agentic.approve_selected_clustering(state, cluster_labels)
```

## 🚀 Workflow Steps

### **Node 1: Initialize**
- Loads data from specified table
- Sets up processing state
- Initializes thresholds

### **Node 2: Optimize Parameters**
- Auto-selects K values (or uses custom)
- Auto-selects eps values (or uses custom)
- Smart parameter selection based on data size

### **Node 3: Execute Clustering**
- Runs KMeans for each K value
- Runs DBSCAN for each eps value
- Generates staged tables

### **Node 4: Assess Quality** (LLM-Powered)
- Builds variant summary for LLM
- **Sends to LLM**: Quality assessment prompt
- **LLM Analysis** (Ollama by default):
  - Quality level classification
  - Strengths/weaknesses analysis
  - Recommendation scores
- Fallback to rule-based if LLM unavailable
- Ranks all variants by quality score

### **Node 5: Make Decision**
- Selects best variant
- Compares to quality threshold
- Flags for review if needed

### **Node 6: Prepare Approval**
- Prepares clustering for human review
- Awaits cluster labeling from UI

### **Node 7: Save Final Result**
- Applies cluster labels
- Creates final table with labels
- Drops staged table
- Updates metadata status

## 💡 LLM Integration

### Default Configuration
- **Provider**: Ollama (local, no API keys needed)
- **Model**: `qwen2.5:0.5b` (fast, lightweight)
- **Temperature**: 0.3 (deterministic)
- **Available models** (from `ollama list`):
  - `nomic-embed-text` (embeddings)
  - `qwen2.5:0.5b` (LLM)
  - `qwen2.5:3b` (larger LLM)

### Alternative Providers

**Switch to Azure:**
```json
{
  "default_provider": "azure",
  "llm_providers": {
    "azure": {
      "enabled": true,
      "api_endpoint": "https://your-instance.openai.azure.com/v1",
      "model": "your-deployment-name",
      "api_key_env": "AZURE_API_KEY"
    }
  }
}
```

**Switch to OpenAI:**
```json
{
  "default_provider": "openai",
  "llm_providers": {
    "openai": {
      "enabled": true,
      "model": "gpt-4",
      "api_key_env": "OPENAI_API_KEY"
    }
  }
}
```

## 📊 Database Schema

### Metadata Table
```sql
CREATE TABLE clustering_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    table_name TEXT NOT NULL,
    variant_name TEXT NOT NULL,              -- "KMeans K=3"
    algorithm TEXT NOT NULL,                 -- "kmeans" or "dbscan"
    parameters TEXT,                         -- JSON: {k: 3} or {eps: 0.5}
    silhouette_score REAL,
    quality_assessment TEXT,
    llm_explanation TEXT,                    -- LLM analysis
    status TEXT DEFAULT 'staged',            -- staged → approved
    metadata_json TEXT
)
```

### Staged Table Example
```
transactions_kmeans_k3_staged
├── [original columns]
└── cluster (INT)
```

### Final Table Example
```
transactions_kmeans_k3_final
├── [original columns]
├── cluster (INT)
└── cluster_label (TEXT)  -- "High Risk", "Low Risk", etc.
```

## 🔄 Complete Workflow Example

```python
from agentic_orchestrator import AgenticClusteringOrchestrator

# 1. Initialize
agentic = AgenticClusteringOrchestrator()

# 2. Run ingestion (loads config.yaml)
ingest = agentic.agent.orchestrator.run_ingestion()
print(f"Tables loaded: {ingest['tables']}")  # ['transactions', 'users', ...]

# 3. Run autonomous clustering
state = agentic.run_autonomous_clustering(
    table_name='transactions',
    custom_k_values=[2, 3, 5, 7],
    custom_eps_values=[0.3, 0.5, 0.7]
)

# 4. Get LLM-powered recommendations
recs = agentic.get_recommendations(state)
# Output includes LLM analysis for each variant

# 5. Approve with cluster labeling
cluster_labels = {0: "High Risk", 1: "Medium Risk", 2: "Low Risk"}
final_state = agentic.approve_selected_clustering(
    state,
    cluster_labels=cluster_labels
)

# 6. Query final table
import sqlite3
conn = sqlite3.connect('src/clusterer/cluster_data.db')
df = pd.read_sql_query(
    "SELECT * FROM transactions_kmeans_k3_final",
    conn
)
print(df[['amount', 'cluster', 'cluster_label']])
```

## 📋 Re-ingestion Handling

When you re-ingest data:
1. **Old staged/final tables** are automatically dropped
2. **Metadata** is cleared
3. **Fresh clustering** can be run
4. **No "table already exists" errors**

```python
# First run
state1 = agentic.run_autonomous_clustering('transactions', ...)
final1 = agentic.approve_selected_clustering(state1, cluster_labels)

# Second run (fresh ingestion)
agentic.agent.orchestrator.run_ingestion()  # Auto-cleans old tables
state2 = agentic.run_autonomous_clustering('transactions', ...)  # Succeeds
final2 = agentic.approve_selected_clustering(state2, cluster_labels)
```

## 🎯 Key Features

✅ **Self-contained** - `llm_service.py` and `llm_config.json` are local to clusterer folder  
✅ **Multi-provider LLM** - Switch providers without code changes  
✅ **Agentic workflow** - LangGraph handles orchestration  
✅ **LLM-powered analysis** - Quality assessment via AI  
✅ **Cluster labeling** - Meaningful names for final table  
✅ **Re-ingestion safe** - Auto-cleanup of old tables  
✅ **Clean architecture** - UI-only dashboard, logic in orchestrator  
✅ **Production-ready** - Error handling, logging, SSL bypass  

## 🚦 Running the Dashboard

```bash
cd src/clusterer
streamlit run dashboard_enhanced.py
```

Then:
1. **Ingestion Page**: Click "Ingest Data" 
2. **Clustering Page**: Select table → Run autonomous agent
3. **Approval Page**: Label clusters → Approve variants
4. Final tables created with `cluster_label` column ✓

## 📝 Next Steps

The orchestrator is now **fully agentic and self-contained**. You can:
- Use it in other projects (copy `agentic_orchestrator.py`, `orchestrator.py`, `llm_service.py`, `llm_config.json`)
- Switch LLM providers by editing `llm_config.json`
- Add custom clustering algorithms to `orchestrator.py`
- Extend LangGraph nodes for additional analysis
