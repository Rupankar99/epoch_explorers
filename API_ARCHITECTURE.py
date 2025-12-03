"""
API Server Architecture Overview

This file documents the FastAPI implementation structure for both agents.
"""

# ==============================================================================
# PORT ALLOCATION
# ==============================================================================

PORT_LANGGRAPH = 8001    # LangGraph RAG Agent
PORT_DEEPAGENTS = 8002   # DeepAgents RAG Orchestrator


# ==============================================================================
# LANGGRAPH RAG AGENT API (Port 8001)
# ==============================================================================

LANGGRAPH_API_ENDPOINTS = {
    "Health & Status": {
        "GET /health": "Check agent health and service readiness",
        "GET /status": "Get current agent status",
        "GET /": "Root endpoint with API info"
    },
    
    "Ingestion": {
        "POST /ingest": {
            "request": {
                "text": "Document content (string)",
                "doc_id": "Document ID (string)",
                "metadata": "Optional metadata (dict)"
            },
            "response": {
                "success": "bool",
                "doc_id": "string",
                "chunks_created": "int",
                "vectors_saved": "int",
                "metadata_stored": "bool",
                "errors": "list"
            }
        }
    },
    
    "Retrieval": {
        "POST /ask": {
            "request": {
                "question": "Question to ask (string)",
                "response_mode": "concise|verbose|internal (default: concise)",
                "top_k": "Number of chunks to retrieve (default: 5)",
                "user_role": "Optional user role for RBAC (string)",
                "doc_id": "Optional specific document (string)",
                "performance_history": "Optional metrics (list)"
            },
            "response": {
                "success": "bool",
                "question": "string",
                "answer": "string",
                "response_mode": "string",
                "context_chunks": "int",
                "guardrails_passed": "bool",
                "traceability": "dict",
                "confidence_score": "float",
                "errors": "list"
            }
        }
    },
    
    "Optimization": {
        "POST /optimize": {
            "request": {
                "performance_history": "List of performance metrics (list)",
                "config_updates": "Config changes to apply (dict)"
            },
            "response": {
                "success": "bool",
                "optimizations_applied": "int",
                "config_changes": "dict",
                "performance_improvement": "float",
                "errors": "list"
            }
        }
    }
}

# Response Modes for LangGraph
LANGGRAPH_RESPONSE_MODES = {
    "concise": "Brief, user-friendly answers (RECOMMENDED for production)",
    "verbose": "Detailed with reasoning and context chains",
    "internal": "Full debug trace and metadata (for development)"
}


# ==============================================================================
# DEEPAGENTS RAG ORCHESTRATOR API (Port 8002)
# ==============================================================================

DEEPAGENTS_API_ENDPOINTS = {
    "Health & Status": {
        "GET /health": "Check orchestrator health",
        "GET /status": "Get orchestration status",
        "GET /": "Root endpoint with API info"
    },
    
    "Ingestion (Multi-Agent)": {
        "POST /ingest": {
            "request": {
                "text": "Document content (string)",
                "doc_id": "Document ID (string)",
                "metadata": "Optional metadata (dict)"
            },
            "response": {
                "success": "bool",
                "doc_id": "string",
                "chunks_created": "int",
                "vectors_saved": "int",
                "task_id": "string (tracking)",
                "errors": "list"
            },
            "agents_involved": ["Ingestion subagent", "Retrieval subagent"]
        }
    },
    
    "Retrieval (Multi-Agent Orchestration)": {
        "POST /ask": {
            "request": {
                "question": "Question to ask (string)",
                "top_k": "Number of chunks (default: 5)",
                "user_role": "Optional user role (string)"
            },
            "response": {
                "success": "bool",
                "question": "string",
                "answer": "string",
                "context_chunks": "int",
                "task_id": "string (tracking)",
                "reasoning_steps": "int",
                "errors": "list"
            },
            "agents_involved": ["Retrieval subagent", "Healing agent"]
        }
    },
    
    "Optimization (Healing Agent)": {
        "POST /optimize": {
            "request": {
                "performance_history": "List of metrics (list)"
            },
            "response": {
                "success": "bool",
                "optimizations_applied": "int",
                "performance_improvement": "float",
                "task_id": "string (tracking)",
                "errors": "list"
            },
            "agents_involved": ["Healing subagent"]
        }
    },
    
    "Task Management": {
        "GET /tasks": "Get task execution summary",
        "GET /tasks/json": "Export all tasks as JSON"
    }
}

# DeepAgents Architecture
DEEPAGENTS_SUBAGENTS = {
    "Master Agent": "Main orchestrator (Flashpoint integration)",
    "Ingestion Subagent": "Document parsing and chunking",
    "Retrieval Subagent": "Context retrieval and ranking",
    "Healing Subagent": "Performance optimization and fixes",
    "Config Subagent": "System configuration management"
}

DEEPAGENTS_PERSISTENCE = {
    "FilesystemBackend": "Persists agent state to disk",
    "TodoListMiddleware": "Maintains task planning and tracking",
    "TaskManager": "Chain-of-thought reasoning tracking"
}


# ==============================================================================
# REQUEST/RESPONSE EXAMPLES
# ==============================================================================

LANGGRAPH_INGEST_EXAMPLE = {
    "request": {
        "text": "Artificial intelligence is transforming how we work and live.",
        "doc_id": "ai_doc_001",
        "metadata": {
            "source": "whitepaper.pdf",
            "category": "technology"
        }
    },
    "response": {
        "success": True,
        "doc_id": "ai_doc_001",
        "chunks_created": 3,
        "vectors_saved": 3,
        "metadata_stored": True,
        "message": "Document ai_doc_001 ingested successfully",
        "errors": []
    }
}

