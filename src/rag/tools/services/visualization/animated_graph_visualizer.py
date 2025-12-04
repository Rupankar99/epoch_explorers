"""
Animated Graph Visualizer for RAG pipeline tracking
Provides real-time visualization of ingestion and retrieval processes
"""

from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GraphEvent:
    """Track individual graph events"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    event_type: str = "node_process"
    source: str = ""
    target: str = ""
    status: str = "in_progress"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnimatedGraphTracker:
    """Track and visualize animated graph changes"""
    name: str = "tracker"
    workflow_type: str = "general"
    workflow_id: str = ""
    events: List[GraphEvent] = field(default_factory=list)

    def add_event(
        self,
        event_type: str,
        source: str,
        target: str = "",
        status: str = "in_progress",
        metadata: Dict[str, Any] = None
    ) -> GraphEvent:
        """Add a new event to the tracker"""
        event = GraphEvent(
            event_type=event_type,
            source=source,
            target=target,
            status=status,
            metadata=metadata or {}
        )
        self.events.append(event)
        return event

    def update_status(self, event_index: int, status: str):
        """Update the status of a tracked event"""
        if 0 <= event_index < len(self.events):
            self.events[event_index].status = status

    def node_start(self, node_name: str, description: str = "", metadata: Dict = None):
        """Mark the start of a node execution"""
        self.add_event(
            event_type="node_start",
            source=node_name,
            status="in_progress",
            metadata=metadata or {"description": description}
        )

    def node_end(self, node_name: str, status: str = "completed", metadata: Dict = None):
        """Mark the end of a node execution"""
        self.add_event(
            event_type="node_end",
            source=node_name,
            status=status,
            metadata=metadata or {}
        )

    def edge_traversal(self, source: str, target: str, metadata: Dict = None):
        """Track edge traversal between nodes"""
        self.add_event(
            event_type="edge_traversal",
            source=source,
            target=target,
            status="completed",
            metadata=metadata or {}
        )

    def record_node_start(self, node_name: str, state: Dict = None):
        """Record the start of a node (alias for node_start)"""
        self.node_start(node_name, metadata=state or {})

    def record_node_end(self, node_name: str, status: str = "completed", state: Dict = None):
        """Record the end of a node (alias for node_end)"""
        self.node_end(node_name, status=status, metadata=state or {})

    def get_graph_data(self) -> Dict[str, Any]:
        """Get graph data for visualization"""
        nodes = set()
        edges = []
        
        for event in self.events:
            if event.source:
                nodes.add(event.source)
            if event.target:
                nodes.add(event.target)
            if event.target:
                edges.append((event.source, event.target))
        
        return {
            "nodes": list(nodes),
            "edges": edges,
            "summary": self.get_summary()
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked events"""
        return {
            "tracker_name": self.name,
            "workflow_type": self.workflow_type,
            "workflow_id": self.workflow_id,
            "total_events": len(self.events),
            "in_progress": sum(1 for e in self.events if e.status == "in_progress"),
            "completed": sum(1 for e in self.events if e.status == "completed"),
            "failed": sum(1 for e in self.events if e.status == "failed"),
            "events": [
                {
                    "timestamp": e.timestamp,
                    "type": e.event_type,
                    "source": e.source,
                    "target": e.target,
                    "status": e.status
                }
                for e in self.events
            ]
        }


def create_ingestion_tracker(name: str = "Document Ingestion") -> AnimatedGraphTracker:
    """Create an animated tracker for document ingestion process"""
    return AnimatedGraphTracker(name=name, workflow_type="ingestion")


def create_retrieval_tracker(name: str = "Document Retrieval") -> AnimatedGraphTracker:
    """Create an animated tracker for document retrieval process"""
    return AnimatedGraphTracker(name=name, workflow_type="retrieval")
