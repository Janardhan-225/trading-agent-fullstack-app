# Trading Agents - Project Overview

## What This Is

A minimalist AI trading system that analyzes 10 tech stocks using local models and PostgreSQL.

## Key Components

### 1. Agents (3 AI agents)
- **Sentiment Analyst** - FinBERT analyzes news headlines
- **Technical Specialist** - Llama 3.2 computes RSI/MACD
- **Portfolio Manager** - DeepSeek-R1 makes final decisions with reasoning

### 2. Data Sources
- **Finnhub API** - Real-time market quotes
- **yfinance** - News headlines and historical prices

### 3. Database (PostgreSQL)
- **market_quotes** - Real-time quotes
- **sentiment_scores** - Sentiment analysis results
- **trade_ledger** - All decisions with reasoning

### 4. Workflow (LangGraph)
```
Data Ingestion → Sentiment Analysis → Technical Analysis → Portfolio Manager
```

## Stock Universe

10 tech stocks only:
- AAPL, MSFT, NVDA, TSLA, GOOGL
- AMZN, META, NFLX, AMD, INTC

## Models

All models run locally (no API costs):
- **FinBERT** - CPU-based sentiment analysis
- **Llama 3.2** - Via Ollama for technical analysis
- **DeepSeek-R1** - Via Ollama for decision making with Chain of Thought

## Usage Modes

1. **Single Stock**: `python main.py --ticker NVDA`
2. **Batch Analysis**: `python main.py`
3. **Monitoring**: `python main.py --monitor` (runs every 15 minutes)

## Output

Rich terminal dashboard showing:
- Summary table with all stocks
- Price changes (color-coded)
- Sentiment indicators
- RSI values
- Trading decisions (BUY/SELL/HOLD)
- Confidence levels
- Detailed analysis per stock

## Configuration

Edit `config.py` to customize:
- Stock list
- Monitoring interval (default: 15 minutes)
- Model paths
- Database settings
- Ollama URL

## Database Schema

### market_quotes
- ticker, current_price, change, percent_change
- high, low, open, previous_close
- timestamp

### sentiment_scores
- ticker, headline, sentiment, score
- timestamp

### trade_ledger
- ticker, action, price, quantity
- reasoning (short explanation)
- sentiment_avg, rsi, macd
- approved (boolean)
- portfolio_manager_reasoning (full Chain of Thought)
- timestamp

## File Structure

```
├── agents/                    # AI agents
├── data/                      # Data clients
├── database/                  # PostgreSQL
├── graph/                     # LangGraph workflow
├── cli/                       # Dashboard
├── model/finbert/            # FinBERT model (download separately)
├── config.py                 # Configuration
├── main.py                   # Entry point
└── requirements.txt          # Dependencies
```

## Requirements

- Python 3.10+
- PostgreSQL 12+
- Ollama (for Llama 3.2 and DeepSeek-R1)
- Finnhub API key (free tier)
- 8GB RAM minimum
- No GPU required

## Notes

- Educational project, not financial advice
- All models run locally on CPU
- Data stored in PostgreSQL for analysis
- Monitoring mode for continuous operation
- Complete audit trail of all decisions
