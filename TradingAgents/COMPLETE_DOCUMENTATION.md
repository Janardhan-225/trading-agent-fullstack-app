# Trading Agents - Complete Technical Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Low-Level Architecture](#low-level-architecture)
4. [Data Flow](#data-flow)
5. [Component Details](#component-details)
6. [Database Schema](#database-schema)
7. [AI Models](#ai-models)
8. [Execution Flow](#execution-flow)

---

## System Overview

Trading Agents is an AI-powered stock analysis system that uses:
- **Local AI Models** (FinBERT, Llama 3.2, DeepSeek-R1)
- **Real-time Market Data** (Finnhub API)
- **News Sentiment Analysis** (yfinance)
- **PostgreSQL Database** for persistence
- **LangGraph** for workflow orchestration

**Purpose**: Analyze 10 tech stocks and make BUY/SELL/HOLD decisions with transparent reasoning.

**Asset Universe**: AAPL, MSFT, NVDA, TSLA, GOOGL, AMZN, META, NFLX, AMD, INTC

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TRADING AGENTS SYSTEM                           │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Finnhub    │     │  yfinance    │     │  PostgreSQL  │
│   API        │     │  (News)      │     │  Database    │
│  (Quotes)    │     │              │     │              │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────┬───────┴────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   Data Ingestion     │
         │   (Workflow Node 1)  │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Sentiment Analysis   │
         │   (FinBERT - CPU)    │
         │   (Workflow Node 2)  │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Technical Analysis   │
         │  (Llama 3.2 + RSI/   │
         │   MACD Computation)  │
         │   (Workflow Node 3)  │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Portfolio Manager   │
         │  (DeepSeek-R1:7b)    │
         │  Chain of Thought    │
         │   (Workflow Node 4)  │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   Rich Dashboard     │
         │   (Terminal UI)      │
         └──────────────────────┘
```

---

## Low-Level Architecture

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            MAIN.PY (Entry Point)                        │
│  - Loads .env configuration                                             │
│  - Removes SSL environment variables                                    │
│  - Parses command-line arguments                                        │
│  - Initializes TradingWorkflow                                          │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    TRADING WORKFLOW (LangGraph)                         │
│  File: graph/trading_workflow.py                                        │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  STATE MANAGEMENT (TypedDict)                                  │    │
│  │  - ticker: str                                                 │    │
│  │  - market_data: Dict                                           │    │
│  │  - price_history: DataFrame                                    │    │
│  │  - headlines: List[str]                                        │    │
│  │  - sentiment_data: Dict                                        │    │
│  │  - technical_data: Dict                                        │    │
│  │  - decision: Dict                                              │    │
│  │  - error: str                                                  │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  NODE 1: DATA INGESTION                                         │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │  FinnhubClient (data/finnhub_client.py)                  │  │   │
│  │  │  - GET /quote endpoint                                    │  │   │
│  │  │  - Returns: price, change, high, low, volume             │  │   │
│  │  │  - Stores in: market_quotes table                        │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │  YFinanceClient (data/yfinance_client.py)                │  │   │
│  │  │  - Fetches news headlines (10 max)                       │  │   │
│  │  │  - Fetches 1-month price history                         │  │   │
│  │  │  - Returns: OHLCV DataFrame                              │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                             │                                            │
│                             ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  NODE 2: SENTIMENT ANALYSIS                                     │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │  SentimentAnalyst (agents/sentiment_analyst.py)          │  │   │
│  │  │                                                           │  │   │
│  │  │  FinBERT Model (./model/finbert/)                        │  │   │
│  │  │  ├─ Tokenizer: BertTokenizer                             │  │   │
│  │  │  ├─ Model: BertForSequenceClassification                 │  │   │
│  │  │  ├─ Device: CPU                                           │  │   │
│  │  │  └─ Output: positive/negative/neutral + confidence       │  │   │
│  │  │                                                           │  │   │
│  │  │  For each headline:                                       │  │   │
│  │  │  1. Tokenize (max 512 tokens)                            │  │   │
│  │  │  2. Run inference (no_grad)                              │  │   │
│  │  │  3. Softmax probabilities                                │  │   │
│  │  │  4. Store in sentiment_scores table                      │  │   │
│  │  │                                                           │  │   │
│  │  │  Aggregation:                                             │  │   │
│  │  │  - Count positive/negative/neutral                       │  │   │
│  │  │  - Calculate sentiment score: (pos - neg) / total        │  │   │
│  │  │  - Range: -1 (very negative) to +1 (very positive)       │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                             │                                            │
│                             ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  NODE 3: TECHNICAL ANALYSIS                                     │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │  TechnicalSpecialist (agents/technical_specialist.py)    │  │   │
│  │  │                                                           │  │   │
│  │  │  STEP 1: Compute Indicators (pandas)                     │  │   │
│  │  │  ┌────────────────────────────────────────────────────┐  │  │   │
│  │  │  │  RSI (Relative Strength Index)                     │  │  │   │
│  │  │  │  - Period: 14 days                                 │  │  │   │
│  │  │  │  - Formula: 100 - (100 / (1 + RS))                │  │  │   │
│  │  │  │  - RS = Average Gain / Average Loss                │  │  │   │
│  │  │  │  - Interpretation:                                 │  │  │   │
│  │  │  │    * > 70: Overbought                              │  │  │   │
│  │  │  │    * < 30: Oversold                                │  │  │   │
│  │  │  │    * 30-70: Neutral                                │  │  │   │
│  │  │  └────────────────────────────────────────────────────┘  │  │   │
│  │  │  ┌────────────────────────────────────────────────────┐  │  │   │
│  │  │  │  MACD (Moving Average Convergence Divergence)      │  │  │   │
│  │  │  │  - Fast EMA: 12 periods                            │  │  │   │
│  │  │  │  - Slow EMA: 26 periods                            │  │  │   │
│  │  │  │  - Signal: 9-period EMA of MACD                    │  │  │   │
│  │  │  │  - MACD Line = EMA(12) - EMA(26)                   │  │  │   │
│  │  │  │  - Signal Line = EMA(9) of MACD                    │  │  │   │
│  │  │  │  - Histogram = MACD - Signal                       │  │  │   │
│  │  │  │  - Interpretation:                                 │  │  │   │
│  │  │  │    * MACD > Signal: Bullish                        │  │  │   │
│  │  │  │    * MACD < Signal: Bearish                        │  │  │   │
│  │  │  │    * Histogram > 0: Momentum increasing            │  │  │   │
│  │  │  └────────────────────────────────────────────────────┘  │  │   │
│  │  │                                                           │  │   │
│  │  │  STEP 2: LLM Analysis (Llama 3.2 via Ollama)             │  │   │
│  │  │  ┌────────────────────────────────────────────────────┐  │  │   │
│  │  │  │  Prompt includes:                                  │  │  │   │
│  │  │  │  - Current price, change, high, low                │  │  │   │
│  │  │  │  - RSI value and interpretation                    │  │  │   │
│  │  │  │  - MACD values (line, signal, histogram)           │  │  │   │
│  │  │  │                                                     │  │  │   │
│  │  │  │  Llama 3.2 generates:                              │  │  │   │
│  │  │  │  - 2-3 sentence technical analysis                 │  │  │   │
│  │  │  │  - Bullish/Bearish/Neutral signal                  │  │  │   │
│  │  │  │  - Momentum assessment                              │  │  │   │
│  │  │  │                                                     │  │  │   │
│  │  │  │  Timeout: 60 seconds                               │  │  │   │
│  │  │  │  Model: llama3.2:latest                            │  │  │   │
│  │  │  └────────────────────────────────────────────────────┘  │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                             │                                            │
│                             ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  NODE 4: PORTFOLIO MANAGER (DECISION MAKER)                     │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │  PortfolioManager (agents/portfolio_manager.py)          │  │   │
│  │  │                                                           │  │   │
│  │  │  INPUTS RECEIVED:                                         │  │   │
│  │  │  ├─ Sentiment Data (from Node 2)                         │  │   │
│  │  │  │  └─ avg_sentiment, score, ratios                      │  │   │
│  │  │  ├─ Technical Data (from Node 3)                         │  │   │
│  │  │  │  └─ RSI, MACD, Llama analysis                         │  │   │
│  │  │  ├─ Market Data (from Node 1)                            │  │   │
│  │  │  │  └─ price, change, high, low                          │  │   │
│  │  │  └─ Historical Trades (from Database)                    │  │   │
│  │  │     └─ Past 5 trades for this ticker                     │  │   │
│  │  │                                                           │  │   │
│  │  │  DEEPSEEK-R1:7B REASONING PROCESS:                       │  │   │
│  │  │  ┌────────────────────────────────────────────────────┐  │  │   │
│  │  │  │  PHASE 1: Chain of Thought (<think> tags)          │  │  │   │
│  │  │  │  ─────────────────────────────────────────────────  │  │  │   │
│  │  │  │  1. Analyze sentiment-technical alignment          │  │  │   │
│  │  │  │     - Do sentiment and RSI agree?                  │  │  │   │
│  │  │  │     - Is MACD confirming sentiment?                │  │  │   │
│  │  │  │                                                     │  │  │   │
│  │  │  │  2. Identify conflicts and risks                   │  │  │   │
│  │  │  │     - Positive sentiment but overbought RSI?       │  │  │   │
│  │  │  │     - Negative news but oversold conditions?       │  │  │   │
│  │  │  │                                                     │  │  │   │
│  │  │  │  3. Evaluate market conditions                     │  │  │   │
│  │  │  │     - Price momentum (up/down)                     │  │  │   │
│  │  │  │     - Volatility (high - low range)                │  │  │   │
│  │  │  │                                                     │  │  │   │
│  │  │  │  4. Review historical patterns                     │  │  │   │
│  │  │  │     - Past decisions for this stock                │  │  │   │
│  │  │  │     - What worked, what didn't                     │  │  │   │
│  │  │  │                                                     │  │  │   │
│  │  │  │  5. Justify decision                               │  │  │   │
│  │  │  │     - Why BUY/SELL/HOLD?                           │  │  │   │
│  │  │  │     - What's the confidence level?                 │  │  │   │
│  │  │  └────────────────────────────────────────────────────┘  │  │   │
│  │  │  ┌────────────────────────────────────────────────────┐  │  │   │
│  │  │  │  PHASE 2: Final Decision (after </think>)          │  │  │   │
│  │  │  │  ─────────────────────────────────────────────────  │  │  │   │
│  │  │  │  DECISION: BUY / SELL / HOLD                       │  │  │   │
│  │  │  │  CONFIDENCE: HIGH / MEDIUM / LOW                   │  │  │   │
│  │  │  │  REASONING: One sentence explanation               │  │  │   │
│  │  │  │                                                     │  │  │   │
│  │  │  │  Approval Logic:                                   │  │  │   │
│  │  │  │  - approved = True if BUY or SELL                  │  │  │   │
│  │  │  │  - approved = False if HOLD                        │  │  │   │
│  │  │  └────────────────────────────────────────────────────┘  │  │   │
│  │  │                                                           │  │   │
│  │  │  Model: deepseek-r1:7b                                    │  │   │
│  │  │  Timeout: 180 seconds (3 minutes)                         │  │   │
│  │  │  Output stored in: trade_ledger table                     │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATABASE STORAGE (PostgreSQL)                        │
│  File: database/db_manager.py                                           │
│                                                                          │
│  All data persisted for:                                                │
│  - Historical analysis                                                  │
│  - Pattern recognition                                                  │
│  - Performance tracking                                                 │
│  - Audit trail                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    RICH DASHBOARD (Terminal UI)                         │
│  File: cli/dashboard.py                                                 │
│                                                                          │
│  Displays:                                                              │
│  - Summary table (all stocks)                                           │
│  - Detailed panels (per stock)                                          │
│  - Color-coded indicators                                               │
│  - Real-time updates                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────┐
│   START     │
│ (main.py)   │
└──────┬──────┘
       │
       ├─ Load .env configuration
       ├─ Remove SSL env vars
       ├─ Parse CLI arguments (--ticker, --monitor, --init-db)
       │
       ▼
┌──────────────────────┐
│  Initialize Workflow │
│  (TradingWorkflow)   │
└──────┬───────────────┘
       │
       ├─ Create SentimentAnalyst (load FinBERT)
       ├─ Create TechnicalSpecialist (connect Ollama)
       ├─ Create PortfolioManager (connect Ollama)
       ├─ Create FinnhubClient (API key from .env)
       ├─ Create YFinanceClient
       ├─ Create DatabaseManager (PostgreSQL connection)
       │
       ▼
┌──────────────────────┐
│  For each ticker:    │
│  (AAPL, MSFT, etc.)  │
└──────┬───────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 1: DATA INGESTION                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Finnhub API Call                                   │   │
│  │  GET https://finnhub.io/api/v1/quote               │   │
│  │  Params: symbol=AAPL, token=<API_KEY>              │   │
│  │                                                      │   │
│  │  Response:                                           │   │
│  │  {                                                   │   │
│  │    "c": 272.14,    // current price                 │   │
│  │    "d": 5.96,      // change                        │   │
│  │    "dp": 2.24,     // percent change                │   │
│  │    "h": 275.50,    // high                          │   │
│  │    "l": 270.00,    // low                           │   │
│  │    "o": 271.00,    // open                          │   │
│  │    "pc": 266.18    // previous close                │   │
│  │  }                                                   │   │
│  │                                                      │   │
│  │  ↓ Store in market_quotes table                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  yfinance News Fetch                                │   │
│  │  stock = yf.Ticker("AAPL")                          │   │
│  │  news = stock.news                                  │   │
│  │                                                      │   │
│  │  Extract headlines (max 10):                        │   │
│  │  [                                                   │   │
│  │    "Apple announces new iPhone...",                 │   │
│  │    "AAPL stock rises on earnings...",               │   │
│  │    ...                                               │   │
│  │  ]                                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  yfinance Price History                             │   │
│  │  hist = stock.history(period="1mo")                 │   │
│  │                                                      │   │
│  │  Returns DataFrame:                                 │   │
│  │  Date       | Open   | High   | Low    | Close      │   │
│  │  2026-01-27 | 270.00 | 275.00 | 268.50 | 272.14     │   │
│  │  2026-01-26 | 268.00 | 271.00 | 267.00 | 269.50     │   │
│  │  ...                                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Output State:                                               │
│  - market_data: Dict (price, change, etc.)                  │
│  - headlines: List[str] (10 headlines)                      │
│  - price_history: DataFrame (1 month OHLCV)                 │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 2: SENTIMENT ANALYSIS                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: headlines = ["Apple announces...", ...]              │
│                                                              │
│  For each headline:                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. Tokenization                                    │   │
│  │     inputs = tokenizer(                             │   │
│  │         headline,                                   │   │
│  │         return_tensors="pt",                        │   │
│  │         truncation=True,                            │   │
│  │         max_length=512                              │   │
│  │     )                                                │   │
│  │                                                      │   │
│  │  2. FinBERT Inference (CPU)                         │   │
│  │     with torch.no_grad():                           │   │
│  │         outputs = model(**inputs)                   │   │
│  │         probs = softmax(outputs.logits)             │   │
│  │                                                      │   │
│  │  3. Classification                                  │   │
│  │     scores = {                                      │   │
│  │         'negative': 0.05,                           │   │
│  │         'neutral': 0.15,                            │   │
│  │         'positive': 0.80  ← highest                 │   │
│  │     }                                                │   │
│  │     sentiment = 'positive'                          │   │
│  │     confidence = 0.80                               │   │
│  │                                                      │   │
│  │  4. Store in Database                               │   │
│  │     INSERT INTO sentiment_scores                    │   │
│  │     (ticker, headline, sentiment, score)            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Aggregation:                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Results: [                                         │   │
│  │    {'sentiment': 'positive', 'confidence': 0.80},   │   │
│  │    {'sentiment': 'neutral', 'confidence': 0.65},    │   │
│  │    {'sentiment': 'positive', 'confidence': 0.75},   │   │
│  │    ...                                               │   │
│  │  ]                                                   │   │
│  │                                                      │   │
│  │  Count:                                              │   │
│  │  - positive_count = 7                               │   │
│  │  - negative_count = 1                               │   │
│  │  - neutral_count = 2                                │   │
│  │  - total = 10                                       │   │
│  │                                                      │   │
│  │  Sentiment Score:                                   │   │
│  │  score = (7 - 1) / 10 = 0.60                        │   │
│  │                                                      │   │
│  │  Overall Sentiment:                                 │   │
│  │  if score > 0.2: 'positive'                         │   │
│  │  elif score < -0.2: 'negative'                      │   │
│  │  else: 'neutral'                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Output State:                                               │
│  sentiment_data = {                                          │
│      'ticker': 'AAPL',                                       │
│      'avg_sentiment': 'positive',                            │
│      'avg_score': 0.60,                                      │
│      'positive_ratio': 0.70,                                 │
│      'negative_ratio': 0.10,                                 │
│      'neutral_ratio': 0.20,                                  │
│      'total_headlines': 10                                   │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
       │
       ▼

## Component Details

### 1. Configuration (config.py)

```python
# Loads environment variables from .env
load_dotenv()

# Asset Universe
STOCKS = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL', 
          'AMZN', 'META', 'NFLX', 'AMD', 'INTC']

# Database Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "trading_agents"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "")
}

# Ollama Models
SPECIALIST_MODEL = "llama3.2"
PORTFOLIO_MANAGER_MODEL = "deepseek-r1:7b"
```

### 2. Data Clients

#### FinnhubClient (data/finnhub_client.py)
- **Purpose**: Fetch real-time market quotes
- **API**: Finnhub REST API
- **Endpoint**: `/quote`
- **Rate Limit**: 60 calls/minute (free tier)
- **Returns**: Current price, change, high, low, volume
- **Storage**: Inserts into `market_quotes` table

#### YFinanceClient (data/yfinance_client.py)
- **Purpose**: Fetch news and historical prices
- **Library**: yfinance (Python wrapper)
- **Methods**:
  - `get_news()`: Fetches recent headlines (max 10)
  - `get_price_history()`: Fetches OHLCV data (1 month)
- **No API key required**

### 3. AI Agents

#### SentimentAnalyst (agents/sentiment_analyst.py)
- **Model**: FinBERT (ProsusAI/finbert)
- **Type**: BERT-based sequence classification
- **Device**: CPU
- **Input**: News headlines (text)
- **Output**: positive/negative/neutral + confidence score
- **Process**:
  1. Tokenize headline (max 512 tokens)
  2. Run inference with torch.no_grad()
  3. Apply softmax to logits
  4. Select highest probability class
  5. Store in database
- **Aggregation**: Calculates overall sentiment from all headlines

#### TechnicalSpecialist (agents/technical_specialist.py)
- **Indicators**: RSI (14), MACD (12/26/9)
- **Computation**: Pure pandas (no external libraries)
- **LLM**: Llama 3.2 via Ollama
- **Purpose**: Interpret indicators and provide analysis
- **Timeout**: 60 seconds
- **Output**: 2-3 sentence technical analysis + bullish/bearish signal

#### PortfolioManager (agents/portfolio_manager.py)
- **Model**: DeepSeek-R1:7b via Ollama
- **Purpose**: Final decision maker with reasoning
- **Input**: All data from previous nodes + historical trades
- **Process**:
  1. Builds comprehensive prompt with all signals
  2. Calls DeepSeek-R1 with 180-second timeout
  3. Extracts `<think>` reasoning block
  4. Parses DECISION/CONFIDENCE/REASONING
  5. Stores complete reasoning in database
- **Output**: BUY/SELL/HOLD + confidence + reasoning

---

## Database Schema

### Table: market_quotes
```sql
CREATE TABLE market_quotes (
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
    UNIQUE (ticker, timestamp)
);
CREATE INDEX idx_market_quotes_ticker ON market_quotes(ticker);
CREATE INDEX idx_market_quotes_timestamp ON market_quotes(timestamp);
```

**Purpose**: Store real-time market data from Finnhub
**Retention**: All historical quotes
**Usage**: Price trend analysis, historical context

### Table: sentiment_scores
```sql
CREATE TABLE sentiment_scores (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    headline TEXT NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    score DECIMAL(6, 4) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_sentiment_ticker ON sentiment_scores(ticker);
CREATE INDEX idx_sentiment_timestamp ON sentiment_scores(timestamp);
```

**Purpose**: Store individual headline sentiment analysis
**Retention**: All historical sentiments
**Usage**: Sentiment trend analysis, news impact tracking

### Table: trade_ledger
```sql
CREATE TABLE trade_ledger (
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
    portfolio_manager_reasoning TEXT,  -- Full <think> block
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_trade_ledger_ticker ON trade_ledger(ticker);
CREATE INDEX idx_trade_ledger_timestamp ON trade_ledger(timestamp);
CREATE INDEX idx_trade_ledger_action ON trade_ledger(action);
```

**Purpose**: Complete audit trail of all trading decisions
**Retention**: All historical trades
**Usage**: 
- Performance tracking
- Pattern recognition
- Historical context for future decisions
- Backtesting

---

## AI Models Deep Dive

### 1. FinBERT (Sentiment Analysis)

**Architecture**:
```
Input Text → Tokenizer → BERT Encoder → Classification Head → Softmax → Output
```

**Specifications**:
- **Base Model**: BERT-base-uncased
- **Training Data**: Financial news and reports
- **Classes**: 3 (positive, negative, neutral)
- **Parameters**: ~110M
- **Input**: Max 512 tokens
- **Output**: Probability distribution over 3 classes

**Loading Process**:
```python
model_path = "./model/finbert"
tokenizer = BertTokenizer.from_pretrained(model_path, local_files_only=True)
model = BertForSequenceClassification.from_pretrained(model_path, local_files_only=True)
model.eval()  # Set to evaluation mode
model.to("cpu")  # Run on CPU
```

**Inference**:
```python
inputs = tokenizer(headline, return_tensors="pt", truncation=True, max_length=512)
with torch.no_grad():
    outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
```

**Why CPU?**:
- Model is small enough (~440MB)
- Inference is fast (~50ms per headline)
- No GPU required for 10 stocks × 10 headlines = 100 inferences

---

### 2. Llama 3.2 (Technical Analysis)

**Architecture**: Transformer-based LLM (Meta)

**Specifications**:
- **Parameters**: ~3B
- **Context Window**: 128K tokens
- **Quantization**: 4-bit (via Ollama)
- **Size**: ~2GB on disk

**Usage in System**:
```python
prompt = f"""
Technical indicators for {ticker}:
- RSI: {rsi}
- MACD: {macd}
Provide 2-3 sentence analysis.
"""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama3.2", "prompt": prompt, "stream": False},
    timeout=60
)
```

**Why Llama 3.2?**:
- Fast inference (~10-20 seconds)
- Good at technical interpretation
- Smaller than DeepSeek-R1 (faster for simple tasks)
- Runs locally via Ollama

---

### 3. DeepSeek-R1:7b (Portfolio Manager)

**Architecture**: Reasoning-optimized LLM

**Specifications**:
- **Parameters**: ~7B
- **Context Window**: 32K tokens
- **Special Feature**: Chain of Thought reasoning with `<think>` tags
- **Quantization**: 4-bit (via Ollama)
- **Size**: ~4.7GB on disk

**Reasoning Process**:
```
Input Prompt
    ↓
<think>
  1. Analyze sentiment-technical alignment
  2. Identify risks and conflicts
  3. Evaluate market conditions
  4. Review historical patterns
  5. Justify decision
</think>
    ↓
DECISION: BUY
CONFIDENCE: HIGH
REASONING: Strong positive sentiment aligns with bullish RSI
```

**Why DeepSeek-R1?**:
- Explicit reasoning (transparent decision-making)
- Better at complex multi-signal analysis
- `<think>` tags provide audit trail
- Designed for logical reasoning tasks

**Timeout**: 180 seconds (3 minutes)
- Reasoning takes longer than simple generation
- Acceptable for final decision quality

---

## Execution Flow

### Command: `python main.py --ticker NVDA`

```
Step 1: Initialization (main.py)
├─ Load .env configuration
├─ Remove SSL environment variables
├─ Parse CLI arguments
└─ Create TradingWorkflow instance
    ├─ Initialize SentimentAnalyst (load FinBERT)
    ├─ Initialize TechnicalSpecialist (connect Ollama)
    ├─ Initialize PortfolioManager (connect Ollama)
    ├─ Initialize FinnhubClient (API key from .env)
    ├─ Initialize YFinanceClient
    └─ Initialize DatabaseManager (PostgreSQL connection)

Step 2: Data Ingestion (Node 1)
├─ Finnhub API Call
│  ├─ GET https://finnhub.io/api/v1/quote?symbol=NVDA
│  ├─ Response: {"c": 184.89, "d": -10.67, "dp": -5.46, ...}
│  └─ INSERT INTO market_quotes (...)
├─ yfinance News Fetch
│  ├─ stock = yf.Ticker("NVDA")
│  ├─ news = stock.news
│  └─ Extract 10 headlines
└─ yfinance Price History
   ├─ hist = stock.history(period="1mo")
   └─ Returns DataFrame with OHLCV data

Step 3: Sentiment Analysis (Node 2)
├─ For each headline:
│  ├─ Tokenize with BertTokenizer
│  ├─ Run FinBERT inference (CPU)
│  ├─ Get sentiment: positive/negative/neutral
│  ├─ Get confidence score
│  └─ INSERT INTO sentiment_scores (...)
└─ Aggregate results:
   ├─ Count positive/negative/neutral
   ├─ Calculate sentiment score: (pos - neg) / total
   └─ Return: {'avg_sentiment': 'positive', 'avg_score': 0.60, ...}

Step 4: Technical Analysis (Node 3)
├─ Compute RSI (pandas)
│  ├─ Calculate price changes
│  ├─ Separate gains and losses
│  ├─ Calculate 14-period averages
│  └─ RSI = 100 - (100 / (1 + RS))
├─ Compute MACD (pandas)
│  ├─ EMA(12) and EMA(26)
│  ├─ MACD = EMA(12) - EMA(26)
│  ├─ Signal = EMA(9) of MACD
│  └─ Histogram = MACD - Signal
└─ Llama 3.2 Analysis
   ├─ Build prompt with indicators
   ├─ POST to Ollama API
   ├─ Wait for response (60s timeout)
   └─ Return: "RSI indicates neutral momentum..."

Step 5: Portfolio Manager Decision (Node 4)
├─ Fetch historical trades from database
│  └─ SELECT * FROM trade_ledger WHERE ticker='NVDA' LIMIT 5
├─ Build comprehensive prompt
│  ├─ Include sentiment data
│  ├─ Include technical data
│  ├─ Include market data
│  └─ Include historical context
├─ Call DeepSeek-R1:7b
│  ├─ POST to Ollama API
│  ├─ Wait for response (180s timeout)
│  └─ Response includes <think> reasoning
├─ Parse response
│  ├─ Extract <think> block
│  ├─ Extract DECISION: BUY/SELL/HOLD
│  ├─ Extract CONFIDENCE: HIGH/MEDIUM/LOW
│  └─ Extract REASONING: "..."
└─ Store in database
   └─ INSERT INTO trade_ledger (
       ticker, action, price, reasoning,
       sentiment_avg, rsi, macd, approved,
       portfolio_manager_reasoning
   )

Step 6: Display Results (Rich Dashboard)
├─ Create summary table
│  ├─ Ticker | Price | Change | Sentiment | RSI | Decision | Confidence
│  └─ Color-code: green (positive), red (negative)
└─ Create detailed panels
   ├─ Decision and confidence
   ├─ Sentiment breakdown
   ├─ Technical indicators
   └─ Analysis text

Total Execution Time: ~2-3 minutes per stock
├─ Data Ingestion: ~5 seconds
├─ Sentiment Analysis: ~10 seconds (FinBERT on CPU)
├─ Technical Analysis: ~20 seconds (Llama 3.2)
└─ Portfolio Manager: ~90-120 seconds (DeepSeek-R1 reasoning)
```

---

## Key Design Decisions

### 1. Why Local Models?
- **No API costs**: All inference runs locally
- **Privacy**: No data sent to external services
- **Control**: Full control over model versions
- **Reliability**: No dependency on external API uptime

### 2. Why PostgreSQL?
- **ACID compliance**: Reliable data storage
- **Indexing**: Fast queries on historical data
- **Relationships**: Easy to join tables for analysis
- **Mature**: Well-tested, production-ready

### 3. Why LangGraph?
- **State management**: Clean state passing between nodes
- **Error handling**: Graceful degradation
- **Modularity**: Easy to add/remove nodes
- **Visualization**: Can visualize workflow

### 4. Why Three Separate Models?
- **Specialization**: Each model optimized for its task
- **Speed**: Smaller models (Llama 3.2) for simple tasks
- **Quality**: Larger model (DeepSeek-R1) for complex reasoning
- **Transparency**: Clear separation of concerns

### 5. Why Chain of Thought?
- **Transparency**: See how decisions are made
- **Debugging**: Understand why model chose BUY/SELL/HOLD
- **Trust**: Users can verify reasoning
- **Audit**: Complete trail for compliance

---

## Performance Characteristics

### Throughput
- **Single Stock**: ~2-3 minutes
- **10 Stocks (Batch)**: ~20-30 minutes
- **Monitoring Mode**: Runs every 15 minutes

### Resource Usage
- **CPU**: 4-8 cores recommended
- **RAM**: 
  - FinBERT: ~2GB
  - Llama 3.2: ~4GB
  - DeepSeek-R1: ~8GB
  - Total: ~16GB recommended
- **Disk**: ~10GB (models + database)
- **Network**: Minimal (only API calls)

### Bottlenecks
1. **DeepSeek-R1 Inference**: 90-120 seconds per stock
2. **FinBERT on CPU**: ~10 seconds for 10 headlines
3. **API Rate Limits**: Finnhub 60 calls/minute

### Optimization Opportunities
1. **Parallel Processing**: Analyze multiple stocks simultaneously
2. **GPU Acceleration**: Speed up FinBERT (10x faster)
3. **Caching**: Cache news/prices for repeated analysis
4. **Batch Inference**: Process multiple headlines at once

---

## Error Handling

### Network Errors
- **Finnhub API**: Retry with exponential backoff
- **Ollama**: Timeout after 60s (Llama) or 180s (DeepSeek)
- **yfinance**: Graceful fallback if no news available

### Model Errors
- **FinBERT**: Skip headline if tokenization fails
- **Llama 3.2**: Return "unavailable" if timeout
- **DeepSeek-R1**: Default to HOLD if error

### Database Errors
- **Connection**: Retry with backoff
- **Constraint Violation**: Log and continue
- **Transaction**: Rollback on error

### State Management
- **Error Field**: Each node can set state['error']
- **Early Exit**: Subsequent nodes skip if error present
- **Logging**: All errors logged to console

---

## Security Considerations

### API Keys
- Stored in `.env` file (not committed)
- Loaded via python-dotenv
- Never logged or displayed

### Database
- Parameterized queries (no SQL injection)
- Connection pooling
- Credentials in environment variables

### SSL/TLS
- Disabled for local Ollama (localhost only)
- Enabled for external APIs (Finnhub)
- Certificate verification bypassed for PostgreSQL issue

### Data Privacy
- All processing local (no external model APIs)
- Database on localhost
- No PII collected

---

## Monitoring and Observability

### Logging
- **Console Output**: Real-time progress
- **LLM Calls**: Logged with timestamps
- **Errors**: Full stack traces
- **Decisions**: Complete reasoning logged

### Metrics
- **Execution Time**: Per node and total
- **API Calls**: Count and latency
- **Model Inference**: Time per model
- **Database Operations**: Query time

### Debugging
- **Verbose Mode**: Print LLM prompts and responses
- **State Inspection**: View state at each node
- **Database Queries**: Inspect stored data
- **Error Messages**: Detailed error context

---

## Future Enhancements

### Short Term
1. Add volume analysis
2. Multi-timeframe indicators
3. Sentiment trend (7-day average)
4. Risk management rules

### Medium Term
1. Backtesting framework
2. Portfolio-level decisions
3. Confidence-based position sizing
4. Alert system

### Long Term
1. GPU acceleration
2. Real-time streaming
3. Web dashboard
4. Multi-asset support (crypto, forex)

---

## Conclusion

This system demonstrates a production-ready AI trading pipeline with:
- ✅ Transparent reasoning (Chain of Thought)
- ✅ Multi-signal analysis (sentiment + technical + market)
- ✅ Complete audit trail (PostgreSQL)
- ✅ Local execution (no API costs)
- ✅ Modular design (easy to extend)

The architecture balances simplicity with functionality, making it suitable for educational purposes while maintaining production-ready standards.

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-27  
**Author**: Trading Agents System
