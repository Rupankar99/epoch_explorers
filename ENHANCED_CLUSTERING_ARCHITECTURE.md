# Enhanced LangGraph Clustering Pipeline Architecture

## Overview

The enhanced clustering pipeline integrates multi-source data ingestion, dynamic clustering with variability analysis, and human-in-the-loop approval workflow for intelligent data clustering.

## Architecture Components

### 1. **Data Allocation Layer** (`data_allocator.py`)
- **YAML Configuration**: Defines multiple data sources with file paths and patterns
- **Multi-Source Ingestion**: Supports CSV, JSON, and wildcard patterns
- **Auto-Schema Detection**: Automatically detects data types (INTEGER, REAL, TEXT, BOOLEAN)
- **SQLite Storage**: Persists parsed data for clustering operations

**Config Example (`config.yaml`):**
```yaml
data_sources:
  - path: "data/input"
    file_name: "*.csv"
  - path: "data/json"
    file_name: "*.json"
```

### 2. **LangGraph Orchestrator** (`langgraph_orchestrator.py`)

#### Pipeline Flow:
```
START 
  → DataAllocation (Load YAML config, parse multi-source data)
  → Clustering (KMeans with K=3,5,8 + DBSCAN with eps=0.3,0.5,0.7)
  → LLM Analysis (Analyze clustering variability)
  → HITL Approval (User selects clustering variant)
  → SaveFinal (Rename staged→final tables)
  → END
```

#### Key Features:

**Data Allocation Node:**
- Reads `config.yaml` for data source definitions
- Parses files matching patterns (wildcards supported)
- Saves raw data to SQLite base tables

**Clustering Node:**
- Generates multiple clustering variants:
  - **KMeans**: Tests K=3, 5, 8 (configurable)
  - **DBSCAN**: Tests eps=0.3, 0.5, 0.7
- Saves each variant to staged table: `{table}_kmeans_k{k}_staged` or `{table}_dbscan_eps{eps}_staged`
- Computes silhouette scores and quality metrics for each variant

**LLM Analysis Node:**
- Analyzes clustering variability across all variants
- Provides interpretable summaries of quality differences
- Explains trade-offs between algorithms and parameters

**HITL Approval Node:**
- Displays all clustering variants with quality scores
- User selects preferred variant (K value + algorithm)
- Stores approval configuration for final save

**SaveFinal Node:**
- Renames approved staged tables to final tables
- Tables named: `{table}_{algorithm}_k{k}_final` or `{table}_{algorithm}_eps{eps}_final`
- Uses automatic schema detection from raw data

### 3. **Enhanced Streamlit Dashboard** (`dashboard_enhanced.py`)

#### Three-Step Workflow:

**Step 1: Data Ingestion**
- Loads config from `src/clusterer/config.yaml`
- Displays loaded data sources
- Creates base tables in SQLite

**Step 2: Clustering**
- Select table to cluster
- Choose K values for KMeans (default: 3, 5, 8)
- Generates clustering variants
- Shows silhouette scores and quality metrics
- Stores variants for approval

**Step 3: Approval**
- Display all clustering variants
- User selects preferred variant
- Preview data with cluster assignments
- Approve and save to final table

#### Benefits:
- **Interactive Exploration**: Try multiple K values and algorithms
- **Visual Comparison**: See silhouette scores for each variant
- **Human Approval**: Let domain experts select best clustering
- **No Hardcoding**: Schema auto-detected, works with any data structure
- **Audit Trail**: Staged tables preserve variants for comparison

### 4. **Schema Auto-Detection**

Automatically detects column types:
```python
def auto_detect_schema(df: pd.DataFrame) -> Dict[str, str]:
    # int64, int32 → INTEGER
    # float64, float32 → REAL
    # bool → BOOLEAN
    # others → TEXT
```

### 5. **Table Naming Convention**

**Source Tables:**
```
original_data           # Raw ingested data
```

**Staged Tables (Clustering Variants):**
```
original_data_kmeans_k3_staged
original_data_kmeans_k5_staged
original_data_kmeans_k8_staged
original_data_dbscan_eps0.3_staged
original_data_dbscan_eps0.5_staged
original_data_dbscan_eps0.7_staged
```

**Final Tables (After HITL Approval):**
```
original_data_kmeans_k5_final           # User selected K=5 for KMeans
original_data_dbscan_eps0.5_final       # Or user selected DBSCAN
```

## Integration with Existing Systems

### Compatibility:
- Works with LangGraph state management
- Compatible with existing agent pipeline architecture
- Integrates with FastAPI for future REST endpoints
- Uses standard SQLite (no specialized databases)

### No Breaking Changes:
- Old agents remain available (DataAcquisitionAgent, etc.)
- Can run simultaneously with existing pipelines
- Modular design allows gradual adoption

## Usage Flow

### 1. Configuration
Create `src/clusterer/config.yaml`:
```yaml
data_sources:
  - path: "path/to/data"
    file_name: "*.csv"
```

### 2. Run Dashboard
```bash
streamlit run src/clusterer/dashboard_enhanced.py
```

### 3. Orchestrate Programmatically
```python
from langgraph_orchestrator import LangGraphDataPipeline
import asyncio

pipeline = LangGraphDataPipeline(
    config_path="src/clusterer/config.yaml",
    db_path="src/clusterer/cluster_data.db",
    k_values=[3, 5, 8]
)

result = await pipeline.run({})
```

## Data Flow Diagram

```
┌─────────────────┐
│   config.yaml   │
│  (Data Sources) │
└────────┬────────┘
         │
         ▼
┌──────────────────────────┐
│   DataAllocation Node    │
│  • Load config           │
│  • Parse files           │
│  • Auto-detect schema    │
└──────────┬───────────────┘
           │
           ▼
    ┌──────────────┐
    │  SQLite DB   │
    │ (Base Tables)│
    └──────────────┘
           │
           ▼
┌──────────────────────────┐
│   Clustering Node        │
│  • KMeans variants       │
│  • DBSCAN variants       │
│  • Save staged tables    │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  LLM Analysis Node       │
│  • Analyze variability   │
│  • Generate insights     │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  HITL Approval (Dashboard)
│  • User selects variant  │
│  • Confirms clustering   │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│   SaveFinal Node         │
│  • Rename staged→final   │
│  • Create audit records  │
└──────────┬───────────────┘
           │
           ▼
    ┌──────────────┐
    │  SQLite DB   │
    │ (Final Table)│
    └──────────────┘
```

## Key Advantages

1. **No Hardcoding**: Uses YAML config + auto-schema detection
2. **Multiple Algorithms**: Tests KMeans and DBSCAN variants
3. **Variability Analysis**: LLM-based explanation of differences
4. **Human Approval**: Dashboard for visual selection
5. **Audit Trail**: Preserves all variants in staged tables
6. **Flexible K Values**: Configurable cluster counts
7. **DB-Only**: All connections use db_path parameter
8. **Modular**: Each step is independent and composable

## Future Enhancements

- [ ] Real LLM integration for advanced variability analysis
- [ ] Visualization of cluster distributions
- [ ] Historical tracking of user approvals
- [ ] REST API endpoints for remote access
- [ ] Batch processing for multiple tables
- [ ] Custom distance metrics and preprocessing
- [ ] Integration with MLOps platforms
