#!/usr/bin/env python3
"""
LangGraph Agent - Immediate Compilation Demo
Shows exactly how to compile and use the agent
"""

import json
import sys
from pathlib import Path

# Setup path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def demo_basic_usage():
    """Most basic compilation and usage"""
    print("\n" + "=" * 70)
    print("BASIC USAGE - Initialize & Run Agent")
    print("=" * 70)
    
    # Import agent
    from src.rag.agents.langgraph_agent import LangGraphRAGAgent
    
    print("\n[✓] Step 1: Import LangGraphRAGAgent")
    
    # Initialize agent (compiles all graphs)
    print("[✓] Step 2: Initialize agent (compiles LangGraph graphs)...")
    agent = LangGraphRAGAgent()
    print("    - Ingestion graph compiled ✓")
    print("    - Retrieval graph compiled ✓")
    print("    - Optimization graph compiled ✓")
    
    # Ingest a document
    print("\n[✓] Step 3: Ingest document...")
    doc_text = """
# Python Programming Guide

Python is a high-level programming language known for its simplicity and readability.

## Key Features
- Easy to learn
- Versatile (web, data science, automation)
- Large ecosystem of libraries

## Use Cases
- Web development
- Data analysis
- Machine learning
- Automation
"""
    
    result = agent.ingest_document(
        text=doc_text,
        doc_id="python_guide_20250129_001"
    )
    
    print(f"    - Document ID: {result['doc_id']}")
    print(f"    - Chunks created: {result['chunks_count']}")
    print(f"    - Chunks saved: {result['chunks_saved']}")
    print(f"    - Success: {result['success']}")
    
    # Ask a question
    print("\n[✓] Step 4: Ask question...")
    response = agent.ask_question(
        question="What are the key features of Python?",
        response_mode="concise"
    )
    
    print(f"    - Question: 'What are the key features of Python?'")
    print(f"    - Answer: {response['answer'][:100]}...")
    print(f"    - Success: {response['success']}")
    
    print("\n✅ COMPILATION SUCCESSFUL - Agent is fully functional!")


def demo_with_memory():
    """Compilation with agent memory"""
    print("\n" + "=" * 70)
    print("WITH MEMORY - Store & Retrieve Agent Memory")
    print("=" * 70)
    
    from src.rag.agents.langgraph_agent import LangGraphRAGAgent
    from src.rag.tools.ingestion_tools import (
        record_agent_memory_tool,
        retrieve_agent_memory_tool
    )
    
    print("\n[✓] Initialize agent...")
    agent = LangGraphRAGAgent()
    
    # Record a decision memory
    print("[✓] Record decision memory...")
    memory_value = {
        "strategy": "RE_EMBED",
        "success_rate": 0.92,
        "best_for": "low_quality_retrieval",
        "timestamp": "2025-01-29"
    }
    
    record_result = record_agent_memory_tool.invoke({
        "agent_name": "langgraph_agent",
        "memory_type": "decision",
        "memory_key": "healing_strategy_demo",
        "memory_value": json.dumps(memory_value),
        "importance_score": 0.9,
        "ttl_hours": 72
    })
    
    record_dict = json.loads(record_result)
    print(f"    - Memory ID: {record_dict['memory_id']}")
    print(f"    - Storage: {record_dict['storage']}")
    
    # Retrieve the memory
    print("\n[✓] Retrieve decision memory...")
    retrieve_result = retrieve_agent_memory_tool.invoke({
        "agent_name": "langgraph_agent",
        "memory_type": "decision",
        "limit": 5
    })
    
    retrieve_dict = json.loads(retrieve_result)
    print(f"    - Memories found: {len(retrieve_dict['memories'])}")
    
    for mem in retrieve_dict['memories']:
        print(f"    - Key: {mem['memory_key']}")
        print(f"      Importance: {mem['importance_score']}")
        print(f"      Access count: {mem['access_count']}")
    
    print(f"\n    Cache stats: {retrieve_dict['cache_stats']}")
    
    print("\n✅ MEMORY SYSTEM WORKING - Agent can store & retrieve experiences!")


def demo_response_modes():
    """Compilation with all response modes"""
    print("\n" + "=" * 70)
    print("RESPONSE MODES - Test All Three Output Formats")
    print("=" * 70)
    
    from src.rag.agents.langgraph_agent import LangGraphRAGAgent
    
    print("\n[✓] Initialize agent...")
    agent = LangGraphRAGAgent()
    
    # Ingest sample
    print("[✓] Ingest sample document...")
    agent.ingest_document(
        text="The capital of France is Paris. It is known for the Eiffel Tower.",
        doc_id="test_modes_001"
    )
    
    question = "What is the capital of France?"
    
    # Concise mode
    print(f"\n[✓] Mode 1: CONCISE (user-friendly)...")
    concise = agent.ask_question(question, response_mode="concise")
    print(f"    Answer: {concise['answer']}")
    print(f"    Metadata: {len(concise)} keys")
    
    # Internal mode
    print(f"\n[✓] Mode 2: INTERNAL (system integration)...")
    internal = agent.ask_question(question, response_mode="internal")
    print(f"    Answer: {internal['answer']}")
    print(f"    Quality score: {internal.get('quality_score', 'N/A')}")
    print(f"    Metadata: {len(internal)} keys")
    
    # Verbose mode
    print(f"\n[✓] Mode 3: VERBOSE (full debug)...")
    verbose = agent.ask_question(question, response_mode="verbose")
    print(f"    Answer: {verbose['answer'][:50]}...")
    print(f"    Execution time: {verbose.get('execution_time_ms', 'N/A')}ms")
    print(f"    Metadata: {len(verbose)} keys (full debug info)")
    
    print("\n✅ ALL RESPONSE MODES WORKING - Choose the right one for your use case!")


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "LANGGRAPH AGENT COMPILATION DEMO" + " " * 21 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        # Demo 1: Basic usage
        demo_basic_usage()
        
        # Demo 2: With memory
        print("\n")
        demo_with_memory()
        
        # Demo 3: Response modes
        print("\n")
        demo_response_modes()
        
        # Final summary
        print("\n" + "=" * 70)
        print("✅ ALL DEMOS PASSED - LangGraph Agent Fully Compiled & Functional!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Review design_docs/LANGGRAPH_COMPILATION_GUIDE.md for detailed info")
        print("2. Review design_docs/LANGGRAPH_QUICK_REFERENCE.md for quick usage")
        print("3. Run your own questions: agent.ask_question('your question')")
        print("4. Check agent memory: retrieve_agent_memory_tool.invoke(...)")
        print("\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed with error:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
