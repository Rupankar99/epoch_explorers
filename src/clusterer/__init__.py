"""
Autonomous Data Exploration Clusterer

Autonomous unsupervised learning pipeline with LangGraph orchestration.
Non-breaking additive module.
"""

# Core exports - MVP
from .state_manager import (
    PipelineState,
    StateManager,
    PipelineMetrics,
    DataQualityReport,
    ClusteringResult
)

from .pipeline_agents import (
    PipelineAgent,
    DataAcquisitionAgent,
    NormalizationAgent,
    CleaningAgent,
    ClusteringAgent,
    EvaluationAgent
)

# Data sources - Web APIs and external data (NEW - optional, non-breaking)
from .data_sources import (
    DataSourceType,
    DataSourceConfig,
    APIRequest,
    APIResponse,
    WebDataSource,
    DataSourceFactory,
    fetch_from_api,
    fetch_from_csv
)

# LangGraph-powered orchestration (NEW - optional, non-breaking)
try:
    from .langgraph_orchestrator import (
        LangGraphDataPipeline,
        GraphState,
        run_autonomous_pipeline as run_langgraph_pipeline
    )
    HAS_LANGGRAPH_ORCHESTRATOR = True
except ImportError:
    HAS_LANGGRAPH_ORCHESTRATOR = False

__all__ = [
    # State management
    "PipelineState",
    "StateManager",
    "PipelineMetrics",
    "DataQualityReport",
    "ClusteringResult",
    
    # Agents
    "PipelineAgent",
    "DataAcquisitionAgent",
    "NormalizationAgent",
    "CleaningAgent",
    "ClusteringAgent",
    "EvaluationAgent",
    
    # Data sources
    "DataSourceType",
    "DataSourceConfig",
    "APIRequest",
    "APIResponse",
    "WebDataSource",
    "DataSourceFactory",
    "fetch_from_api",
    "fetch_from_csv"
]

__version__ = "0.1.0"
__status__ = "MVP - Foundation Phase"
