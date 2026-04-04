# Troubleshooting Guide

## Common Issues

### "Module not found" Error

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Connection refused" (Ollama)

**Solution:**
```bash
# Start Ollama
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```

### "Database does not exist"

**Solution:**
```bash
# Create database
createdb trading_agents

# Initialize schema
python main.py --init-db
```

### "FinBERT model not found"

**Solution:**
```bash
# Verify model directory exists
ls -la model/finbert/

# Should contain: config.json, pytorch_model.bin, vocab.txt
# Download from: https://huggingface.co/ProsusAI/finbert
```

### "Finnhub API error"

**Solution:**
```bash
# Check .env file
cat .env | grep FINNHUB

# Test API key
curl "https://finnhub.io/api/v1/quote?symbol=AAPL&token=YOUR_KEY"
```

### "Out of memory"

**Solution:**
- Close other applications
- FinBERT uses ~2GB RAM
- Ollama models use ~4GB RAM
- Minimum 8GB RAM recommended

### PostgreSQL Authentication Failed

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list                # macOS

# Update .env with correct credentials
```

## Verification Commands

```bash
# Check Python version
python --version

# Check PostgreSQL
psql --version

# Check Ollama
ollama list

# Test imports
python -c "from graph.trading_workflow import TradingWorkflow; print('OK')"

# Check database tables
psql -d trading_agents -c "\dt"
```

## Getting Help

1. Check error message carefully
2. Verify all prerequisites installed
3. Ensure virtual environment activated
4. Check .env file configuration
5. Verify database is running
6. Confirm Ollama is running
7. Check model files exist
