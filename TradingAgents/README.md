# Trading Agents - Minimalist AI Trading System

A production-ready AI trading system using local models and PostgreSQL for analyzing 10 tech stocks.

## Features

- **Local Models**: FinBERT, Llama 3.2, DeepSeek-R1 (no API costs)
- **PostgreSQL**: Persistent storage for quotes, sentiment, and trades
- **Real-time Data**: Finnhub API + yfinance
- **Rich Dashboard**: Terminal UI with monitoring mode
- **10 Stocks**: AAPL, MSFT, NVDA, TSLA, GOOGL, AMZN, META, NFLX, AMD, INTC

## Architecture

```
Data Ingestion → Sentiment (FinBERT) → Technical (Llama 3.2) → Portfolio Manager (DeepSeek-R1)
```

## 🚀 Quick Start

**📖 For detailed step-by-step instructions, see [START_HERE.md](START_HERE.md)**

### Prerequisites ✓

- Python 3.10+ ✓
- PostgreSQL
- Ollama
- Dependencies installed ✓

### Installation Steps

```bash
# 1. Install Ollama models
ollama pull llama3.2
ollama pull deepseek-r1

# 2. Download FinBERT to ./model/finbert/
# https://huggingface.co/ProsusAI/finbert

# 3. Configure .env with your FINNHUB_API_KEY

# 4. Create and initialize database
createdb trading_agents
python main.py --init-db

# 5. Run!
python main.py
```

### Usage

```bash
# Analyze all 10 stocks
python main.py

# Analyze specific stock
python main.py --ticker NVDA

# Monitoring mode (runs every 15 minutes)
python main.py --monitor
```

## Configuration

Edit `config.py` to customize:
- Stock list
- Monitoring interval
- Model paths
- Database settings

## Database Schema

- **market_quotes**: Real-time quotes from Finnhub
- **sentiment_scores**: FinBERT sentiment analysis
- **trade_ledger**: All decisions with reasoning

## Project Structure

```
├── agents/                    # AI agents
│   ├── sentiment_analyst.py  # FinBERT sentiment
│   ├── technical_specialist.py # Llama 3.2 technical
│   └── portfolio_manager.py  # DeepSeek-R1 decisions
├── data/                      # Data clients
│   ├── finnhub_client.py     # Finnhub API
│   └── yfinance_client.py    # yfinance wrapper
├── database/                  # PostgreSQL
│   ├── schema.sql            # Database schema
│   └── db_manager.py         # DB operations
├── graph/                     # LangGraph workflow
│   └── trading_workflow.py   # Pipeline
├── cli/                       # Dashboard
│   └── dashboard.py          # Rich UI
├── model/finbert/            # Local FinBERT model
├── config.py                 # Configuration
└── main.py                   # Entry point
```

## License

MIT License - Educational use only. Not financial advice.
