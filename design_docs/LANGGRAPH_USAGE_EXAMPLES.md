# LangGraph Pipeline Usage Examples

## Quick Start

### Basic Usage (Async)

```python
import asyncio
from src.clusterer.langgraph_orchestrator import LangGraphDataPipeline

async def main():
    # Create pipeline
    pipeline = LangGraphDataPipeline(
        use_case="market_analysis",
        domain_context="customer segmentation",
        hitl_enabled=True,
        verbose=True
    )
    
    # Prepare input data
    data = {
        "customers": [
            {"id": 1, "age": 25, "income": 50000, "visits": 12},
            {"id": 2, "age": 35, "income": 75000, "visits": 8},
            {"id": 3, "age": 45, "income": 120000, "visits": 25},
            # ... more data
        ]
    }
    
    # Run pipeline
    result = await pipeline.run(
        input_data=data,
        user_query="Find customer segments",
        session_id="session_001"
    )
    
    # Access results
    print(f"Clustering Silhouette Score: {result['clustering_silhouette']:.4f}")
    print(f"Data Quality: {result['data_quality_score']:.4f}")
    print(f"Best Algorithm: {result['final_evaluation']['best_algorithm']}")
    print(f"Total Iterations: {result['iteration_count']}")

# Run
asyncio.run(main())
```

---

## Flow Visualization During Execution

```
[2025-01-28T10:00:00] Starting LangGraph pipeline: pipeline_abc123
[2025-01-28T10:00:05] → Data Acquisition Stage
[2025-01-28T10:15:30] ✓ Acquisition complete: 500 records retrieved
[2025-01-28T10:15:35] → Clustering Stage (Iteration 1)
[2025-01-28T10:20:45] → Clustering Stage: K-Means (k=2-15), DBSCAN (ε search)
[2025-01-28T10:20:50] ✓ Best silhouette score: 0.45 (DBSCAN, ε=0.5)
[2025-01-28T10:20:55] ⏳ HITL: Awaiting clustering validation approval...
[2025-01-28T10:23:00] ✓ Clustering approved, proceeding to normalization
[2025-01-28T10:23:05] → Normalization Stage (Iteration 1)
[2025-01-28T10:23:45] ✓ Schema generated: 4 tables, 12 columns
[2025-01-28T10:23:50] ⏳ HITL: Awaiting schema validation approval...
[2025-01-28T10:25:30] ✓ Schema approved, proceeding to data cleaning
[2025-01-28T10:25:35] → Data Cleaning Stage (Iteration 1)
[2025-01-28T10:26:15] ⟳ Data quality needs improvement, looping back
[2025-01-28T10:26:20] → Data Cleaning Stage (Iteration 2)
[2025-01-28T10:27:05] ✓ Data quality score: 0.87
[2025-01-28T10:27:10] ⏳ HITL: Awaiting data quality gate approval...
[2025-01-28T10:28:45] ✓ Data quality approved, proceeding to evaluation
[2025-01-28T10:28:50] → Evaluation Stage
[2025-01-28T10:28:55] ✓ Best model: DBSCAN (silhouette: 0.65)
[2025-01-28T10:29:00] ⏳ HITL: Awaiting model acceptance approval...
[2025-01-28T10:31:15] ✓ Model approved, pipeline complete!
[2025-01-28T10:31:20] ✓ Pipeline complete. Final stage: evaluation
  Best silhouette score: 0.6500
  Data quality score: 0.8700
  Errors: 0
```

---

## Advanced Usage with Error Handling

