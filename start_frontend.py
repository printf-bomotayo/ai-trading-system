#!/usr/bin/env python3
"""
Startup script for the AI Trading System Frontend
Handles dependency checking and launches the Streamlit application
"""

import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    
    required_packages = [
        'streamlit',
        'plotly', 
        'pandas',
        'requests',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("ERROR Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        print("   OR")
        print("   pip install -r requirements_frontend.txt")
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
    
    # Check API configuration
    api_url = os.getenv("API_BASE_URL", "http://localhost:8035")
    api_key = os.getenv("API_KEY", "dev-key-12345")
    
    print(f"OK API URL: {api_url}")
    print(f"OK API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else '****'}")

def print_startup_info():
    """Print helpful startup information"""
    
    print("\nAI Trading System Frontend")
    print("=" * 50)
    print("The frontend will be available at:")
    print("  - Web Interface: http://localhost:8501")
    print("  - Network URL: Will be shown after startup")
    print()
    print("Features:")
    print("  - Real-time trading analysis")
    print("  - Interactive market data input")
    print("  - AI agent performance dashboard")
    print("  - System monitoring and analytics")
    print("  - Historical analysis tracking")
    print()
    print("Prerequisites:")
    print("  - AI Trading System API must be running")
    print("  - Start API with: python api.py")
    print("  - API should be available at: http://localhost:8035")
    print()

def start_streamlit_app():
    """Start the Streamlit application"""
    
    print("Starting Streamlit frontend...")
    print("Press Ctrl+C to stop the frontend")
    print("-" * 50)
    
    try:
        # Set Streamlit configuration
        os.environ["STREAMLIT_SERVER_PORT"] = "8501"
        os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
        os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
        
        # Start the Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "frontend.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n\nOK Streamlit frontend stopped")
    except Exception as e:
        print(f"ERROR Failed to start frontend: {e}")

def main():
    """Main startup function"""
    
    print("AI Trading System Frontend - Startup Check")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("frontend.py").exists():
        print("ERROR frontend.py not found in current directory")
        print("Please run this script from the trading system directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    check_environment()
    
    # Print startup info
    print_startup_info()
    
    # Ask user if they want to start the frontend
    if len(sys.argv) > 1 and sys.argv[1] == "--start":
        start_streamlit_app()
    else:
        print("To start the frontend, run:")
        print("  python start_frontend.py --start")
        print("  OR")
        print("  streamlit run frontend.py")
        print()
        print("IMPORTANT: Make sure the API server is running first!")
        print("  python api.py")

if __name__ == "__main__":
    main()