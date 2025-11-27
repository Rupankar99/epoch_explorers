# Autonomous Unsupervised Data Exploration Pipeline
## LangGraph-Orchestrated Data-to-Insight Architecture

**Status**: ✅ Design Document & Modular Architecture  
**Folder**: `src/clusterer/`  
**Integration**: Non-breaking, additive modules  

---

## I. Executive Summary

This document outlines an autonomous data science pipeline capable of:
- Independent data sourcing and ingestion
- Structured relational schema inference and normalization
- Automated data preparation and feature engineering
- Multi-algorithmic unsupervised clustering (K-Means, DBSCAN)
- Objective evaluation and model selection via Silhouette scores
- Human-in-the-loop validation at critical gates

**Key Finding**: Technically feasible but operationally constrained by:
1. **Domain-specificity requirements** for schema validation
2. **High computational cost** from iterative refinement loops
3. **Trust requirements** for production deployment

---

## II. Architecture Components

### A. Orchestration Framework: LangGraph

**Role**: State machine managing complex, cyclical workflows

```
LangGraph Workflow:
├─ StateGraph: Persistent memory across nodes
├─ Supervisor Agent: Routing and control flow
├─ Conditional Edges: Loops for refinement
├─ ToolNodes: Data processing, ML execution
└─ Error Handlers: Self-correction via feedback loops
```

**Benefits**:
- Durable execution with state persistence
- Cyclical loops for iterative refinement
- Non-linear decision making
- Error recovery and self-correction

---

## III. Pipeline Stages

### Stage 1: Data Acquisition
- Web scraping / API integration
- Raw data pool creation
- Intermediate representation

### Stage 2: Structured Data Inference (Normalization)
- Unstructured → Structured conversion
- Dual-LLM self-refinement for schema validation
- 3NF normalization enforcement
- SQLite DDL/DML execution

### Stage 3: Data Preparation
- AutoDC: Automated data cleaning
- Feature relation analysis
- Dimensionality reduction (PCA/UMAP)

### Stage 4: Unsupervised Learning
- K-Means hyperparameter search
- DBSCAN optimization
- Silhouette score calculation
- Model competitive evaluation

### Stage 5: Research & Exploration
- Human validation checkpoint
- SQL-based analysis layer
- Segment-based insights

---

## IV. Critical Components

### A. State Management
```python
class PipelineState:
    """Graph state tracking"""
    raw_data: Dict[str, Any]
    normalized_schema: Dict[str, Any]
    cleaned_data: pd.DataFrame
    features_reduced: pd.DataFrame
    clustering_results: Dict[str, Any]
    silhouette_scores: List[float]
    errors_log: List[str]
    quality_metrics: Dict[str, float]
```

### B. Human-in-the-Loop Checkpoints
1. **Schema Validation**: Human reviews normalized schema
2. **Data Quality Gate**: Confirmation post-cleaning
3. **Model Acceptance**: Final clustering result validation

### C. Key Metrics
- **Silhouette Score**: Range [-1, +1], optimal clustering measure
- **Data Quality Dimensions**: Completeness, Consistency, Accuracy, Validity
- **Normalization Accuracy**: Foreign key integrity, 3NF compliance

---

## V. Constraints & Applicability

### Constraints
❌ **General Purpose**: NOT suitable for arbitrary use cases  
❌ **Cost**: High token consumption, expensive for simple tasks  
❌ **Domain Knowledge**: Requires DSK for schema validation  
❌ **Trust Gap**: HITL mandatory for production deployment  

### Suitable For
✅ **Mission-critical** data problems  
✅ **High-value** analysis where cost justified  
✅ **Domain-specific** data with known structure patterns  
✅ **Iterative** exploration workflows  

---

## VI. Implementation Architecture

