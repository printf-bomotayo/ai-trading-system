# AI Trading System - REST API Layer

## Overview
Production-ready REST API built with FastAPI that provides external integration capabilities for the LLM-Enhanced AI Trading System. Enables remote access to trading analysis, system management, and historical data through secure HTTP endpoints.

## Quick Start

### 1. Install Dependencies
```bash
pip install fastapi uvicorn pydantic aiohttp asyncpg python-dotenv
```

### 2. Check System Readiness
```bash
python start_api.py
```

### 3. Start API Server
```bash
python start_api.py --start
# OR
python api.py
# OR  
uvicorn api:app --reload --port 8000
```

### 4. Access Documentation
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Key Features

### 🔐 **Security & Authentication**
- Bearer token authentication
- Rate limiting (100 requests/minute)
- CORS support with configurable origins
- Input validation and sanitization
- Comprehensive error handling

### 📊 **Trading Analysis Endpoints**
- **POST /analyze** - Full AI-powered trading analysis
- **GET /history/{symbol}** - Historical trading decisions
- **GET /analytics** - System performance metrics
- **POST /configure-llm** - Dynamic LLM provider configuration

### 🔧 **System Management**
- **GET /health** - Component health monitoring
- **GET /status** - Detailed system status and metrics
- Real-time performance tracking
- Database connection monitoring

### 📝 **Request/Response Validation**
- Pydantic models for all data structures
- Automatic API documentation generation
- Type safety and validation
- Comprehensive error responses

## API Usage Examples

### Python Client
```python
import aiohttp
import asyncio

async def analyze_stock():
    headers = {"Authorization": "Bearer dev-key-12345"}
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
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/analyze",
            json=data,
            headers=headers
        ) as response:
            result = await response.json()
            print(f"Recommendation: {result['action']}")
            print(f"Confidence: {result['confidence']}")

asyncio.run(analyze_stock())
```

### cURL Command
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

## Configuration

### Environment Variables (.env)
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_KEYS=dev-key-12345,prod-key-67890

# Database Configuration  
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_system
DB_USER=postgres
DB_PASSWORD=postgres

# LLM Provider API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
DEEPSEEK_API_KEY=your-deepseek-key
```

### Authentication
- **Default Development Key**: `dev-key-12345`
- **Header Format**: `Authorization: Bearer your-api-key`
- **Multiple Keys**: Configure via `API_KEYS` environment variable

## Testing & Development

### Run Test Suite
```bash
python test_api.py          # Test API module imports
python api_client_example.py # Test full client workflow
```

### Interactive Testing
1. Start API server: `python api.py`
2. Open browser: http://localhost:8000/docs
3. Use "Try it out" feature in Swagger UI
4. Test with provided example data

### Example Client
```bash
python api_client_example.py     # Full demo workflow
python api_client_example.py --curl  # Show cURL examples
```

## Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Gunicorn Production Server
```bash
pip install gunicorn
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Production Checklist
- [ ] Configure strong API keys
- [ ] Set up HTTPS/TLS
- [ ] Configure proper CORS origins
- [ ] Set up monitoring and logging
- [ ] Configure database connection pooling
- [ ] Set up health check monitoring
- [ ] Configure rate limiting for your needs
- [ ] Set up backup and disaster recovery

## Architecture

### Request Flow
```
Client Request → Authentication → Rate Limiting → Validation → 
Business Logic → Database → LLM Processing → Response
```

### Key Components
- **FastAPI Application**: Core web framework
- **Pydantic Models**: Request/response validation
- **Authentication Middleware**: Bearer token verification
- **Rate Limiting**: Per-API-key request throttling
- **Database Integration**: Async PostgreSQL operations
- **LLM Orchestration**: Multi-provider AI analysis
- **Error Handling**: Comprehensive exception management

### Database Integration
- Automatic connection management
- Background task processing
- Historical data persistence
- Analytics and reporting
- Performance metrics tracking

## API Endpoints Reference

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | API information | No |
| GET | `/health` | Health check | No |
| GET | `/status` | System status | Yes |
| POST | `/analyze` | Trading analysis | Yes |
| POST | `/configure-llm` | LLM configuration | Yes |
| GET | `/history/{symbol}` | Trading history | Yes |
| GET | `/analytics` | System analytics | Yes |
| POST | `/test/market-data` | Data validation | No |
| POST | `/test/news-event` | Event validation | No |

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

## Monitoring & Observability

### Built-in Monitoring
- Request/response logging
- Performance metrics collection
- Error tracking and alerting
- Health check endpoints
- Rate limiting statistics

### Metrics Available
- Total requests processed
- Average response times
- Error rates by endpoint
- LLM provider usage
- Database performance
- Agent accuracy rates

## Troubleshooting

### Common Issues

**Missing Dependencies**
```bash
python start_api.py  # Check dependencies
pip install -r requirements.txt
```

**Database Connection Failed**
- Check PostgreSQL is running
- Verify database credentials in .env
- Test connection: `python test_database.py`

**LLM Analysis Not Working**
- Verify API keys in .env file
- Check LLM provider service status
- Test with rule-based fallback

**Authentication Errors**
- Verify API key in request headers
- Check API_KEYS environment variable
- Use default dev key for testing: `dev-key-12345`

### Support
For issues and support:
1. Check the interactive docs: http://localhost:8000/docs
2. Review API logs for error details
3. Test individual components with provided test scripts
4. Verify environment configuration

---

## Summary

The AI Trading System API provides a **production-ready REST interface** with:

✅ **Comprehensive Security** - Authentication, rate limiting, validation  
✅ **Full Trading Analysis** - AI-powered decision making via HTTP  
✅ **System Management** - Health monitoring, configuration, analytics  
✅ **Developer Experience** - Interactive docs, client examples, testing tools  
✅ **Production Ready** - Error handling, logging, monitoring, scalability  

Start building with the API in minutes and scale to production with confidence!