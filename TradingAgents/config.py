"""Configuration for the minimalist trading agents system."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Asset Universe - 10 stocks only
STOCKS = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL', 'AMZN', 'META', 'NFLX', 'AMD', 'INTC']

# Model Paths
MODEL_DIR = Path("./model")
FINBERT_PATH = MODEL_DIR / "finbert"

# Database Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "trading_agents"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# API Configuration
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
SPECIALIST_MODEL = "llama3.2"
PORTFOLIO_MANAGER_MODEL = "deepseek-r1:7b"  # Full model tag required

# Monitoring Configuration
MONITOR_INTERVAL_MINUTES = 15
