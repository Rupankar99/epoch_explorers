# LangGraph Clusterer Quick Start

## TL;DR

**YES, we're using LangGraph now!** 

```python
# NEW: Use LangGraph for stateful, cyclical workflows
from src.clusterer import LangGraphDataPipeline

pipeline = LangGraphDataPipeline(hitl_enabled=True)
result = await pipeline.run(input_data)

# OLD: Still works, manual orchestration
from src.clusterer import AutonomousDataPipeline

pipeline = AutonomousDataPipeline()
result = await pipeline.run(input_data)
```

Both work! No breaking changes.

---

## Installation

```bash
# LangGraph is optional (graceful fallback if missing)
pip install langgraph

# Verify
python -c "from langgraph.graph import StateGraph; print('✓ LangGraph ready')"
```

---

## Usage Examples

### Example 1: Basic LangGraph Usage

```python
from src.clusterer import LangGraphDataPipeline
import asyncio

async def main():
    pipeline = LangGraphDataPipeline(
        use_case="incident_analysis",
        domain_context="cybersecurity",
        hitl_enabled=True,
        verbose=True
    )
    
    input_data = {
        "incidents": [...],
        "features": ["severity", "type", "source", ...]
    }
    
    result = await pipeline.run(
        input_data=input_data,
        user_query="Identify patterns in security incidents"
    )
    
    print(f"✓ Pipeline completed!")
    print(f"  Final stage: {result['current_stage']}")
    print(f"  Quality score: {result['data_quality_score']:.2%}")
    print(f"  Silhouette: {result['clustering_silhouette']:.2f}")
    print(f"  Iterations: {result['iteration_count']}")

asyncio.run(main())
```

### Example 2: With Error Handling

```python
try:
    result = await pipeline.run(input_data)
    
    if result.get("errors"):
        print(f"⚠ Pipeline had errors:")
        for err in result["errors"]:
            print(f"  - {err}")
    
    if result.get("current_stage") == "END":
        print("✓ Successfully completed!")
    else:
        print(f"⚠ Stopped at: {result['current_stage']}")

except Exception as e:
    print(f"✗ Pipeline failed: {e}")
```

### Example 3: Examining Execution Log

```python
result = await pipeline.run(input_data)

print("Execution Timeline:")
print("=" * 60)
for log in result["execution_log"]:
    stage = log["stage"]
    timestamp = log["timestamp"]
    
    if "iteration" in log:
        print(f"[{timestamp}] {stage} (iteration {log['iteration']})")
    else:
        print(f"[{timestamp}] {stage}")
    
    if "quality" in log:
        print(f"           Quality: {log['quality']:.2%}")
    if "silhouette" in log:
        print(f"           Silhouette: {log['silhouette']:.2f}")
    if "valid" in log:
        print(f"           Valid: {log['valid']}")

print("\nTimestamps:")
for stage, ts in result["timestamps"].items():
    print(f"  {stage}: {ts}")
```

### Example 4: Using Without HITL (Faster)

```python
# HITL disabled - auto-approval for faster execution
pipeline = LangGraphDataPipeline(hitl_enabled=False)

result = await pipeline.run(input_data)

# Still get full metrics
print(f"Quality: {result['data_quality_score']}")
print(f"Silhouette: {result['clustering_silhouette']}")
```

### Example 5: With Fallback (No LangGraph Required)

```python
from src.clusterer import HAS_LANGGRAPH_ORCHESTRATOR

if HAS_LANGGRAPH_ORCHESTRATOR:
    from src.clusterer import LangGraphDataPipeline
    pipeline = LangGraphDataPipeline()
else:
    # Fallback to manual orchestration
    from src.clusterer import AutonomousDataPipeline
    pipeline = AutonomousDataPipeline()

result = await pipeline.run(input_data)
```

---

## Architecture at a Glance

### What LangGraph Gives Us

```
┌─────────────────────────────────────────────────┐
│          LangGraph StateGraph                   │
├─────────────────────────────────────────────────┤
│ • Persistent state across all nodes             │
│ • Conditional routing based on metrics          │
│ • Built-in cycles for iteration                 │
│ • Automatic error recovery                      │
│ • Complete audit trail                          │
└─────────────────────────────────────────────────┘
         ↓           ↓           ↓
    [Nodes]   [Conditional]  [Cycles]
         ↓           ↓           ↓
  Agents    Routing    Refinement
```

