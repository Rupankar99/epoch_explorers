#!/usr/bin/env python3
"""
Quick launcher for epoch_explorers services (API + Streamlit)
Starts both services in separate background processes without waiting/hanging
"""

import subprocess
import sys
import time
import os
from pathlib import Path


def main():
    """Launch API and Streamlit services in separate processes"""
    
    # Get workspace root
    workspace_root = Path(__file__).parent.parent
    os.chdir(workspace_root)
    
    print("=" * 70)
    print("EPOCH EXPLORERS - Service Launcher")
    print("=" * 70)
    
    # Kill any existing processes on the ports
    print("\n[1/3] Cleaning up ports 8001, 8002, 8501...")
    try:
        cleanup_cmd = f'powershell.exe -Command "Get-NetTCPConnection -LocalPort 8001,8002,8501 -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"'
        subprocess.run(cleanup_cmd, shell=True, capture_output=True, timeout=5)
        time.sleep(1)
    except Exception as e:
        print(f"  [WARN] Could not cleanup ports: {e}")
    
    # Start FastAPI backend
    print("\n[2/3] Starting FastAPI backend (port 8001)...")
    try:
        api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", 
             "src.rag.agents.langgraph_agent.api:app", 
             "--host", "127.0.0.1", 
             "--port", "8001",
             "--reload"],
            cwd=workspace_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("  ✓ API process started (PID: {})".format(api_process.pid))
    except Exception as e:
        print(f"  ✗ Failed to start API: {e}")
        return 1
    
    time.sleep(3)  # Give API time to initialize
    
    # Start Streamlit dashboard
    print("\n[3/3] Starting Streamlit dashboard (port 8501)...")
    try:
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run",
             "src/pages/streamlit_app.py",
             "--server.port=8501",
             "--server.address=127.0.0.1",
             "--logger.level=info"],
            cwd=workspace_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("  ✓ Streamlit process started (PID: {})".format(streamlit_process.pid))
    except Exception as e:
        print(f"  ✗ Failed to start Streamlit: {e}")
        if api_process:
            api_process.terminate()
        return 1
    
    print("\n" + "=" * 70)
    print("SERVICES STARTED SUCCESSFULLY")
    print("=" * 70)
    print("\n📊 Dashboard: http://localhost:8501")
    print("🔌 API Docs: http://localhost:8001/docs")
    print("\nPress Ctrl+C to stop all services...\n")
    
    try:
        # Wait for both processes (they should run indefinitely)
        api_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\n\n[SHUTDOWN] Stopping services...")
        
        try:
            api_process.terminate()
            streamlit_process.terminate()
            time.sleep(2)
            
            api_process.kill()
            streamlit_process.kill()
        except Exception as e:
            print(f"[WARN] Error during shutdown: {e}")
        
        print("[OK] Services stopped")
        return 0


if __name__ == "__main__":
    sys.exit(main())
