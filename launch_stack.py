#!/usr/bin/env python3
"""
Launch Stack - Start Backend API, Streamlit, and RBAC Testing
Run from project root: python launch_stack.py
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def launch_backend_api():
    """Launch LangGraph Backend API on port 8001"""
    print_header("🚀 LAUNCHING BACKEND API (Port 8001)")
    print("Command: python run_api.py langgraph")
    print("\nWaiting for API to start...")
    print("  📚 Swagger UI: http://localhost:8001/docs")
    print("  ✅ When you see 'Uvicorn running', the API is ready\n")
    
    try:
        subprocess.Popen(
            [sys.executable, "run_api.py", "langgraph"],
            cwd=str(Path(__file__).parent),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        print("✓ Backend API process started (check new window)")
        time.sleep(3)
    except Exception as e:
        print(f"✗ Failed to launch backend API: {e}")
        return False
    
    return True

def launch_streamlit():
    """Launch Streamlit Dashboard on port 8501"""
    print_header("🎨 LAUNCHING STREAMLIT DASHBOARD (Port 8501)")
    print("Command: streamlit run streamlit_launcher.py")
    print("\nWaiting for dashboard to start...")
    print("  🌐 Dashboard: http://localhost:8501")
    print("  ⏳ First run takes 30-60 seconds (loading models)\n")
    
    try:
        subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "streamlit_launcher.py", 
             "--logger.level=warning"],
            cwd=str(Path(__file__).parent),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        print("✓ Streamlit dashboard process started (check new window)")
        time.sleep(5)
    except Exception as e:
        print(f"✗ Failed to launch Streamlit: {e}")
        return False
    
    return True

def test_rbac():
    """Run RBAC test suite"""
    print_header("🔐 TESTING RBAC SYSTEM")
    print("Command: python test_namespace_rbac.py")
    print("\nRunning RBAC namespace tests...\n")
    
    try:
        result = subprocess.run(
            [sys.executable, "test_namespace_rbac.py"],
            cwd=str(Path(__file__).parent),
            capture_output=False,
            timeout=120
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("✗ RBAC tests timed out")
        return False
    except Exception as e:
        print(f"✗ Failed to run RBAC tests: {e}")
        return False

def main():
    """Main launcher"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║          EPOCH EXPLORERS - FULL STACK LAUNCHER                     ║
║                                                                    ║
║  This will launch:                                                 ║
║  1. Backend API (LangGraph) - Port 8001                            ║
║  2. Streamlit Dashboard - Port 8501                                ║
║  3. RBAC Testing Suite                                             ║
║                                                                    ║
║  Each will open in a new window                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    input("Press ENTER to start launching services...\n")
    
    # Launch backend API
    if not launch_backend_api():
        print("⚠️  Backend API launch failed, but continuing...")
    
    # Wait for API to be ready
    print("⏳ Waiting 10 seconds for API to initialize...")
    time.sleep(10)
    
    # Launch Streamlit
    if not launch_streamlit():
        print("⚠️  Streamlit launch failed, but continuing...")
    
    # Wait for dashboard to be ready
    print("⏳ Waiting 15 seconds for dashboard to initialize...")
    time.sleep(15)
    
    print_header("📋 SERVICES LAUNCHED")
    print("""
✅ Backend API:
   URL: http://localhost:8001
   Docs: http://localhost:8001/docs
   Test endpoint: curl http://localhost:8001/health

✅ Streamlit Dashboard:
   URL: http://localhost:8501
   
✅ Ready for RBAC Testing

To test RBAC functionality:
   1. Open http://localhost:8501 in browser
   2. Use the dashboard to upload documents
   3. Test with different user roles (root, tenant, etc.)
   4. Run: python test_namespace_rbac.py
    """)
    
    # Ask if user wants to run RBAC tests
    print("\n" + "="*70)
    response = input("\nRun RBAC tests now? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\n")
        test_rbac()
    
    print_header("✨ SETUP COMPLETE")
    print("""
Your services are running in separate windows:
  • Check the Backend API window for API logs
  • Check the Streamlit window for dashboard logs
  • Both windows will continue running

To stop services:
  • Close the windows, or
  • Ctrl+C in each window

Happy testing! 🚀
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⛔ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
