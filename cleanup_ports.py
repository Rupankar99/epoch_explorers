#!/usr/bin/env python3
"""
Kill processes using specific ports
Useful for cleaning up stuck API servers
"""

import subprocess
import sys
import os

def kill_port(port):
    """Kill process using a specific port"""
    try:
        # Get PID using netstat
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            # Extract PID (last column)
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'LISTENING' in line:
                    parts = line.split()
                    pid = parts[-1]
                    
                    print(f"Found process on port {port}: PID {pid}")
                    
                    # Kill the process
                    kill_result = subprocess.run(
                        f'taskkill /PID {pid} /F',
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    
                    if kill_result.returncode == 0:
                        print(f"✅ Killed process {pid}")
                        return True
                    else:
                        print(f"❌ Failed to kill process {pid}")
                        return False
        else:
            print(f"ℹ️  No process using port {port}")
            return True
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    ports = [8001, 8002, 8501]
    
    print("\n" + "="*60)
    print("🧹 CLEANING UP PORTS")
    print("="*60 + "\n")
    
    for port in ports:
        print(f"Checking port {port}...")
        kill_port(port)
        print()
    
    print("="*60)
    print("✅ Cleanup complete\n")
    print("Now you can run:")
    print("  python quick_launch.py\n")

if __name__ == "__main__":
    main()
