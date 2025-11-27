"""
State Management for Autonomous Data Pipeline

Tracks pipeline state across multiple nodes without breaking existing code.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json


@dataclass
class PipelineMetrics:
    """Track pipeline execution metrics"""
    stage: str  # "acquisition", "normalization", "cleaning", "clustering"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    quality_score: float = 0.0
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    error_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "stage": self.stage,
            "timestamp": self.timestamp,
            "quality_score": self.quality_score,
            "execution_time_ms": self.execution_time_ms,
            "tokens_used": self.tokens_used,
            "error_count": self.error_count
        }


@dataclass
class DataQualityReport:
    """Data quality assessment"""
    completeness: float = 0.0  # % non-null values
    consistency: float = 0.0   # % consistent format
    accuracy: float = 0.0      # % valid values
    validity: float = 0.0      # % schema-compliant
    
    @property
    def overall_score(self) -> float:
        """Average quality across dimensions"""
        scores = [self.completeness, self.consistency, self.accuracy, self.validity]
        return sum(s for s in scores if s > 0) / len([s for s in scores if s > 0]) if any(scores) else 0.0


@dataclass
class ClusteringResult:
    """Clustering execution result"""
    algorithm: str  # "kmeans" or "dbscan"
    num_clusters: int
    silhouette_score: float
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    cluster_labels: Optional[List[int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineState:
    """
    Complete pipeline state - persists across nodes.
    Non-breaking: independent from existing code.
    """
    # Tracking
    session_id: str
    pipeline_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Data stages
    raw_data: Dict[str, Any] = field(default_factory=dict)
    raw_data_source: Optional[str] = None
    
    normalized_schema: Dict[str, Any] = field(default_factory=dict)
    schema_validation_passed: bool = False
    schema_errors: List[str] = field(default_factory=list)
    
    cleaned_data: Optional[Dict[str, Any]] = None
    data_quality_report: DataQualityReport = field(default_factory=DataQualityReport)
    
    features_processed: Optional[Dict[str, Any]] = None
    dimensionality_reduction_applied: Optional[str] = None  # "pca", "umap", etc
    
    clustering_results: List[ClusteringResult] = field(default_factory=list)
    best_clustering: Optional[ClusteringResult] = None
    
    # Execution tracking
    metrics_history: List[PipelineMetrics] = field(default_factory=list)
    errors_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # HITL flags
    awaiting_schema_validation: bool = False
    awaiting_data_quality_approval: bool = False
    awaiting_model_approval: bool = False
    
    # Configuration
    use_case: str = "general"
    domain_context: str = "unknown"
    max_iterations: int = 5
    hitl_enabled: bool = True
    
    # Status
    current_stage: str = "initialization"
    completion_percentage: float = 0.0
    is_active: bool = True
    
    def log_metric(self, metric: PipelineMetrics):
        """Add metric to history"""
        self.metrics_history.append(metric)
    
    def log_error(self, stage: str, error: str, context: Dict[str, Any] = None):
        """Log error with context"""
        self.errors_log.append({
            "stage": stage,
            "error": error,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def update_stage(self, stage: str, completion: float):
        """Update current execution stage"""
        self.current_stage = stage
        self.completion_percentage = completion
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            "session_id": self.session_id,
            "pipeline_id": self.pipeline_id,
            "current_stage": self.current_stage,
            "completion_percentage": self.completion_percentage,
            "schema_validation_passed": self.schema_validation_passed,
            "data_quality_score": self.data_quality_report.overall_score,
            "best_silhouette_score": self.best_clustering.silhouette_score if self.best_clustering else None,
            "error_count": len(self.errors_log),
            "awaiting_approvals": {
                "schema": self.awaiting_schema_validation,
                "data_quality": self.awaiting_data_quality_approval,
                "model": self.awaiting_model_approval
            }
        }
    
    def get_summary(self) -> str:
        """Human-readable pipeline summary"""
        summary = f"""
Pipeline Status: {self.session_id}
=====================================
Stage: {self.current_stage} ({self.completion_percentage:.0f}% complete)
Use Case: {self.use_case}
Domain: {self.domain_context}

Data Quality: {self.data_quality_report.overall_score:.2f}/1.0
  - Completeness: {self.data_quality_report.completeness:.2f}
  - Consistency: {self.data_quality_report.consistency:.2f}
  - Accuracy: {self.data_quality_report.accuracy:.2f}
  - Validity: {self.data_quality_report.validity:.2f}

Best Clustering: {self.best_clustering.algorithm if self.best_clustering else 'None'}
  - Clusters: {self.best_clustering.num_clusters if self.best_clustering else 'N/A'}
  - Silhouette Score: {self.best_clustering.silhouette_score:.3f if self.best_clustering else 'N/A'}

Awaiting Approvals:
  - Schema Validation: {'YES' if self.awaiting_schema_validation else 'No'}
  - Data Quality: {'YES' if self.awaiting_data_quality_approval else 'No'}
  - Model Acceptance: {'YES' if self.awaiting_model_approval else 'No'}

Errors: {len(self.errors_log)}
{'Metrics Tracked: ' + str(len(self.metrics_history))}
"""
        return summary


class StateManager:
    """Manage pipeline state - non-breaking, standalone"""
    
    def __init__(self):
        self.states: Dict[str, PipelineState] = {}
    
    def create_state(
        self,
        session_id: str,
        pipeline_id: str,
        use_case: str = "general",
        domain_context: str = "unknown",
        hitl_enabled: bool = True
    ) -> PipelineState:
        """Create new pipeline state"""
        state = PipelineState(
            session_id=session_id,
            pipeline_id=pipeline_id,
            use_case=use_case,
            domain_context=domain_context,
            hitl_enabled=hitl_enabled
        )
        self.states[pipeline_id] = state
        return state
    
    def get_state(self, pipeline_id: str) -> Optional[PipelineState]:
        """Get pipeline state by ID"""
        return self.states.get(pipeline_id)
    
    def update_state(self, pipeline_id: str, **kwargs):
        """Update state attributes"""
        state = self.get_state(pipeline_id)
        if state:
            for key, value in kwargs.items():
                if hasattr(state, key):
                    setattr(state, key, value)
    
    def save_state(self, pipeline_id: str, filepath: str):
        """Persist state to JSON"""
        state = self.get_state(pipeline_id)
        if state:
            with open(filepath, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)
    
    def load_state(self, pipeline_id: str, filepath: str):
        """Restore state from JSON"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        # Basic restoration - can be enhanced
        state = self.get_state(pipeline_id)
        if state:
            state.current_stage = data.get("current_stage", state.current_stage)
            state.completion_percentage = data.get("completion_percentage", 0.0)
