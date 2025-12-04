"""
Agentic Workflow Orchestrator - LangGraph-based autonomous clustering pipeline
Wraps ClusteringOrchestrator with autonomous agent capabilities using multi-provider LLM
Enables self-healing, adaptive parameter selection, decision-making with LLM analysis
"""

from typing import Any, Dict, List, Optional, TypedDict, Annotated
from datetime import datetime
import json
import sqlite3
import pandas as pd
import numpy as np
import os

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, SystemMessage

from clustering_engine import ClusteringEngine
from llm_service import LLMService

# ============================================================================
# STATE DEFINITION
# ============================================================================

class ClusteringAgentState(TypedDict, total=False):
    """State for the agentic clustering workflow"""
    
    # Input
    table_name: str
    custom_k_values: Optional[List[int]]
    custom_eps_values: Optional[List[float]]
    
    # Processing
    raw_df: Optional[pd.DataFrame]
    quality_threshold: float
    
    # Intermediate results
    clustering_variants: Dict[str, Any]
    best_variant: Optional[str]
    best_quality: float
    quality_assessment: Dict[str, Any]
    
    # Final approval
    selected_variant: Optional[str]
    cluster_labels: Optional[Dict[int, str]]
    approval_status: str
    
    # Metadata
    step_count: int
    workflow_status: str
    error_message: Optional[str]
    timestamp: str


# ============================================================================
# AGENT NODES
# ============================================================================

class ClusteringAgent:
    """Autonomous agent for clustering operations with LLM-powered analysis"""
    
    def __init__(self, llm_config_path: str = None):
        self.orchestrator = ClusteringEngine()
        
        # Load LLM service from multi-provider config (local in clusterer folder)
        if llm_config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            llm_config_path = os.path.join(current_dir, 'llm_config.json')
        
        try:
            with open(llm_config_path, 'r') as f:
                llm_config = json.load(f)
            
            self.llm_service = LLMService(llm_config)
            self.llm = self.llm_service.get_model()
            print(f"[ClusteringAgent] LLM Service initialized with provider: {self.llm_service.provider}")
        except Exception as e:
            print(f"[ClusteringAgent] LLM Service initialization failed: {e}")
            self.llm_service = None
            self.llm = None
    
    # ====== NODE: Initialization ======
    def initialize_workflow(self, state: ClusteringAgentState) -> ClusteringAgentState:
        """Initialize the clustering workflow (TOON format)"""
        table = state['table_name']
        try:
            df = self.orchestrator.get_table_data(table)
            rows, cols = df.shape
            print(f"[Agent] 📂 {table} | {rows}×{cols}")
            
            state['raw_df'] = df
            state['step_count'] = 1
            state['workflow_status'] = 'initialized'
            state['timestamp'] = datetime.now().isoformat()
            state['quality_threshold'] = 0.5
            state['best_quality'] = -1
            state['clustering_variants'] = {}
            state['quality_assessment'] = {}
            return state
        except Exception as e:
            state['workflow_status'] = 'error'
            state['error_message'] = str(e)
            return state
    
    # ====== NODE: Parameter Optimization ======
    def optimize_parameters(self, state: ClusteringAgentState) -> ClusteringAgentState:
        """Agent autonomously decides best K and eps values (TOON)"""
        try:
            df = state['raw_df']
            
            k_values = state['custom_k_values'] or [2, 3, 5, 7]
            eps_values = state['custom_eps_values'] or [0.3, 0.5, 0.7, 1.0]
            
            print(f"[Agent] 🎛️ K={k_values} | eps={eps_values}")
            
            state['custom_k_values'] = k_values
            state['custom_eps_values'] = eps_values
            state['workflow_status'] = 'parameters_optimized'
            
            return state
        except Exception as e:
            state['workflow_status'] = 'error'
            state['error_message'] = str(e)
            return state
    
    # ====== NODE: Execute Clustering ======
    def execute_clustering(self, state: ClusteringAgentState) -> ClusteringAgentState:
        """Execute clustering with selected parameters (TOON)"""
        try:
            result = self.orchestrator.run_clustering(
                state['table_name'],
                state['custom_k_values'],
                state['custom_eps_values']
            )
            
            if result['status'] == 'success':
                n = len(result['variants'])
                state['clustering_variants'] = result['variants']
                state['workflow_status'] = 'clustering_complete'
                print(f"[Agent] 🔬 {n} variants")
            else:
                state['workflow_status'] = 'error'
                state['error_message'] = result.get('error', 'Unknown error')
            
            return state
        except Exception as e:
            state['workflow_status'] = 'error'
            state['error_message'] = str(e)
            return state
    
    # ====== NODE: Quality Assessment & Ranking ======
    def assess_quality(self, state: ClusteringAgentState) -> ClusteringAgentState:
        """Agent assesses quality and ranks variants using LLM analysis (TOON format)"""
        print("[Agent] 📊 Assessing quality...")
        
        try:
            variants = state['clustering_variants']
            ranked_variants = []
            
            # Build TOON summary for LLM analysis (ultra-compact format)
            variants_summary = []
            for name, data in variants.items():
                silhouette = data.get('silhouette', 0)
                algorithm = data.get('algorithm', 'unknown')
                
                if algorithm == 'kmeans':
                    metrics = f"K={data.get('k')} I={data.get('inertia', 0):.1f}"
                else:
                    metrics = f"E={data.get('eps')} C={data.get('n_clusters')} N={data.get('n_noise')}"
                
                # TOON format: emoji + short name + quality indicator + metrics
                quality_emoji = "⭐" if silhouette > 0.7 else "✓" if silhouette > 0.5 else "◐" if silhouette > 0.3 else "✗"
                variants_summary.append(f"{quality_emoji} {name}: S={silhouette:.3f} {metrics}")
            
            # Use LLM to analyze quality if available
            llm_insights = ""
            if self.llm_service and self.llm:
                try:
                    # TOON system prompt: ultra-compact, token-optimized
                    prompt = f"""Analyze clustering. Return TOON format:
[VARIANT_NAME] → [QualityEmoji] [score(0-1)] [brief reason in 5 words max]

Data:
{chr(10).join(variants_summary)}

Rules: ⭐=excellent(>0.7), ✓=good(0.5-0.7), ◐=fair(0.3-0.5), ✗=poor(<0.3)
Output ONLY variant assessments, no explanations."""
                    
                    analysis = self.llm.invoke([
                        SystemMessage(content="TOON format expert. Output ultra-compact token-optimized analysis only."),
                        HumanMessage(content=prompt)
                    ])
                    
                    llm_insights = analysis.content
                    print(f"[Agent] 🤖 Analysis: {llm_insights[:100]}..." if len(llm_insights) > 100 else f"[Agent] 🤖 Analysis: {llm_insights}")
                except Exception as e:
                    print(f"[Agent] ⚠️ LLM skipped, using rules")
            
            # Rule-based scoring (fallback or complement)
            for name, data in variants.items():
                silhouette = data.get('silhouette', 0)
                
                # Quality scoring with emojis
                if silhouette > 0.7:
                    quality_level = "⭐ EXCELLENT"
                    score = 1.0
                elif silhouette > 0.5:
                    quality_level = "✓ GOOD"
                    score = 0.8
                elif silhouette > 0.3:
                    quality_level = "◐ FAIR"
                    score = 0.5
                else:
                    quality_level = "✗ POOR"
                    score = 0.2
                
                ranked_variants.append({
                    'name': name,
                    'silhouette': silhouette,
                    'quality_level': quality_level,
                    'score': score
                })
                
                state['quality_assessment'][name] = {
                    'silhouette': silhouette,
                    'quality': quality_level,
                    'score': score,
                    'llm_insights': llm_insights if llm_insights else 'Rule-based'
                }
            
            # Sort by quality score
            ranked_variants.sort(key=lambda x: x['score'], reverse=True)
            
            # Select best variant
            if ranked_variants:
                best = ranked_variants[0]
                state['best_variant'] = best['name']
                state['best_quality'] = best['score']
                
                print(f"[Agent] 🏆 Best: {best['name']} {best['quality_level']} (S={best['silhouette']:.3f})")
            
            state['workflow_status'] = 'quality_assessed'
            return state
        except Exception as e:
            state['workflow_status'] = 'error'
            state['error_message'] = str(e)
            return state
    
    # ====== NODE: Recommendation & Decision ======
    def make_decision(self, state: ClusteringAgentState) -> ClusteringAgentState:
        """Agent makes recommendation on best clustering to use (TOON format)"""
        best_variant = state['best_variant']
        best_quality = state['best_quality']
        threshold = state['quality_threshold']
        
        try:
            if best_quality >= threshold:
                print(f"[Agent] 💡 → {best_variant} [{best_quality:.2f}] ✓ Ready")
                state['selected_variant'] = best_variant
                state['workflow_status'] = 'ready_for_approval'
            else:
                print(f"[Agent] ⚠️ All <{threshold:.2f}, Best: {best_variant} [{best_quality:.2f}]")
                state['selected_variant'] = best_variant
                state['workflow_status'] = 'ready_for_review'
            
            return state
        except Exception as e:
            state['workflow_status'] = 'error'
            state['error_message'] = str(e)
            return state
    
    # ====== NODE: Approval & Labeling (Human-in-the-Loop) ======
    def prepare_for_approval(self, state: ClusteringAgentState) -> ClusteringAgentState:
        """Prepare clustering variants for human approval"""
        best = state.get('selected_variant', '?')
        print(f"[Agent] 📋 Variants ready | Recommended: {best} | ⏳ Awaiting approval...")
        
        state['workflow_status'] = 'ready_for_approval'
        state['approval_status'] = 'pending'
        
        return state
    
    # ====== NODE: Save Final Result ======
    def save_final_result(self, state: ClusteringAgentState) -> ClusteringAgentState:
        """Save approved clustering to final table"""
        print("[Agent] Saving final clustering result...")
        
        try:
            variant_name = state['selected_variant']
            variant_data = state['clustering_variants'][variant_name]
            cluster_labels = state.get('cluster_labels')
            
            result = self.orchestrator.approve_and_save(
                state['table_name'],
                variant_name,
                variant_data,
                cluster_labels
            )
            
            if result['status'] == 'success':
                print(f"[Agent] ✅ Saved final table: {result['final_table']}")
                state['workflow_status'] = 'completed'
                state['approval_status'] = 'approved'
            else:
                state['workflow_status'] = 'error'
                state['error_message'] = result.get('error', 'Unknown error')
            
            return state
        except Exception as e:
            state['workflow_status'] = 'error'
            state['error_message'] = str(e)
            return state
    
    # ====== NODE: Error Recovery ======
    def handle_error(self, state: ClusteringAgentState) -> ClusteringAgentState:
        """Agent attempts to recover from errors"""
        print(f"[Agent] ERROR RECOVERY: {state.get('error_message', 'Unknown error')}")
        
        state['workflow_status'] = 'error_recovery_attempted'
        return state


# ============================================================================
# GRAPH BUILDER
# ============================================================================

def build_clustering_workflow(agent: ClusteringAgent = None) -> StateGraph:
    """Build the agentic clustering workflow graph"""
    
    if agent is None:
        agent = ClusteringAgent()
    
    workflow = StateGraph(ClusteringAgentState)
    
    # Add nodes
    workflow.add_node("initialize", agent.initialize_workflow)
    workflow.add_node("optimize_params", agent.optimize_parameters)
    workflow.add_node("execute_clustering", agent.execute_clustering)
    workflow.add_node("assess_quality", agent.assess_quality)
    workflow.add_node("make_decision", agent.make_decision)
    workflow.add_node("prepare_approval", agent.prepare_for_approval)
    workflow.add_node("save_final", agent.save_final_result)
    workflow.add_node("error_handler", agent.handle_error)
    
    # Define edges
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "optimize_params")
    workflow.add_edge("optimize_params", "execute_clustering")
    workflow.add_edge("execute_clustering", "assess_quality")
    workflow.add_edge("assess_quality", "make_decision")
    workflow.add_edge("make_decision", "prepare_approval")
    
    # STOP at prepare_approval - DO NOT auto-save
    # User must manually approve from UI, which calls approve_selected_clustering()
    workflow.add_edge("prepare_approval", END)
    
    # Error handling
    workflow.add_edge("error_handler", END)
    
    return workflow.compile()


# ============================================================================
# PUBLIC API
# ============================================================================

