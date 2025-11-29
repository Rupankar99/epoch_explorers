#!/usr/bin/env python3
"""
Quick compilation and test script for LangGraph Agent
Run this to verify everything is working correctly
"""

import sys
import json
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test all critical imports"""
    print("\n[1/7] Testing imports...")
    try:
        from langgraph.graph import StateGraph, START, END
        print("  ✓ LangGraph imported")
        
        from langchain_core.messages import HumanMessage
        print("  ✓ LangChain imported")
        
        from src.rag.agents.langgraph_agent import LangGraphRAGAgent
        print("  ✓ LangGraphRAGAgent imported")
        
        from src.database.models.agent_memory_model import AgentMemoryModel
        print("  ✓ AgentMemoryModel imported")
        
        from src.database.cache.agent_memory_cache import get_agent_memory_cache
        print("  ✓ AgentMemoryCache imported")
        
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        traceback.print_exc()
        return False


def test_config():
    """Test configuration files"""
    print("\n[2/7] Testing configuration...")
    try:
        from src.rag.config.env_config import EnvConfig
        
        rag_config = EnvConfig.get_rag_config_path()
        print(f"  ✓ RAG config path: {rag_config}")
        
        db_path = EnvConfig.get_db_path()
        print(f"  ✓ Database path: {db_path}")
        
        chroma_path = EnvConfig.get_chroma_db_path()
        print(f"  ✓ ChromaDB path: {chroma_path}")
        
        return True
    except Exception as e:
        print(f"  ✗ Config check failed: {e}")
        return False


def test_initialization():
    """Test agent initialization"""
    print("\n[3/7] Testing agent initialization...")
    try:
        from src.rag.agents.langgraph_agent import LangGraphRAGAgent
        
        agent = LangGraphRAGAgent()
        print("  ✓ Agent initialized successfully")
        
        # Check graphs compiled
        assert agent.ingestion_graph is not None, "Ingestion graph not compiled"
        print("  ✓ Ingestion graph compiled")
        
        assert agent.retrieval_graph is not None, "Retrieval graph not compiled"
        print("  ✓ Retrieval graph compiled")
        
        assert agent.optimization_graph is not None, "Optimization graph not compiled"
        print("  ✓ Optimization graph compiled")
        
        print("  ✓ All graphs compiled successfully")
        return True, agent
    except Exception as e:
        print(f"  ✗ Initialization failed: {e}")
        traceback.print_exc()
        return False, None


def test_ingestion(agent):
    """Test document ingestion"""
    print("\n[4/7] Testing document ingestion...")
    try:
        test_doc = """
# Test Document

This is a test document for LangGraph agent compilation.

## Section 1
Content about section 1.

## Section 2
Content about section 2.
"""
        
        result = agent.ingest_document(
            text=test_doc,
            doc_id="test_doc_compilation_001"
        )
        
        print(f"  ✓ Document ingested: {result['doc_id']}")
        print(f"  ✓ Chunks created: {result['chunks_count']}")
        print(f"  ✓ Chunks saved: {result['chunks_saved']}")
        
        if result['errors']:
            print(f"  ⚠ Errors: {result['errors']}")
        
        return result['success']
    except Exception as e:
        print(f"  ✗ Ingestion test failed: {e}")
        traceback.print_exc()
        return False


def test_retrieval(agent):
    """Test question retrieval"""
    print("\n[5/7] Testing question retrieval...")
    try:
        response = agent.ask_question(
            question="What is this document about?",
            response_mode="concise"
        )
        
        print(f"  ✓ Question answered")
        print(f"  ✓ Answer length: {len(response.get('answer', ''))} chars")
        print(f"  ✓ Success: {response.get('success', False)}")
        
        if response.get('errors'):
            print(f"  ⚠ Errors: {response['errors']}")
        
        print(f"  Sample answer: {response.get('answer', '')[:100]}...")
        
        return response.get('success', False)
    except Exception as e:
        print(f"  ✗ Retrieval test failed: {e}")
        traceback.print_exc()
        return False


def test_memory():
    """Test agent memory"""
    print("\n[6/7] Testing agent memory...")
    try:
        from src.rag.tools.ingestion_tools import record_agent_memory_tool, retrieve_agent_memory_tool
        
        # Record memory
        record_result = record_agent_memory_tool.invoke({
            "agent_name": "langgraph_agent",
            "memory_type": "context",
            "memory_key": "test_compilation_memory",
            "memory_value": json.dumps({"test": "compilation"}),
            "importance_score": 0.5,
            "ttl_hours": 24
        })
        
        record_dict = json.loads(record_result)
        assert record_dict.get('success'), "Memory recording failed"
        print(f"  ✓ Memory recorded: ID={record_dict.get('memory_id')}")
        
        # Retrieve memory
        retrieve_result = retrieve_agent_memory_tool.invoke({
            "agent_name": "langgraph_agent",
            "memory_type": "context",
            "limit": 10
        })
        
        retrieve_dict = json.loads(retrieve_result)
        assert retrieve_dict.get('success'), "Memory retrieval failed"
        print(f"  ✓ Memory retrieved: {len(retrieve_dict.get('memories', []))} entries")
        
        cache_stats = retrieve_dict.get('cache_stats', {})
        print(f"  ✓ Cache stats: {cache_stats['hits']} hits, {cache_stats['misses']} misses")
        
        return True
    except Exception as e:
        print(f"  ✗ Memory test failed: {e}")
        traceback.print_exc()
        return False


def test_response_modes(agent):
    """Test different response modes"""
    print("\n[7/7] Testing response modes...")
    try:
        question = "What is this test document?"
        
        # CONCISE mode
        concise_resp = agent.ask_question(question, response_mode="concise")
        print(f"  ✓ Concise mode: answer length={len(concise_resp.get('answer', ''))} chars")
        
        # INTERNAL mode
        internal_resp = agent.ask_question(question, response_mode="internal")
        print(f"  ✓ Internal mode: quality_score={internal_resp.get('quality_score', 'N/A')}")
        
        # VERBOSE mode
        verbose_resp = agent.ask_question(question, response_mode="verbose")
        print(f"  ✓ Verbose mode: execution_time_ms={verbose_resp.get('execution_time_ms', 'N/A')}ms")
        
        return True
    except Exception as e:
        print(f"  ✗ Response mode test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("LANGGRAPH AGENT - COMPILATION TEST")
    print("=" * 70)
    
    results = {}
    
    # Test 1: Imports
    results['imports'] = test_imports()
    if not results['imports']:
        print("\n❌ Import test failed. Cannot continue.")
        return False
    
    # Test 2: Config
    results['config'] = test_config()
    
    # Test 3: Initialization
    success, agent = test_initialization()
    results['initialization'] = success
    if not success or agent is None:
        print("\n❌ Initialization failed. Cannot continue.")
        return False
    
    # Test 4: Ingestion
    results['ingestion'] = test_ingestion(agent)
    
    # Test 5: Retrieval
    results['retrieval'] = test_retrieval(agent)
    
    # Test 6: Memory
    results['memory'] = test_memory()
    
    # Test 7: Response Modes
    results['response_modes'] = test_response_modes(agent)
    
    # Summary
    print("\n" + "=" * 70)
    print("COMPILATION TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 LangGraph Agent compilation successful!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
