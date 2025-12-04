# Quick Start Guide - Enhanced Clustering Pipeline

## Prerequisites

```bash
pip install streamlit pandas numpy scikit-learn pyyaml langgraph
```

## Step 1: Setup Configuration

Create `src/clusterer/config.yaml`:

```yaml
data_sources:
  - path: "data/your_data"
    file_name: "*.csv"
  - path: "data/other_data"
    file_name: "*.json"
```

Create your data directory and add CSV/JSON files.

## Step 2: Prepare Data Directory

```
src/clusterer/
├── config.yaml          # Configuration file
├── data/               # Data directory
│   ├── your_data/
│   │   └── file1.csv
│   └── other_data/
│       └── file2.json
├── langgraph_orchestrator.py
├── data_allocator.py
└── dashboard_enhanced.py
```

## Step 3: Run the Dashboard

```bash
cd src/clusterer
streamlit run dashboard_enhanced.py
```

The dashboard will open at `http://localhost:8501`

## Step 4: Use the Three-Step Workflow

### Step 1: Data Ingestion
- Click "🔄 Ingest Data"
- Checkbox to verify tables loaded
- All tables from config.yaml sources will be ingested

### Step 2: Perform Clustering
- Select a table from dropdown
- Choose K values for KMeans (3, 5, 8 by default)
- Click "🚀 Perform Clustering"
- Review silhouette scores for each variant
- Results are stored in staged tables

### Step 3: Approve Clustering
- Select your preferred clustering variant
- Preview data with cluster assignments
- Click "✅ Approve This Clustering"
- Final table is created with naming: `{table}_{algorithm}_k{k}_final`

## Programmatic Usage

```python
import asyncio
from langgraph_orchestrator import LangGraphDataPipeline

async def main():
    pipeline = LangGraphDataPipeline(
        config_path="src/clusterer/config.yaml",
        db_path="src/clusterer/cluster_data.db",
        k_values=[3, 5, 8],
        verbose=True
    )
    
    result = await pipeline.run({})
    print(result)

asyncio.run(main())
```

## Table Naming Reference

| Stage | Table Name Pattern | Example |
|-------|-------------------|---------|
| Raw | `{filename}` | `customers` |
| KMeans Variant | `{table}_kmeans_k{k}_staged` | `customers_kmeans_k5_staged` |
| DBSCAN Variant | `{table}_dbscan_eps{eps}_staged` | `customers_dbscan_eps0.5_staged` |
| Final Approved | `{table}_{algo}_k{k}_final` | `customers_kmeans_k5_final` |

## Features

✅ **Multi-Source Data**: Load from multiple CSV/JSON sources
✅ **Auto Schema Detection**: Automatically detects column types
✅ **Multiple Algorithms**: Tests KMeans and DBSCAN variants
✅ **Silhouette Scores**: Quality metric for each variant
✅ **Human Approval**: Interactive selection in dashboard
✅ **Audit Trail**: All variants preserved in staged tables
✅ **No Hardcoding**: YAML config + auto-detection only

## Configuration Options

### K Values for KMeans

In `langgraph_orchestrator.py`:
```python
pipeline = LangGraphDataPipeline(
    k_values=[2, 3, 4, 5, 6, 7, 8]  # Customize here
)
```

### DBSCAN Epsilon Values

In `dashboard_enhanced.py`:
```python
for eps in [0.3, 0.5, 0.7]:  # Modify this list
    result = perform_dbscan_clustering(df, eps=eps, min_samples=5)
```

## Troubleshooting

### "No tables found"
- Check `config.yaml` paths are correct
- Verify CSV/JSON files exist in specified directories
- Re-run data ingestion

### "No numeric columns for clustering"
- Ensure data has numeric columns
- Non-numeric data is skipped automatically

### "Silhouette score is negative"
- May indicate poor cluster separation
- Try different K values
- Consider data preprocessing

## Architecture Overview

```
config.yaml
    ↓
    └→ DataAllocation
           ↓
      SQLite Base Table
           ↓
    [Dashboard: Select Table]
           ↓
      Clustering Node
    (Multiple Variants)
           ↓
    SQLite Staged Tables
           ↓
    [Dashboard: Preview & Select]
           ↓
    SaveFinal Node
           ↓
    SQLite Final Table
```

## Example: Custom Configuration

`config.yaml`:
```yaml
data_sources:
  - path: "data/customers"
    file_name: "*.csv"
  - path: "data/transactions"
    file_name: "transactions_*.json"
  - path: "data/archive"
    file_name: "*"  # Load all files
```

## Next Steps

1. Prepare your data in CSV/JSON format
2. Create `config.yaml` with correct paths
3. Run dashboard and follow 3-step workflow
4. Examine final tables in SQLite

For advanced usage, see `ENHANCED_CLUSTERING_ARCHITECTURE.md`
