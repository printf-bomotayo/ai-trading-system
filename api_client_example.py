#!/usr/bin/env python3
"""
Example API client for the AI Trading System
Demonstrates how to interact with the REST API endpoints
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any

class TradingSystemClient:
    """Simple client for the AI Trading System API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "dev-key-12345"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        async with self.session.get(f"{self.base_url}/health") as response:
            return await response.json()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        async with self.session.get(f"{self.base_url}/status") as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.json()
                raise Exception(f"API Error: {error}")
    
    async def analyze_trading_opportunity(self, analysis_request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trading opportunity"""
        async with self.session.post(
            f"{self.base_url}/analyze", 
            json=analysis_request
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.json()
                raise Exception(f"Analysis failed: {error}")
    
    async def configure_llm(self, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure LLM provider"""
        async with self.session.post(
            f"{self.base_url}/configure-llm",
            json=llm_config
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.json()
                raise Exception(f"LLM configuration failed: {error}")
    
    async def get_trading_history(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Get trading history for symbol"""
        async with self.session.get(
            f"{self.base_url}/history/{symbol}?days={days}"
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.json()
                raise Exception(f"History retrieval failed: {error}")

async def demo_api_usage():
    """Demonstrate API usage with example trading analysis"""
    
    print("AI Trading System API Client Demo")
    print("=" * 50)
    
    # Example trading analysis request
    analysis_request = {
        "symbol": "AAPL",
        "market_data": {
            "symbol": "AAPL",
            "price": 185.50,
            "volume": 2500000,
            "bid": 185.45,
            "ask": 185.55,
            "vix": 22.3,
            "sector": "Technology"
        },
        "news_events": [
            {
                "title": "Apple Reports Strong Q1 Earnings Beat",
                "content": "Apple Inc. reported first-quarter earnings that significantly beat analyst estimates, with revenue growing 15% year-over-year driven by strong iPhone and services performance.",
                "source": "Reuters",
                "relevance_score": 0.95,
                "symbols_mentioned": ["AAPL"],
                "sentiment_score": 0.8,
                "event_type": "earnings_surprise"
            },
            {
                "title": "Apple Announces New AI Features",
                "content": "Apple unveiled significant AI capabilities across its product line, positioning the company for the next generation of computing.",
                "source": "TechCrunch",
                "relevance_score": 0.7,
                "symbols_mentioned": ["AAPL"],
                "sentiment_score": 0.6,
                "event_type": "major_news"
            }
        ]
    }
    
    try:
        async with TradingSystemClient() as client:
            
            # 1. Health Check
            print("1. Checking API health...")
            health = await client.health_check()
            print(f"   Health status: {health.get('data', {}).get('overall', 'unknown')}")
            
            # 2. System Status
            print("\n2. Getting system status...")
            try:
                status = await client.get_status()
                print(f"   System status: {status.get('status', 'unknown')}")
                print(f"   Database connected: {status.get('database_connected', False)}")
            except Exception as e:
                print(f"   Status check failed: {e}")
                print("   (This is expected if the API server is not running)")
            
            # 3. Trading Analysis
            print(f"\n3. Analyzing trading opportunity for {analysis_request['symbol']}...")
            try:
                decision = await client.analyze_trading_opportunity(analysis_request)
                
                print(f"   Recommendation: {decision.get('action', 'UNKNOWN')}")
                print(f"   Confidence: {decision.get('confidence', 0):.2f}")
                print(f"   Reasoning: {decision.get('reasoning', 'No reasoning provided')[:100]}...")
                
                if decision.get('target_price'):
                    print(f"   Target Price: ${decision['target_price']:.2f}")
                if decision.get('stop_loss'):
                    print(f"   Stop Loss: ${decision['stop_loss']:.2f}")
                
            except Exception as e:
                print(f"   Analysis failed: {e}")
                print("   (This is expected if the trading system/database is not running)")
            
            # 4. LLM Configuration Example
            print("\n4. Testing LLM configuration...")
            llm_config = {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            try:
                config_result = await client.configure_llm(llm_config)
                print(f"   LLM configured: {config_result.get('success', False)}")
            except Exception as e:
                print(f"   LLM configuration failed: {e}")
                print("   (This is expected if the API server is not running)")
            
            # 5. Trading History
            print(f"\n5. Getting trading history for {analysis_request['symbol']}...")
            try:
                history = await client.get_trading_history(analysis_request['symbol'], days=7)
                decisions_count = len(history.get('data', {}).get('decisions', []))
                print(f"   Found {decisions_count} historical decisions")
            except Exception as e:
                print(f"   History retrieval failed: {e}")
                print("   (This is expected if the database is not running)")
        
        print("\n" + "=" * 50)
        print("Demo completed! To test with a running server:")
        print("1. Start the API server: python api.py")
        print("2. Run this demo again: python api_client_example.py")
        print("3. Check the interactive docs at: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        print("\nThis is expected if the API server is not running.")
        print("Start the server with: python api.py")

def print_curl_examples():
    """Print example cURL commands for testing the API"""
    
    print("\nExample cURL Commands:")
    print("=" * 50)
    
    print("\n1. Health Check:")
    print('curl "http://localhost:8000/health"')
    
    print("\n2. System Status:")
    print('curl -H "Authorization: Bearer dev-key-12345" "http://localhost:8000/status"')
    
    print("\n3. Trading Analysis:")
    print('''curl -X POST "http://localhost:8000/analyze" \\
  -H "Authorization: Bearer dev-key-12345" \\
  -H "Content-Type: application/json" \\
  -d '{
    "symbol": "AAPL",
    "market_data": {
      "symbol": "AAPL",
      "price": 185.50,
      "volume": 2500000,
      "bid": 185.45,
      "ask": 185.55,
      "vix": 22.3,
      "sector": "Technology"
    },
    "news_events": []
  }' ''')
    
    print("\n4. LLM Configuration:")
    print('''curl -X POST "http://localhost:8000/configure-llm" \\
  -H "Authorization: Bearer dev-key-12345" \\
  -H "Content-Type: application/json" \\
  -d '{
    "provider": "openai",
    "model": "gpt-4o-mini",
    "max_tokens": 1000,
    "temperature": 0.1
  }' ''')

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--curl":
        print_curl_examples()
    else:
        asyncio.run(demo_api_usage())