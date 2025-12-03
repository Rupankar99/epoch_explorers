#!/usr/bin/env python3
"""
Service Status Checker
Check if Backend API, Streamlit, and other services are running
"""

import socket
import sys
import time
from datetime import datetime

def check_port(port, service_name):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            return True, "✅ RUNNING"
        else:
            return False, "⏸️  NOT RUNNING"
    except Exception as e:
        return False, f"❌ ERROR: {e}"

def check_health(port):
    """Check health endpoint"""
    try:
        import requests
        response = requests.get(f'http://localhost:{port}/health', timeout=2)
        if response.status_code == 200:
            return True, response.json().get('status', 'OK')
        else:
            return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]

def main():
    """Check all services"""
    
    print("\n" + "="*70)
    print(f"  📊 SERVICE STATUS CHECK - {datetime.now().strftime('%H:%M:%S')}")
    print("="*70 + "\n")
    
    services = [
        (8001, "Backend API (LangGraph)"),
        (8501, "Streamlit Dashboard"),
        (11434, "Ollama LLM"),
    ]
    
    print(f"{'Service':<35} {'Status':<20} {'Details'}\n" + "-"*70)
    
    all_running = True
    
    for port, name in services:
        is_running, status = check_port(port, name)
        
        # Try health check for main API
        details = ""
        if port == 8001 and is_running:
            health_ok, health_msg = check_health(port)
            details = f"Health: {health_msg}"
            if not health_ok:
                all_running = False
        elif not is_running:
            all_running = False
        
        print(f"{name:<35} {status:<20} {details}")
    
    print("\n" + "-"*70)
    
    print("\n🔗 URLS:\n")
    if check_port(8001, "")[0]:
        print("  Backend API: http://localhost:8001")
        print("  API Docs: http://localhost:8001/docs")
    
    if check_port(8501, "")[0]:
        print("  Streamlit: http://localhost:8501")
    
    print("\n" + "="*70)
    
    if all_running:
        print("✅ ALL SERVICES RUNNING\n")
        return 0
    else:
        print("⚠️  SOME SERVICES NOT RUNNING\n")
        print("To start services:")
        print("  python quick_launch.py\n")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        sys.exit(1)
