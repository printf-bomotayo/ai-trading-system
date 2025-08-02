"""
trading_system/database.py
===========================

PostgreSQL database setup, schema management, and data persistence layer
for the AI Trading System. Handles automatic database and table creation,
migrations, and CRUD operations for all system components.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import asdict
import json
import uuid
from dotenv import load_dotenv
import traceback

load_dotenv()   

print(os.getenv('DB_HOST', 'localhost'))

print(os.getenv('DB_PORT', 'localhost'))

print(os.getenv('DB_USER', 'localhost'))


import asyncpg
from asyncpg import Connection, Pool

try:
    from .core import (
        MarketData, NewsEvent, AgentResponse, PerformanceMetric,
        AgentType, MarketEventType, TradeAction
    )
except ImportError:
    from core import (
        MarketData, NewsEvent, AgentResponse, PerformanceMetric,
        AgentType, MarketEventType, TradeAction
    )

logger = logging.getLogger(__name__)


class  DatabaseConfig:
    """Database configuration settings"""
    
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '5432'))
        self.database = os.getenv('DB_NAME', 'trading_system')
        self.username = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')
        self.pool_min_size = int(os.getenv('DB_POOL_MIN', '5'))
        self.pool_max_size = int(os.getenv('DB_POOL_MAX', '20'))
        
    def get_dsn(self) -> str:
        """Get database connection string"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    # def get_admin_dsn(self) -> str:
    #     """Get admin connection string (for database creation)"""
    #     return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/postgres"