LANGGRAPH_ASK_EXAMPLE = {
    "request": {
        "question": "What is artificial intelligence?",
        "response_mode": "concise",
        "top_k": 5
    },
    "response": {
        "success": True,
        "question": "What is artificial intelligence?",
        "answer": "Artificial intelligence is the simulation of human intelligence...",
        "response_mode": "concise",
        "context_chunks": 2,
        "guardrails_passed": True,
        "traceability": {
            "sources": ["ai_doc_001"],
            "retrieval_time_ms": 145,
            "timestamp": "2025-11-29T10:30:00"
        },
        "confidence_score": 0.94
    }
}

DEEPAGENTS_INGEST_EXAMPLE = {
    "request": {
        "text": "Machine learning algorithms learn patterns from data.",
        "doc_id": "ml_doc_001"
    },
    "response": {
        "success": True,
        "doc_id": "ml_doc_001",
        "chunks_created": 4,
        "vectors_saved": 4,
        "task_id": "task_ingest_20251129_001",
        "message": "Document ml_doc_001 ingested via multi-agent workflow"
    }
}

DEEPAGENTS_ASK_EXAMPLE = {
    "request": {
        "question": "How do machine learning algorithms work?",
        "top_k": 5
    },
    "response": {
        "success": True,
        "question": "How do machine learning algorithms work?",
        "answer": "Machine learning algorithms learn patterns from data...",
        "context_chunks": 3,
        "task_id": "task_retrieval_20251129_001",
        "reasoning_steps": 5,
        "message": "Question processed successfully via multi-agent workflow"
    }
}


# ==============================================================================
# ERROR HANDLING
# ==============================================================================

COMMON_ERRORS = {
    "503 Service Unavailable": "Agent not initialized - check logs",
    "500 Internal Server Error": "Processing error - see error details",
    "400 Bad Request": "Invalid input format - check request schema",
    "404 Not Found": "Endpoint not found - verify URL"
}

ERROR_RESPONSE_FORMAT = {
    "success": False,
    "message": "Error description",
    "errors": ["error_1", "error_2"],
    "task_id": "task_xyz (if applicable)"
}


# ==============================================================================
# DEPLOYMENT CHECKLIST
# ==============================================================================

DEPLOYMENT_CHECKLIST = {
    "Pre-Deployment": [
        "✓ Install dependencies: pip install -r requirements.txt",
        "✓ Configure llm_config.json in src/rag/config/",
        "✓ Set up database: python scripts/setup_db.py",
        "✓ Verify Ollama running: ollama serve",
        "✓ Check ports 8001, 8002 are available"
    ],
    
    "Deployment": [
        "✓ Run app.py: python app.py",
        "✓ Verify both servers started successfully",
        "✓ Test health endpoints: /health",
        "✓ Access Swagger docs: /docs"
    ],
    
    "Post-Deployment": [
        "✓ Monitor logs for errors",
        "✓ Test ingest endpoint with sample document",
        "✓ Test ask endpoint with sample question",
        "✓ Set up monitoring/alerting"
    ]
}


# ==============================================================================
# MONITORING & METRICS
# ==============================================================================

METRICS_TO_TRACK = {
    "Request Metrics": [
        "Average response time (ms)",
        "Request throughput (req/sec)",
        "Error rate (%)",
        "P95/P99 latency"
    ],
    
    "RAG Metrics": [
        "Retrieval accuracy",
        "Document ingestion success rate",
        "Guardrails pass rate",
        "Context relevance score"
    ],
    
    "Agent-Specific": {
        "LangGraph": [
            "Response mode distribution",
            "Average confidence score",
            "Guardrails validation rate"
        ],
        "DeepAgents": [
            "Average reasoning steps",
            "Agent collaboration efficiency",
            "Task execution time"
        ]
    }
}


# ==============================================================================
# INTEGRATION PATTERNS
# ==============================================================================

# Pattern 1: Sequential Processing
PATTERN_SEQUENTIAL = """
1. Ingest documents → /ingest
2. Wait for success
3. Ask questions → /ask
4. Get answers with context
"""

# Pattern 2: Batch Processing
PATTERN_BATCH = """
1. Ingest multiple documents → /ingest (parallel)
2. Collect results
3. Ask multiple questions → /ask (sequential)
4. Aggregate answers
"""

# Pattern 3: Optimization Loop
PATTERN_OPTIMIZATION = """
1. Ask questions and collect metrics
2. Analyze performance
3. Send to /optimize endpoint
4. Apply config changes
5. Re-test with optimized config
"""

# Pattern 4: Agent Selection (LangGraph vs DeepAgents)
PATTERN_AGENT_SELECTION = """
Use LangGraph (8001) if:
  ✓ Need fast, consistent answers
  ✓ Standard RAG queries
  ✓ Production environment
  
Use DeepAgents (8002) if:
  ✓ Need complex reasoning
  ✓ Multi-agent collaboration beneficial
  ✓ Require task tracking
"""


if __name__ == "__main__":
    print("API Architecture Documentation")
    print("=" * 60)
    print(f"LangGraph RAG Agent: Port {PORT_LANGGRAPH}")
    print(f"DeepAgents Orchestrator: Port {PORT_DEEPAGENTS}")
    print("=" * 60)
    print("\nBoth servers run simultaneously on different ports.")
    print("See API_README.md for complete documentation.")
