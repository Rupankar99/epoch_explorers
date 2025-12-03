"""
FastAPI Server for DeepAgents RAG Agent

Exposes multi-agent orchestration functionality as REST API endpoints:
- POST /ingest - Ingest documents via multi-agent workflow
- POST /ask - Ask questions via multi-agent orchestration
- POST /optimize - Optimize system via healing agent
- GET /status - Check agent orchestration status
- GET /tasks - Get task execution history
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import logging

from .deepagents_rag_agent import DeepAgentsRAGOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class IngestRequest(BaseModel):
    """Request to ingest a document"""
    text: str
    doc_id: str
    metadata: Optional[Dict[str, Any]] = None


class IngestResponse(BaseModel):
    """Response from document ingestion"""
    success: bool
    doc_id: str
    chunks_created: int
    vectors_saved: int
    task_id: str
    message: str
    errors: List[str] = []


class AskRequest(BaseModel):
    """Request to ask a question"""
    question: str
    top_k: int = 5
    user_role: Optional[str] = None


class AskResponse(BaseModel):
    """Response to question"""
    success: bool
    question: str
    answer: str
    context_chunks: int
    task_id: str
    reasoning_steps: int
    message: str
    errors: List[str] = []


class OptimizeRequest(BaseModel):
    """Request to optimize system"""
    performance_history: List[Dict[str, Any]]


class OptimizeResponse(BaseModel):
    """Response from optimization"""
    success: bool
    optimizations_applied: int
    performance_improvement: Optional[float] = None
    task_id: str
    message: str
    errors: List[str] = []


class StatusResponse(BaseModel):
    """Agent orchestration status response"""
    status: str
    initialized: bool
    master_agent_ready: bool
    subagents_active: int
    total_tasks_planned: int
    completed_tasks: int
    message: str


class TaskSummary(BaseModel):
    """Summary of executed tasks"""
    total_tasks: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    by_subagent: Dict[str, int]


# ============================================================================
# FastAPI Application with Lifespan
# ============================================================================

agent: Optional[DeepAgentsRAGOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage agent lifecycle (startup/shutdown)
    """
    global agent
    
    # Startup
    try:
        logger.info("Initializing DeepAgents RAG Orchestrator...")
        agent = DeepAgentsRAGOrchestrator()
        logger.info("✅ DeepAgents RAG Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent: {str(e)}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down DeepAgents RAG Orchestrator...")
    agent = None