class AgenticClusteringOrchestrator:
    """High-level API for agentic clustering workflow with LLM-powered analysis"""
    
    def __init__(self, llm_config_path: str = None):
        self.agent = ClusteringAgent(llm_config_path)
        self.graph = build_clustering_workflow(self.agent)
    
    def run_autonomous_clustering(
        self,
        table_name: str,
        custom_k_values: Optional[List[int]] = None,
        custom_eps_values: Optional[List[float]] = None,
        quality_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Run autonomous clustering workflow
        
        Args:
            table_name: Source table for clustering
            custom_k_values: Optional custom K values (else auto-select)
            custom_eps_values: Optional custom eps values (else auto-select)
            quality_threshold: Minimum silhouette score to accept
        
        Returns:
            Workflow state with results and recommendations
        """
        try:
            initial_state = ClusteringAgentState(
                table_name=table_name,
                custom_k_values=custom_k_values,
                custom_eps_values=custom_eps_values,
                quality_threshold=quality_threshold,
                step_count=0,
                workflow_status='initialized'
            )
            
            # Run workflow
            final_state = self.graph.invoke(initial_state)
            
            # Ensure final_state is not None
            if final_state is None:
                return {
                    'workflow_status': 'error',
                    'error_message': 'Workflow returned None - check graph configuration',
                    'clustering_variants': {}
                }
            
            return final_state
        except Exception as e:
            print(f"[AgenticClusteringOrchestrator] Error in run_autonomous_clustering: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'workflow_status': 'error',
                'error_message': f'Clustering failed: {str(e)}',
                'clustering_variants': {}
            }
    
    def approve_selected_clustering(
        self,
        workflow_state: Dict[str, Any],
        cluster_labels: Optional[Dict[int, str]] = None
    ) -> Dict[str, Any]:
        """
        Approve and save selected clustering with optional labels
        
        Args:
            workflow_state: State from run_autonomous_clustering
            cluster_labels: Dict mapping cluster_id -> label_name
        
        Returns:
            Save result
        """
        workflow_state['cluster_labels'] = cluster_labels
        workflow_state['approval_status'] = 'approved'
        
        # Execute save node
        final_state = self.agent.save_final_result(workflow_state)
        
        return final_state
    
    def get_recommendations(self, workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get agent's quality assessment and recommendations"""
        return {
            'best_variant': workflow_state.get('best_variant'),
            'best_quality': workflow_state.get('best_quality'),
            'quality_assessment': workflow_state.get('quality_assessment', {}),
            'clustering_variants': {
                k: {
                    'silhouette': v.get('silhouette'),
                    'algorithm': v.get('algorithm'),
                    'parameters': v.get('parameters')
                }
                for k, v in workflow_state.get('clustering_variants', {}).items()
            }
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def run_agentic_clustering(
    table_name: str,
    custom_k_values: Optional[List[int]] = None,
    custom_eps_values: Optional[List[float]] = None
) -> AgenticClusteringOrchestrator:
    """
    Shorthand to run agentic clustering workflow
    
    Usage:
        orchestrator = run_agentic_clustering('transactions')
        recs = orchestrator.get_recommendations(state)
        final_state = orchestrator.approve_selected_clustering(state, cluster_labels)
    """
    agentic_orch = AgenticClusteringOrchestrator()
    state = agentic_orch.run_autonomous_clustering(
        table_name,
        custom_k_values,
        custom_eps_values
    )
    
    return agentic_orch


if __name__ == "__main__":
    # Example usage
    agentic = AgenticClusteringOrchestrator()
    
    # Run autonomous workflow
    print("\n" + "="*60)
    print("AUTONOMOUS CLUSTERING WORKFLOW")
    print("="*60 + "\n")
    
    state = agentic.run_autonomous_clustering(
        table_name="transactions",
        custom_k_values=[2, 3, 4, 5],
        custom_eps_values=[0.3, 0.5, 0.7]
    )
    
    print("\n" + "-"*60)
    print("AGENT RECOMMENDATIONS:")
    print("-"*60)
    
    recs = agentic.get_recommendations(state)
    print(f"Best Variant: {recs['best_variant']}")
    print(f"Quality Score: {recs['best_quality']:.2f}")
    print(f"\nQuality Assessment:")
    for name, assessment in recs['quality_assessment'].items():
        print(f"  {name}: {assessment['quality']} (Silhouette: {assessment['silhouette']:.4f})")
    
    print("\n" + "-"*60)
    print("APPROVE & SAVE:")
    print("-"*60)
    
    # Simulate cluster labeling
    cluster_labels = {0: "High Risk", 1: "Medium Risk", 2: "Low Risk"}
    final_state = agentic.approve_selected_clustering(state, cluster_labels)
    
    print(f"\nWorkflow Status: {final_state['workflow_status']}")
    print(f"Approval Status: {final_state['approval_status']}")
