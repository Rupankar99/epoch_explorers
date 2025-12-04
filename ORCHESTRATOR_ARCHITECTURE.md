# Dashboard Refactoring: Clean Separation of Concerns

## Overview
Refactored the clustering dashboard to follow **clean architecture principles**:
- **Dashboard** = UI/UX only (Streamlit)
- **Orchestrator** = All business logic (backend)

## What Changed

### Dashboard (`dashboard_enhanced.py`)
**Before**: Mixed concerns - UI + DB operations + LLM calls + metadata management
**After**: Pure UI layer only

**Current Responsibilities**:
- Display data ingestion page
- Show clustering selection interface
- Render 3D/2D visualizations (PCA projections)
- Display approval workflow
- Show cluster distributions

**What it DOESN'T do anymore**:
- ❌ No hardcoded database connections
- ❌ No `CREATE TABLE` statements
- ❌ No metadata management
- ❌ No LLM API calls
- ❌ No clustering algorithm implementation
- ❌ No rule-based explanations

### New Backend (`orchestrator.py`)
**Purpose**: Complete orchestration of all backend operations

**Handles**:
✅ Database initialization and schema management
✅ Data loading from config.yaml (via data_allocator)
✅ Multiple clustering algorithms (KMeans, DBSCAN)
✅ Quality metrics (silhouette score, inertia)
✅ Staged table management (pre-approval)
✅ LLM integration (Ollama/OpenAI/local LLM)
✅ Metadata persistence (clustering history + audit trail)
✅ Fallback to rule-based explanations when LLM unavailable

## Class: `ClusteringOrchestrator`

### Methods

#### Initialization & Setup
```python
__init__()                      # Initialize with paths and DB setup
_init_database()                # Create metadata table
_check_llm_availability()       # Check if LLM service is running
```

#### Data Operations
```python
run_ingestion()                 # Load from config.yaml → DB
get_tables()                    # List available tables
get_table_data(table_name)      # Fetch table data
```

#### Clustering Execution
```python
run_clustering(table, k_values) # Execute all clustering variants
_perform_kmeans(df, k)          # Single KMeans run
_perform_dbscan(df, eps)        # Single DBSCAN run
```

#### Metadata & Storage
```python
_save_metadata(...)             # Store to clustering_metadata table
_save_staged_table(...)         # Create staged results table
```

#### LLM Integration
```python
_get_llm_explanation(...)       # Call Ollama/OpenAI for analysis
_get_rule_based_explanation()   # Fallback when LLM unavailable
get_clustering_explanation()    # Public interface for explanations
```

#### Approval & Finalization
```python
approve_and_save(...)           # Move staged → final table
```

## Metadata Table Schema

```sql
CREATE TABLE clustering_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    table_name TEXT NOT NULL,
    variant_name TEXT NOT NULL,          -- "KMeans K=3", "DBSCAN eps=0.5"
    algorithm TEXT NOT NULL,              -- "kmeans" or "dbscan"
    parameters TEXT NOT NULL,             -- JSON: {k: 3} or {eps: 0.5, min_samples: 5}
    silhouette_score REAL,
    quality_assessment TEXT,
    llm_explanation TEXT,                 -- From Ollama/OpenAI
    status TEXT DEFAULT 'staged',         -- staged | approved
    metadata_json TEXT                    -- Full result dictionary
)
```

## LLM Integration Flow

### 1. Check LLM Availability
- Tries to connect to Ollama at `http://localhost:11434`
- Sets `self.llm_enabled` flag

### 2. Generate Explanation
If LLM available:
- Formats clustering metrics and data info
- Sends prompt to Ollama (default model: `llama2`)
- Returns LLM-generated analysis

If LLM unavailable:
- Falls back to rule-based logic
- Assesses quality by silhouette thresholds:
  - `> 0.7`: EXCELLENT
  - `> 0.5`: GOOD
  - `> 0.3`: FAIR
  - `≤ 0.3`: POOR

### 3. Store in Metadata
- Saves full LLM explanation to `clustering_metadata.llm_explanation`
- Persists for audit trail and reproducibility

## Dashboard → Orchestrator Call Flow

### Ingestion Page
```
User clicks "Ingest Data"
    ↓
Dashboard calls: orchestrator.run_ingestion()
    ↓
Orchestrator:
  - Loads config.yaml
  - Parses data sources
  - Creates DB tables
  - Returns tables list
    ↓
Dashboard displays: ✓ Tables loaded
```

### Clustering Page
```
User selects table + K values
    ↓
Dashboard calls: orchestrator.run_clustering(table, k_values)
    ↓
Orchestrator:
  - Runs KMeans for each K
  - Runs DBSCAN for each eps
  - Gets LLM explanations
  - Saves metadata
  - Creates staged tables
  - Returns all variants
    ↓
Dashboard displays: 3D/2D visualizations + metrics
```

### Approval Page
```
User selects variant + clicks Approve
    ↓
Dashboard calls: orchestrator.approve_and_save(table, variant, data)
    ↓
Orchestrator:
  - Finds staged table
  - Renames to _final
  - Updates metadata status
  - Returns confirmation
    ↓
Dashboard displays: ✓ Clustering approved
```

## Benefits of This Architecture

| Aspect | Before | After |
|--------|--------|-------|
| **Testability** | Hard (UI entangled with logic) | Easy (orchestrator is testable) |
| **Reusability** | UI-only code | Orchestrator can be used by other interfaces (CLI, API, etc.) |
| **Maintainability** | Changes ripple through dashboard | Changes isolated to orchestrator |
| **Scalability** | Difficulty adding features | Easy to add new clustering algorithms/LLMs |
| **Separation of Concerns** | Mixed | Clean |
| **Database Logic** | Hardcoded in dashboard | Centralized in orchestrator |
| **LLM Integration** | None | Pluggable (Ollama, OpenAI, local) |
| **Configuration** | Multiple places | Single config.yaml |

## How to Extend

### Add a New Clustering Algorithm
```python
# In orchestrator.py
def _perform_spectral_clustering(self, df, n_clusters):
    """Execute Spectral clustering"""
    # Implementation
    return {...}

# In run_clustering()
for n in [3, 5, 8]:
    result = self._perform_spectral_clustering(df, n)
    variants[f"Spectral n={n}"] = result
```

### Add New LLM Provider
```python
# In _get_llm_explanation()
# Try OpenAI
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)
```

### Add Custom Quality Metrics
```python
# Store additional metrics in metadata
result['davies_bouldin'] = davies_bouldin_score(scaled_data, labels)
result['calinski_harabasz'] = calinski_harabasz_score(scaled_data, labels)
```

## Running the Dashboard

```bash
cd src/clusterer
streamlit run dashboard_enhanced.py
```

The dashboard will:
1. Initialize the orchestrator
2. Load config.yaml path from orchestrator
3. Display 3-page workflow (Ingestion → Clustering → Approval)
4. Delegate all operations to orchestrator
5. Display results with LLM-generated explanations
