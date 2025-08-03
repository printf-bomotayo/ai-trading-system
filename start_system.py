#!/usr/bin/env python3
"""
Complete system startup script for the AI Trading System
Starts both the API backend and Streamlit frontend
"""

import sys
import os
import subprocess
import time
import threading
from pathlib import Path
import requests

def check_dependencies():
    """Check if all required dependencies are installed"""
    
    required_packages = [
        # API dependencies
        'fastapi', 'uvicorn', 'pydantic', 'aiohttp', 'asyncpg',
        # Frontend dependencies  
        'streamlit', 'plotly', 'pandas', 'requests', 'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("ERROR Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall missing packages with:")
        print("   pip install fastapi uvicorn pydantic aiohttp asyncpg streamlit plotly pandas requests numpy")
        print("   OR")
        print("   pip install -r requirements.txt")
        print("   pip install -r requirements_frontend.txt")
        return False
    
    print("OK All required packages are installed")
    return True

def check_files():
    """Check if required files exist"""
    
    required_files = ["api.py", "frontend.py", "core.py", "database.py"]
    missing_files = []
    
    for file_name in required_files:
        if not Path(file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print("ERROR Missing required files:")
        for file_name in missing_files:
            print(f"   - {file_name}")
        print("\nPlease run this script from the trading system directory")
        return False
    
    print("OK All required files found")
    return True

def wait_for_api(url: str, timeout: int = 30) -> bool:
    """Wait for API to become available"""
    
    print(f"Waiting for API at {url}...")
    
    for i in range(timeout):
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                print("OK API is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        if i % 5 == 0:
            print(f"   Still waiting... ({i}/{timeout}s)")
    
    print("ERROR API did not become ready in time")
    return False

def start_api_server():
    """Start the API server in a separate thread"""
    
    print("Starting AI Trading System API...")
    
    try:
        # Start the API server
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "api:app",
            "--host", "0.0.0.0", 
            "--port", "8035",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("API server stopped")
    except Exception as e:
        print(f"ERROR Failed to start API server: {e}")

def start_frontend():
    """Start the Streamlit frontend"""
    
    print("Starting AI Trading System Frontend...")
    
    try:
        # Set environment variables
        os.environ["STREAMLIT_SERVER_PORT"] = "8501"
        os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
        os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
        
        # Start the frontend
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "frontend.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("Frontend stopped")
    except Exception as e:
        print(f"ERROR Failed to start frontend: {e}")

def print_startup_info():
    """Print system startup information"""
    
    print("\nAI Trading System - Complete Startup")
    print("=" * 50)
    print("This script will start both the API backend and web frontend.")
    print()
    print("Services that will be started:")
    print("  1. API Backend (FastAPI) - http://localhost:8035")
    print("     - Trading analysis endpoints")
    print("     - System management API")
    print("     - Interactive documentation")
    print()
    print("  2. Web Frontend (Streamlit) - http://localhost:8501")
    print("     - Interactive trading interface")
    print("     - Analytics dashboard")
    print("     - System monitoring")
    print()
    print("Prerequisites:")
    print("  - Python 3.8+ with required packages installed")
    print("  - PostgreSQL database (optional, for persistence)")
    print("  - LLM API keys (optional, for AI analysis)")
    print()

def print_access_info():
    """Print access information after startup"""
    
    print("\n" + "=" * 50)
    print("SYSTEM READY!")
    print("=" * 50)
    print()
    print("Access your AI Trading System:")
    print("  Web Interface:     http://localhost:8501")
    print("  API Documentation: http://localhost:8035/docs")
    print("  Health Check:      http://localhost:8035/health")
    print()
    print("Quick Start:")
    print("  1. Open http://localhost:8501 in your browser")
    print("  2. Configure API settings in the sidebar")
    print("  3. Enter market data for any stock symbol")
    print("  4. Click 'Analyze Trading Opportunity'")
    print("  5. Review AI-powered recommendations")
    print()
    print("Default Authentication:")
    print("  API Key: dev-key-12345")
    print()
    print("To stop the system:")
    print("  Press Ctrl+C in this terminal")
    print()

def start_both_services():
    """Start both API and frontend services"""
    
    print("Starting both API and frontend services...")
    print("Note: This will start both services in the same terminal")
    print("Use separate terminals for independent control")
    print()
    
    # Start API in a separate thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # Wait for API to be ready
    if not wait_for_api("http://localhost:8035"):
        print("ERROR Failed to start API server")
        return False
    
    print_access_info()
    
    # Start frontend (this will block)
    start_frontend()
    
    return True

def main():
    """Main startup function"""
    
    print("AI Trading System - System Startup")
    print("=" * 50)
    
    # Check requirements
    if not check_files():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    print()
    
    # Show startup options
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--api-only":
            print("Starting API server only...")
            start_api_server()
        elif command == "--frontend-only":
            print("Starting frontend only...")
            start_frontend()
        elif command == "--both":
            start_both_services()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: --api-only, --frontend-only, --both")
            sys.exit(1)
    else:
        print_startup_info()
        
        print("Startup Options:")
        print("  python start_system.py --both         # Start both services")
        print("  python start_system.py --api-only     # Start API only")
        print("  python start_system.py --frontend-only # Start frontend only")
        print()
        print("Separate startup (recommended for development):")
        print("  Terminal 1: python api.py")
        print("  Terminal 2: streamlit run frontend.py")

if __name__ == "__main__":
    main()