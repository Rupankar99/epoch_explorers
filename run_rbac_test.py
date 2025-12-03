#!/usr/bin/env python3
"""
RBAC Test Runner
Executes the RBAC ingestion and retrieval test suite
"""

import subprocess
import sys
import time

def main():
    """Run the RBAC test"""
    print("\n" + "="*80)
    print("  RUNNING RBAC INGESTION & RETRIEVAL TEST")
    print("="*80 + "\n")
    
    # Check if API is running
    print("Checking if API is running on localhost:8001...")
    try:
        import requests
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code != 200:
            print("ERROR: API is not responding properly")
            print("Please start the API with: python scripts/quick_launch.py")
            sys.exit(1)
        print("✓ API is running\n")
    except Exception as e:
        print(f"ERROR: Cannot connect to API: {e}")
        print("Please start the API with: python scripts/quick_launch.py")
        sys.exit(1)
    
    # Run the test
    try:
        result = subprocess.run(
            [sys.executable, "test_rbac_ingestion.py"],
            cwd="e:\\epoch_explorers",
            capture_output=False
        )
        sys.exit(result.returncode)
    except Exception as e:
        print(f"ERROR: Failed to run test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
