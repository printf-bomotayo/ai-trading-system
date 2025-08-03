# AI Trading System - Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Start the API Backend
```bash
python api.py
```
- API will be available at: http://localhost:8035
- Interactive docs at: http://localhost:8035/docs

### 2. Start the Web Frontend
```bash
streamlit run frontend.py
```
- Web interface at: http://localhost:8501
- Modern trading analysis dashboard

### 3. Analyze Your First Stock
1. Open http://localhost:8501 in your browser
2. Enter a stock symbol (e.g., AAPL)
3. Input market data (price, volume, etc.)
4. Click "🚀 Analyze Trading Opportunity"
5. Review AI-powered recommendations!

## 🔧 System Components

### **API Backend (Port 8035)**
- **FastAPI** REST endpoints
- **Multi-agent AI** trading analysis
- **LLM integration** (OpenAI, Anthropic, DeepSeek)
- **PostgreSQL** database support
- **Real-time** market analysis

### **Web Frontend (Port 8501)**
- **Streamlit** modern interface
- **Interactive** market data input
- **Real-time** AI analysis results
- **Analytics** dashboard
- **System** monitoring

## 📊 Key Features

### Trading Analysis
- ✅ Multi-agent AI recommendations
- ✅ News event integration
- ✅ Risk assessment
- ✅ Confidence scoring
- ✅ Price targets & stop losses

### System Analytics
- ✅ Performance dashboards
- ✅ Agent accuracy tracking
- ✅ Decision pattern analysis
- ✅ Historical review

### Configuration
- ✅ Multiple LLM providers
- ✅ API key management
- ✅ Real-time status monitoring
- ✅ Health checks

## 🔑 Authentication

**Default API Key**: `dev-key-12345`

Configure in the frontend sidebar or set environment variable:
```bash
export API_KEY=your-api-key-here
```

## 🐛 Troubleshooting

### "API Disconnected" Error
- Ensure API is running: `python api.py`
- Check API URL: http://localhost:8035
- Verify API key in sidebar

### Import Errors
```bash
pip install fastapi uvicorn streamlit plotly pandas requests
```

### Database Errors
- PostgreSQL optional for basic usage
- System works with rule-based fallback
- Check `.env` configuration

## 📱 Access URLs

- **Frontend**: http://localhost:8501
- **API Docs**: http://localhost:8035/docs
- **API Health**: http://localhost:8035/health

## 🎯 Example Analysis

Try analyzing **AAPL** with:
- Price: $185.50
- Volume: 2,500,000
- Add positive earnings news
- Review AI recommendation!

---

**🎉 Start building intelligent trading decisions with AI!**