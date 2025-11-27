"""
Usage Examples - Autonomous Data Exploration Pipeline

Demonstrates how to use the pipeline without breaking existing code.
"""

import asyncio
from src.clusterer import AutonomousDataPipeline, run_autonomous_pipeline


# Example 1: Simple usage with convenience function
async def example_simple():
    """Minimal example using convenience function"""
    print("=" * 60)
    print("Example 1: Simple Pipeline Execution")
    print("=" * 60)
    
    # Sample data
    sample_data = {
        "customer_id": [1, 2, 3, 4, 5],
        "age": [25, 35, 28, 45, 32],
        "purchase_amount": [100, 250, 150, 500, 200],
        "frequency": [2, 5, 3, 10, 4]
    }
    
    # Run pipeline
    result = await run_autonomous_pipeline(
        input_data=sample_data,
        use_case="customer_segmentation",
        domain_context="e-commerce",
        hitl_enabled=True
    )
    
    print(f"\nPipeline Summary:")
    print(result.get_summary())


# Example 2: Full control with orchestrator
async def example_full_control():
    """Advanced example with full pipeline control"""
    print("\n" + "=" * 60)
    print("Example 2: Full Control - Custom Pipeline")
    print("=" * 60)
    
    # Initialize pipeline with custom settings
    pipeline = AutonomousDataPipeline(
        use_case="incident_analysis",
        domain_context="cybersecurity",
        hitl_enabled=True,
        max_iterations=5,
        verbose=True
    )
    
    # Prepare data
    incident_data = {
        "incident_id": list(range(1, 21)),
        "severity": [1, 2, 1, 3, 2] * 4,
        "response_time": [15, 45, 20, 120, 60] * 4,
        "impact_score": [10, 35, 12, 200, 80] * 4
    }
    
    # Run with custom session ID
    result = await pipeline.run(
        input_data=incident_data,
        session_id="incident_analysis_001",
        pipeline_id="pipeline_incident_001"
    )
    
    # Check status
    status = pipeline.get_status("pipeline_incident_001")
    print(f"\nFinal Status: {status}")
    
    # Get full state
    state = pipeline.get_pipeline_state("pipeline_incident_001")
    print(f"\nClustering Results: {len(state.clustering_results)} models evaluated")
    if state.best_clustering:
        print(f"Best Model: {state.best_clustering.algorithm}")
        print(f"Silhouette Score: {state.best_clustering.silhouette_score:.3f}")


# Example 3: Multiple parallel pipelines
async def example_parallel():
    """Run multiple independent pipelines"""
    print("\n" + "=" * 60)
    print("Example 3: Parallel Pipeline Execution")
    print("=" * 60)
    
    pipeline = AutonomousDataPipeline(
        use_case="multi_analysis",
        domain_context="general",
        verbose=False  # Reduce noise for parallel execution
    )
    
    # Define multiple datasets
    datasets = {
        "dataset_1": {"col1": [1, 2, 3, 4, 5], "col2": [10, 20, 30, 40, 50]},
        "dataset_2": {"col1": [5, 4, 3, 2, 1], "col2": [50, 40, 30, 20, 10]},
        "dataset_3": {"col1": [2, 4, 1, 5, 3], "col2": [25, 50, 15, 75, 45]},
    }
    
    # Run all in parallel
    tasks = [
        pipeline.run(data, pipeline_id=f"parallel_{i}")
        for i, (name, data) in enumerate(datasets.items())
    ]
    
    results = await asyncio.gather(*tasks)
    
    print(f"\n✓ Executed {len(results)} pipelines in parallel")
    for i, result in enumerate(results):
        score = result.best_clustering.silhouette_score if result.best_clustering else 0.0
        print(f"  Pipeline {i+1}: Silhouette = {score:.3f}")


# Example 4: Integration with existing RAG system (optional)
async def example_rag_integration():
    """Show how to integrate with RAG if desired (non-breaking)"""
    print("\n" + "=" * 60)
    print("Example 4: Optional RAG Integration")
    print("=" * 60)
    
    print("""
    The clusterer can work standalone OR with the RAG system:
    
    # Standalone (recommended for MVP):
    from src.clusterer import AutonomousDataPipeline
    pipeline = AutonomousDataPipeline()
    result = await pipeline.run(data)
    
    # With RAG (future enhancement - non-breaking):
    from src.rag.agents.langgraph_agent import LangGraphRAGAgent
    from src.clusterer import AutonomousDataPipeline
    
    rag_agent = LangGraphRAGAgent()
    # RAG ingests docs → creates structured tables
    
    pipeline = AutonomousDataPipeline(vectordb=rag_agent.vectordb_service)
    # Pipeline clusters the structured data
    
    Both systems remain independent and can be used together optionally.
    """)


# Main execution
async def main():
    """Run all examples"""
    print("\n" + "#" * 60)
    print("# AUTONOMOUS DATA EXPLORATION PIPELINE - USAGE EXAMPLES")
    print("#" * 60)
    
    # Run examples
    await example_simple()
    await example_full_control()
    await example_parallel()
    await example_rag_integration()
    
    print("\n" + "#" * 60)
    print("# All examples completed!")
    print("#" * 60)


if __name__ == "__main__":
    asyncio.run(main())
