#!/usr/bin/env python3
"""
Quick Launch - Start all services with minimal wait time
"""

import subprocess
import sys
import os
from pathlib import Path

def launch():
    """Launch all services in new windows"""
    
    root = Path(__file__).parent
    
    print("\n" + "="*70)
    print("🚀 LAUNCHING FULL STACK")
    print("="*70 + "\n")
    
    # Launch Backend API
    print("📡 Launching Backend API (Port 8001)...")
    try:
        subprocess.Popen(
            [sys.executable, "run_api.py", "langgraph"],
            cwd=str(root),
            shell=False
        )
        print("   ✓ Backend API started")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n")
    
    # Launch Streamlit Dashboard
    print("🎨 Launching Streamlit Dashboard (Port 8501)...")
    try:
        subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "streamlit_launcher.py", "--logger.level=warning"],
            cwd=str(root),
            shell=False
        )
        print("   ✓ Streamlit started")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "="*70)
    print("""
✅ SERVICES LAUNCHED!

🌐 Open in browser:
   Backend API Docs: http://localhost:8001/docs
   Streamlit Dashboard: http://localhost:8501

📊 Test RBAC:
   python test_namespace_rbac.py

⏹️  To stop: Close the windows or Ctrl+C in terminal
    """)
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        launch()
        # Keep script running
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⛔ Stopped")
        sys.exit(0)
