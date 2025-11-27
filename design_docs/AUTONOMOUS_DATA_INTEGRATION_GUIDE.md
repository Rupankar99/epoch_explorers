# Autonomous Data Pipeline - Integration Guide

## What Was Added

Non-breaking, standalone autonomous data exploration pipeline in `src/clusterer/`:

```
src/clusterer/
├── __init__.py                     ← Exports all modules
├── state_manager.py                ← Pipeline state tracking
├── pipeline_agents.py              ← Individual stage agents
├── pipeline_orchestrator.py        ← Main orchestrator
└── example_usage.py                ← Usage examples
```

## Key Features

✅ **Non-breaking**: No modifications to existing code  
✅ **Standalone**: Works independently  
✅ **Optional**: Can integrate with RAG later if desired  
✅ **MVP-ready**: Foundation for future enhancements  

---

## Quick Start

### 1. Basic Usage

```python
import asyncio
from src.clusterer import AutonomousDataPipeline

async def run():
    pipeline = AutonomousDataPipeline(
        use_case="customer_segmentation",
        domain_context="e-commerce"
    )
    
    data = {
        "age": [25, 35, 28, 45],
        "spending": [100, 250, 150, 500]
    }
    
    result = await pipeline.run(data)
    print(result.get_summary())

asyncio.run(run())
```

### 2. Using Convenience Function

```python
from src.clusterer import run_autonomous_pipeline

result = await run_autonomous_pipeline(
    input_data={"col1": [1,2,3], "col2": [10,20,30]},
    use_case="analysis",
    domain_context="domain"
)
```

### 3. Full Control

```python
from src.clusterer import AutonomousDataPipeline

pipeline = AutonomousDataPipeline(
    use_case="incident_clustering",
    domain_context="cybersecurity",
    hitl_enabled=True,      # Enable human checkpoints
    max_iterations=5        # Refinement iterations
)

# Run with custom IDs
result = await pipeline.run(
    input_data=data,
    session_id="custom_session",
    pipeline_id="custom_pipeline"
)

# Check status
status = pipeline.get_status("custom_pipeline")
```

---

## Pipeline Stages

| Stage | Purpose | Output |
|-------|---------|--------|
| **1. Data Acquisition** | Load/ingest data | raw_data |
| **2. Normalization** | Infer schema & normalize | normalized_schema |
| **3. Data Cleaning** | AutoDC workflow | cleaned_data + quality_report |
| **4. Clustering** | K-Means (MVP) / DBSCAN | clustering_results |
| **5. Evaluation** | Select best model | best_clustering |

---

## State Management

Track pipeline execution:

```python
# Get state
state = pipeline.get_pipeline_state("pipeline_id")

# View summary
print(state.get_summary())

# Convert to dict
status_dict = state.to_dict()

# Access specific fields
print(state.current_stage)
print(state.completion_percentage)
print(state.best_clustering.silhouette_score)
print(state.data_quality_report.overall_score)
```

---

## HITL Checkpoints (Human-in-the-Loop)

Three mandatory approval gates when enabled:

1. **Schema Validation**: Review normalized database schema
2. **Data Quality Gate**: Confirm cleaned data is ready
3. **Model Acceptance**: Validate optimal clustering result

```python
pipeline = AutonomousDataPipeline(hitl_enabled=True)
# Will pause at checkpoints and log details for review
```

---

## Error Handling

Pipeline tracks errors in `state.errors_log`:

```python
result = await pipeline.run(data)

if result.errors_log:
    for error in result.errors_log:
        print(f"Stage: {error['stage']}")
        print(f"Error: {error['error']}")
        print(f"Context: {error['context']}")
```

---

## Parallel Execution

Run multiple pipelines simultaneously:

```python
tasks = [
    pipeline.run(data1, pipeline_id="pipeline_1"),
    pipeline.run(data2, pipeline_id="pipeline_2"),
    pipeline.run(data3, pipeline_id="pipeline_3"),
]

results = await asyncio.gather(*tasks)
```

---

## Metrics & Monitoring

Access pipeline metrics:

