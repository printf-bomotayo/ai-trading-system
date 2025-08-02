#!/usr/bin/env python3
"""
Simple test script to verify API functionality
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_api_imports():
    """Test that API module imports correctly"""
    
    print("Testing API Module Imports")
    print("=" * 40)
    
    try:
        # Test basic imports
        from api import app, APIResponse, MarketDataRequest
        print("OK FastAPI app imports successfully")
        
        # Test Pydantic models
        from api import TradingAnalysisRequest, TradingDecisionResponse
        print("OK Pydantic models import successfully")
        
        # Test that FastAPI app is properly configured
        print(f"OK App title: {app.title}")
        print(f"OK App version: {app.version}")
        
        # Test model validation
        market_data = MarketDataRequest(
            symbol="AAPL",
            price=150.0,
            volume=1000000,
            bid=149.95,
            ask=150.05,
            vix=20.0,
            sector="Technology"
        )
        print("OK MarketDataRequest validation works")
        
        print()
        print("SUCCESS API module is ready!")
        print()
        print("To start the API server, run:")
        print("  python api.py")
        print("  OR")
        print("  uvicorn api:app --reload --port 8000")
        print()
        print("API Documentation will be available at:")
        print("  http://localhost:8000/docs")
        print("  http://localhost:8000/redoc")
        
        return True
        
    except Exception as e:
        print(f"ERROR API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_api_imports())
    sys.exit(0 if success else 1)