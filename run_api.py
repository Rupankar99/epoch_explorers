#!/usr/bin/env python3
"""
Single-Server Runner
Run either LangGraph or DeepAgents server individually
"""

import sys
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_langgraph():
    """Run only LangGraph API"""
    import uvicorn
    from src.rag.agents.langgraph_agent.api import app
    
    logger.info("🚀 Starting LangGraph RAG Agent API on port 8001...")
    logger.info("📚 Swagger UI: http://localhost:8001/docs")
    logger.info("❌ DeepAgents NOT running")
    logger.info("")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )


def run_deepagents():
    """Run only DeepAgents API"""
    import uvicorn
    from src.rag.agents.deepagents.api import app
    
    logger.info("🚀 Starting DeepAgents RAG Orchestrator API on port 8002...")
    logger.info("📚 Swagger UI: http://localhost:8002/docs")
    logger.info("❌ LangGraph NOT running")
    logger.info("")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )


def run_both():
    """Run both servers using subprocess (no threading)"""
    import subprocess
    import time
    
    logger.info("🚀 Starting both API servers...")
    logger.info("=" * 60)
    
    # Start LangGraph in subprocess
    logger.info("Starting LangGraph on port 8001...")
    lg_process = subprocess.Popen(
        [sys.executable, __file__, "langgraph"],
        cwd="."
    )
    
    time.sleep(2)
    
    # Start DeepAgents in subprocess
    logger.info("Starting DeepAgents on port 8002...")
    da_process = subprocess.Popen(
        [sys.executable, __file__, "deepagents"],
        cwd="."
    )
    
    logger.info("=" * 60)
    logger.info("✅ Both servers started!")
    logger.info("")
    logger.info("📚 API Documentation:")
    logger.info("  - LangGraph: http://localhost:8001/docs")
    logger.info("  - DeepAgents: http://localhost:8002/docs")
    logger.info("")
    logger.info("Press Ctrl+C to stop all servers")
    logger.info("=" * 60)
    
    try:
        # Wait for both processes
        lg_process.wait()
        da_process.wait()
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        lg_process.terminate()
        da_process.terminate()
        lg_process.wait()
        da_process.wait()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "langgraph":
            run_langgraph()
        elif sys.argv[1] == "deepagents":
            run_deepagents()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Usage: python run_api.py [langgraph|deepagents|both]")
            sys.exit(1)
    else:
        run_both()