```python
import asyncio
from src.clusterer.langgraph_orchestrator import LangGraphDataPipeline

async def advanced_example():
    pipeline = LangGraphDataPipeline(
        use_case="product_clustering",
        domain_context="e-commerce items",
        hitl_enabled=True,
        verbose=True
    )
    
    data = {
        "products": [...]  # Your data
    }
    
    try:
        result = await pipeline.run(
            input_data=data,
            user_query="Cluster products by features"
        )
        
        # Check if pipeline succeeded
        if result.get("last_error"):
            print(f"⚠ Pipeline had errors: {result['last_error']}")
        
        if result.get("current_stage") == "evaluation":
            print("✓ Pipeline completed successfully!")
            
            # Extract insights
            evaluation = result.get("final_evaluation", {})
            print(f"  Algorithm: {evaluation.get('best_algorithm')}")
            print(f"  Silhouette: {result['clustering_silhouette']:.4f}")
            print(f"  Clusters: {evaluation.get('num_clusters')}")
        else:
            print(f"⚠ Pipeline stopped at: {result.get('current_stage')}")
        
        # Check audit trail
        print(f"\nExecution log ({len(result['execution_log'])} entries):")
        for entry in result['execution_log']:
            print(f"  - {entry['stage']}: iteration {entry['iteration']}")
    
    except Exception as e:
        print(f"✗ Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
```

---

## Using the Convenience Function

```python
import asyncio
from src.clusterer.langgraph_orchestrator import run_autonomous_pipeline

async def quick_start():
    # Even simpler one-liner approach
    result = await run_autonomous_pipeline(
        input_data={"data": [...]},
        use_case="general_analysis",
        domain_context="unsupervised learning",
        hitl_enabled=True,
        verbose=True
    )
    
    return result

asyncio.run(quick_start())
```

---

## Pipeline State Inspection

```python
async def inspect_pipeline_state():
    pipeline = LangGraphDataPipeline(verbose=True)
    
    result = await pipeline.run(
        input_data={"data": [...]},
        user_query="Find patterns"
    )
    
    # Inspect final state
    print("=== Final Pipeline State ===")
    print(f"Session ID: {result['session_id']}")
    print(f"Pipeline ID: {result['pipeline_id']}")
    print(f"Current Stage: {result['current_stage']}")
    print(f"Iteration Count: {result['iteration_count']}")
    print(f"\n=== Metrics ===")
    print(f"Silhouette Score: {result['clustering_silhouette']:.4f}")
    print(f"Data Quality: {result['data_quality_score']:.4f}")
    print(f"Schema Valid: {result['schema_validity']}")
    print(f"\n=== Errors ===")
    if result['errors']:
        for error in result['errors']:
            print(f"  - {error}")
    else:
        print("  None!")
    
    print(f"\n=== Execution Timeline ===")
    for stage, timestamp in result['timestamps'].items():
        print(f"  {stage}: {timestamp}")
    
    print(f"\n=== Execution Log ===")
    for entry in result['execution_log']:
        print(f"  Stage: {entry['stage']}, Iter: {entry['iteration']}, Time: {entry['timestamp']}")

asyncio.run(inspect_pipeline_state())
```

---

## Conditional Flow Examples

### Example 1: Clustering Refinement Loop

```
Initial Clustering:
  Silhouette: 0.25 (below 0.3 threshold)
  ↓
HITL Validation: REFINEMENT
  ↓
Loop back to Clustering:
  - Try different hyperparameters
  - K-Means: k increases from 3 to 5
  - Result: Silhouette 0.42 ✓
  ↓
Proceed to Normalization
```

### Example 2: Schema Validation and Refinement

```
Initial Schema:
  Tables: 5, Foreign Keys: 3
  Validation: FAILED (circular dependencies)
  ↓
HITL Validation: REFINEMENT
  ↓
Loop back to Normalization:
  - Dual-LLM detects and fixes cycles
  - Verifier re-validates
  - Result: Valid schema ✓
  ↓
Proceed to Data Cleaning
```

### Example 3: Data Quality Loop

```
Cleaning Iteration 1:
  - Remove 15% missing values
  - Standardize formats
  - Quality: 0.72 (below 0.85 target)
  ↓
Auto-loop Cleaning Iteration 2:
  - Apply advanced imputation
  - Detect outliers
  - Quality: 0.81 (getting better)
  ↓
Auto-loop Cleaning Iteration 3:
  - Final normalization
  - Constraint validation
  - Quality: 0.88 ✓
  ↓
Proceed to Evaluation
```

---

## Integration with Existing Code

The LangGraph orchestrator **doesn't break** existing code because:

1. **Wraps existing agents** (DataAcquisitionAgent, etc.)
2. **Uses same StateManager**
3. **No changes to agent implementations**
4. **Optional import** - works with or without LangGraph

