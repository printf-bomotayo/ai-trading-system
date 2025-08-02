# AI Trading System API Documentation

## Overview
RESTful API for the LLM-Enhanced AI Trading System providing external integration capabilities with comprehensive endpoints for market analysis, trading decisions, and system management.

## Base URL
```
http://localhost:8000
```

## Authentication
All protected endpoints require API key authentication using Bearer token:
```
Authorization: Bearer your-api-key-here
```

Default development API key: `dev-key-12345`

## Rate Limiting
- **Limit**: 100 requests per minute per API key
- **Response**: HTTP 429 when exceeded

## API Endpoints

### 1. System Information

#### GET `/`
Root endpoint with API information.
- **Authentication**: None
- **Response**: Basic API information and navigation links

#### GET `/health`
Health check endpoint for monitoring.
- **Authentication**: None
- **Response**: System component health status

#### GET `/status`
Comprehensive system status and metrics.
- **Authentication**: Required
- **Response**: Detailed system status including uptime, active sessions, and performance metrics

### 2. Trading Analysis

#### POST `/analyze`
**Primary endpoint** - Analyze trading opportunity with AI agents.

**Request Body**:
```json
{
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
      "title": "Apple Reports Strong Q1 Earnings",
      "content": "Apple Inc. reported first-quarter earnings that beat analyst estimates...",
      "source": "Reuters",
      "relevance_score": 0.95,
      "symbols_mentioned": ["AAPL"],
      "sentiment_score": 0.8,
      "event_type": "earnings_surprise"
    }
  ]
}
```

**Response**:
```json
{
  "action": "BUY",
  "confidence": 0.85,
  "reasoning": "Strong earnings beat with positive sentiment...",
  "agent_contributions": {
    "news_intelligence": 0.3,
    "market_analysis": 0.25,
    "risk_assessment": 0.2
  },
  "risk_score": 0.4,
  "target_price": 195.0,
  "stop_loss": 180.0,
  "system_metadata": {
    "llm_enabled": true,
    "agent_count": 6,
    "analysis_timestamp": "2024-01-15T10:30:00"
  }
}
```

### 3. Configuration Management

#### POST `/configure-llm`
Configure LLM provider settings.

**Request Body**:
```json
{
  "provider": "openai",
  "model": "gpt-4o-mini",
  "api_key": "your-api-key",
  "max_tokens": 1000,
  "temperature": 0.1
}
```

**Supported Providers**:
- `openai` - OpenAI GPT models
- `anthropic` - Anthropic Claude models  
- `deepseek` - DeepSeek models
- `local` - Local models (Ollama)

### 4. Historical Data

#### GET `/history/{symbol}`
Get trading decision history for a specific symbol.

**Parameters**:
- `symbol` (path): Stock symbol (e.g., AAPL)
- `days` (query): Number of days to retrieve (default: 30)

**Response**: Array of historical trading decisions with timestamps and analysis details.

### 5. Analytics

#### GET `/analytics`
Get system analytics and performance metrics.

**Parameters**:
- `days` (query): Analysis period in days (default: 7)

**Response**: Comprehensive analytics including decision statistics, agent performance, LLM usage, and error rates.

### 6. Testing Endpoints

#### POST `/test/market-data`
Validate market data structure without performing analysis.

#### POST `/test/news-event`
Validate news event structure without performing analysis.

## Data Models

### MarketData
```json
{
  "symbol": "string (1-10 chars, required)",
  "price": "number (>0, required)",
  "volume": "integer (>=0, required)", 
  "bid": "number (>0, required)",
  "ask": "number (>0, must be > bid, required)",
  "vix": "number (0-100, optional)",
  "sector": "string (max 50 chars, optional)"
}
```

### NewsEvent
```json
{
  "title": "string (1-500 chars, required)",
  "content": "string (required)",
  "source": "string (1-100 chars, required)",
  "relevance_score": "number (0-1, required)",
  "symbols_mentioned": "array of strings (min 1, required)",
  "sentiment_score": "number (-1 to 1, required)",
  "event_type": "string (optional)"
}
```

### Event Types
- `earnings_surprise`
- `fed_announcement` 
- `geopolitical_shock`
- `sector_rotation`
- `vix_spike`
- `major_news`

## Error Handling

### Standard Error Response
```json
{
  "success": false,
  "error": "Error description",
  "error_code": "ERROR_CODE",
  "details": {},
  "timestamp": "2024-01-15T10:30:00",
  "request_id": "uuid"
}
```

### Common Error Codes
- `HTTP_401` - Invalid API key
- `HTTP_429` - Rate limit exceeded
- `HTTP_503` - Service unavailable
- `VALIDATION_ERROR` - Invalid request data
- `INTERNAL_ERROR` - Server error

## Usage Examples

### Python Client Example
```python
import requests

# Configure API
API_BASE = "http://localhost:8000"
API_KEY = "dev-key-12345"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Analyze trading opportunity
data = {
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
}

response = requests.post(f"{API_BASE}/analyze", json=data, headers=headers)
decision = response.json()

print(f"Recommendation: {decision['action']}")
print(f"Confidence: {decision['confidence']}")
```

### cURL Example
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Authorization: Bearer dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "market_data": {
      "symbol": "AAPL", 
      "price": 185.50,
      "volume": 2500000,
      "bid": 185.45,
      "ask": 185.55
    },
    "news_events": []
  }'
```

## Development Setup

### 1. Install Dependencies
```bash
pip install fastapi uvicorn pydantic asyncpg aiohttp python-dotenv
```

### 2. Configure Environment
Set up your `.env` file with database and API configurations.

### 3. Start Development Server
```bash
python api.py
# OR
uvicorn api:app --reload --port 8000
```

### 4. Access Documentation
- Interactive API docs: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

## Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
Configure production settings in your `.env` file:
- Set `ENVIRONMENT=production`
- Configure proper `CORS_ORIGINS`
- Set strong `API_KEYS`
- Configure database connection
- Set LLM provider API keys

### Security Considerations
- Use HTTPS in production
- Implement proper API key management
- Configure CORS appropriately
- Set up proper logging and monitoring
- Implement request validation and sanitization

## Monitoring and Observability

The API provides built-in monitoring through:
- Health check endpoints
- System status metrics
- Request logging
- Error tracking
- Performance analytics

Monitor these endpoints for production health:
- `GET /health` - Basic health check
- `GET /status` - Detailed system metrics  
- `GET /analytics` - Performance analytics