### State Flow

```
START
  ↓
Data Acquisition
  │ output: raw_data
  ↓
Normalization
  │ output: normalized_schema
  ↓ (conditional)
  ├─→ Schema Valid? → Data Cleaning
  ├─→ Invalid? → Loop back (max 3x)
  └─→ Rejected? → END
  ↓
Data Cleaning
  │ output: cleaned_data
  ↓ (conditional)
  ├─→ Quality > 85%? → Clustering
  ├─→ Lower? → Loop back (max 3x)
  └─→ Rejected? → END
  ↓
Clustering
  │ output: cluster_results
  ↓
Evaluation
  │ output: final_evaluation
  ↓ (conditional)
  ├─→ Silhouette > 0.5? → END (success)
  ├─→ Lower? → Loop back to Clustering (max 3x)
  └─→ Rejected? → END (fail)
```

---

## State Fields

```python
# Session info
state["session_id"]       # Unique session identifier
state["pipeline_id"]      # Unique pipeline run identifier

# Inputs
state["raw_data"]         # Original input data
state["user_query"]       # User's question/request

# Outputs per stage
state["structured_data"]  # After acquisition
state["normalized_schema"] # After normalization
state["cleaned_data"]     # After cleaning
state["cluster_results"]  # After clustering
state["final_evaluation"] # After evaluation

# Metrics
state["data_quality_score"]     # 0.0-1.0
state["schema_validity"]        # Boolean
state["clustering_silhouette"]  # Silhouette score

# Control
state["current_stage"]       # Current node name
state["iteration_count"]     # Refinement loops so far
state["requires_refinement"] # Should we loop?
state["hitl_approval"]       # Human decision (if HITL enabled)

# Audit
state["execution_log"]       # List of all steps executed
state["timestamps"]          # Timing per stage
state["errors"]              # Any errors encountered
```

---

## Return Value Example

```python
result = {
    "session_id": "session_a1b2c3d4",
    "pipeline_id": "pipeline_e5f6g7h8",
    "current_stage": "END",
    "iteration_count": 2,
    "data_quality_score": 0.88,
    "clustering_silhouette": 0.72,
    "errors": [],
    "execution_log": [
        {
            "stage": "data_acquisition",
            "timestamp": "2025-01-28T15:30:00Z"
        },
        {
            "stage": "normalization",
            "iteration": 1,
            "valid": False,
            "timestamp": "2025-01-28T15:31:00Z"
        },
        {
            "stage": "normalization",
            "iteration": 2,
            "valid": True,
            "timestamp": "2025-01-28T15:32:00Z"
        },
        {
            "stage": "data_cleaning",
            "iteration": 1,
            "quality": 0.88,
            "timestamp": "2025-01-28T15:33:00Z"
        },
        {
            "stage": "clustering",
            "iteration": 1,
            "silhouette": 0.72,
            "timestamp": "2025-01-28T15:35:00Z"
        },
        {
            "stage": "evaluation",
            "timestamp": "2025-01-28T15:36:00Z"
        }
    ],
    "timestamps": {
        "start": "2025-01-28T15:30:00Z",
        "acquisition_completed": "2025-01-28T15:30:30Z",
        "normalization_completed_1": "2025-01-28T15:31:00Z",
        "normalization_completed_2": "2025-01-28T15:32:00Z",
        "cleaning_completed_1": "2025-01-28T15:33:00Z",
        "clustering_completed_1": "2025-01-28T15:35:00Z",
        "evaluation_completed": "2025-01-28T15:36:00Z"
    }
}
```

---

## Comparison: With vs Without LangGraph

### Without LangGraph (Basic Flow)
```python
async def run_basic():
    data = await acquisition.execute(input_data)
    schema = await normalization.execute(data)
    cleaned = await cleaning.execute(schema)
    clusters = await clustering.execute(cleaned)
    eval = await evaluation.execute(clusters)
    return eval
```
- ❌ No cycles
- ❌ State lost between steps
- ❌ Manual error handling
- ❌ Hard to add decisions

### With LangGraph (Smart Flow)
```python
async def run_langgraph():
    pipeline = LangGraphDataPipeline()
    return await pipeline.run(input_data)
```
- ✅ Automatic cycles (max 3 iterations)
- ✅ Full state persistence
- ✅ Built-in error recovery
- ✅ Conditional routing
- ✅ HITL checkpoints
- ✅ Complete audit trail