```python
# Data quality
print(f"Completeness: {state.data_quality_report.completeness}")
print(f"Consistency: {state.data_quality_report.consistency}")
print(f"Overall: {state.data_quality_report.overall_score}")

# Clustering
print(f"Algorithm: {state.best_clustering.algorithm}")
print(f"Clusters: {state.best_clustering.num_clusters}")
print(f"Silhouette: {state.best_clustering.silhouette_score}")

# Execution
print(f"Active Pipelines: {len(pipeline.list_pipelines())}")
```

---

## Future Enhancements (Phase 2+)

### Phase 2: Core Functionality
- [ ] Dual-LLM normalization loops
- [ ] Full AutoDC data cleaning
- [ ] K-Means hyperparameter search
- [ ] DBSCAN clustering
- [ ] Secondary evaluation metrics

### Phase 3: Advanced
- [ ] Dimensionality reduction (PCA/UMAP)
- [ ] HITL implementation (real checkpoints)
- [ ] Error recovery loops
- [ ] Advanced state persistence

### Phase 4: Integration
- [ ] RAG system integration
- [ ] Production monitoring
- [ ] Performance optimization
- [ ] Comprehensive testing

---

## Constraints & Considerations

### Current MVP Limitations
- ✓ Basic 5-stage orchestration
- ✓ State management
- ✓ Error tracking
- ✗ No actual ML algorithms (placeholders)
- ✗ No LLM integration yet
- ✗ HITL checkpoints are auto-approved

### Operational Constraints (Design)
- **Domain Specificity**: Schema inference needs DSK
- **Computational Cost**: Iterative refinement is token-expensive
- **Trust Requirements**: HITL mandatory for production
- **Economic Viability**: Only for mission-critical tasks

### Applicability
❌ NOT suitable for:
- General-purpose analysis
- Simple data tasks
- Cost-sensitive operations
- Arbitrary unstructured data

✅ Suitable for:
- Mission-critical analysis
- Complex multi-step workflows
- Domain-specific data
- High-value problems

---

## Integration with Existing Systems

### With RAG Agent (Optional, Future)

```python
# RAG handles document ingestion and structuring
from src.rag.agents.langgraph_agent import LangGraphRAGAgent

rag_agent = LangGraphRAGAgent()
# RAG → structured tables in vectordb

# Pipeline clusters the structured data
from src.clusterer import AutonomousDataPipeline

pipeline = AutonomousDataPipeline()
# Retrieve structured data from RAG
# Apply clustering pipeline
# Return segmented insights
```

### With Chat Interface (Optional, Future)

```python
# Chat ingests files/text
# System structures via RAG or direct pipeline
# Clustering pipeline can be triggered from admin chat

# Admin Chat → "cluster: knowledge_base"
# → Triggers AutonomousDataPipeline
# → Returns cluster analysis
```

---

## Testing the Implementation

### Run Examples

```bash
cd e:\epoch_explorers
python -m src.clusterer.example_usage
```

### Test Individual Components

```python
# Test state manager
from src.clusterer import StateManager
sm = StateManager()
state = sm.create_state("session_1", "pipeline_1")

# Test agents
from src.clusterer import DataAcquisitionAgent
agent = DataAcquisitionAgent()
# Can be tested independently

# Test orchestrator
from src.clusterer import AutonomousDataPipeline
pipeline = AutonomousDataPipeline()
# Full pipeline testing
```

---

## File Sizes & Complexity

| File | Lines | Purpose |
|------|-------|---------|
| state_manager.py | ~250 | State tracking and metrics |
| pipeline_agents.py | ~280 | Individual stage agents |
| pipeline_orchestrator.py | ~350 | Main orchestrator |
| example_usage.py | ~200 | Usage examples |
| Total | ~1080 | Complete MVP |

**Minimal overhead**: ~1100 LOC for complete orchestration framework

---

## Summary

✅ **Complete MVP** of autonomous unsupervised data pipeline  
✅ **Non-breaking** to existing codebase  
✅ **Standalone** operation or optional RAG integration  
✅ **Foundation** for Phase 2+ enhancements  
✅ **Well-documented** with examples  

**Ready for**: Testing, feedback, and iterative enhancement

---

**Status**: MVP Complete - Ready for Phase 2  
**Next**: Add actual ML algorithms and LLM agents