class DatabaseManager:
    """Manages PostgreSQL database operations for the trading system"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.pool: Optional[Pool] = None
        self.schema_version = "1.0.0"
        
    async def initialize(self) -> None:
        """Initialize database connection and ensure schema exists"""
        
        try:
            logger.info("Initializing database connection...")
            
            # Ensure database exists
            await self._ensure_database_exists()
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.config.get_dsn(),
                min_size=self.config.pool_min_size,
                max_size=self.config.pool_max_size,
                command_timeout=60
            )
            
            # Ensure schema exists and is up to date
            await self._ensure_schema_exists()
            
            logger.info("✅ Database initialization complete")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _ensure_database_exists(self) -> None:
        """Ensure the trading system database exists"""
        
        try:
            # Connect to postgres database first
            conn = await asyncpg.connect(self.config.get_dsn())
            
            # Check if our database exists
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                self.config.database
            )
            
            if not exists:
                logger.info(f"Creating database: {self.config.database}")
                await conn.execute(f'CREATE DATABASE "{self.config.database}"')
                logger.info(f"✅ Database {self.config.database} created successfully")
            else:
                logger.info(f"Database {self.config.database} already exists")
            
            await conn.close()
            
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error ensuring database exists: {e}")
            raise
    
    async def _ensure_schema_exists(self) -> None:
        """Ensure all required tables and schema exist"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as conn:
            try:
                # Check if schema version table exists
                schema_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'schema_version'
                    )
                """)
                
                current_version = None
                if schema_exists:
                    current_version = await conn.fetchval(
                        "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
                    )
                
                if current_version != self.schema_version:
                    logger.info(f"Creating/updating schema to version {self.schema_version}")
                    await self._create_schema(conn)
                    await self._record_schema_version(conn)
                else:
                    logger.info(f"Schema version {current_version} is current")
                
            except Exception as e:
                traceback.print_exc()
                logger.error(f"Error ensuring schema exists: {e}")
                raise
    
    async def _create_schema(self, conn: Connection) -> None:
        """Create all required tables and indexes"""
        
        # Schema version tracking table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                id SERIAL PRIMARY KEY,
                version VARCHAR(20) NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                description TEXT
            )
        """)
        
        # Market data table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                price DECIMAL(12,4) NOT NULL,
                volume BIGINT NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                bid DECIMAL(12,4) NOT NULL,
                ask DECIMAL(12,4) NOT NULL,
                vix DECIMAL(6,2),
                sector VARCHAR(50),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # News events table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS news_events (
                id UUID PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source VARCHAR(100) NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                relevance_score DECIMAL(3,2) NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1),
                symbols_mentioned TEXT[] NOT NULL,
                sentiment_score DECIMAL(3,2) NOT NULL CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
                event_type VARCHAR(50),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Agent responses table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_responses (
                id SERIAL PRIMARY KEY,
                agent_type VARCHAR(50) NOT NULL,
                symbol VARCHAR(10) NOT NULL,
                confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
                recommendation VARCHAR(10) NOT NULL,
                reasoning TEXT NOT NULL,
                supporting_data JSONB,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                risk_score DECIMAL(3,2) CHECK (risk_score >= 0 AND risk_score <= 1),
                target_price DECIMAL(12,4),
                stop_loss DECIMAL(12,4),
                session_id UUID,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Trading decisions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS trading_decisions (
                id SERIAL PRIMARY KEY,
                session_id UUID NOT NULL,
                symbol VARCHAR(10) NOT NULL,
                final_action VARCHAR(10) NOT NULL,
                confidence DECIMAL(3,2) NOT NULL,
                reasoning TEXT NOT NULL,
                weighted_votes JSONB NOT NULL,
                total_weight DECIMAL(8,4) NOT NULL,
                event_type VARCHAR(50),
                agent_contributions JSONB,
                failed_agents TEXT[],
                is_significant_event BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Performance metrics table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id SERIAL PRIMARY KEY,
                agent_type VARCHAR(50) NOT NULL UNIQUE,
                accuracy_rate DECIMAL(5,4) NOT NULL CHECK (accuracy_rate >= 0 AND accuracy_rate <= 1),
                confidence_calibration DECIMAL(5,4) NOT NULL,
                total_predictions INTEGER NOT NULL DEFAULT 0,
                correct_predictions INTEGER NOT NULL DEFAULT 0,
                performance_by_event_type JSONB,
                last_updated TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # System events/logs table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id SERIAL PRIMARY KEY,
                event_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL DEFAULT 'INFO',
                message TEXT NOT NULL,
                details JSONB,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # LLM service usage tracking
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_usage (
                id SERIAL PRIMARY KEY,
                provider VARCHAR(50) NOT NULL,
                model VARCHAR(100) NOT NULL,
                agent_type VARCHAR(50) NOT NULL,
                tokens_used INTEGER NOT NULL,
                response_time_ms INTEGER,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create indexes for performance
        await self._create_indexes(conn)
        
        logger.info("✅ Database schema created successfully")
    
    async def _create_indexes(self, conn: Connection) -> None:
        """Create database indexes for optimal performance"""
        
        indexes = [
            # Market data indexes
            "CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp DESC)",
            
            # News events indexes
            "CREATE INDEX IF NOT EXISTS idx_news_events_timestamp ON news_events(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_news_events_symbols ON news_events USING GIN (symbols_mentioned)",
            "CREATE INDEX IF NOT EXISTS idx_news_events_event_type ON news_events(event_type)",
            
            # Agent responses indexes
            "CREATE INDEX IF NOT EXISTS idx_agent_responses_agent_symbol ON agent_responses(agent_type, symbol)",
            "CREATE INDEX IF NOT EXISTS idx_agent_responses_timestamp ON agent_responses(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_agent_responses_session ON agent_responses(session_id)",
            
            # Trading decisions indexes
            "CREATE INDEX IF NOT EXISTS idx_trading_decisions_symbol_timestamp ON trading_decisions(symbol, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_trading_decisions_session ON trading_decisions(session_id)",
            
            # Performance metrics indexes
            "CREATE INDEX IF NOT EXISTS idx_performance_metrics_agent_type ON performance_metrics(agent_type)",
            
            # System events indexes
            "CREATE INDEX IF NOT EXISTS idx_system_events_timestamp ON system_events(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_system_events_type ON system_events(event_type)",
            
            # LLM usage indexes
            "CREATE INDEX IF NOT EXISTS idx_llm_usage_provider_model ON llm_usage(provider, model)",
            "CREATE INDEX IF NOT EXISTS idx_llm_usage_timestamp ON llm_usage(timestamp DESC)"
        ]
        
        for index_sql in indexes:
            try:
                await conn.execute(index_sql)
            except Exception as e:
                logger.warning(f"Error creating index: {e}")
    
    async def _record_schema_version(self, conn: Connection) -> None:
        """Record the current schema version"""
        
        await conn.execute("""
            INSERT INTO schema_version (version, description)
            VALUES ($1, $2)
        """, self.schema_version, f"AI Trading System schema version {self.schema_version}")
    
    # CRUD Operations for Market Data
    async def save_market_data(self, market_data: MarketData) -> int:
        """Save market data to database"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as conn:
            return await conn.fetchval("""
                INSERT INTO market_data (symbol, price, volume, timestamp, bid, ask, vix, sector)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """, market_data.symbol, market_data.price, market_data.volume, 
                market_data.timestamp, market_data.bid, market_data.ask, 
                market_data.vix, market_data.sector)
    
    async def get_latest_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get the latest market data for a symbol"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT symbol, price, volume, timestamp, bid, ask, vix, sector
                FROM market_data
                WHERE symbol = $1
                ORDER BY timestamp DESC
                LIMIT 1
            """, symbol)
            
            if row:
                return MarketData(**dict(row))
            return None
    
    async def get_market_data_history(self, symbol: str, hours: int = 24) -> List[MarketData]:
        """Get market data history for a symbol"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        since = datetime.now() - timedelta(hours=hours)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT symbol, price, volume, timestamp, bid, ask, vix, sector
                FROM market_data
                WHERE symbol = $1 AND timestamp >= $2
                ORDER BY timestamp DESC
            """, symbol, since)
            
            return [MarketData(**dict(row)) for row in rows]
    
    # CRUD Operations for News Events
    async def save_news_event(self, news_event: NewsEvent) -> None:
        """Save news event to database"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO news_events (
                    id, title, content, source, timestamp, relevance_score,
                    symbols_mentioned, sentiment_score, event_type
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    relevance_score = EXCLUDED.relevance_score,
                    sentiment_score = EXCLUDED.sentiment_score,
                    event_type = EXCLUDED.event_type
            """, news_event.id, news_event.title, news_event.content, news_event.source,
                news_event.timestamp, news_event.relevance_score, news_event.symbols_mentioned,
                news_event.sentiment_score, news_event.event_type.value if news_event.event_type else None)
    
    async def get_recent_news(self, symbol: str, hours: int = 24) -> List[NewsEvent]:
        """Get recent news events for a symbol"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        since = datetime.now() - timedelta(hours=hours)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, title, content, source, timestamp, relevance_score,
                       symbols_mentioned, sentiment_score, event_type
                FROM news_events
                WHERE $1 = ANY(symbols_mentioned) AND timestamp >= $2
                ORDER BY timestamp DESC, relevance_score DESC
            """, symbol, since)
            
            news_events = []
            for row in rows:
                event_type = MarketEventType(row['event_type']) if row['event_type'] else None
                news_events.append(NewsEvent(
                    id=row['id'],
                    title=row['title'],
                    content=row['content'],
                    source=row['source'],
                    timestamp=row['timestamp'],
                    relevance_score=row['relevance_score'],
                    symbols_mentioned=row['symbols_mentioned'],
                    sentiment_score=row['sentiment_score'],
                    event_type=event_type
                ))
            
            return news_events
    
    # CRUD Operations for Agent Responses
    async def save_agent_response(self, response: AgentResponse, symbol: str, session_id: str) -> int:
        """Save agent response to database"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as conn:
            return await conn.fetchval("""
                INSERT INTO agent_responses (
                    agent_type, symbol, confidence, recommendation, reasoning,
                    supporting_data, timestamp, risk_score, target_price, stop_loss, session_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
            """, response.agent_type.value, symbol, response.confidence, response.recommendation.value,
                response.reasoning, json.dumps(response.supporting_data), response.timestamp,
                response.risk_score, response.target_price, response.stop_loss, session_id)
    
    # CRUD Operations for Trading Decisions
    async def save_trading_decision(self, decision: Dict[str, Any], symbol: str, session_id: str) -> int:
        """Save trading decision to database"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as conn:
            return await conn.fetchval("""
                INSERT INTO trading_decisions (
                    session_id, symbol, final_action, confidence, reasoning,
                    weighted_votes, total_weight, event_type, agent_contributions,
                    failed_agents, is_significant_event, timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id
            """, 
                session_id, symbol, 
                decision['action'].value if hasattr(decision['action'], 'value') else decision['action'],
                decision['confidence'], decision['reasoning'],
                json.dumps(decision.get('weighted_votes', {})), decision.get('total_weight', 0),
                decision.get('event_type'), json.dumps(decision.get('agent_contributions', {})),
                decision.get('failed_agents', []), decision.get('is_significant_event', False),
                datetime.now()
            )
    
    async def get_decision_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get trading decision history for a symbol"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        since = datetime.now() - timedelta(days=days)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT session_id, symbol, final_action, confidence, reasoning,
                       weighted_votes, total_weight, event_type, agent_contributions,
                       failed_agents, is_significant_event, timestamp
                FROM trading_decisions
                WHERE symbol = $1 AND timestamp >= $2
                ORDER BY timestamp DESC
            """, symbol, since)
            
            return [dict(row) for row in rows]
    
    # CRUD Operations for Performance Metrics
    async def save_performance_metrics(self, metrics: PerformanceMetric) -> None:
        """Save/update performance metrics for an agent"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO performance_metrics (
                    agent_type, accuracy_rate, confidence_calibration,
                    total_predictions, correct_predictions, performance_by_event_type, last_updated
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (agent_type) DO UPDATE SET
                    accuracy_rate = EXCLUDED.accuracy_rate,
                    confidence_calibration = EXCLUDED.confidence_calibration,
                    total_predictions = EXCLUDED.total_predictions,
                    correct_predictions = EXCLUDED.correct_predictions,
                    performance_by_event_type = EXCLUDED.performance_by_event_type,
                    last_updated = EXCLUDED.last_updated
            """, 
                metrics.agent_type.value, metrics.accuracy_rate, metrics.confidence_calibration,
                metrics.total_predictions, metrics.correct_predictions,
                json.dumps({k.value: v for k, v in metrics.performance_by_event_type.items()}),
                metrics.last_updated
            )
    
    async def get_performance_metrics(self, agent_type: AgentType) -> Optional[PerformanceMetric]:
        """Get performance metrics for an agent"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT agent_type, accuracy_rate, confidence_calibration,
                       total_predictions, correct_predictions, performance_by_event_type, last_updated
                FROM performance_metrics
                WHERE agent_type = $1
            """, agent_type.value)
            
            if row:
                # Parse performance_by_event_type JSON
                perf_by_event = {}
                if row['performance_by_event_type']:
                    perf_data = json.loads(row['performance_by_event_type'])
                    perf_by_event = {MarketEventType(k): v for k, v in perf_data.items()}
                
                return PerformanceMetric(
                    agent_type=AgentType(row['agent_type']),
                    accuracy_rate=row['accuracy_rate'],
                    confidence_calibration=row['confidence_calibration'],
                    total_predictions=row['total_predictions'],
                    correct_predictions=row['correct_predictions'],
                    performance_by_event_type=perf_by_event,
                    last_updated=row['last_updated']
                )
            return None
    
    # System Events and Logging
    async def log_system_event(self, event_type: str, message: str, severity: str = "INFO", details: Optional[Dict] = None) -> None:
        """Log system event to database"""
        
        if not self.pool:
            return  # Fail silently for logging
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO system_events (event_type, severity, message, details)
                    VALUES ($1, $2, $3, $4)
                """, event_type, severity, message, json.dumps(details) if details else None)
        except Exception as e:
            logger.error(f"Failed to log system event: {e}")
    
    # LLM Usage Tracking
    async def log_llm_usage(self, provider: str, model: str, agent_type: str, tokens_used: int, 
                           response_time_ms: Optional[int] = None, success: bool = True, 
                           error_message: Optional[str] = None) -> None:
        """Log LLM API usage for monitoring and cost tracking"""
        
        if not self.pool:
            return
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO llm_usage (provider, model, agent_type, tokens_used, 
                                         response_time_ms, success, error_message)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, provider, model, agent_type, tokens_used, response_time_ms, success, error_message)
        except Exception as e:
            logger.error(f"Failed to log LLM usage: {e}")
    
    # Analytics and Reporting
    async def get_system_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive system analytics"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        since = datetime.now() - timedelta(days=days)
        
        async with self.pool.acquire() as conn:
            # Decision summary
            decision_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_decisions,
                    AVG(confidence) as avg_confidence,
                    COUNT(CASE WHEN final_action = 'BUY' THEN 1 END) as buy_decisions,
                    COUNT(CASE WHEN final_action = 'SELL' THEN 1 END) as sell_decisions,
                    COUNT(CASE WHEN final_action = 'HOLD' THEN 1 END) as hold_decisions
                FROM trading_decisions
                WHERE timestamp >= $1
            """, since)
            
            # Agent performance summary
            agent_stats = await conn.fetch("""
                SELECT agent_type, accuracy_rate, total_predictions, correct_predictions
                FROM performance_metrics
                ORDER BY accuracy_rate DESC
            """)
            
            # LLM usage summary
            llm_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(tokens_used) as total_tokens,
                    AVG(response_time_ms) as avg_response_time_ms,
                    COUNT(CASE WHEN success THEN 1 END)::FLOAT / COUNT(*) as success_rate
                FROM llm_usage
                WHERE timestamp >= $1
            """, since)
            
            # System events summary
            error_count = await conn.fetchval("""
                SELECT COUNT(*) FROM system_events
                WHERE severity IN ('ERROR', 'CRITICAL') AND timestamp >= $1
            """, since)
            
            return {
                "period_days": days,
                "decisions": dict(decision_stats) if decision_stats else {},
                "agents": [dict(row) for row in agent_stats],
                "llm_usage": dict(llm_stats) if llm_stats else {},
                "error_count": error_count or 0,
                "generated_at": datetime.now().isoformat()
            }
    
    # Database Maintenance
    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """Clean up old data to maintain database performance"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_counts = {}
        
        async with self.pool.acquire() as conn:
            # Clean up old market data
            deleted_count = await conn.execute("""
                DELETE FROM market_data WHERE timestamp < $1
            """, cutoff_date)
            deleted_counts['market_data'] = int(deleted_count.split()[-1]) if deleted_count else 0
            
            # Clean up old news events
            deleted_count = await conn.execute("""
                DELETE FROM news_events WHERE timestamp < $1
            """, cutoff_date)
            deleted_counts['news_events'] = int(deleted_count.split()[-1]) if deleted_count else 0
            
            # Clean up old agent responses
            deleted_count = await conn.execute("""
                DELETE FROM agent_responses WHERE timestamp < $1
            """, cutoff_date)
            deleted_counts['agent_responses'] = int(deleted_count.split()[-1]) if deleted_count else 0
            
            # Clean up old system events (keep errors longer)
            error_cutoff = datetime.now() - timedelta(days=days_to_keep * 2)
            deleted_count = await conn.execute("""
                DELETE FROM system_events 
                WHERE (timestamp < $1 AND severity NOT IN ('ERROR', 'CRITICAL'))
                OR timestamp < $2
            """, cutoff_date, error_cutoff)
            deleted_counts['system_events'] = int(deleted_count.split()[-1]) if deleted_count else 0
            
            # Clean up old LLM usage logs
            deleted_count = await conn.execute("""
                DELETE FROM llm_usage WHERE timestamp < $1
            """, cutoff_date)
            deleted_counts['llm_usage'] = int(deleted_count.split()[-1]) if deleted_count else 0
        
        total_deleted = sum(deleted_counts.values())
        logger.info(f"Cleanup complete: {total_deleted} records deleted")
        
        return deleted_counts
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics and health info"""
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as conn:
            # Table sizes
            table_stats = await conn.fetch("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE schemaname = 'public'
                ORDER BY tablename, attname
            """)
            
            # Database size
            db_size = await conn.fetchval("""
                SELECT pg_size_pretty(pg_database_size($1))
            """, self.config.database)
            
            # Connection info
            connection_count = await conn.fetchval("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE datname = $1
            """, self.config.database)
            
            return {
                "database_size": db_size,
                "active_connections": connection_count,
                "pool_size": f"{self.pool.get_size()}/{self.pool.get_max_size()}",
                "table_stats": [dict(row) for row in table_stats],
                "schema_version": self.schema_version
            }
    
    async def close(self) -> None:
        """Close database connections"""
        
        if self.pool:
            await self.pool.close()
            logger.info("Database connections closed")


