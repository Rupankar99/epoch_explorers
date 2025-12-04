# LLM Integration Setup Guide

## Current Status

The dashboard **uses an intelligent fallback system**:

```
┌─────────────────────────────────────┐
│ Try to Use LLM                      │
├─────────────────────────────────────┤
│ 1. Check if Ollama is running      │
│    (http://localhost:11434)        │
│    └─ If YES → Use Ollama (llama2) │
│                                    │
│ 2. Check if OpenAI API key set     │
│    └─ If YES → Use OpenAI (GPT)    │
│                                    │
│ 3. If no LLM available             │
│    └─ Use rule-based explanations  │
└─────────────────────────────────────┘
```

## How to Enable LLM

### Option 1: Use Ollama (Local, Free, Private)

#### Install Ollama
- **Download**: https://ollama.ai
- **Run**: `ollama serve`

#### Start Ollama Service
```bash
# On Windows (PowerShell)
ollama serve

# On macOS/Linux
ollama serve
```

#### Download a Model
```bash
ollama pull llama2
# Or: ollama pull mistral, neural-chat, etc.
```

#### Test Connection
```bash
curl http://localhost:11434/api/tags
# Should see: {"models": [{"name": "llama2:latest", ...}]}
```

#### Run Dashboard (Ollama will be auto-detected)
```bash
cd src/clusterer
streamlit run dashboard_enhanced.py
```

**You should see:**
```
[ClusteringOrchestrator] LLM Mode: OLLAMA (llama2)
✓ Ollama available with models: ['llama2:latest']
```

---

### Option 2: Use OpenAI (Cloud, Paid, Fast)

#### Get API Key
1. Sign up: https://platform.openai.com
2. Create API key: https://platform.openai.com/api-keys
3. Copy the key

#### Set Environment Variable

**PowerShell (Windows):**
```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:CLUSTERING_LLM_PROVIDER = "openai"
streamlit run dashboard_enhanced.py
```

**Bash (macOS/Linux):**
```bash
export OPENAI_API_KEY="sk-..."
export CLUSTERING_LLM_PROVIDER="openai"
streamlit run dashboard_enhanced.py
```

**Persistent (add to ~/.bashrc or ~/.zshrc):**
```bash
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
echo 'export CLUSTERING_LLM_PROVIDER="openai"' >> ~/.bashrc
source ~/.bashrc
```

**You should see:**
```
✓ OpenAI API key found
[ClusteringOrchestrator] LLM Mode: OPENAI (GPT-3.5/4)
```

---

## Troubleshooting

### "LLM Mode: RULE_BASED"
This means no LLM is available. The dashboard will still work but use rule-based explanations.

**Fix:**
- Start Ollama: `ollama serve`
- OR set OpenAI key: `$env:OPENAI_API_KEY = "sk-..."`
- Restart dashboard

### "⚠️ No LLM available (ollama)"
Ollama connection failed.

**Fix:**
```powershell
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve

# If running, check firewall/port 11434
```

### "OpenAI error: Unauthorized"
API key is invalid or expired.

**Fix:**
```powershell
# Verify key format (should start with "sk-")
echo $env:OPENAI_API_KEY

# Get new key from https://platform.openai.com/api-keys
```

### Slow LLM Responses
Ollama models run locally, so first response is slower. Subsequent calls are faster.

**Speed comparison:**
- **Ollama (local)**: ~5-10 seconds first call, ~2-3s cached
- **OpenAI (cloud)**: ~1-2 seconds (needs API calls + network)

---

## LLM Configuration in Code

The orchestrator reads these environment variables:

```python
# LLM Provider selection
CLUSTERING_LLM_PROVIDER = os.getenv('CLUSTERING_LLM_PROVIDER', 'ollama')
# Options: 'ollama' (default), 'openai', or 'none'

# OpenAI API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# Format: sk-...
```

### Change Provider Programmatically

```python
import os
os.environ['CLUSTERING_LLM_PROVIDER'] = 'openai'
os.environ['OPENAI_API_KEY'] = 'sk-...'

from orchestrator import ClusteringOrchestrator
orchestrator = ClusteringOrchestrator()
```

---

## What the LLM Analyzes

When LLM is enabled, it receives this context:

```
Algorithm: KMEANS
Silhouette Score: 0.5342
K Value: 3
Inertia: 2341.52

Data shape: (40, 10)
Columns: amount, merchant, category, timestamp, ...

Provide a brief analysis of clustering quality, what it means, 
and recommendations.
```

### Example LLM Response (Ollama llama2)
```
The clustering with K=3 and silhouette score of 0.5342 indicates 
moderate cluster separation. This means:

1. Clusters are reasonably well-defined but have some overlap
2. Some data points are close to cluster boundaries
3. The algorithm found meaningful patterns in your transaction data

For production use, consider:
- Try K=5 to see if finer-grained clustering improves separation
- Check for outliers that might be blurring cluster boundaries
- Consider feature engineering to highlight differences
```

### Example LLM Response (OpenAI GPT-3.5)
```
The silhouette score of 0.5342 with K=3 indicates good cluster 
cohesion. Your 40 transactions are well-separated into 3 risk groups:

Recommendation: APPROVED for production
- Score > 0.5 is considered good separation
- The 10 features provide sufficient information for clustering
- Transaction patterns are consistent within each cluster

If you need finer granularity, test K=5 next.
```

---

## Fallback (Rule-Based)

When **no LLM available**, you get this:

```
## KMeans K=3
**Algorithm**: KMEANS

Silhouette Score: 0.5342
**Quality**: GOOD ✅ - Reasonable cluster structure

### Metrics:
- K: 3
- Inertia: 2341.52

### Recommendations:
✅ This clustering is of good quality and ready for production use.
```

---

## Performance Notes

| Feature | Ollama | OpenAI | Rule-Based |
|---------|--------|--------|-----------|
| **Cost** | FREE | $0.002/1K tokens | FREE |
| **Speed** | 5-10s | 1-2s | Instant |
| **Privacy** | Local only | Sent to cloud | Local only |
| **Offline** | ✅ Yes | ❌ No | ✅ Yes |
| **Quality** | Good (llama2) | Excellent (GPT-4) | Basic |
| **Setup** | Easy | 2 steps | None |

---

## Next Steps

**Try Ollama** (recommended for local development):
1. `ollama pull llama2`
2. `ollama serve`
3. Run dashboard

**Try OpenAI** (recommended for production):
1. Get API key from OpenAI
2. Set `OPENAI_API_KEY` environment variable
3. Set `CLUSTERING_LLM_PROVIDER=openai`
4. Run dashboard

**Stay with Rule-Based** (always works):
- Dashboard works perfectly fine without any LLM
- Uses silhouette score thresholds for quality assessment
