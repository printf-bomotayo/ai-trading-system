"""
AI Trading System - Streamlit Frontend
=====================================

Modern, intuitive web interface for the LLM-Enhanced AI Trading System.
Provides real-time trading analysis, system monitoring, and configuration management.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import asyncio
import aiohttp
import time
from typing import Dict, List, Any, Optional
import os
from dataclasses import dataclass

# Page configuration
st.set_page_config(
    page_title="AI Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/ai-trading-system',
        'Report a bug': 'https://github.com/your-repo/ai-trading-system/issues',
        'About': "LLM-Enhanced AI Trading System - Intelligent market analysis powered by AI agents"
    }
)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8035")
DEFAULT_API_KEY = os.getenv("API_KEY", "dev-key-12345")

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    .stSelectbox > div > div > select {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = DEFAULT_API_KEY
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []
if 'system_status' not in st.session_state:
    st.session_state.system_status = {}

@dataclass
class APIResponse:
    """Wrapper for API responses"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None

class TradingSystemAPI:
    """API client for the trading system"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def health_check(self) -> APIResponse:
        """Check API health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return APIResponse(success=True, data=response.json())
            else:
                return APIResponse(success=False, data=None, error=f"HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            return APIResponse(success=False, data=None, error=str(e))
    
    def get_status(self) -> APIResponse:
        """Get system status"""
        try:
            response = requests.get(
                f"{self.base_url}/status",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return APIResponse(success=True, data=response.json())
            else:
                return APIResponse(success=False, data=None, error=f"HTTP {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            return APIResponse(success=False, data=None, error=str(e))
    
    def analyze_trading_opportunity(self, analysis_request: Dict) -> APIResponse:
        """Analyze trading opportunity"""
        try:
            response = requests.post(
                f"{self.base_url}/analyze",
                json=analysis_request,
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                return APIResponse(success=True, data=response.json())
            else:
                return APIResponse(success=False, data=None, error=f"HTTP {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            return APIResponse(success=False, data=None, error=str(e))
    
    def configure_llm(self, llm_config: Dict) -> APIResponse:
        """Configure LLM provider"""
        try:
            response = requests.post(
                f"{self.base_url}/configure-llm",
                json=llm_config,
                headers=self.headers,
                timeout=15
            )
            if response.status_code == 200:
                return APIResponse(success=True, data=response.json())
            else:
                return APIResponse(success=False, data=None, error=f"HTTP {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            return APIResponse(success=False, data=None, error=str(e))
    
    def get_analytics(self, days: int = 7) -> APIResponse:
        """Get system analytics"""
        try:
            response = requests.get(
                f"{self.base_url}/analytics?days={days}",
                headers=self.headers,
                timeout=15
            )
            if response.status_code == 200:
                return APIResponse(success=True, data=response.json())
            else:
                return APIResponse(success=False, data=None, error=f"HTTP {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            return APIResponse(success=False, data=None, error=str(e))
    
    def get_trading_history(self, symbol: str, days: int = 30) -> APIResponse:
        """Get trading history"""
        try:
            response = requests.get(
                f"{self.base_url}/history/{symbol}?days={days}",
                headers=self.headers,
                timeout=15
            )
            if response.status_code == 200:
                return APIResponse(success=True, data=response.json())
            else:
                return APIResponse(success=False, data=None, error=f"HTTP {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            return APIResponse(success=False, data=None, error=str(e))

def display_header():
    """Display the main header"""
    st.markdown('<h1 class="main-header">🤖 AI Trading System</h1>', unsafe_allow_html=True)
    st.markdown("### LLM-Enhanced Trading Analysis Platform")
    
    # Connection status indicator
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("**Real-time AI-powered trading decisions with multi-agent analysis**")
    
    with col2:
        if st.session_state.api_connected:
            st.success("🟢 API Connected")
        else:
            st.error("🔴 API Disconnected")
    
    with col3:
        if st.button("🔄 Refresh Connection"):
            check_api_connection()

def check_api_connection():
    """Check and update API connection status"""
    api = TradingSystemAPI(API_BASE_URL, st.session_state.api_key)
    health_response = api.health_check()
    
    if health_response.success:
        st.session_state.api_connected = True
        st.success("✅ Connected to AI Trading System API")
        
        # Get system status
        status_response = api.get_status()
        if status_response.success:
            st.session_state.system_status = status_response.data
    else:
        st.session_state.api_connected = False
        st.error(f"❌ Failed to connect to API: {health_response.error}")
        st.info(f"Trying to connect to: {API_BASE_URL}")

def sidebar_configuration():
    """Sidebar configuration panel"""
    st.sidebar.title("⚙️ Configuration")
    
    # API Configuration
    # st.sidebar.subheader("API Settings")
    
    # # API URL (for advanced users)
    # with st.sidebar.expander("🔧 Advanced Settings"):
    #     global API_BASE_URL
    #     API_BASE_URL = st.text_input(
    #         "API Base URL",
    #         value=API_BASE_URL,
    #         help="URL of the AI Trading System API"
    #     )
    
    # # API Key
    # st.session_state.api_key = st.sidebar.text_input(
    #     "API Key",
    #     value=st.session_state.api_key,
    #     type="password",
    #     help="API key for authentication"
    # )
    
    # Test Connection Button
    if st.sidebar.button("🔗 Test Connection", use_container_width=True):
        check_api_connection()
    
    st.sidebar.divider()
    
    # LLM Configuration
    st.sidebar.subheader("🧠 LLM Configuration")
    
    llm_provider = st.sidebar.selectbox(
        "LLM Provider",
        ["openai", "anthropic", "deepseek", "local"],
        help="Select the LLM provider for analysis"
    )
    
    llm_model = st.sidebar.text_input(
        "Model",
        value="gpt-4o" if llm_provider == "openai" else "claude-3-sonnet-20240229",
        help="Specific model to use"
    )
    
    # llm_api_key = st.sidebar.text_input(
    #     "LLM API Key",
    #     type="password",
    #     help="API key for the LLM provider"
    # )
    
    if st.sidebar.button("🔄 Update LLM Config", use_container_width=True):
        if st.session_state.api_connected:
            api = TradingSystemAPI(API_BASE_URL, st.session_state.api_key)
            config = {
                "provider": llm_provider,
                "model": llm_model,
                # "api_key": llm_api_key if llm_api_key else None
            }
            response = api.configure_llm(config)
            if response.success:
                st.sidebar.success("✅ LLM configuration updated")
            else:
                st.sidebar.error(f"❌ Configuration failed: {response.error}")
        else:
            st.sidebar.error("❌ Connect to API first")

def main_trading_interface():
    """Main trading analysis interface"""
    st.header("📊 Trading Analysis")
    
    if not st.session_state.api_connected:
        st.warning("⚠️ Please connect to the API first using the sidebar configuration.")
        return
    
    # Input Section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Market Data Input")
        
        # Symbol input
        symbol = st.text_input(
            "Stock Symbol",
            value="AAPL",
            help="Enter the stock symbol (e.g., AAPL, TSLA, MSFT)"
        ).upper()
        
        # Market data inputs
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            price = st.number_input("Current Price ($)", value=185.50, min_value=0.01, step=0.01)
            volume = st.number_input("Volume", value=2500000, min_value=0, step=1000)
        
        with col_b:
            bid = st.number_input("Bid Price ($)", value=185.45, min_value=0.01, step=0.01)
            ask = st.number_input("Ask Price ($)", value=185.55, min_value=0.01, step=0.01)
        
        with col_c:
            vix = st.number_input("VIX", value=22.3, min_value=0.0, max_value=100.0, step=0.1)
            sector = st.selectbox(
                "Sector",
                ["Technology", "Healthcare", "Financial", "Energy", "Consumer", "Industrial", "Other"],
                index=0
            )
    
    with col2:
        st.subheader("Quick Analysis")
        
        # Quick metrics
        spread = ask - bid
        spread_pct = (spread / price) * 100 if price > 0 else 0
        
        st.metric("Bid-Ask Spread", f"${spread:.3f}", f"{spread_pct:.3f}%")
        st.metric("Market Cap Estimate", f"${(price * volume / 1000000):.1f}M")
        
        # VIX interpretation
        if vix < 15:
            vix_status = "🟢 Low Volatility"
        elif vix < 25:
            vix_status = "🟡 Normal Volatility" 
        else:
            vix_status = "🔴 High Volatility"
        
        st.metric("VIX Status", vix_status)
    
    # News Events Section
    st.subheader("📰 News Events")
    
    # Toggle for news input
    include_news = st.checkbox("Include News Events in Analysis", value=True)
    
    news_events = []
    if include_news:
        with st.expander("➕ Add News Events", expanded=False):
            news_title = st.text_input(
                "News Title",
                placeholder="e.g., Apple Reports Strong Q1 Earnings Beat"
            )
            news_content = st.text_area(
                "News Content",
                placeholder="Enter the full news content here...",
                height=100
            )
            news_source = st.selectbox(
                "News Source",
                ["Reuters", "Bloomberg", "CNBC", "SEC Filings", "Company Press Release", "Other"]
            )
            
            col_news1, col_news2, col_news3 = st.columns(3)
            with col_news1:
                relevance_score = st.slider("Relevance Score", 0.0, 1.0, 0.8, 0.1)
            with col_news2:
                sentiment_score = st.slider("Sentiment Score", -1.0, 1.0, 0.3, 0.1)
            with col_news3:
                event_type = st.selectbox(
                    "Event Type",
                    ["earnings_surprise", "fed_announcement", "major_news", "geopolitical_shock", "sector_rotation", "vix_spike"]
                )
            
            if st.button("📰 Add News Event"):
                if news_title and news_content:
                    news_event = {
                        "title": news_title,
                        "content": news_content,
                        "source": news_source,
                        "relevance_score": relevance_score,
                        "symbols_mentioned": [symbol],
                        "sentiment_score": sentiment_score,
                        "event_type": event_type
                    }
                    news_events.append(news_event)
                    st.success("✅ News event added!")
                else:
                    st.error("❌ Please fill in title and content")
    
    # Analysis Button
    st.divider()
    
    col_analyze1, col_analyze2, col_analyze3 = st.columns([1, 2, 1])
    with col_analyze2:
        if st.button("🚀 Analyze Trading Opportunity", use_container_width=True, type="primary"):
            perform_analysis(symbol, price, volume, bid, ask, vix, sector, news_events)

def perform_analysis(symbol: str, price: float, volume: int, bid: float, ask: float, vix: float, sector: str, news_events: List[Dict]):
    """Perform trading analysis"""
    
    # Validation
    if ask <= bid:
        st.error("❌ Ask price must be greater than bid price")
        return
    
    # Prepare request
    analysis_request = {
        "symbol": symbol,
        "market_data": {
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "bid": bid,
            "ask": ask,
            "vix": vix,
            "sector": sector
        },
        "news_events": news_events
    }
    
    # Show loading spinner
    with st.spinner("🤖 AI agents are analyzing the market..."):
        api = TradingSystemAPI(API_BASE_URL, st.session_state.api_key)
        response = api.analyze_trading_opportunity(analysis_request)
    
    if response.success:
        display_analysis_results(response.data, symbol)
        
        # Add to history
        analysis_record = {
            "timestamp": datetime.now(),
            "symbol": symbol,
            "analysis": response.data
        }
        st.session_state.analysis_history.append(analysis_record)
        
    else:
        st.error(f"❌ Analysis failed: {response.error}")

def display_analysis_results(analysis: Dict, symbol: str):
    """Display trading analysis results"""
    
    st.success("✅ Analysis Complete!")
    
    # Main recommendation
    action = analysis.get("action", "UNKNOWN")
    confidence = analysis.get("confidence", 0)
    reasoning = analysis.get("reasoning", "No reasoning provided")
    
    # Color coding for actions
    action_colors = {
        "BUY": "🟢",
        "SELL": "🔴", 
        "HOLD": "🟡",
        "SHORT": "🔻",
        "COVER": "🔼"
    }
    
    action_color = action_colors.get(action, "⚪")
    
    st.markdown(f"## {action_color} Recommendation: **{action}**")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Confidence",
            f"{confidence:.1%}",
            delta=None,
            help="AI confidence in the recommendation"
        )
    
    with col2:
        risk_score = analysis.get("risk_score", 0.5)
        risk_level = "Low" if risk_score < 0.3 else "Medium" if risk_score < 0.7 else "High"
        st.metric(
            "Risk Level",
            risk_level,
            delta=f"{risk_score:.2f}",
            help="Risk assessment score"
        )
    
    with col3:
        target_price = analysis.get("target_price")
        if target_price:
            st.metric(
                "Target Price",
                f"${target_price:.2f}",
                help="Suggested target price"
            )
        else:
            st.metric("Target Price", "N/A")
    
    with col4:
        stop_loss = analysis.get("stop_loss")
        if stop_loss:
            st.metric(
                "Stop Loss",
                f"${stop_loss:.2f}",
                help="Suggested stop loss level"
            )
        else:
            st.metric("Stop Loss", "N/A")
    
    # Reasoning
    st.subheader("🧠 AI Analysis Reasoning")
    st.info(reasoning)
    
    # Agent Contributions
    agent_contributions = analysis.get("agent_contributions", {})
    if agent_contributions:
        st.subheader("🤖 Agent Contributions")
        
        # Create a bar chart for agent contributions
        agents = list(agent_contributions.keys())
        contributions = list(agent_contributions.values())
        
        fig = px.bar(
            x=contributions,
            y=agents,
            orientation='h',
            title="AI Agent Contribution Weights",
            labels={'x': 'Contribution Weight', 'y': 'AI Agent'},
            color=contributions,
            color_continuous_scale="viridis"
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # System metadata
    system_metadata = analysis.get("system_metadata", {})
    if system_metadata:
        with st.expander("🔍 System Details"):
            st.json(system_metadata)

def analytics_dashboard():
    """Analytics and monitoring dashboard"""
    st.header("📈 Analytics Dashboard")
    
    if not st.session_state.api_connected:
        st.warning("⚠️ Please connect to the API first.")
        return
    
    # Time period selector
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("System Performance Analytics")
    with col2:
        days = st.selectbox("Time Period", [7, 14, 30, 90], index=0)
    
    # Get analytics data
    api = TradingSystemAPI(API_BASE_URL, st.session_state.api_key)
    
    with st.spinner("📊 Loading analytics..."):
        analytics_response = api.get_analytics(days)
    
    if analytics_response.success:
        analytics_data = analytics_response.data.get("data", {})
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        decisions = analytics_data.get("decisions", {})
        llm_usage = analytics_data.get("llm_usage", {})
        
        with col1:
            total_decisions = decisions.get("total_decisions", 0)
            st.metric("Total Decisions", total_decisions)
        
        with col2:
            avg_confidence = decisions.get("avg_confidence", 0)
            st.metric("Avg Confidence", f"{avg_confidence:.1%}")
        
        with col3:
            total_requests = llm_usage.get("total_requests", 0)
            st.metric("LLM Requests", total_requests)
        
        with col4:
            error_count = analytics_data.get("error_count", 0)
            st.metric("Error Count", error_count)
        
        # Decision breakdown
        if decisions:
            st.subheader("📊 Trading Decisions Breakdown")
            
            decision_types = {
                "BUY": decisions.get("buy_decisions", 0),
                "SELL": decisions.get("sell_decisions", 0),
                "HOLD": decisions.get("hold_decisions", 0)
            }
            
            if sum(decision_types.values()) > 0:
                fig = px.pie(
                    values=list(decision_types.values()),
                    names=list(decision_types.keys()),
                    title="Decision Distribution",
                    color_discrete_map={
                        "BUY": "#28a745",
                        "SELL": "#dc3545", 
                        "HOLD": "#ffc107"
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Agent performance
        agents_data = analytics_data.get("agents", [])
        if agents_data:
            st.subheader("🤖 Agent Performance")
            
            agent_df = pd.DataFrame(agents_data)
            if not agent_df.empty:
                # Sort by accuracy rate
                agent_df = agent_df.sort_values("accuracy_rate", ascending=False)
                
                fig = px.bar(
                    agent_df,
                    x="agent_type",
                    y="accuracy_rate",
                    title="Agent Accuracy Rates",
                    labels={"accuracy_rate": "Accuracy Rate", "agent_type": "Agent Type"}
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
                
                # Agent details table
                st.dataframe(agent_df, use_container_width=True)
    
    else:
        st.error(f"❌ Failed to load analytics: {analytics_response.error}")

def analysis_history():
    """Display analysis history"""
    st.header("📚 Analysis History")
    
    if not st.session_state.analysis_history:
        st.info("🔍 No analysis history yet. Perform some analyses to see them here!")
        return
    
    # Display recent analyses
    st.subheader(f"Recent Analyses ({len(st.session_state.analysis_history)})")
    
    for i, record in enumerate(reversed(st.session_state.analysis_history[-10:])):
        with st.expander(f"📊 {record['symbol']} - {record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
            analysis = record['analysis']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Action", analysis.get("action", "N/A"))
            with col2:
                st.metric("Confidence", f"{analysis.get('confidence', 0):.1%}")
            with col3:
                st.metric("Risk Score", f"{analysis.get('risk_score', 0):.2f}")
            
            st.write("**Reasoning:**", analysis.get("reasoning", "No reasoning provided"))

def system_status_page():
    """System status monitoring page"""
    st.header("🔧 System Status")
    
    if not st.session_state.api_connected:
        st.warning("⚠️ Please connect to the API first.")
        return
    
    # Refresh button
    if st.button("🔄 Refresh Status"):
        check_api_connection()
    
    # Display system status
    if st.session_state.system_status:
        status_data = st.session_state.system_status
        
        # Overall status
        overall_status = status_data.get("status", "unknown")
        if overall_status == "operational":
            st.success("🟢 System Operational")
        else:
            st.error(f"🔴 System Status: {overall_status}")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            uptime = status_data.get("uptime", "Unknown")
            st.metric("Uptime", uptime)
        
        with col2:
            total_requests = status_data.get("total_requests", 0)
            st.metric("Total Requests", total_requests)
        
        with col3:
            active_sessions = status_data.get("active_sessions", 0)
            st.metric("Active Sessions", active_sessions)
        
        with col4:
            db_connected = status_data.get("database_connected", False)
            db_status = "🟢 Connected" if db_connected else "🔴 Disconnected"
            st.metric("Database", db_status)
        
        # LLM Provider status
        llm_provider = status_data.get("llm_provider")
        if llm_provider:
            st.subheader("🧠 LLM Provider")
            st.info(f"Current provider: **{llm_provider}**")
        
        # Agent status
        agents_active = status_data.get("agents_active", {})
        if agents_active:
            st.subheader("🤖 AI Agents Status")
            
            agent_status_df = pd.DataFrame([
                {"Agent": agent, "Status": "🟢 Active" if active else "🔴 Inactive"}
                for agent, active in agents_active.items()
            ])
            st.dataframe(agent_status_df, use_container_width=True)
        
        # Performance metrics
        performance_metrics = status_data.get("performance_metrics", {})
        if performance_metrics:
            st.subheader("📊 Performance Metrics")
            st.json(performance_metrics)

def main():
    """Main application"""
    
    # Display header
    display_header()
    
    # Sidebar configuration
    sidebar_configuration()
    
    # Main navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Trading Analysis", 
        "📈 Analytics", 
        "📚 History", 
        "🔧 System Status",
        "📖 Documentation"
    ])
    
    with tab1:
        main_trading_interface()
    
    with tab2:
        analytics_dashboard()
    
    with tab3:
        analysis_history()
    
    with tab4:
        system_status_page()
    
    with tab5:
        display_documentation()

def display_documentation():
    """Display documentation and help"""
    st.header("📖 Documentation")
    
    st.markdown("""
    ## Welcome to the AI Trading System
    
    This is a **LLM-Enhanced AI Trading System** that provides intelligent market analysis using multiple AI agents.
    
    ### 🚀 Getting Started
    
    1. **Configure API Connection**: Use the sidebar to set your API key and test the connection
    2. **Input Market Data**: Enter stock symbol, price, volume, and other market data
    3. **Add News Events** (optional): Include relevant news for more comprehensive analysis
    4. **Run Analysis**: Click "Analyze Trading Opportunity" to get AI-powered recommendations
    
    ### 🤖 AI Agents
    
    The system uses multiple specialized AI agents:
    
    - **📰 News Intelligence Agent**: Analyzes news events and their market impact
    - **📊 Market Analysis Agent**: Performs technical analysis and pattern recognition
    - **⚠️ Risk Assessment Agent**: Evaluates risks and suggests position sizing
    - **💭 Sentiment Analysis Agent**: Analyzes market sentiment from multiple sources
    - **⚡ Execution Strategy Agent**: Optimizes trade timing and execution
    - **📈 Visualization Agent**: Creates intuitive data visualizations
    
    ### 📋 Features
    
    - **Real-time Analysis**: Get instant AI-powered trading recommendations
    - **Multi-Agent Consensus**: Decisions based on multiple AI agent inputs
    - **Risk Management**: Built-in risk assessment and position sizing
    - **News Integration**: Incorporate breaking news into analysis
    - **Historical Tracking**: View past analyses and performance
    - **System Monitoring**: Real-time system health and performance metrics
    
    ### 🔧 Configuration
    
    - **LLM Providers**: Support for OpenAI, Anthropic, DeepSeek, and local models
    - **API Authentication**: Secure access with API keys
    - **Customizable Parameters**: Adjust confidence thresholds and risk tolerance
    
    ### 📊 Interpreting Results
    
    - **Action**: BUY, SELL, HOLD recommendation
    - **Confidence**: AI confidence in the recommendation (0-100%)
    - **Risk Score**: Risk level assessment (0-1, higher = more risky)
    - **Target Price**: Suggested price target
    - **Stop Loss**: Recommended stop loss level
    
    ### 🆘 Troubleshooting
    
    **API Connection Issues:**
    - Check that the API server is running
    - Verify the API URL in advanced settings
    - Ensure your API key is correct
    
    **Analysis Errors:**
    - Verify market data inputs are valid
    - Check that ask price > bid price
    - Ensure LLM provider is properly configured
    
    **Performance Issues:**
    - Check system status in the monitoring tab
    - Verify database connectivity
    - Monitor API response times
    
    ### 📞 Support
    
    For additional help:
    - Check the system status page for any issues
    - Review the analytics dashboard for system performance
    - Contact support if problems persist
    """)

if __name__ == "__main__":
    # Initialize connection check on startup
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        check_api_connection()
    
    # Run main application
    main()