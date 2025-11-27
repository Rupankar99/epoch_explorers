"""
LangGraph-Powered Data Pipeline Orchestrator

Implements actual LangGraph StateGraph for autonomous unsupervised data exploration.
Wraps existing pipeline code without breaking functionality.

Features:
- StateGraph for persistent state management
- Conditional edges for intelligent routing
- Cyclical workflows for iterative refinement
- Tool nodes for specialized operations
"""

from typing import Any, Dict, List, Optional, TypedDict, Annotated
from dataclasses import dataclass, field, asdict
from datetime import datetime
import asyncio
import json

try:
    from langgraph.graph import StateGraph, START, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    print("WARNING: LangGraph not installed. Using fallback orchestration.")

from .state_manager import PipelineState, StateManager
from .pipeline_agents import (
    DataAcquisitionAgent,
    NormalizationAgent,
    CleaningAgent,
    ClusteringAgent,
    EvaluationAgent
)


class GraphState(TypedDict, total=False):
    """LangGraph state definition for data pipeline"""
    
    # Session info
    session_id: str
    pipeline_id: str
    
    # Input/Output
    raw_data: Dict[str, Any]
    user_query: str
    
    # Stage outputs
    structured_data: Dict[str, Any]
    normalized_schema: Dict[str, Any]
    cleaned_data: Dict[str, Any]
    cluster_results: Dict[str, Any]
    final_evaluation: Dict[str, Any]
    
    # State tracking
    current_stage: str
    iteration_count: int
    max_iterations: int
    
    # Quality metrics
    data_quality_score: float
    schema_validity: bool
    clustering_silhouette: float
    
    # Control flow
    proceed_to_next: bool
    requires_refinement: bool
    hitl_approval: Optional[bool]
    
    # Error handling
    errors: List[str]
    last_error: Optional[str]
    
    # Audit trail
    execution_log: List[Dict[str, Any]]
    timestamps: Dict[str, str]