### File Structure (Non-Breaking)
```
src/clusterer/
├── __init__.py (existing)
├── orchestrator/
│   ├── __init__.py
│   ├── pipeline_orchestrator.py
│   └── state_manager.py
├── agents/
│   ├── __init__.py
│   ├── acquisition_agent.py
│   ├── normalization_agent.py
│   ├── cleaning_agent.py
│   ├── clustering_agent.py
│   └── evaluation_agent.py
├── tools/
│   ├── __init__.py
│   ├── data_tools.py
│   ├── ml_tools.py
│   └── sql_tools.py
├── schemas/
│   ├── __init__.py
│   └── normalization_schemas.py
└── checkpoints/
    ├── __init__.py
    └── hitl_manager.py
```

---

## VII. Usage Example

### Basic Pipeline Invocation

```python
from src.clusterer.orchestrator import AutonomousDataPipeline

# Initialize
pipeline = AutonomousDataPipeline(
    use_case="customer_segmentation",
    domain_context="E-commerce"
)

# Execute with HITL checkpoints
result = pipeline.run(
    input_data="https://api.example.com/data",
    hitl_checkpoints=True,
    max_iterations=5
)

# Access results
print(f"Optimal clusters: {result.best_clustering}")
print(f"Quality score: {result.silhouette_score}")
print(f"Insights: {result.segment_analysis}")
```

---

## VIII. Non-Breaking Integration

### Why This Doesn't Break Existing Code

✅ **Isolated folder structure**: All code in `src/clusterer/`  
✅ **No modifications to existing imports**: Uses relative imports only  
✅ **Optional integration**: Can be used independently or with RAG  
✅ **Additive only**: No modifications to parent modules  
✅ **Gradual adoption**: Can test with small datasets first  

### Integration with Existing Systems

**With RAG Agent**: Data → RAG ingestion → Structured tables → Clustering

```python
# RAG ingests data → creates tables
from src.rag.agents.langgraph_agent import LangGraphRAGAgent

# Clustering pipeline uses those tables
from src.clusterer.orchestrator import AutonomousDataPipeline

# Optional combined workflow
rag_agent = LangGraphRAGAgent()
pipeline = AutonomousDataPipeline(vectordb=rag_agent.vectordb_service)
```

---

## IX. Development Roadmap

### Phase 1: Foundation (MVP)
- [ ] State manager implementation
- [ ] Basic orchestrator scaffold
- [ ] Data acquisition agent (simple)
- [ ] Documentation

### Phase 2: Core Functionality
- [ ] Normalization agent with dual-LLM loop
- [ ] Data cleaning agent (AutoDC)
- [ ] Clustering agent (K-Means)
- [ ] Evaluation and metrics

### Phase 3: Advanced Features
- [ ] DBSCAN clustering
- [ ] Dimensionality reduction (PCA/UMAP)
- [ ] HITL checkpoint system
- [ ] Error recovery loops

### Phase 4: Production Readiness
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation & examples
- [ ] Integration with existing systems

---

## X. Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Orchestration | LangGraph | Stateful workflow management |
| LLM | OpenAI/Ollama | Schema inference, cleaning decisions |
| ML | Scikit-learn | K-Means, DBSCAN clustering |
| Data Processing | Pandas | Feature engineering |
| Dimension Reduction | PCA/UMAP | Feature space optimization |
| Evaluation | Silhouette, Davies-Bouldin | Clustering quality metrics |
| Database | SQLite | Structured data storage |
| Validation | Custom validators | Schema and data integrity |

---

## XI. Success Metrics

| Metric | Target | Description |
|--------|--------|---|
| Silhouette Score | > 0.50 | Good clustering separation |
| Schema Accuracy | > 95% | Correct normalization |
| Data Quality | > 90% | Completeness + Consistency |
| Pipeline Success Rate | > 80% | End-to-end completion |
| HITL Approval Rate | > 85% | Human validation passes |

---

## XII. References & Inspiration

- **LangGraph**: Stateful agent orchestration
- **Miffie**: Dual-LLM schema normalization
- **Self-Regeneration Machines**: Holistic data structuring
- **AutoDC**: Autonomous data cleaning workflows
- **Silhouette Score**: Unsupervised clustering evaluation
- **RAG-to-SQL**: Iterative SQL error correction

---

**Document Version**: 1.0  
**Status**: Design Phase Complete  
**Next Step**: Implementation Phase 1 (State Manager)
