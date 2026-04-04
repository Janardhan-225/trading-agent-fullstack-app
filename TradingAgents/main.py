"""Main entry point for the trading agents system.

Setup:
1. Install dependencies: pip install -r requirements.txt
2. Pull Ollama models: ollama pull llama3.2 && ollama pull deepseek-r1
3. Download FinBERT to ./model/finbert/ from https://huggingface.co/ProsusAI/finbert
4. Create .env file with FINNHUB_API_KEY and DB credentials
5. Create database: createdb trading_agents
6. Initialize: python main.py --init-db

Usage:
- python main.py                    # Analyze all 10 stocks
- python main.py --ticker NVDA      # Analyze single stock
- python main.py --monitor          # Run every 15 minutes
"""
import argparse
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from graph.trading_workflow import TradingWorkflow
from cli.dashboard import TradingDashboard
from database.db_manager import DatabaseManager
import config

# Load environment variables
load_dotenv()

# Fix SSL certificate issue from PostgreSQL
os.environ.pop('REQUESTS_CA_BUNDLE', None)
os.environ.pop('CURL_CA_BUNDLE', None)
os.environ.pop('SSL_CERT_FILE', None)


def run_single_analysis(ticker: str = None):
    """Run analysis for a single ticker or all tickers."""
    workflow = TradingWorkflow()
    dashboard = TradingDashboard()
    
    if ticker:
        print(f"\nAnalyzing {ticker}...")
        result = workflow.run(ticker)
        results = {ticker: result}
    else:
        print(f"\nAnalyzing {len(config.STOCKS)} stocks...")
        results = workflow.run_batch(config.STOCKS)
    
    dashboard.display_results(results)


def run_monitoring():
    """Run continuous monitoring mode."""
    workflow = TradingWorkflow()
    dashboard = TradingDashboard()
    
    dashboard.display_monitoring_header(config.MONITOR_INTERVAL_MINUTES)
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running analysis...")
            results = workflow.run_batch(config.STOCKS)
            dashboard.display_results(results)
            
            print(f"\nNext run in {config.MONITOR_INTERVAL_MINUTES} minutes...")
            time.sleep(config.MONITOR_INTERVAL_MINUTES * 60)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")


def init_database():
    """Initialize database schema."""
    print("Initializing database...")
    db = DatabaseManager()
    db.initialize_schema()
    print("Database initialized successfully!")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Trading Agents - Minimalist AI Trading System")
    parser.add_argument('--ticker', type=str, help='Analyze a specific ticker')
    parser.add_argument('--monitor', action='store_true', help='Run in monitoring mode (every 15 minutes)')
    parser.add_argument('--init-db', action='store_true', help='Initialize database schema')
    
    args = parser.parse_args()
    
    if args.init_db:
        init_database()
    elif args.monitor:
        run_monitoring()
    elif args.ticker:
        if args.ticker.upper() not in config.STOCKS:
            print(f"Error: {args.ticker} is not in the allowed stock list.")
            print(f"Allowed stocks: {', '.join(config.STOCKS)}")
            return
        run_single_analysis(args.ticker.upper())
    else:
        run_single_analysis()


if __name__ == "__main__":
    main()
