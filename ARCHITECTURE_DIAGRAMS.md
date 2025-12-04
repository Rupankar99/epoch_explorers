# Architecture Diagram

## Before (Mixed Concerns)
```
┌─────────────────────────────────────────────┐
│         Streamlit Dashboard                 │
├─────────────────────────────────────────────┤
│ • Database connections (sqlite3)            │
│ • CREATE TABLE statements                   │
│ • KMeans/DBSCAN clustering code             │
│ • LLM API calls (hardcoded)                 │
│ • Metadata management                       │
│ • Silhouette score calculations             │
│ • Visualization (PCA)                       │
│ • Session state management                  │
│ • UI rendering                              │
└─────────────────────────────────────────────┘
         ↓ (Everything mixed together)
```

## After (Clean Separation)
```
┌────────────────────────────────────┐
│    Streamlit Dashboard (UI)         │
│  dashboard_enhanced.py              │
├────────────────────────────────────┤
│ ✓ Data display                      │
│ ✓ Visualizations (PCA 3D/2D)       │
│ ✓ Forms & buttons                   │
│ ✓ Session state management          │
│ ✗ NO business logic                 │
│ ✗ NO DB operations                  │
│ ✗ NO LLM calls                      │
└────────────────────────────────────┘
         ↓ (Delegates)
┌────────────────────────────────────┐
│  ClusteringOrchestrator (Backend)   │
│  orchestrator.py                    │
├────────────────────────────────────┤
│ ✓ Database schema & operations      │
│ ✓ Data loading from config.yaml    │
│ ✓ KMeans/DBSCAN clustering         │
│ ✓ LLM integration (Ollama/OpenAI)  │
│ ✓ Metadata persistence             │
│ ✓ Quality metrics calculation      │
│ ✓ Staged/Final table management    │
│ ✓ Rule-based fallback explanations │
└────────────────────────────────────┘
         ↓ (Uses)
┌────────────────────────────────────┐
│    External Services                │
├────────────────────────────────────┤
│ • SQLite DB (cluster_data.db)      │
│ • config.yaml (data sources)       │
│ • data_allocator (multi-source)    │
│ • Ollama/OpenAI LLM                │
│ • scikit-learn (clustering)        │
└────────────────────────────────────┘
```

## Data Flow: Clustering Operation

```
1. USER ACTION
   Dashboard: Select table + K values
   
   ↓
   
2. ORCHESTRATOR CALL
   orchestrator.run_clustering(table="transactions", k_values=[3,5,8])
   
   ↓
   
3. ORCHESTRATOR OPERATIONS
   ┌─ For each K:
   │  ├─ Load data
   │  ├─ Scale features (StandardScaler)
   │  ├─ Run KMeans
   │  ├─ Calculate silhouette score
   │  ├─ Get LLM explanation
   │  ├─ Save metadata → clustering_metadata
   │  └─ Save to staged table → transactions_kmeans_k3_staged
   │
   ├─ For each eps:
   │  ├─ Load data
   │  ├─ Scale features
   │  ├─ Run DBSCAN
   │  ├─ Calculate silhouette score
   │  ├─ Get LLM explanation
   │  ├─ Save metadata
   │  └─ Save to staged table → transactions_dbscan_eps0.3_staged
   │
   └─ Return all variants with explanations
   
   ↓
   
4. DASHBOARD DISPLAY
   ├─ Render KMeans variants
   │  ├─ Silhouette score badge
   │  ├─ 2D PCA visualization
   │  ├─ 3D PCA visualization
   │  └─ Cluster distribution
   │
   ├─ Render DBSCAN variants
   │  ├─ Silhouette score badge
   │  ├─ 2D PCA visualization
   │  ├─ 3D PCA visualization (animated)
   │  └─ Cluster distribution
   │
   └─ LLM Explanation (from orchestrator)
      "Based on the silhouette score of 0.53 and cluster distribution..."
```

## Metadata Flow

```
CLUSTERING EVENT
      ↓
┌─────────────────────────────────────┐
│ orchestrator._save_metadata()        │
├─────────────────────────────────────┤
│ Inserts into clustering_metadata:   │
│ • timestamp: 2025-12-03T22:30:15    │
│ • table_name: "transactions"        │
│ • variant_name: "KMeans K=3"        │
│ • algorithm: "kmeans"               │
│ • parameters: {"k": 3}              │
│ • silhouette_score: 0.5342          │
│ • llm_explanation: "..."            │  ← From Ollama/OpenAI
│ • status: "staged"                  │
│ • metadata_json: {...full result}   │
└─────────────────────────────────────┘
      ↓
   SQLite Database
   (audit trail, reproducibility)
      ↓
   On Approval: status → "approved"
```

## LLM Integration Flow

```
orchestrator._get_llm_explanation()
      ↓
  ┌─ Check if LLM available? ─┐
  │                            │
  NO                           YES
  │                            │
  ↓                            ↓
Rule-based              Call Ollama
Analysis                (llama2 model)
  │                            │
  ├─ Silhouette score     ├─ Format prompt
  ├─ Quality assessment   ├─ Send request
  ├─ Metrics analysis     ├─ Get response
  └─ Simple recommendations   └─ Return LLM text
                               
      ↓ (Both paths)
  ┌──────────────────┐
  │ Return explanation  │ → Save to metadata
  └──────────────────┘     → Display in dashboard
```

## Configuration & Extensibility

```
orchestrator.py
    ↓
├─ _perform_kmeans()     ← Easy to add: _perform_gaussian_mixture()
├─ _perform_dbscan()     ← Easy to add: _perform_spectral()
├─ _perform_agglomerative() ← Could add
│
├─ _get_llm_explanation()
│   ├─ Try Ollama
│   ├─ Try OpenAI              ← Easy to switch providers
│   ├─ Try Claude
│   └─ Fallback rule-based     ← Always works
│
├─ _save_metadata()
│   └─ SQLite database         ← Easy to switch: PostgreSQL, MongoDB
│
└─ _save_staged_table()
    └─ SQLite database         ← Same DB, easy to change
```

## Benefits Summary

| Feature | Benefit |
|---------|---------|
| **Clean Separation** | Dashboard focuses on UX, orchestrator on logic |
| **No Hardcoding** | Config-driven, database schema in orchestrator |
| **LLM Pluggable** | Easy to swap Ollama ↔ OpenAI ↔ local LLM |
| **Audit Trail** | All operations logged with timestamps |
| **Reusable Backend** | Orchestrator can be used by API, CLI, batch jobs |
| **Testable** | Each component independently testable |
| **Extensible** | Add algorithms/LLMs without touching UI |
| **Resilient** | Falls back to rule-based when LLM unavailable |