# Create FastAPI app
app = FastAPI(
    title="DeepAgents RAG Orchestrator API",
    description="REST API for multi-agent RAG orchestration with DeepAgents",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/health", response_model=StatusResponse)
async def health_check():
    """Check agent orchestrator health and readiness"""
    if agent is None:
        return StatusResponse(
            status="error",
            initialized=False,
            master_agent_ready=False,
            subagents_active=0,
            total_tasks_planned=0,
            completed_tasks=0,
            message="Orchestrator not initialized"
        )
    
    try:
        task_summary = agent.task_manager.get_task_summary()
        
        return StatusResponse(
            status="ready",
            initialized=True,
            master_agent_ready=agent.master_agent is not None,
            subagents_active=4,  # ingestion, retrieval, healing, config
            total_tasks_planned=task_summary.get("total_tasks", 0),
            completed_tasks=task_summary.get("completed_count", 0),
            message="DeepAgents orchestrator is ready"
        )
    except Exception as e:
        return StatusResponse(
            status="error",
            initialized=True,
            master_agent_ready=False,
            subagents_active=0,
            total_tasks_planned=0,
            completed_tasks=0,
            message=f"Error checking status: {str(e)}"
        )


@app.get("/status", response_model=StatusResponse)
async def status():
    """Get agent orchestration status"""
    return await health_check()


# ============================================================================
# Ingestion Endpoints
# ============================================================================

@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    """
    Ingest a document via multi-agent workflow
    
    Agents involved:
    - Ingestion subagent: Document parsing and chunking
    - Retrieval subagent: Vector embedding and storage
    
    - **text**: Document content
    - **doc_id**: Unique document identifier
    - **metadata**: Optional metadata dictionary
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        logger.info(f"Ingesting document via multi-agent workflow: {request.doc_id}")
        
        result = agent.ingest_document(
            text=request.text,
            doc_id=request.doc_id
        )
        
        if result.get("success"):
            return IngestResponse(
                success=True,
                doc_id=request.doc_id,
                chunks_created=result.get("chunks_created", 0),
                vectors_saved=result.get("vectors_saved", 0),
                task_id=result.get("task_id", ""),
                message=f"Document {request.doc_id} ingested via multi-agent workflow",
                errors=result.get("errors", [])
            )
        else:
            return IngestResponse(
                success=False,
                doc_id=request.doc_id,
                chunks_created=0,
                vectors_saved=0,
                task_id=result.get("task_id", ""),
                message="Document ingestion workflow failed",
                errors=result.get("errors", ["Unknown error"])
            )
    
    except Exception as e:
        logger.error(f"Error ingesting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


# ============================================================================
# Retrieval Endpoints
# ============================================================================

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Ask a question via multi-agent orchestration
    
    Agents involved:
    - Retrieval subagent: Context retrieval and ranking
    - Healing agent: Response optimization and fact-checking
    
    - **question**: The question to ask
    - **top_k**: Number of context chunks to retrieve
    - **user_role**: User role for access control
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        logger.info(f"Processing question via multi-agent orchestration: {request.question}")
        
        result = agent.ask_question(question=request.question)
        
        if result.get("success"):
            return AskResponse(
                success=True,
                question=request.question,
                answer=result.get("answer", ""),
                context_chunks=result.get("context_chunks", 0),
                task_id=result.get("task_id", ""),
                reasoning_steps=result.get("reasoning_steps", 0),
                message="Question processed successfully via multi-agent workflow",
                errors=result.get("errors", [])
            )
        else:
            return AskResponse(
                success=False,
                question=request.question,
                answer="",
                context_chunks=0,
                task_id=result.get("task_id", ""),
                reasoning_steps=0,
                message="Question processing workflow failed",
                errors=result.get("errors", ["Failed to generate answer"])
            )
    
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Question processing failed: {str(e)}")


# ============================================================================
# Optimization Endpoints
# ============================================================================

@app.post("/optimize", response_model=OptimizeResponse)
async def optimize_system(request: OptimizeRequest):
    """
    Optimize the system via healing agent
    
    Agents involved:
    - Healing subagent: Performance analysis and optimization
    
    - **performance_history**: List of performance metrics
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        logger.info("Starting system optimization via healing agent")
        
        result = agent.optimize_system(
            performance_history=request.performance_history
        )
        
        if result.get("success"):
            return OptimizeResponse(
                success=True,
                optimizations_applied=result.get("optimizations_applied", 0),
                performance_improvement=result.get("performance_improvement"),
                task_id=result.get("task_id", ""),
                message="System optimized successfully via healing agent",
                errors=result.get("errors", [])
            )
        else:
            return OptimizeResponse(
                success=False,
                optimizations_applied=0,
                task_id=result.get("task_id", ""),
                message="System optimization failed",
                errors=result.get("errors", ["Optimization failed"])
            )
    
    except Exception as e:
        logger.error(f"Error optimizing system: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


# ============================================================================
# Task Management Endpoints
# ============================================================================

@app.get("/tasks", response_model=TaskSummary)
async def get_tasks_summary():
    """Get summary of all executed tasks"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        summary = agent.task_manager.get_task_summary()
        
        return TaskSummary(
            total_tasks=summary.get("total_tasks", 0),
            by_type=summary.get("by_type", {}),
            by_status=summary.get("by_status", {}),
            by_subagent=summary.get("by_subagent", {})
        )
    except Exception as e:
        logger.error(f"Error getting task summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tasks: {str(e)}")


@app.get("/tasks/json")
async def export_tasks_json():
    """Export all tasks as JSON"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        return {"tasks": agent.task_manager.export_tasks_json()}
    except Exception as e:
        logger.error(f"Error exporting tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export tasks: {str(e)}")


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "name": "DeepAgents RAG Orchestrator API",
        "version": "1.0.0",
        "status": "ready" if agent else "initializing",
        "agents": {
            "master": "Main orchestrator",
            "ingestion": "Document processing subagent",
            "retrieval": "Context retrieval subagent",
            "healing": "Performance optimization subagent",
            "config": "System configuration subagent"
        },
        "endpoints": {
            "health": "GET /health",
            "status": "GET /status",
            "ingest": "POST /ingest",
            "ask": "POST /ask",
            "optimize": "POST /optimize",
            "tasks": "GET /tasks",
            "tasks_json": "GET /tasks/json",
            "docs": "GET /docs",
            "openapi": "GET /openapi.json"
        }
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )
