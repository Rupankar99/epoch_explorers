#!/usr/bin/env python3
"""
Pre-Flight Checklist for FastAPI Servers

Run this before starting the API servers to ensure everything is configured.
"""

import os
import sys
import json
from pathlib import Path

def check_file_exists(path: str, name: str) -> bool:
    """Check if a file exists"""
    if Path(path).exists():
        print(f"  ✅ {name}: {path}")
        return True
    else:
        print(f"  ❌ {name}: {path} (MISSING)")
        return False

def check_python_package(package: str) -> bool:
    """Check if a Python package is installed"""
    try:
        __import__(package)
        print(f"  ✅ {package} installed")
        return True
    except ImportError:
        print(f"  ❌ {package} not installed")
        return False

def check_port_available(port: int) -> bool:
    """Check if a port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result == 0:
        print(f"  ⚠️  Port {port} is in use")
        return False
    else:
        print(f"  ✅ Port {port} available")
        return True

def main():
    print("\n" + "=" * 70)
    print("🚀 FastAPI Servers Pre-Flight Checklist")
    print("=" * 70 + "\n")
    
    checks_passed = 0
    checks_failed = 0
    warnings = 0
    
    # 1. File Structure Check
    print("📁 FILE STRUCTURE CHECK")
    print("-" * 70)
    
    files_to_check = [
        ("e:/epoch_explorers/app.py", "Main app.py"),
        ("e:/epoch_explorers/src/rag/agents/langgraph_agent/api.py", "LangGraph API"),
        ("e:/epoch_explorers/src/rag/agents/deepagents/api.py", "DeepAgents API"),
        ("e:/epoch_explorers/src/rag/agents/langgraph_agent/langgraph_rag_agent.py", "LangGraph Agent"),
        ("e:/epoch_explorers/src/rag/agents/deepagents/deepagents_rag_agent.py", "DeepAgents Agent"),
    ]
    
    for file_path, name in files_to_check:
        if check_file_exists(file_path, name):
            checks_passed += 1
        else:
            checks_failed += 1
    
    print()
    
    # 2. Configuration Check
    print("⚙️  CONFIGURATION CHECK")
    print("-" * 70)
    
    config_files = [
        ("e:/epoch_explorers/src/rag/config/llm_config.json", "LLM Config"),
        ("e:/epoch_explorers/.env", ".env File (optional)"),
    ]
    
    for file_path, name in config_files:
        if check_file_exists(file_path, name):
            checks_passed += 1
        else:
            if "optional" in name:
                warnings += 1
                print(f"     ({name} is optional, can run without it)")
            else:
                checks_failed += 1
    
    print()
    
    # 3. Database Check
    print("💾 DATABASE CHECK")
    print("-" * 70)
    
    db_file = "e:/epoch_explorers/incident_iq.db"
    if check_file_exists(db_file, "SQLite Database"):
        checks_passed += 1
    else:
        print("     Run: python scripts/setup_db.py")
        checks_failed += 1
    
    print()
    
    # 4. Python Packages Check
    print("📦 PYTHON PACKAGES CHECK")
    print("-" * 70)
    
    packages_to_check = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("langchain", "LangChain"),
        ("langgraph", "LangGraph"),
        ("chromadb", "ChromaDB"),
    ]
    
    for package, name in packages_to_check:
        if check_python_package(package):
            checks_passed += 1
        else:
            checks_failed += 1
    
    print()
    
    # 5. Port Availability Check
    print("🔌 PORT AVAILABILITY CHECK")
    print("-" * 70)
    
    ports_to_check = [
        (8001, "LangGraph API"),
        (8002, "DeepAgents API"),
    ]
    
    for port, name in ports_to_check:
        if check_port_available(port):
            checks_passed += 1
        else:
            warnings += 1
            print(f"     Run: netstat -ano | findstr :{port}")
    
    print()
    
    # 6. External Services Check
    print("🌐 EXTERNAL SERVICES CHECK")
    print("-" * 70)
    
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 11434))
        sock.close()
        
        if result == 0:
            print("  ✅ Ollama is running (Port 11434)")
            checks_passed += 1
        else:
            print("  ⚠️  Ollama not detected (Port 11434)")
            print("     Run: ollama serve")
            warnings += 1
    except Exception as e:
        print(f"  ❌ Error checking Ollama: {str(e)}")
        checks_failed += 1
    
    print()
    
    # Summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"  ✅ Passed:  {checks_passed}")
    print(f"  ❌ Failed:  {checks_failed}")
    print(f"  ⚠️  Warnings: {warnings}")
    print("=" * 70)
    
    if checks_failed == 0:
        print("\n✅ ALL CHECKS PASSED! Ready to start API servers.\n")
        print("🚀 Start servers with: python app.py\n")
        return 0
    else:
        print(f"\n❌ {checks_failed} checks failed. Please fix the issues above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
