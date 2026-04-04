"""Database manager for PostgreSQL operations."""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Dict, List, Optional
import config


class DatabaseManager:
    """Manages PostgreSQL database connections and operations."""
    
    def __init__(self):
        self.config = config.DB_CONFIG
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = psycopg2.connect(**self.config)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def initialize_schema(self):
        """Initialize database schema from schema.sql."""
        from pathlib import Path
        schema_path = Path(__file__).parent / "schema.sql"
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
    
    def insert_market_quote(self, ticker: str, quote_data: Dict):
        """Insert market quote data."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO market_quotes 
                    (ticker, current_price, change, percent_change, high, low, open, previous_close)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, timestamp) DO NOTHING
                """, (
                    ticker,
                    quote_data.get('c'),
                    quote_data.get('d'),
                    quote_data.get('dp'),
                    quote_data.get('h'),
                    quote_data.get('l'),
                    quote_data.get('o'),
                    quote_data.get('pc')
                ))
    
    def insert_sentiment_score(self, ticker: str, headline: str, sentiment: str, score: float):
        """Insert sentiment analysis result."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sentiment_scores (ticker, headline, sentiment, score)
                    VALUES (%s, %s, %s, %s)
                """, (ticker, headline, sentiment, score))
    
    def insert_trade(self, ticker: str, action: str, price: float, quantity: int,
                    reasoning: str, sentiment_avg: float, rsi: float, macd: float,
                    approved: bool, portfolio_manager_reasoning: str):
        """Insert trade decision into ledger."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO trade_ledger 
                    (ticker, action, price, quantity, reasoning, sentiment_avg, 
                     rsi, macd, approved, portfolio_manager_reasoning)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (ticker, action, price, quantity, reasoning, sentiment_avg,
                      rsi, macd, approved, portfolio_manager_reasoning))
                return cur.fetchone()[0]
    
    def get_recent_sentiments(self, ticker: str, limit: int = 10) -> List[Dict]:
        """Get recent sentiment scores for a ticker."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM sentiment_scores 
                    WHERE ticker = %s 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (ticker, limit))
                return cur.fetchall()
    
    def upsert_news_article(self, ticker: str, source: str, headline: str, url: str,
                            published_at, sentiment_score: float = None) -> bool:
        """Insert news article, ignore if URL already exists. Returns True if inserted."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO news_staging (ticker, source, headline, url, published_at, sentiment_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                """, (ticker, source, headline, url, published_at, sentiment_score))
                return cur.rowcount > 0

    def update_news_sentiment(self, url: str, sentiment_score: float):
        """Update sentiment score for a news article."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE news_staging SET sentiment_score = %s WHERE url = %s
                """, (sentiment_score, url))

    def get_recent_news(self, ticker: str, hours: int = 1) -> List[Dict]:
        """Get news articles from the last N hours for a ticker, using created_at for recency."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM news_staging
                    WHERE ticker = %s
                      AND created_at >= NOW() - INTERVAL '1 hour' * %s
                      AND sentiment_score IS NOT NULL
                    ORDER BY published_at DESC
                """, (ticker, hours))
                return cur.fetchall()

    def get_recent_trades(self, ticker: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get recent trades, optionally filtered by ticker."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if ticker:
                    cur.execute("""
                        SELECT * FROM trade_ledger 
                        WHERE ticker = %s 
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    """, (ticker, limit))
                else:
                    cur.execute("""
                        SELECT * FROM trade_ledger 
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    """, (limit,))
                return cur.fetchall()