---

## Key Differences

| Aspect | Basic | LangGraph |
|--------|-------|-----------|
| **State** | Lost between steps | Persisted across all steps |
| **Cycles** | Manual if/else | Automatic via conditional edges |
| **Iterations** | Hard to track | All logged in execution_log |
| **Refinement** | Manual loop code | Built-in routing |
| **HITL** | Not supported | Checkpoint nodes included |
| **Metrics** | Manual calculation | In state, updated per step |
| **Routing** | If/else chains | Conditional edge functions |
| **Audit** | Manual logging | Automatic timestamps & logs |

---

## Common Patterns

### Pattern 1: Check if Successful
```python
result = await pipeline.run(input_data)

if result["current_stage"] == "END" and not result["errors"]:
    print("✓ Success!")
else:
    print(f"✗ Failed at stage: {result['current_stage']}")
```

### Pattern 2: Get Best Metrics
```python
silhouette = result["clustering_silhouette"]
quality = result["data_quality_score"]

print(f"Quality: {quality:.1%}")
print(f"Clustering: {silhouette:.2f}")

if silhouette > 0.7 and quality > 0.85:
    print("→ Results are excellent!")
elif silhouette > 0.5 and quality > 0.75:
    print("→ Results are acceptable")
else:
    print("→ Results need improvement")
```

### Pattern 3: Inspect Iterations
```python
log = result["execution_log"]

refinements = [x for x in log if "iteration" in x and x["iteration"] > 1]

print(f"Total refinements: {len(refinements)}")

for ref in refinements:
    print(f"  {ref['stage']}: iteration {ref['iteration']}")
```

### Pattern 4: Timeline View
```python
ts = result["timestamps"]

start = datetime.fromisoformat(ts["start"])

for stage in ["acquisition", "normalization", "cleaning", "clustering", "evaluation"]:
    key = f"{stage}_completed"
    if key in ts:
        stage_ts = datetime.fromisoformat(ts[key])
        elapsed = (stage_ts - start).total_seconds()
        print(f"{stage:20} {elapsed:6.1f}s")
```

---

## Troubleshooting

### LangGraph Not Found
```python
# Automatic fallback happens
# If you want to know:
from src.clusterer import HAS_LANGGRAPH_ORCHESTRATOR

if not HAS_LANGGRAPH_ORCHESTRATOR:
    print("⚠ LangGraph not available, using fallback")
    print("  Install: pip install langgraph")
```

### Pipeline Stopped Early
```python
result = await pipeline.run(input_data)

if result["current_stage"] != "END":
    print(f"⚠ Stopped at: {result['current_stage']}")
    print(f"Last error: {result['last_error']}")
    print(f"All errors: {result['errors']}")
```

### Too Many Iterations
```python
# LangGraph limits iterations to prevent infinite loops (default: 3)
result = await pipeline.run(input_data)

if result["iteration_count"] >= 3:
    print("⚠ Max iterations reached")
    print(f"Last silhouette: {result['clustering_silhouette']}")
    # Consider: different parameters, data preprocessing, etc.
```

---

## Integration with Existing Code

### Add to Your RAG Agent
```python
from src.rag.agents.langgraph_agent import LangGraphRAGAgent
from src.clusterer import LangGraphDataPipeline

rag_agent = LangGraphRAGAgent()
cluster_pipeline = LangGraphDataPipeline()

# Use both together
rag_results = await rag_agent.invoke({"query": "..."})
cluster_results = await cluster_pipeline.run(rag_results)
```

### Use in Chat Interface
```python
from src.rag.chat import ChatRAGInterface
from src.clusterer import LangGraphDataPipeline

chat = ChatRAGInterface(agent.ask_question)
pipeline = LangGraphDataPipeline()

# Via admin chat command
response = await chat.process_message(
    text="cluster_analyze: /path/to/data.csv",
    session_id=session_id
)
```

---

## Summary

✅ **LangGraph is now integrated** into the clusterer  
✅ **Fully backward compatible** - old code still works  
✅ **Optional** - graceful fallback if not installed  
✅ **Production ready** with HITL, cycles, and audit trail  

**Use it for:**
- Complex workflows
- Iterative refinement
- Critical decisions
- Complete audit trails

**Status**: Ready for production! 🚀
