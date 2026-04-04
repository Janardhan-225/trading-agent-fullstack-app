-- PostgreSQL Schema for Trading Agents

-- Market quotes from Finnhub
CREATE TABLE IF NOT EXISTS market_quotes (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    current_price DECIMAL(12, 4),
    change DECIMAL(12, 4),
    percent_change DECIMAL(8, 4),
    high DECIMAL(12, 4),
    low DECIMAL(12, 4),
    open DECIMAL(12, 4),
    previous_close DECIMAL(12, 4),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_ticker_timestamp UNIQUE (ticker, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_market_quotes_ticker ON market_quotes(ticker);
CREATE INDEX IF NOT EXISTS idx_market_quotes_timestamp ON market_quotes(timestamp);

-- Sentiment scores from FinBERT
CREATE TABLE IF NOT EXISTS sentiment_scores (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    headline TEXT NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    score DECIMAL(6, 4) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sentiment_ticker ON sentiment_scores(ticker);
CREATE INDEX IF NOT EXISTS idx_sentiment_timestamp ON sentiment_scores(timestamp);

-- Trade ledger for all transactions
CREATE TABLE IF NOT EXISTS trade_ledger (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL', 'HOLD')),
    price DECIMAL(12, 4),
    quantity INTEGER,
    reasoning TEXT,
    sentiment_avg DECIMAL(6, 4),
    rsi DECIMAL(6, 2),
    macd DECIMAL(12, 4),
    approved BOOLEAN NOT NULL,
    portfolio_manager_reasoning TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trade_ledger_ticker ON trade_ledger(ticker);
CREATE INDEX IF NOT EXISTS idx_trade_ledger_timestamp ON trade_ledger(timestamp);
CREATE INDEX IF NOT EXISTS idx_trade_ledger_action ON trade_ledger(action);

-- News staging table for Sentinel News Engine
CREATE TABLE IF NOT EXISTS news_staging (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(10) NOT NULL,
    source VARCHAR(50) NOT NULL,
    headline TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    published_at TIMESTAMP,
    sentiment_score FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_staging_ticker ON news_staging(ticker);
CREATE INDEX IF NOT EXISTS idx_news_staging_published_at ON news_staging(published_at);
CREATE INDEX IF NOT EXISTS idx_news_staging_created_at ON news_staging(created_at);
