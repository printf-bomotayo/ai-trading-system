#!/usr/bin/env python3
"""
Demo data generator for testing the AI Trading System Frontend
Provides realistic example data for demonstrations
"""

from datetime import datetime, timedelta
import random
from typing import Dict, List, Any

class DemoDataGenerator:
    """Generate realistic demo data for the trading system"""
    
    def __init__(self):
        self.symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", 
            "META", "NVDA", "NFLX", "AMD", "INTC"
        ]
        
        self.sectors = [
            "Technology", "Healthcare", "Financial", "Energy", 
            "Consumer", "Industrial", "Utilities", "Materials"
        ]
        
        self.news_sources = [
            "Reuters", "Bloomberg", "CNBC", "MarketWatch", 
            "SEC Filings", "Company Press Release", "WSJ"
        ]
        
        self.event_types = [
            "earnings_surprise", "fed_announcement", "major_news",
            "geopolitical_shock", "sector_rotation", "vix_spike"
        ]
    
    def generate_market_data(self, symbol: str = None) -> Dict[str, Any]:
        """Generate realistic market data for a symbol"""
        
        if not symbol:
            symbol = random.choice(self.symbols)
        
        # Base price ranges by symbol
        price_ranges = {
            "AAPL": (150, 200),
            "MSFT": (300, 400), 
            "GOOGL": (120, 180),
            "AMZN": (140, 180),
            "TSLA": (200, 300),
            "META": (250, 350),
            "NVDA": (400, 800),
            "NFLX": (350, 500),
            "AMD": (100, 150),
            "INTC": (40, 60)
        }
        
        price_min, price_max = price_ranges.get(symbol, (50, 200))
        price = round(random.uniform(price_min, price_max), 2)
        
        # Generate realistic bid/ask spread (0.01-0.10)
        spread = round(random.uniform(0.01, 0.10), 3)
        bid = round(price - spread/2, 2)
        ask = round(price + spread/2, 2)
        
        # Generate volume (realistic trading volumes)
        volume = random.randint(500000, 5000000)
        
        # VIX typically ranges from 10-50
        vix = round(random.uniform(12, 35), 1)
        
        sector = random.choice(self.sectors)
        
        return {
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "bid": bid,
            "ask": ask,
            "vix": vix,
            "sector": sector
        }
    
    def generate_news_event(self, symbol: str = None, sentiment: str = "neutral") -> Dict[str, Any]:
        """Generate a realistic news event"""
        
        if not symbol:
            symbol = random.choice(self.symbols)
        
        # Sentiment-based templates
        positive_templates = [
            f"{symbol} Reports Strong Quarterly Earnings Beat",
            f"{symbol} Announces Major Product Launch",
            f"{symbol} Secures Large Partnership Deal",
            f"{symbol} Receives Analyst Upgrade",
            f"{symbol} Shows Impressive Revenue Growth"
        ]
        
        negative_templates = [
            f"{symbol} Misses Earnings Expectations",
            f"{symbol} Faces Regulatory Investigation", 
            f"{symbol} Reports Declining Market Share",
            f"{symbol} Announces Layoffs and Restructuring",
            f"{symbol} Downgrades Guidance for Next Quarter"
        ]
        
        neutral_templates = [
            f"{symbol} Announces Quarterly Results",
            f"{symbol} Holds Investor Conference Call",
            f"{symbol} Updates on Business Operations",
            f"{symbol} Provides Market Update",
            f"{symbol} Releases Routine Business Update"
        ]
        
        # Select title based on sentiment
        if sentiment == "positive":
            title = random.choice(positive_templates)
            sentiment_score = random.uniform(0.3, 0.9)
        elif sentiment == "negative":
            title = random.choice(negative_templates)
            sentiment_score = random.uniform(-0.9, -0.3)
        else:
            title = random.choice(neutral_templates)
            sentiment_score = random.uniform(-0.2, 0.2)
        
        # Generate content based on title
        content_templates = {
            "earnings": f"{symbol} reported quarterly earnings that {'exceeded' if sentiment_score > 0 else 'missed' if sentiment_score < 0 else 'met'} analyst expectations. Revenue showed {'strong growth' if sentiment_score > 0 else 'decline' if sentiment_score < 0 else 'steady performance'} compared to the previous quarter.",
            "product": f"{symbol} announced a {'breakthrough' if sentiment_score > 0 else 'delayed' if sentiment_score < 0 else 'new'} product launch that is expected to {'significantly boost' if sentiment_score > 0 else 'face challenges in' if sentiment_score < 0 else 'impact'} market position.",
            "default": f"{symbol} made an announcement regarding business operations. The market reaction has been {'positive' if sentiment_score > 0 else 'negative' if sentiment_score < 0 else 'mixed'} with analysts {'optimistic' if sentiment_score > 0 else 'concerned' if sentiment_score < 0 else 'neutral'} about the implications."
        }
        
        # Select content template
        if "earnings" in title.lower():
            content = content_templates["earnings"]
        elif "product" in title.lower() or "launch" in title.lower():
            content = content_templates["product"]
        else:
            content = content_templates["default"]
        
        return {
            "title": title,
            "content": content,
            "source": random.choice(self.news_sources),
            "relevance_score": round(random.uniform(0.5, 1.0), 2),
            "symbols_mentioned": [symbol],
            "sentiment_score": round(sentiment_score, 2),
            "event_type": random.choice(self.event_types)
        }
    
    def generate_trading_analysis_request(self, symbol: str = None) -> Dict[str, Any]:
        """Generate a complete trading analysis request"""
        
        if not symbol:
            symbol = random.choice(self.symbols)
        
        market_data = self.generate_market_data(symbol)
        
        # Generate 0-3 news events
        num_events = random.randint(0, 3)
        news_events = []
        
        for _ in range(num_events):
            sentiment = random.choice(["positive", "negative", "neutral"])
            news_event = self.generate_news_event(symbol, sentiment)
            news_events.append(news_event)
        
        return {
            "symbol": symbol,
            "market_data": market_data,
            "news_events": news_events
        }
    
    def generate_historical_decisions(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Generate historical trading decisions"""
        
        decisions = []
        current_date = datetime.now()
        
        # Generate decisions for random days in the past
        for _ in range(random.randint(5, 20)):
            days_ago = random.randint(0, days)
            decision_date = current_date - timedelta(days=days_ago)
            
            action = random.choice(["BUY", "SELL", "HOLD"])
            confidence = round(random.uniform(0.4, 0.95), 2)
            
            decision = {
                "timestamp": decision_date.isoformat(),
                "symbol": symbol,
                "final_action": action,
                "confidence": confidence,
                "reasoning": f"AI analysis suggested {action} based on market conditions and sentiment analysis.",
                "weighted_votes": {
                    action: confidence,
                    "HOLD": 1 - confidence
                },
                "total_weight": 1.0,
                "is_significant_event": random.choice([True, False])
            }
            
            decisions.append(decision)
        
        return decisions
    
    def generate_system_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Generate system analytics data"""
        
        total_decisions = random.randint(50, 200)
        
        return {
            "period_days": days,
            "decisions": {
                "total_decisions": total_decisions,
                "avg_confidence": round(random.uniform(0.65, 0.85), 3),
                "buy_decisions": random.randint(int(total_decisions * 0.2), int(total_decisions * 0.5)),
                "sell_decisions": random.randint(int(total_decisions * 0.1), int(total_decisions * 0.3)),
                "hold_decisions": random.randint(int(total_decisions * 0.3), int(total_decisions * 0.6))
            },
            "agents": [
                {
                    "agent_type": "news_intelligence",
                    "accuracy_rate": round(random.uniform(0.7, 0.9), 3),
                    "total_predictions": random.randint(100, 300),
                    "correct_predictions": random.randint(70, 250)
                },
                {
                    "agent_type": "market_analysis", 
                    "accuracy_rate": round(random.uniform(0.6, 0.85), 3),
                    "total_predictions": random.randint(100, 300),
                    "correct_predictions": random.randint(60, 220)
                },
                {
                    "agent_type": "risk_assessment",
                    "accuracy_rate": round(random.uniform(0.75, 0.95), 3),
                    "total_predictions": random.randint(100, 300),
                    "correct_predictions": random.randint(80, 280)
                }
            ],
            "llm_usage": {
                "total_requests": random.randint(500, 2000),
                "total_tokens": random.randint(50000, 200000),
                "avg_response_time_ms": random.randint(500, 2000),
                "success_rate": round(random.uniform(0.95, 0.99), 3)
            },
            "error_count": random.randint(0, 10),
            "generated_at": datetime.now().isoformat()
        }

# Example usage and testing
if __name__ == "__main__":
    generator = DemoDataGenerator()
    
    print("AI Trading System - Demo Data Generator")
    print("=" * 50)
    
    # Generate sample market data
    print("\n1. Sample Market Data:")
    market_data = generator.generate_market_data("AAPL")
    for key, value in market_data.items():
        print(f"   {key}: {value}")
    
    # Generate sample news event
    print("\n2. Sample News Event:")
    news_event = generator.generate_news_event("AAPL", "positive")
    print(f"   Title: {news_event['title']}")
    print(f"   Sentiment: {news_event['sentiment_score']}")
    print(f"   Source: {news_event['source']}")
    
    # Generate complete analysis request
    print("\n3. Complete Analysis Request:")
    analysis_request = generator.generate_trading_analysis_request("TSLA")
    print(f"   Symbol: {analysis_request['symbol']}")
    print(f"   Price: ${analysis_request['market_data']['price']}")
    print(f"   News Events: {len(analysis_request['news_events'])}")
    
    print("\nOK Demo data generator is working correctly!")
    print("\nUse this class to generate test data for the frontend:")