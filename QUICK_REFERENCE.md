# Quick Reference - Agentic Clustering Orchestrator

## 🎯 TL;DR

Your clustering system is now:
- ✅ **Agentic** (LangGraph workflow)
- ✅ **Multi-provider LLM** (Ollama/Azure/OpenAI/Anthropic)
- ✅ **Self-contained** (all files in `src/clusterer/`)
- ✅ **Portable** (can be used in any project)

## 📂 Self-Contained Files

```
src/clusterer/
├── llm_service.py           ← Multi-provider LLM wrapper (NEW)
├── llm_config.json          ← LLM configuration (NEW)
├── agentic_orchestrator.py  ← LangGraph workflow (UPDATED)
├── orchestrator.py          ← Business logic
├── dashboard_enhanced.py    ← Streamlit UI
```

**No more** `sys.path.insert` or imports from `../rag/` folder!

## 🚀 Quick Start

### 1. Run Dashboard
```bash
cd src/clusterer
streamlit run dashboard_enhanced.py
```

### 2. Use Programmatically
```python
from agentic_orchestrator import AgenticClusteringOrchestrator

# Initialize
agentic = AgenticClusteringOrchestrator()

# Ingest data
agentic.agent.orchestrator.run_ingestion()

# Run clustering with LLM analysis
state = agentic.run_autonomous_clustering(
    table_name='transactions',
    custom_k_values=[2, 3, 5, 7],
    custom_eps_values=[0.3, 0.5, 0.7]
)

# Get AI recommendations
recs = agentic.get_recommendations(state)
print(f"Best: {recs['best_variant']}")
print(f"Quality: {recs['best_quality']}")

# Approve with labels
labels = {0: "High Risk", 1: "Medium Risk", 2: "Low Risk"}
agentic.approve_selected_clustering(state, cluster_labels=labels)
```

## ⚙️ Configure LLM

Edit `src/clusterer/llm_config.json`:

### Use Ollama (Default)
```json
{
  "default_provider": "ollama",
  "llm_providers": {
    "ollama": {
      "enabled": true,
      "base_url": "http://localhost:11434",
      "model": "qwen2.5:0.5b"
    }
  }
}
```

### Use Azure
```json
{
  "default_provider": "azure",
  "llm_providers": {
    "azure": {
      "enabled": true,
      "api_endpoint": "https://your-instance.openai.azure.com/v1",
      "model": "your-deployment",
      "api_key_env": "AZURE_API_KEY"
    }
  }
}
```

### Use OpenAI
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

## 📊 Workflow Stages

1. **Initialize** → Load table data
2. **Optimize Parameters** → Auto-select K/eps or use custom
3. **Execute Clustering** → Run KMeans + DBSCAN
4. **Assess Quality** → **LLM analyzes all variants** 🤖
5. **Make Decision** → Pick best variant
6. **Prepare Approval** → Wait for human review
7. **Save Final** → Apply labels, create final table

## 💬 LLM Analysis

The agent sends each variant to the LLM:

```
Prompt:
"Analyze these clustering results and provide quality insights:
- KMeans K=2: Silhouette=0.5, Inertia=1000
- KMeans K=3: Silhouette=0.7, Inertia=800
- DBSCAN eps=0.3: Silhouette=0.4, Clusters=5, Noise=10
..."

LLM Response (Ollama):
"KMeans K=3 shows EXCELLENT quality with high silhouette score...
DBSCAN eps=0.3 has too many noise points, not recommended...
RECOMMENDATION: Use KMeans K=3..."
```

## 🔄 Re-ingestion (No Errors!)

```python
# Old tables auto-cleaned
agentic.agent.orchestrator.run_ingestion()

# Fresh clustering
state = agentic.run_autonomous_clustering('transactions', ...)

# Works every time ✓
```

## 📋 Database Tables

| Table | Purpose |
|-------|---------|
| `clustering_metadata` | All variants + metadata + LLM analysis |
| `{table}_{algo}_{param}_staged` | Clustered data (staging) |
| `{table}_{algo}_{param}_final` | Approved result with labels |

## 🎨 Final Table Structure

```
Original: [amount, type, merchant, ...]
Staged:   [amount, type, merchant, ..., cluster]
Final:    [amount, type, merchant, ..., cluster, cluster_label]
```

Example:
```
| amount | type   | cluster | cluster_label  |
|--------|--------|---------|----------------|
| 1000   | debit  | 0       | High Risk      |
| 50     | credit | 1       | Low Risk       |
| 5000   | transfer| 0      | High Risk      |
```

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| LLM not responding | Check Ollama is running: `ollama serve` |
| "Table exists" error | Already fixed! Auto-cleanup on re-ingest |
| Import errors | All files are local in `src/clusterer/` |
| Different LLM provider | Edit `llm_config.json` and set `"enabled": true` |

## 📦 Reuse in Other Projects

Copy to your project:
```bash
cp llm_service.py        /your/project/
cp llm_config.json       /your/project/
cp agentic_orchestrator.py /your/project/
cp orchestrator.py       /your/project/
```

Then use:
```python
from agentic_orchestrator import AgenticClusteringOrchestrator
agentic = AgenticClusteringOrchestrator()
```

No sys.path hacks needed! 🎉

## 📞 Support

**Components:**
- `agentic_orchestrator.py` → LangGraph workflow + LLM integration
- `orchestrator.py` → Clustering + database operations
- `llm_service.py` → Multi-provider LLM abstraction
- `dashboard_enhanced.py` → Streamlit UI

**Key Methods:**
```python
# Agentic Orchestrator
agentic.run_autonomous_clustering(table, k_vals, eps_vals)
agentic.get_recommendations(state)
agentic.approve_selected_clustering(state, labels)

# Basic Orchestrator
orchestrator.run_ingestion()
orchestrator.get_tables()
orchestrator.get_table_data(table)
orchestrator.run_clustering(table, k_vals, eps_vals)
orchestrator.approve_and_save(table, variant, data, labels)

# LLM Service
llm_service.generate_response(prompt)
llm_service.generate_json(prompt)
llm_service.generate_embeddings(texts)
```

---

✨ **You're all set! Everything is self-contained and ready to use.** ✨
