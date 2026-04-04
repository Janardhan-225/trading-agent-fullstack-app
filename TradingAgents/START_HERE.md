# 🚀 How to Start the Project

Follow these steps in order to get the Trading Agents system running.

## Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.10+ installed
- ✅ PostgreSQL installed and running
- ✅ Ollama installed
- ✅ Dependencies installed (`pip install -r requirements.txt` - DONE ✓)

---

## Step 1: Install Ollama Models

Open a terminal and run:

```bash
# Pull Llama 3.2 (for Technical Specialist)
ollama pull llama3.2

# Pull DeepSeek-R1 (for Portfolio Manager)
ollama pull deepseek-r1

# Verify models are installed
ollama list
```

You should see both models listed.

---

## Step 2: Download FinBERT Model

### Option A: Using Git LFS (Recommended)

```bash
# Install git-lfs if not already installed
# Windows: Download from https://git-lfs.github.com/
# Linux: sudo apt install git-lfs
# macOS: brew install git-lfs

# Initialize git-lfs
git lfs install

# Clone FinBERT model
git clone https://huggingface.co/ProsusAI/finbert model/finbert
```

### Option B: Manual Download

1. Go to: https://huggingface.co/ProsusAI/finbert
2. Download these files to `./model/finbert/`:
   - `config.json`
   - `pytorch_model.bin` (large file ~440MB)
   - `tokenizer_config.json`
   - `vocab.txt`
   - `special_tokens_map.json`

### Verify FinBERT Installation

```bash
# Check if files exist
ls model/finbert/

# Should show: config.json, pytorch_model.bin, vocab.txt, etc.
```

---

## Step 3: Get Finnhub API Key

1. Go to: https://finnhub.io
2. Sign up for a free account
3. Copy your API key from the dashboard
4. Keep it ready for the next step

---

## Step 4: Configure Environment Variables

Edit the `.env` file in the project root:

```bash
# Open .env file
notepad .env  # Windows
nano .env     # Linux/Mac
```

Add your credentials:

```env
# Finnhub API Key (REQUIRED)
FINNHUB_API_KEY=your_actual_api_key_here

# PostgreSQL Database (adjust if needed)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_agents
DB_USER=postgres
DB_PASSWORD=your_postgres_password

# Ollama (usually default is fine)
OLLAMA_BASE_URL=http://localhost:11434
```

**Important**: Replace `your_actual_api_key_here` with your real Finnhub API key!

---

## Step 5: Start PostgreSQL

Make sure PostgreSQL is running:

### Windows
```bash
# Check if running
pg_isready

# If not running, start it from Services or:
net start postgresql-x64-14
```

### Linux
```bash
sudo systemctl start postgresql
sudo systemctl status postgresql
```

### macOS
```bash
brew services start postgresql@14
```

---

## Step 6: Create Database

```bash
# Create the database
createdb trading_agents

# Or if you need to specify user:
createdb -U postgres trading_agents

# Verify database exists
psql -l | grep trading_agents
```

---

## Step 7: Start Ollama Service

Make sure Ollama is running:

```bash
# Start Ollama (if not already running)
ollama serve

# In another terminal, verify it's running:
curl http://localhost:11434/api/tags
```

Leave the Ollama service running in the background.

---

## Step 8: Initialize Database Schema

Run this command to create the database tables:

```bash
python main.py --init-db
```

Expected output:
```
Initializing database...
Database initialized successfully!
```

---

## Step 9: Verify Everything is Ready

Run this quick check:

```bash
python -c "
import config
from database.db_manager import DatabaseManager
from data.finnhub_client import FinnhubClient

print('✓ Config loaded')
print(f'✓ Stocks: {config.STOCKS}')
print('✓ Database manager imported')
print('✓ Finnhub client imported')
print('\nSystem ready!')
"
```

---

## Step 10: Run Your First Analysis

### Option A: Analyze All 10 Stocks

```bash
python main.py
```

This will analyze all 10 stocks: AAPL, MSFT, NVDA, TSLA, GOOGL, AMZN, META, NFLX, AMD, INTC

### Option B: Analyze Single Stock

```bash
python main.py --ticker NVDA
```

### Option C: Monitoring Mode (Continuous)

```bash
python main.py --monitor
```

This runs analysis every 15 minutes. Press `Ctrl+C` to stop.

---

## Expected Output

You should see:

1. **Summary Table**
   - Ticker, Price, Change, Sentiment, RSI, Decision, Confidence

2. **Detailed Panels** for each stock showing:
   - Portfolio Manager decision
   - Sentiment analysis breakdown
   - Technical indicators (RSI, MACD)
   - Llama 3.2 technical analysis

---

## Troubleshooting

### "Connection refused" (Ollama)
```bash
# Start Ollama service
ollama serve
```

### "Database does not exist"
```bash
createdb trading_agents
python main.py --init-db
```

### "FinBERT model not found"
```bash
# Check if model files exist
ls model/finbert/
# Should see: config.json, pytorch_model.bin, vocab.txt
```

### "Finnhub API error"
```bash
# Verify API key in .env
cat .env | grep FINNHUB

# Test API key
curl "https://finnhub.io/api/v1/quote?symbol=AAPL&token=YOUR_KEY"
```

### "Module not found"
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Verify packages installed
pip list | grep -E "torch|transformers|langgraph"
```

---

## Quick Start Checklist

- [ ] Ollama models installed (`ollama list`)
- [ ] FinBERT downloaded to `./model/finbert/`
- [ ] `.env` file configured with API key
- [ ] PostgreSQL running
- [ ] Database created (`createdb trading_agents`)
- [ ] Ollama service running (`ollama serve`)
- [ ] Database initialized (`python main.py --init-db`)
- [ ] Run first analysis (`python main.py`)

---

## What Happens When You Run

1. **Data Ingestion**: Fetches real-time quotes from Finnhub and news from yfinance
2. **Sentiment Analysis**: FinBERT analyzes news headlines
3. **Technical Analysis**: Computes RSI/MACD, Llama 3.2 provides analysis
4. **Portfolio Manager**: DeepSeek-R1 makes final decision with reasoning
5. **Storage**: All data saved to PostgreSQL
6. **Display**: Rich dashboard shows results

---

## Next Steps After First Run

1. **Query Database**:
   ```bash
   psql -d trading_agents
   SELECT * FROM trade_ledger ORDER BY timestamp DESC LIMIT 5;
   ```

2. **Customize Configuration**:
   - Edit `config.py` to change stock list
   - Adjust monitoring interval
   - Modify model settings

3. **Explore Data**:
   - Check sentiment scores
   - Review Portfolio Manager reasoning
   - Analyze trading patterns

---

## Need Help?

- Check `TROUBLESHOOTING.md` for common issues
- Review `PROJECT.md` for system overview
- Read `README.md` for quick reference

---

**Ready to start? Run:**

```bash
python main.py
```

🎉 Happy Trading!
