"""
LangGraph Visualizer - Creates visualizations for LangGraph agent workflows
"""

import os
from typing import Any, Optional


def create_visualization(graph: Any, title: str = "LangGraph Workflow") -> Optional[str]:
    """
    Create a visualization of the LangGraph workflow.
    
    Args:
        graph: The LangGraph graph object
        title: Title for the visualization
        
    Returns:
        str: Visualization content or None if failed
    """
    try:
        try:
            from graphviz import Digraph
            
            dot = Digraph(comment=title)
            dot.attr(rankdir='TB')
            
            if hasattr(graph, 'nodes'):
                for node_name in graph.nodes:
                    dot.node(node_name, node_name)
                    
            if hasattr(graph, 'edges'):
                for edge in graph.edges:
                    if isinstance(edge, tuple) and len(edge) >= 2:
                        dot.edge(edge[0], edge[1])
                        
            return dot.source
            
        except ImportError:
            return f"[Visualization] {title}\n(Install graphviz for visual output)"
            
    except Exception as e:
        print(f"[Visualizer] Warning: Could not create visualization: {e}")
        return None


def save_visualization(
    graph: Any, 
    output_path: str, 
    title: str = "LangGraph Workflow",
    format: str = "png"
) -> Optional[str]:
    """
    Save a visualization of the LangGraph workflow to a file.
    
    Args:
        graph: The LangGraph graph object
        output_path: Path to save the visualization
        title: Title for the visualization
        format: Output format (png, svg, pdf)
        
    Returns:
        str: Path to the saved file or None if failed
    """
    try:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        try:
            from graphviz import Digraph
            
            dot = Digraph(comment=title)
            dot.attr(rankdir='TB')
            
            if hasattr(graph, 'nodes'):
                for node_name in graph.nodes:
                    dot.node(node_name, node_name)
                    
            if hasattr(graph, 'edges'):
                for edge in graph.edges:
                    if isinstance(edge, tuple) and len(edge) >= 2:
                        dot.edge(edge[0], edge[1])
            
            output_file = output_path.replace(f'.{format}', '')
            dot.render(output_file, format=format, cleanup=True)
            return f"{output_file}.{format}"
            
        except ImportError:
            text_path = output_path.replace(f'.{format}', '.txt')
            with open(text_path, 'w') as f:
                f.write(f"[Visualization] {title}\n")
                f.write("(Install graphviz for visual output)\n")
                if hasattr(graph, 'nodes'):
                    f.write(f"\nNodes: {list(graph.nodes)}\n")
                if hasattr(graph, 'edges'):
                    f.write(f"Edges: {list(graph.edges)}\n")
            return text_path
            
    except Exception as e:
        print(f"[Visualizer] Warning: Could not save visualization: {e}")
        return None