```python
# Old code still works
from src.clusterer.pipeline import Pipeline
pipeline = Pipeline()
result = pipeline.run(data)

# New LangGraph approach (alongside old code)
from src.clusterer.langgraph_orchestrator import LangGraphDataPipeline
graph_pipeline = LangGraphDataPipeline()
result = await graph_pipeline.run(data)
```

---

## Performance Monitoring

```python
import asyncio
import time

async def monitor_performance():
    pipeline = LangGraphDataPipeline(verbose=False)
    
    start_time = time.time()
    
    result = await pipeline.run(
        input_data={"data": [...]},
        user_query="Analyze data"
    )
    
    total_time = time.time() - start_time
    
    print(f"Total pipeline time: {total_time:.2f}s")
    print(f"Per-stage breakdown:")
    
    timestamps = result['timestamps']
    stage_times = {}
    
    stages = ['acquisition', 'clustering', 'normalization', 'cleaning', 'evaluation']
    for i, stage in enumerate(stages):
        key = f"{stage}_completed"
        if key in timestamps:
            if i == 0:
                stage_time = 0  # First stage
            else:
                # Calculate time from previous stage
                prev_key = f"{stages[i-1]}_completed"
                if prev_key in timestamps:
                    prev_time = timestamps[prev_key]
                    curr_time = timestamps[key]
                    # Parse ISO timestamps and calculate diff
                    # (simplified for example)
                    stage_time = "~estimated"
            
            print(f"  {stage}: {stage_time}")
    
    print(f"\nQuality metrics:")
    print(f"  Silhouette: {result['clustering_silhouette']:.4f}")
    print(f"  Data Quality: {result['data_quality_score']:.4f}")
    print(f"  Iterations: {result['iteration_count']}")

asyncio.run(monitor_performance())
```

---

## Deployment Checklist

Before deploying LangGraph pipeline:

- [ ] LangGraph package installed: `pip install langgraph`
- [ ] All agents (Acquisition, Normalization, Cleaning, Clustering, Evaluation) implemented
- [ ] StateManager initialized
- [ ] HITL handlers configured (manual review process)
- [ ] Error handling tested (network, API, LLM failures)
- [ ] Max iterations configured (prevent infinite loops)
- [ ] Logging/monitoring in place
- [ ] Database connections tested
- [ ] LLM service initialized
- [ ] VectorDB initialized (if used in agents)

---

## Configuration Reference

```python
# Minimal configuration
pipeline = LangGraphDataPipeline()

# Full configuration
pipeline = LangGraphDataPipeline(
    use_case="customer_segmentation",           # Application domain
    domain_context="SaaS customer behavior",     # Specific context for LLM
    hitl_enabled=True,                          # Enable human-in-the-loop
    verbose=True                                # Enable detailed logging
)

# Run with options
result = await pipeline.run(
    input_data=raw_data,                        # Required: input data
    user_query="Find customer types",           # Required: business question
    session_id="session_2025_01",               # Optional: unique session ID
    pipeline_id="pipeline_analysis_v1"          # Optional: unique pipeline ID
)
```

---

## Troubleshooting

### LangGraph Not Installed
```
Error: "LangGraph not installed. Using fallback orchestration."
Solution: pip install langgraph
```

### HITL Approval Stuck
```
Check: hitl_approval is None → awaiting human input
Solution: Implement interactive HITL review system
```

### Silhouette Score Too Low
```
If clustering_silhouette < 0.3:
- Data may not be naturally clusterable
- Try different feature engineering
- Consider domain-specific preprocessing
```

### Data Quality Not Improving
```
If data_quality_score stuck below 0.85:
- Max iterations reached (default: 3)
- Increase max_iterations in initial_state
- Review data source quality
```

---

**Status**: ✅ Updated Pipeline  
**Flow**: START → Acquisition → Clustering → Normalization → Cleaning → Evaluation → END  
**HITL Checkpoints**: 4 (Clustering, Schema, Quality, Model)  
**Refinement Loops**: 4 (each stage can loop back)  
**Complexity**: Production-ready for autonomous data exploration
