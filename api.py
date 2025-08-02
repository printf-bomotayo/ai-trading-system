"""
trading_system/api.py
=====================

FastAPI REST API layer for the AI Trading System.
Provides external integration capabilities with comprehensive endpoints
for market analysis, trading decisions, and system management.
"""

from fastapi import FastAPI, HTTPException, Depends, Security, BackgroundTasks, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
import asyncio
import uuid
import os
from contextlib import asynccontextmanager

# Import our trading system components
try:
    from .core import MarketData, NewsEvent, LLMConfig, MarketEventType, TradeAction
    from .main import TradingSystemApp
    from .database import DatabaseManager, DatabaseConfig
except ImportError:
    from core import MarketData, NewsEvent, LLMConfig, MarketEventType, TradeAction
    from main import TradingSystemApp
    from database import DatabaseManager, DatabaseConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Global application state
app_state = {
    "trading_system": None,
    "database": None,
    "api_keys": set(),
    "rate_limits": {},
    "startup_time": None
}

# Pydantic Models for Request/Response
class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = True
    message: str = "Request completed successfully"
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class MarketDataRequest(BaseModel):
    """Market data input request"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (e.g., AAPL)")
    price: float = Field(..., gt=0, description="Current stock price")
    volume: int = Field(..., ge=0, description="Trading volume")
    bid: float = Field(..., gt=0, description="Bid price")
    ask: float = Field(..., gt=0, description="Ask price")
    vix: Optional[float] = Field(None, ge=0, le=100, description="VIX volatility index")
    sector: Optional[str] = Field(None, max_length=50, description="Market sector")
    
    @validator('ask')
    def ask_must_be_greater_than_bid(cls, v, values):
        if 'bid' in values and v <= values['bid']:
            raise ValueError('Ask price must be greater than bid price')
        return v

class NewsEventRequest(BaseModel):
    """News event input request"""
    title: str = Field(..., min_length=1, max_length=500, description="News headline")
    content: str = Field(..., min_length=1, description="News content")
    source: str = Field(..., min_length=1, max_length=100, description="News source")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score (0-1)")
    symbols_mentioned: List[str] = Field(..., min_items=1, description="List of symbols mentioned")
    sentiment_score: float = Field(..., ge=-1, le=1, description="Sentiment score (-1 to 1)")
    event_type: Optional[str] = Field(None, description="Type of market event")

class TradingAnalysisRequest(BaseModel):
    """Complete trading analysis request"""
    symbol: str = Field(..., min_length=1, max_length=10)
    market_data: MarketDataRequest
    news_events: List[NewsEventRequest] = Field(default_factory=list)
    llm_config: Optional[Dict[str, Any]] = Field(None, description="LLM configuration override")

class TradingDecisionResponse(BaseModel):
    """Trading decision response"""
    action: str = Field(..., description="Recommended trading action")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    reasoning: str = Field(..., description="Analysis reasoning")
    agent_contributions: Dict[str, float] = Field(default_factory=dict)
    risk_score: Optional[float] = Field(None, ge=0, le=1)
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    system_metadata: Dict[str, Any] = Field(default_factory=dict)

class SystemStatusResponse(BaseModel):
    """System status response"""
    status: str
    uptime: str
    total_requests: int
    active_sessions: int
    llm_provider: Optional[str] = None
    database_connected: bool
    agents_active: Dict[str, bool] = Field(default_factory=dict)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)

class LLMConfigRequest(BaseModel):
    """LLM configuration request"""
    provider: str = Field(..., pattern="^(openai|anthropic|deepseek|local)$")
    model: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    max_tokens: Optional[int] = Field(1000, ge=1, le=4000)
    temperature: Optional[float] = Field(0.1, ge=0, le=2)

# Application Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    
    # Startup
    logger.info("🚀 Starting AI Trading System API...")
    app_state["startup_time"] = datetime.now()
    
    try:
        # Initialize database
        db_config = DatabaseConfig()
        app_state["database"] = DatabaseManager(db_config)
        await app_state["database"].initialize()
        logger.info("✅ Database initialized")
        
        # Initialize trading system with default config
        default_llm_config = None
        if os.getenv("OPENAI_API_KEY"):
            default_llm_config = LLMConfig(
                provider="openai",
                model="gpt-4o-mini",
                api_key=os.getenv("OPENAI_API_KEY")
            )
        
        app_state["trading_system"] = TradingSystemApp(default_llm_config)
        await app_state["trading_system"].initialize()
        logger.info("✅ Trading system initialized")
        
        # Load API keys from environment
        api_keys_env = os.getenv("API_KEYS", "")
        if api_keys_env:
            app_state["api_keys"] = set(api_keys_env.split(","))
        else:
            # Default development key
            app_state["api_keys"] = {"dev-key-12345"}
        
        logger.info("✅ AI Trading System API ready!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AI Trading System API...")
    
    if app_state["trading_system"]:
        await app_state["trading_system"].shutdown()
    
    if app_state["database"]:
        await app_state["database"].close()
    
    logger.info("✅ Shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="AI Trading System API",
    description="LLM-Enhanced AI Trading System with Multi-Agent Analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Authentication
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key authentication"""
    
    if not app_state["api_keys"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available"
        )
    
    if credentials.credentials not in app_state["api_keys"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return credentials.credentials

# Rate Limiting (Simple implementation)
async def check_rate_limit(api_key: str):
    """Simple rate limiting check"""
    
    current_time = datetime.now()
    if api_key not in app_state["rate_limits"]:
        app_state["rate_limits"][api_key] = []
    
    # Clean old requests (older than 1 minute)
    app_state["rate_limits"][api_key] = [
        req_time for req_time in app_state["rate_limits"][api_key]
        if current_time - req_time < timedelta(minutes=1)
    ]
    
    # Check rate limit (100 requests per minute)
    if len(app_state["rate_limits"][api_key]) >= 100:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 100 requests per minute."
        )
    
    app_state["rate_limits"][api_key].append(current_time)

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code=f"HTTP_{exc.status_code}"
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            details={"type": type(exc).__name__}
        ).dict()
    )

