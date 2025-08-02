#!/usr/bin/env python3
"""
Startup script for the AI Trading System API
Handles dependency checking and provides helpful startup information
"""

import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    
    required_packages = [
        'fastapi',
        'uvicorn', 
        'pydantic',
        'aiohttp',
        'asyncpg',
        'python-dotenv'
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
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("OK All required packages are installed")
    return True

def check_environment():
    """Check environment configuration"""
    
    env_file = Path(".env")
    if env_file.exists():
        print("OK Found .env configuration file")
    else:
        print("WARNING No .env file found - using default configuration")
    
    # Check if API keys are available
    if os.getenv("OPENAI_API_KEY"):
        print("OK OpenAI API key configured")
    elif os.getenv("ANTHROPIC_API_KEY"):
        print("OK Anthropic API key configured") 
    elif os.getenv("DEEPSEEK_API_KEY"):
        print("OK DeepSeek API key configured")
    else:
        print("WARNING No LLM API keys found - will use rule-based analysis")

def print_startup_info():
    """Print helpful startup information"""
    
    print("\nAI Trading System API")
    print("=" * 50)
    print("The API will be available at:")
    print("  - Main API: http://localhost:8000")
    print("  - Interactive docs: http://localhost:8000/docs")
    print("  - ReDoc docs: http://localhost:8000/redoc")
    print("  - Health check: http://localhost:8000/health")
    print()
    print("API Authentication:")
    print("  - Default dev key: dev-key-12345")
    print("  - Header format: Authorization: Bearer dev-key-12345")
    print()
    print("Test the API:")
    print("  - python api_client_example.py")
    print("  - curl http://localhost:8000/health")
    print()

def start_api_server():
    """Start the API server using uvicorn"""
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = os.getenv("API_PORT", "8000")
    
    print(f"Starting API server on {host}:{port}...")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start the uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api:app",
            "--host", host,
            "--port", port,
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\nOK API server stopped")
    except Exception as e:
        print(f"ERROR Failed to start server: {e}")

def main():
    """Main startup function"""
    
    print("AI Trading System API - Startup Check")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("api.py").exists():
        print("ERROR api.py not found in current directory")
        print("Please run this script from the trading system directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    check_environment()
    
    # Print startup info
    print_startup_info()
    
    # Ask user if they want to start the server
    if len(sys.argv) > 1 and sys.argv[1] == "--start":
        start_api_server()
    else:
        print("To start the API server, run:")
        print("  python start_api.py --start")
        print("  OR")
        print("  python api.py")
        print("  OR") 
        print("  uvicorn api:app --reload --port 8000")

if __name__ == "__main__":
    main()