@dataclass
class LangGraphDataPipeline:
    """
    LangGraph-based autonomous data pipeline orchestrator.
    
    Architecture:
    - START → DataAcquisition → Normalization → DataCleaning → Clustering → Evaluation → END
    - Conditional edges for refinement loops
    - HITL checkpoints for critical decisions
    """
    
    use_case: str = "general"
    domain_context: str = "unknown"
    hitl_enabled: bool = True
    verbose: bool = True
    
    # Lazy-initialized graph
    _graph: Optional[Any] = field(default=None, init=False, repr=False)
    _state_manager: Optional[StateManager] = field(default=None, init=False, repr=False)
    _agents: Optional[Dict[str, Any]] = field(default=None, init=False, repr=False)
    
    def __post_init__(self):
        """Initialize after dataclass creation"""
        self._state_manager = StateManager()
        self._agents = {
            "acquisition": DataAcquisitionAgent(),
            "normalization": NormalizationAgent(),
            "cleaning": CleaningAgent(),
            "clustering": ClusteringAgent(),
            "evaluation": EvaluationAgent()
        }
        
        if HAS_LANGGRAPH:
            self._graph = self._build_graph()
    
    def _log(self, message: str):
        """Log if verbose enabled"""
        if self.verbose:
            timestamp = datetime.now().isoformat()
            print(f"[{timestamp}] {message}")
    
    def _build_graph(self) -> "StateGraph":
        """
        Build LangGraph StateGraph for data pipeline.
        
        Pipeline flow:
        START → DataAcquisition → Clustering → Normalization → DataCleaning → Evaluation → END
        
        With conditional edges for refinement loops and HITL checkpoints.
        
        Returns:
            Compiled StateGraph
        """
        if not HAS_LANGGRAPH:
            raise RuntimeError("LangGraph not installed")
        
        graph = StateGraph(GraphState)
        
        # Add nodes
        graph.add_node("data_acquisition", self._node_data_acquisition)
        graph.add_node("clustering", self._node_clustering)
        graph.add_node("normalization", self._node_normalization)
        graph.add_node("data_cleaning", self._node_data_cleaning)
        graph.add_node("evaluation", self._node_evaluation)
        graph.add_node("hitl_clustering_validation", self._node_hitl_clustering)
        graph.add_node("hitl_schema_validation", self._node_hitl_schema)
        graph.add_node("hitl_data_quality_gate", self._node_hitl_quality)
        graph.add_node("hitl_model_acceptance", self._node_hitl_model)
        
        # Main flow: START → DataAcquisition
        graph.add_edge(START, "data_acquisition")
        
        # DataAcquisition → Clustering (unsupervised learning)
        graph.add_edge("data_acquisition", "clustering")
        
        # Clustering → HITL Clustering Validation
        graph.add_edge("clustering", "hitl_clustering_validation")
        
        # Conditional: clustering validation pass/fail
        graph.add_conditional_edges(
            "hitl_clustering_validation",
            self._route_after_clustering_validation,
            {
                "approved": "normalization",
                "refinement": "clustering",
                "rejected": END
            }
        )
        
        # Clustering Validation Approved → Normalization
        graph.add_edge("hitl_clustering_validation", "normalization")
        
        # Normalization → HITL Schema Validation
        graph.add_edge("normalization", "hitl_schema_validation")
        
        # Conditional: schema validation pass/fail
        graph.add_conditional_edges(
            "hitl_schema_validation",
            self._route_after_schema_validation,
            {
                "approved": "data_cleaning",
                "refinement": "normalization",
                "rejected": END
            }
        )
        
        # Data Cleaning → HITL Quality Gate
        graph.add_edge("data_cleaning", "hitl_data_quality_gate")
        
        # Conditional: quality gate pass/fail
        graph.add_conditional_edges(
            "hitl_data_quality_gate",
            self._route_after_quality_gate,
            {
                "approved": "evaluation",
                "refinement": "data_cleaning",
                "rejected": END
            }
        )
        
        # Evaluation → HITL Model Acceptance
        graph.add_edge("evaluation", "hitl_model_acceptance")
        
        # Conditional: model acceptance pass/fail
        graph.add_conditional_edges(
            "hitl_model_acceptance",
            self._route_after_model_acceptance,
            {
                "approved": END,
                "refinement": "clustering",
                "rejected": END
            }
        )
        
        # Compile graph
        return graph.compile()
    
    # ========== Node Implementations ==========
    
    def _node_data_acquisition(self, state: GraphState) -> Dict[str, Any]:
        """Data acquisition node"""
        self._log(f"→ Data Acquisition Stage")
        
        try:
            result = self._agents["acquisition"].execute({
                "query": state.get("user_query", ""),
                "use_case": self.use_case
            })
            
            return {
                "current_stage": "data_acquisition",
                "raw_data": result.get("data"),
                "data_quality_score": result.get("quality_score", 0.5),
                "proceed_to_next": True,
                "timestamps": {
                    **state.get("timestamps", {}),
                    "acquisition_completed": datetime.now().isoformat()
                }
            }
        except Exception as e:
            self._log(f"✗ Data Acquisition Failed: {str(e)}")
            return {
                "current_stage": "data_acquisition",
                "proceed_to_next": False,
                "errors": [*state.get("errors", []), str(e)],
                "last_error": str(e)
            }
    
    def _node_normalization(self, state: GraphState) -> Dict[str, Any]:
        """Normalization node with dual-LLM loop"""
        self._log(f"→ Normalization Stage (Iteration {state.get('iteration_count', 0)})")
        
        try:
            result = self._agents["normalization"].execute({
                "data": state.get("raw_data", {}),
                "domain": self.domain_context,
                "target_schema": "3NF"
            })
            
            iteration = state.get("iteration_count", 0) + 1
            
            return {
                "current_stage": "normalization",
                "normalized_schema": result.get("schema"),
                "schema_validity": result.get("is_valid", False),
                "iteration_count": iteration,
                "requires_refinement": not result.get("is_valid", False),
                "timestamps": {
                    **state.get("timestamps", {}),
                    f"normalization_completed_{iteration}": datetime.now().isoformat()
                },
                "execution_log": [
                    *state.get("execution_log", []),
                    {
                        "stage": "normalization",
                        "iteration": iteration,
                        "valid": result.get("is_valid", False),
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
        except Exception as e:
            self._log(f"✗ Normalization Failed: {str(e)}")
            return {
                "current_stage": "normalization",
                "requires_refinement": True,
                "errors": [*state.get("errors", []), str(e)],
                "last_error": str(e)
            }
    
    def _node_data_cleaning(self, state: GraphState) -> Dict[str, Any]:
        """Data cleaning node (AutoDC workflow)"""
        self._log(f"→ Data Cleaning Stage (Iteration {state.get('iteration_count', 0)})")
        
        try:
            result = self._agents["cleaning"].execute({
                "data": state.get("raw_data", {}),
                "schema": state.get("normalized_schema", {}),
                "target_quality": 0.85
            })
            
            iteration = state.get("iteration_count", 0) + 1
            
            return {
                "current_stage": "data_cleaning",
                "cleaned_data": result.get("data"),
                "data_quality_score": result.get("quality_score", 0.5),
                "iteration_count": iteration,
                "requires_refinement": result.get("quality_score", 0.5) < 0.85,
                "timestamps": {
                    **state.get("timestamps", {}),
                    f"cleaning_completed_{iteration}": datetime.now().isoformat()
                },
                "execution_log": [
                    *state.get("execution_log", []),
                    {
                        "stage": "data_cleaning",
                        "iteration": iteration,
                        "quality": result.get("quality_score", 0.5),
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
        except Exception as e:
            self._log(f"✗ Data Cleaning Failed: {str(e)}")
            return {
                "current_stage": "data_cleaning",
                "requires_refinement": True,
                "errors": [*state.get("errors", []), str(e)],
                "last_error": str(e)
            }
    
    def _node_clustering(self, state: GraphState) -> Dict[str, Any]:
        """Clustering node with hyperparameter search"""
        self._log(f"→ Clustering Stage (Iteration {state.get('iteration_count', 0)})")
        
        try:
            result = self._agents["clustering"].execute({
                "data": state.get("cleaned_data", {}),
                "algorithms": ["kmeans", "dbscan"],
                "optimize_metric": "silhouette"
            })
            
            iteration = state.get("iteration_count", 0) + 1
            
            return {
                "current_stage": "clustering",
                "cluster_results": result.get("models"),
                "clustering_silhouette": result.get("best_silhouette", 0.0),
                "iteration_count": iteration,
                "requires_refinement": result.get("best_silhouette", 0.0) < 0.5,
                "timestamps": {
                    **state.get("timestamps", {}),
                    f"clustering_completed_{iteration}": datetime.now().isoformat()
                },
                "execution_log": [
                    *state.get("execution_log", []),
                    {
                        "stage": "clustering",
                        "iteration": iteration,
                        "silhouette": result.get("best_silhouette", 0.0),
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
        except Exception as e:
            self._log(f"✗ Clustering Failed: {str(e)}")
            return {
                "current_stage": "clustering",
                "requires_refinement": True,
                "errors": [*state.get("errors", []), str(e)],
                "last_error": str(e)
            }
    
    def _node_evaluation(self, state: GraphState) -> Dict[str, Any]:
        """Evaluation node for model selection"""
        self._log(f"→ Evaluation Stage")
        
        try:
            result = self._agents["evaluation"].execute({
                "cluster_results": state.get("cluster_results", {}),
                "data": state.get("cleaned_data", {}),
                "primary_metric": "silhouette"
            })
            
            return {
                "current_stage": "evaluation",
                "final_evaluation": result.get("evaluation"),
                "clustering_silhouette": result.get("best_silhouette", 0.0),
                "timestamps": {
                    **state.get("timestamps", {}),
                    "evaluation_completed": datetime.now().isoformat()
                },
                "execution_log": [
                    *state.get("execution_log", []),
                    {
                        "stage": "evaluation",
                        "best_algorithm": result.get("best_algorithm"),
                        "silhouette": result.get("best_silhouette", 0.0),
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
        except Exception as e:
            self._log(f"✗ Evaluation Failed: {str(e)}")
            return {
                "current_stage": "evaluation",
                "errors": [*state.get("errors", []), str(e)],
                "last_error": str(e)
            }
    
    # ========== HITL Nodes ==========
    
    def _node_hitl_schema(self, state: GraphState) -> Dict[str, Any]:
        """HITL checkpoint: Schema validation"""
        if not self.hitl_enabled:
            return {"hitl_approval": True}
        
        self._log("⏳ HITL: Awaiting schema validation approval...")
        schema = state.get("normalized_schema", {})
        
        # In real implementation, this would be interactive
        # For now, we auto-approve if schema is valid
        approval = state.get("schema_validity", False)
        
        return {"hitl_approval": approval}
    
    def _node_hitl_clustering(self, state: GraphState) -> Dict[str, Any]:
        """HITL checkpoint: Clustering validation"""
        if not self.hitl_enabled:
            return {"hitl_approval": True}
        
        self._log("⏳ HITL: Awaiting clustering validation approval...")
        silhouette = state.get("clustering_silhouette", 0.0)
        
        # Auto-approve if silhouette > 0.3 (early validation)
        approval = silhouette > 0.3
        
        return {"hitl_approval": approval}
    
    def _node_hitl_quality(self, state: GraphState) -> Dict[str, Any]:
        """HITL checkpoint: Data quality gate"""
        if not self.hitl_enabled:
            return {"hitl_approval": True}
        
        self._log("⏳ HITL: Awaiting data quality gate approval...")
        quality = state.get("data_quality_score", 0.0)
        
        # Auto-approve if quality > 0.85
        approval = quality > 0.85
        
        return {"hitl_approval": approval}
    
    def _node_hitl_model(self, state: GraphState) -> Dict[str, Any]:
        """HITL checkpoint: Model acceptance"""
        if not self.hitl_enabled:
            return {"hitl_approval": True}
        
        self._log("⏳ HITL: Awaiting model acceptance approval...")
        silhouette = state.get("clustering_silhouette", 0.0)
        
        # Auto-approve if silhouette > 0.5
        approval = silhouette > 0.5
        
        return {"hitl_approval": approval}
    
    # ========== Routing Functions ==========
    
    def _route_after_clustering_validation(self, state: GraphState) -> str:
        """Route based on clustering validation result"""
        approval = state.get("hitl_approval")
        
        if approval is None:
            return "hitl_clustering_validation"
        elif approval is True:
            self._log("✓ Clustering approved, proceeding to normalization")
            return "approved"
        else:
            iteration = state.get("iteration_count", 0)
            if iteration < state.get("max_iterations", 3):
                self._log("⟳ Clustering needs refinement, looping back")
                return "refinement"
            else:
                self._log("✗ Max iterations reached, rejecting clustering")
                return "rejected"
    
    def _route_after_schema_validation(self, state: GraphState) -> str:
        """Route based on schema validation result"""
        approval = state.get("hitl_approval")
        
        if approval is None:
            return "hitl_schema_validation"
        elif approval is True:
            self._log("✓ Schema approved, proceeding to data cleaning")
            return "approved"
        else:
            iteration = state.get("iteration_count", 0)
            if iteration < state.get("max_iterations", 3):
                self._log("⟳ Schema needs refinement, looping back")
                return "refinement"
            else:
                self._log("✗ Max iterations reached, rejecting schema")
                return "rejected"
    
    def _route_after_quality_gate(self, state: GraphState) -> str:
        """Route based on data quality gate result"""
        approval = state.get("hitl_approval")
        
        if approval is None:
            return "hitl_data_quality_gate"
        elif approval is True:
            self._log("✓ Data quality approved, proceeding to clustering")
            return "approved"
        else:
            iteration = state.get("iteration_count", 0)
            if iteration < state.get("max_iterations", 3):
                self._log("⟳ Data quality needs improvement, looping back")
                return "refinement"
            else:
                self._log("✗ Max iterations reached, rejecting model")
                return "rejected"
    
    def _route_after_model_acceptance(self, state: GraphState) -> str:
        """Route based on model acceptance result"""
        approval = state.get("hitl_approval")
        
        if approval is None:
            return "hitl_model_acceptance"
        elif approval is True:
            self._log("✓ Model approved, pipeline complete!")
            return "approved"
        else:
            iteration = state.get("iteration_count", 0)
            if iteration < state.get("max_iterations", 3):
                self._log("⟳ Model needs optimization, looping back to clustering")
                return "refinement"
            else:
                self._log("✗ Max iterations reached, cannot improve model")
                return "rejected"
    
    # ========== Public Interface ==========
    
    async def run(
        self,
        input_data: Dict[str, Any],
        user_query: str = "",
        session_id: Optional[str] = None,
        pipeline_id: Optional[str] = None
    ) -> GraphState:
        """
        Run autonomous data pipeline using LangGraph.
        
        Args:
            input_data: Raw input data
            user_query: User's question/request
            session_id: Optional session identifier
            pipeline_id: Optional pipeline identifier
        
        Returns:
            Final graph state with results
        """
        if not HAS_LANGGRAPH:
            self._log("⚠ LangGraph not available, using fallback orchestration")
            return await self._run_fallback(input_data, user_query)
        
        import uuid
        session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        pipeline_id = pipeline_id or f"pipeline_{uuid.uuid4().hex[:8]}"
        
        self._log(f"Starting LangGraph pipeline: {pipeline_id}")
        
        # Initial state
        initial_state: GraphState = {
            "session_id": session_id,
            "pipeline_id": pipeline_id,
            "raw_data": input_data,
            "user_query": user_query,
            "current_stage": "start",
            "iteration_count": 0,
            "max_iterations": 3,
            "data_quality_score": 0.0,
            "schema_validity": False,
            "clustering_silhouette": 0.0,
            "proceed_to_next": True,
            "requires_refinement": False,
            "hitl_approval": None,
            "errors": [],
            "last_error": None,
            "execution_log": [],
            "timestamps": {
                "start": datetime.now().isoformat()
            }
        }
        
        # Execute graph
        final_state = await asyncio.to_thread(self._graph.invoke, initial_state)
        
        self._log(f"✓ Pipeline complete. Final stage: {final_state.get('current_stage')}")
        self._log(f"  Best silhouette score: {final_state.get('clustering_silhouette', 0.0):.4f}")
        self._log(f"  Data quality score: {final_state.get('data_quality_score', 0.0):.4f}")
        self._log(f"  Errors: {len(final_state.get('errors', []))}")
        
        return final_state
    
    async def _run_fallback(
        self,
        input_data: Dict[str, Any],
        user_query: str
    ) -> Dict[str, Any]:
        """Fallback orchestration without LangGraph"""
        self._log("Using fallback orchestration")
        
        return {
            "error": "LangGraph not available",
            "fallback": True
        }


# Convenience function for direct usage
async def run_autonomous_pipeline(
    input_data: Dict[str, Any],
    use_case: str = "general",
    domain_context: str = "unknown",
    hitl_enabled: bool = True,
    verbose: bool = True,
    **kwargs
) -> GraphState:
    """
    Quick-start function to run autonomous data pipeline.
    
    Args:
        input_data: Raw data to analyze
        use_case: Application domain
        domain_context: Specific context for LLM
        hitl_enabled: Enable human-in-the-loop
        verbose: Enable logging
        **kwargs: Additional arguments passed to pipeline
    
    Returns:
        Final pipeline state with results
    """
    pipeline = LangGraphDataPipeline(
        use_case=use_case,
        domain_context=domain_context,
        hitl_enabled=hitl_enabled,
        verbose=verbose
    )
    
    return await pipeline.run(input_data, **kwargs)