# API Endpoints

@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint with API information"""
    return APIResponse(
        message="AI Trading System API is running",
        data={
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            "status": "/status"
        }
    )

@app.get("/health", response_model=APIResponse)
async def health_check():
    """Health check endpoint"""
    
    health_status = {
        "api": "healthy",
        "database": "unknown",
        "trading_system": "unknown"
    }
    
    # Check database
    try:
        if app_state["database"] and app_state["database"].pool:
            async with app_state["database"].pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health_status["database"] = "healthy"
    except Exception:
        health_status["database"] = "unhealthy"
    
    # Check trading system
    try:
        if app_state["trading_system"] and app_state["trading_system"].is_initialized:
            health_status["trading_system"] = "healthy"
    except Exception:
        health_status["trading_system"] = "unhealthy"
    
    overall_healthy = all(status == "healthy" for status in health_status.values())
    
    return APIResponse(
        message="Health check completed",
        data={
            "overall": "healthy" if overall_healthy else "degraded",
            "components": health_status,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/status", response_model=SystemStatusResponse)
async def system_status(api_key: str = Depends(verify_api_key)):
    """Get comprehensive system status"""
    
    await check_rate_limit(api_key)
    
    uptime = datetime.now() - app_state["startup_time"] if app_state["startup_time"] else timedelta(0)
    
    # Get trading system status
    trading_status = {}
    if app_state["trading_system"]:
        trading_status = await app_state["trading_system"].get_system_status()
    
    return SystemStatusResponse(
        status="operational",
        uptime=str(uptime),
        total_requests=sum(len(reqs) for reqs in app_state["rate_limits"].values()),
        active_sessions=len(app_state["rate_limits"]),
        llm_provider=trading_status.get("llm_service", {}).get("provider"),
        database_connected=app_state["database"] is not None and app_state["database"].pool is not None,
        agents_active=trading_status.get("agents", {}),
        performance_metrics=trading_status.get("system_health", {})
    )

@app.post("/analyze", response_model=TradingDecisionResponse)
async def analyze_trading_opportunity(
    request: TradingAnalysisRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Analyze trading opportunity with AI agents"""
    
    await check_rate_limit(api_key)
    
    if not app_state["trading_system"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trading system not available"
        )
    
    try:
        # Convert request to internal data structures
        market_data = MarketData(
            symbol=request.market_data.symbol,
            price=request.market_data.price,
            volume=request.market_data.volume,
            timestamp=datetime.now(),
            bid=request.market_data.bid,
            ask=request.market_data.ask,
            vix=request.market_data.vix,
            sector=request.market_data.sector
        )
        
        news_events = []
        for news_req in request.news_events:
            event_type = None
            if news_req.event_type:
                try:
                    event_type = MarketEventType(news_req.event_type)
                except ValueError:
                    pass  # Invalid event type, continue without it
            
            news_event = NewsEvent(
                id=str(uuid.uuid4()),
                title=news_req.title,
                content=news_req.content,
                source=news_req.source,
                timestamp=datetime.now(),
                relevance_score=news_req.relevance_score,
                symbols_mentioned=news_req.symbols_mentioned,
                sentiment_score=news_req.sentiment_score,
                event_type=event_type
            )
            news_events.append(news_event)
        
        # Perform analysis
        decision = await app_state["trading_system"].analyze_trading_opportunity(
            request.symbol, market_data, news_events
        )
        
        # Save to database in background
        if app_state["database"]:
            session_id = str(uuid.uuid4())
            background_tasks.add_task(save_analysis_to_db, session_id, request.symbol, decision, market_data, news_events)
        
        return TradingDecisionResponse(
            action=decision["action"].value if hasattr(decision["action"], "value") else str(decision["action"]),
            confidence=decision["confidence"],
            reasoning=decision["reasoning"],
            agent_contributions=decision.get("agent_contributions", {}),
            risk_score=decision.get("risk_score"),
            target_price=decision.get("target_price"),
            stop_loss=decision.get("stop_loss"),
            system_metadata=decision.get("system_metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@app.post("/configure-llm", response_model=APIResponse)
async def configure_llm(
    config: LLMConfigRequest,
    api_key: str = Depends(verify_api_key)
):
    """Configure LLM provider for the trading system"""
    
    await check_rate_limit(api_key)
    
    try:
        # Create new LLM config
        llm_config = LLMConfig(
            provider=config.provider,
            model=config.model,
            api_key=config.api_key,
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )
        
        # Reinitialize trading system with new config
        if app_state["trading_system"]:
            await app_state["trading_system"].shutdown()
        
        app_state["trading_system"] = TradingSystemApp(llm_config)
        await app_state["trading_system"].initialize()
        
        return APIResponse(
            message="LLM configuration updated successfully",
            data={
                "provider": config.provider,
                "model": config.model,
                "configured_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error configuring LLM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM configuration failed: {str(e)}"
        )

@app.get("/history/{symbol}", response_model=APIResponse)
async def get_trading_history(
    symbol: str,
    days: int = 30,
    api_key: str = Depends(verify_api_key)
):
    """Get trading decision history for a symbol"""
    
    await check_rate_limit(api_key)
    
    if not app_state["database"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        history = await app_state["database"].get_decision_history(symbol, days)
        
        return APIResponse(
            message=f"Retrieved {len(history)} decisions for {symbol}",
            data={
                "symbol": symbol,
                "period_days": days,
                "decisions": history
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve history: {str(e)}"
        )

@app.get("/analytics", response_model=APIResponse)
async def get_system_analytics(
    days: int = 7,
    api_key: str = Depends(verify_api_key)
):
    """Get system analytics and performance metrics"""
    
    await check_rate_limit(api_key)
    
    if not app_state["database"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    try:
        analytics = await app_state["database"].get_system_analytics(days)
        
        return APIResponse(
            message="System analytics retrieved successfully",
            data=analytics
        )
        
    except Exception as e:
        logger.error(f"Error retrieving analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )

# Background Tasks
async def save_analysis_to_db(session_id: str, symbol: str, decision: Dict, market_data: MarketData, news_events: List[NewsEvent]):
    """Save analysis results to database"""
    
    try:
        if app_state["database"]:
            # Save market data
            await app_state["database"].save_market_data(market_data)
            
            # Save news events
            for event in news_events:
                await app_state["database"].save_news_event(event)
            
            # Save trading decision
            await app_state["database"].save_trading_decision(decision, symbol, session_id)
            
            logger.info(f"Saved analysis for {symbol} to database")
            
    except Exception as e:
        logger.error(f"Error saving to database: {e}")

# Development and Testing Endpoints
@app.post("/test/market-data", response_model=APIResponse)
async def test_market_data_validation(data: MarketDataRequest):
    """Test endpoint for market data validation"""
    return APIResponse(
        message="Market data validation successful",
        data=data.dict()
    )

@app.post("/test/news-event", response_model=APIResponse)
async def test_news_event_validation(event: NewsEventRequest):
    """Test endpoint for news event validation"""
    return APIResponse(
        message="News event validation successful", 
        data=event.dict()
    )

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8035"))
    workers = int(os.getenv("API_WORKERS", "1"))
    
    logger.info(f"Starting AI Trading System API on {host}:{port}")
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        workers=workers,
        reload=True,
        log_level="info"
    )