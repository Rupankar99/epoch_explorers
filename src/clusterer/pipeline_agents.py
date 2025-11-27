"""
Pipeline Agents for Autonomous Data Exploration

Non-breaking modular agents for each pipeline stage.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from .state_manager import PipelineState
from .data_sources import (
    DataSourceFactory,
    DataSourceConfig,
    DataSourceType,
    WebDataSource
)


class PipelineAgent(ABC):
    """Base agent for pipeline stages"""
    
    def __init__(self, name: str):
        self.name = name
        self.agent_id = f"{name}_{id(self)}"
    
    @abstractmethod
    async def execute(self, state: PipelineState) -> PipelineState:
        """Execute agent logic"""
        pass
    
    def _log_stage_start(self, state: PipelineState):
        """Log stage start"""
        print(f"[{self.name}] Starting execution...")
        state.update_stage(self.name, state.completion_percentage)
    
    def _log_stage_end(self, state: PipelineState, success: bool = True):
        """Log stage completion"""
        status = "✓ Completed" if success else "✗ Failed"
        print(f"[{self.name}] {status}")


class DataAcquisitionAgent(PipelineAgent):
    """Stage 1: Data sourcing and ingestion"""
    
    def __init__(self):
        super().__init__("DataAcquisition")
    
    async def execute(self, state: PipelineState) -> PipelineState:
        """
        Acquire data from source.
        
        Supports:
        - Direct input (MVP): raw_data field passed in
        - REST APIs: fetch JSON from endpoint
        - CSV URLs: fetch and parse CSV files
        - JSON URLs: fetch JSON from URL
        
        Configuration via state:
        - state.raw_data: Direct input data (highest priority)
        - state.api_url: REST API endpoint
        - state.csv_url: CSV file URL
        - state.api_params: Query parameters for API
        - state.api_headers: Custom headers for API
        - state.api_urls: List of API URLs to try in fallback order (NEW)
        - state.fallback_apis: List of APIRequest objects (NEW)
        """
        self._log_stage_start(state)
        
        try:
            # Priority 1: Direct input data
            if state.raw_data and isinstance(state.raw_data, dict):
                print(f"[{self.name}] Using direct input data")
                state.raw_data_source = "direct_input"
                state.update_stage(self.name, 15.0)
                self._log_stage_end(state, True)
                return state
            
            # Priority 2: Multiple API fallback (NEW - try multiple APIs, skip empty/failed)
            if hasattr(state, 'fallback_apis') and state.fallback_apis:
                print(f"[{self.name}] Trying {len(state.fallback_apis)} APIs with fallback...")
                async with WebDataSource() as source:
                    response = await source.fetch_first_available_api(
                        state.fallback_apis,
                        min_records=1
                    )
                    
                    if response.success and response.data:
                        state.raw_data = response.data
                        state.raw_data_source = "rest_api_fallback"
                        state.update_stage(self.name, 15.0)
                        print(f"[{self.name}] ✓ Got data from fallback API")
                        self._log_stage_end(state, True)
                        return state
                    else:
                        print(f"[{self.name}] ✗ All fallback APIs failed: {response.error}")
                        # Continue to next priority
            
            # Priority 3: Single REST API
            if hasattr(state, 'api_url') and state.api_url:
                print(f"[{self.name}] Fetching from REST API: {state.api_url}")
                config = DataSourceConfig(
                    source_type=DataSourceType.REST_API,
                    url=state.api_url,
                    params=getattr(state, 'api_params', None),
                    headers=getattr(state, 'api_headers', None),
                    method=getattr(state, 'api_method', 'GET')
                )
                data = await DataSourceFactory.fetch_data(config)
                
                if "error" not in data:
                    state.raw_data = data
                    state.raw_data_source = "rest_api"
                    state.update_stage(self.name, 15.0)
                    print(f"[{self.name}] ✓ Fetched {len(data)} records from API")
                    self._log_stage_end(state, True)
                    return state
                else:
                    raise ValueError(f"API error: {data.get('error')}")
            
            # Priority 4: CSV URL
            if hasattr(state, 'csv_url') and state.csv_url:
                print(f"[{self.name}] Fetching CSV from: {state.csv_url}")
                config = DataSourceConfig(
                    source_type=DataSourceType.CSV_URL,
                    url=state.csv_url
                )
                data = await DataSourceFactory.fetch_data(config)
                
                if "error" not in data:
                    state.raw_data = data
                    state.raw_data_source = "csv_url"
                    state.update_stage(self.name, 15.0)
                    print(f"[{self.name}] ✓ Fetched CSV with {data.get('row_count', 0)} rows")
                    self._log_stage_end(state, True)
                    return state
                else:
                    raise ValueError(f"CSV fetch error: {data.get('error')}")
            
            # Priority 5: JSON URL
            if hasattr(state, 'json_url') and state.json_url:
                print(f"[{self.name}] Fetching JSON from: {state.json_url}")
                config = DataSourceConfig(
                    source_type=DataSourceType.JSON_URL,
                    url=state.json_url
                )
                data = await DataSourceFactory.fetch_data(config)
                
                if "error" not in data:
                    state.raw_data = data
                    state.raw_data_source = "json_url"
                    state.update_stage(self.name, 15.0)
                    print(f"[{self.name}] ✓ Fetched JSON data")
                    self._log_stage_end(state, True)
                    return state
                else:
                    raise ValueError(f"JSON fetch error: {data.get('error')}")
            
            # No data source found
            raise ValueError(
                "No data source provided. Set one of: "
                "raw_data (direct), fallback_apis (list), api_url, csv_url, or json_url"
            )
            
        except Exception as e:
            state.log_error(self.name, str(e))
            self._log_stage_end(state, False)
        
        return state


class NormalizationAgent(PipelineAgent):
    """Stage 2: Schema inference and normalization"""
    
    def __init__(self):
        super().__init__("Normalization")
        self.max_refinement_loops = 3
    
    async def execute(self, state: PipelineState) -> PipelineState:
        """
        Convert unstructured data to normalized schema (3NF).
        MVP: basic structuring logic.
        Future: Dual-LLM self-refinement loops.
        """
        self._log_stage_start(state)
        
        try:
            # MVP: simple schema inference from dict structure
            if not state.raw_data:
                raise ValueError("No raw data to normalize")
            
            # Create basic schema from data keys
            state.normalized_schema = {
                "tables": {
                    "main": {
                        "columns": list(state.raw_data.keys()),
                        "primary_key": "id" if "id" in state.raw_data else list(state.raw_data.keys())[0],
                        "foreign_keys": []
                    }
                }
            }
            
            state.schema_validation_passed = True
            state.update_stage(self.name, 30.0)
            
            # Mark for HITL approval if enabled
            if state.hitl_enabled:
                state.awaiting_schema_validation = True
            
            self._log_stage_end(state, True)
            
        except Exception as e:
            state.log_error(self.name, str(e))
            self._log_stage_end(state, False)
        
        return state


class CleaningAgent(PipelineAgent):
    """Stage 3: Automated data preparation"""
    
    def __init__(self):
        super().__init__("DataCleaning")
    
    async def execute(self, state: PipelineState) -> PipelineState:
        """
        AutoDC workflow: data cleaning and feature engineering.
        MVP: basic quality assessment.
        Future: LLM-driven cleaning decisions.
        """
        self._log_stage_start(state)
        
        try:
            if not state.raw_data:
                raise ValueError("No data to clean")
            
            # MVP: basic quality metrics
            state.data_quality_report.completeness = 0.95  # Placeholder
            state.data_quality_report.consistency = 0.90
            state.data_quality_report.accuracy = 0.92
            state.data_quality_report.validity = 0.88
            
            state.cleaned_data = state.raw_data  # MVP: pass through
            state.update_stage(self.name, 50.0)
            
            # Mark for HITL approval if enabled
            if state.hitl_enabled:
                state.awaiting_data_quality_approval = True
            
            self._log_stage_end(state, True)
            
        except Exception as e:
            state.log_error(self.name, str(e))
            self._log_stage_end(state, False)
        
        return state


class ClusteringAgent(PipelineAgent):
    """Stage 4: Unsupervised learning"""
    
    def __init__(self):
        super().__init__("Clustering")
    
    async def execute(self, state: PipelineState) -> PipelineState:
        """
        Execute K-Means and DBSCAN clustering.
        MVP: K-Means only with fixed hyperparameters.
        Future: Full hyperparameter search + DBSCAN.
        """
        self._log_stage_start(state)
        
        try:
            if not state.cleaned_data:
                raise ValueError("No cleaned data for clustering")
            
            # MVP: placeholder clustering result
            from .state_manager import ClusteringResult
            
            result = ClusteringResult(
                algorithm="kmeans",
                num_clusters=3,
                silhouette_score=0.65,
                hyperparameters={"k": 3, "max_iter": 300}
            )
            
            state.clustering_results.append(result)
            state.best_clustering = result
            state.update_stage(self.name, 75.0)
            
            # Mark for HITL approval if enabled
            if state.hitl_enabled:
                state.awaiting_model_approval = True
            
            self._log_stage_end(state, True)
            
        except Exception as e:
            state.log_error(self.name, str(e))
            self._log_stage_end(state, False)
        
        return state


class EvaluationAgent(PipelineAgent):
    """Stage 5: Model evaluation and selection"""
    
    def __init__(self):
        super().__init__("Evaluation")
    
    async def execute(self, state: PipelineState) -> PipelineState:
        """
        Evaluate and select best clustering model.
        MVP: report best result.
        Future: Competitive evaluation with secondary metrics.
        """
        self._log_stage_start(state)
        
        try:
            if not state.clustering_results:
                raise ValueError("No clustering results to evaluate")
            
            # Select best by Silhouette score
            state.best_clustering = max(
                state.clustering_results,
                key=lambda r: r.silhouette_score
            )
            
            state.update_stage(self.name, 90.0)
            self._log_stage_end(state, True)
            
        except Exception as e:
            state.log_error(self.name, str(e))
            self._log_stage_end(state, False)
        
        return state