# Utility functions for database setup
async def setup_database(config: Optional[DatabaseConfig] = None, force_recreate: bool = False) -> DatabaseManager:
    """Setup database with proper error handling and logging"""
    
    db_manager = DatabaseManager(config)
    
    try:
        if force_recreate:
            logger.warning("Force recreating database schema...")
            # Additional logic for dropping and recreating tables would go here
        
        await db_manager.initialize()
        
        logger.info("✅ Database setup completed successfully")
        return db_manager
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise


# Database migration utilities
class DatabaseMigration:
    """Handle database schema migrations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def run_migration(self, from_version: str, to_version: str) -> None:
        """Run database migration between versions"""
        
        if not self.db_manager.pool:
            raise RuntimeError("Database pool not initialized")
        
        logger.info(f"Running migration from {from_version} to {to_version}")
        
        async with self.db_manager.pool.acquire() as conn:
            async with conn.transaction():
                # Example migration logic
                if from_version == "0.9.0" and to_version == "1.0.0":
                    await self._migrate_v0_9_to_v1_0(conn)
                
                # Record migration
                await conn.execute("""
                    INSERT INTO schema_version (version, description)
                    VALUES ($1, $2)
                """, to_version, f"Migration from {from_version} to {to_version}")
        
        logger.info(f"✅ Migration to {to_version} completed")
    
    async def _migrate_v0_9_to_v1_0(self, conn: Connection) -> None:
        """Example migration from v0.9 to v1.0"""
        
        # Add new columns, tables, indexes as needed
        await conn.execute("""
            ALTER TABLE agent_responses 
            ADD COLUMN IF NOT EXISTS session_id UUID
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_responses_session 
            ON agent_responses(session_id)
        """)


if __name__ == "__main__":
    """
    Database setup script - can be run standalone for initial setup
    """
    
    import sys
    import argparse
    
    async def main():
        parser = argparse.ArgumentParser(description='Trading System Database Setup')
        # parser.add_argument('--host', default='localhost', help='Database host')
        # parser.add_argument('--port', type=int, default=5432, help='Database port')
        # parser.add_argument('--database', default='trading_system', help='Database name')
        # parser.add_argument('--username', default='postgres', help='Database username')
        # parser.add_argument('--password', help='Database password')
        parser.add_argument('--force-recreate', action='store_true', help='Force recreate schema')
        parser.add_argument('--test-only', action='store_true', help='Only test connection')
        parser.add_argument('--cleanup', type=int, help='Cleanup data older than N days')
        parser.add_argument('--analytics', action='store_true', help='Show system analytics')
        
        args = parser.parse_args()
        
        # Setup configuration
        config = DatabaseConfig()
        # if args.host:
        #     config.host = args.host
        # if args.port:
        #     config.port = args.port
        # if args.database:
        #     config.database = args.database
        # if args.username:
        #     config.username = args.username
        # if args.password:
        #     config.password = args.password
        
        print("🗄️  AI Trading System - Database Setup")
        print("=" * 50)
        print(f"Host: {config.host}:{config.port}")
        print(f"Database: {config.database}")
        print(f"Username: {config.username}")
        print()
        
        try:
            if args.test_only:
                print("🔍 Testing database connection...")
                success = await test_database_connection(config)
                if success:
                    print("✅ Connection test passed!")
                    return 0
                else:
                    print("❌ Connection test failed!")
                    return 1
            
            # Setup database
            print("🚀 Initializing database...")
            db_manager = await setup_database(config, args.force_recreate)
            
            if args.cleanup:
                print(f"🧹 Cleaning up data older than {args.cleanup} days...")
                deleted = await db_manager.cleanup_old_data(args.cleanup)
                print(f"✅ Cleanup complete: {sum(deleted.values())} records deleted")
                for table, count in deleted.items():
                    if count > 0:
                        print(f"   {table}: {count} records")
            
            if args.analytics:
                print("📊 Generating system analytics...")
                analytics = await db_manager.get_system_analytics()
                print(f"Analytics for last {analytics['period_days']} days:")
                print(f"  Total decisions: {analytics['decisions'].get('total_decisions', 0)}")
                print(f"  Average confidence: {analytics['decisions'].get('avg_confidence', 0):.3f}")
                print(f"  LLM requests: {analytics['llm_usage'].get('total_requests', 0)}")
                print(f"  Error count: {analytics['error_count']}")
            
            # Show database stats
            stats = await db_manager.get_database_stats()
            print(f"📈 Database Statistics:")
            print(f"  Database size: {stats['database_size']}")
            print(f"  Active connections: {stats['active_connections']}")
            print(f"  Connection pool: {stats['pool_size']}")
            print(f"  Schema version: {stats['schema_version']}")
            
            await db_manager.close()
            print("✅ Database setup completed successfully!")
            return 0
            
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            return 1
    
    # Run the setup
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


async def test_database_connection(config: Optional[DatabaseConfig] = None) -> bool:
    """Test database connection and basic operations"""
    
    try:
        db_manager = DatabaseManager(config)
        await db_manager.initialize()
        
        # Test basic operations
        async with db_manager.pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            assert result == 1
        
        await db_manager.close()
        
        logger.info("✅ Database connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


        