"""LangGraph workflow: News Sensing -> Data Ingestion -> Sentiment -> Technical -> Portfolio Manager."""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, List, Optional
from agents.sentiment_analyst import SentimentAnalyst
from agents.technical_specialist import TechnicalSpecialist
from agents.portfolio_manager import PortfolioManager
from data.finnhub_client import FinnhubClient
from data.yfinance_client import YFinanceClient
from data.news_engine import SentinelNewsEngine
from database.db_manager import DatabaseManager
import config


class TradingState(TypedDict):
    """State for the trading workflow."""
    ticker: str
    market_data: Dict
    price_history: Dict
    headlines: List[str]
    sentiment_data: Dict
    technical_data: Dict
    news_alert: Optional[Dict]
    decision: Dict
    error: str


class TradingWorkflow:
    """Trading workflow using LangGraph."""

    def __init__(self):
        # Load FinBERT once via NewsEngine, share with SentimentAnalyst for fallback scoring
        self.news_engine = SentinelNewsEngine()
        self.sentiment_analyst = SentimentAnalyst(
            model=self.news_engine.model,
            tokenizer=self.news_engine.tokenizer
        )
        self.technical_specialist = TechnicalSpecialist()
        self.portfolio_manager = PortfolioManager()
        self.finnhub = FinnhubClient()
        self.yfinance = YFinanceClient()
        self.db = DatabaseManager()
        self.graph = self._build_graph()
        print("[Workflow] Initialized — FinBERT loaded once, shared across NewsEngine + SentimentAnalyst")

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(TradingState)
        workflow.add_node("news_sensing", self.news_sensing_node)
        workflow.add_node("data_ingestion", self.data_ingestion_node)
        workflow.add_node("sentiment_analysis", self.sentiment_analysis_node)
        workflow.add_node("technical_analysis", self.technical_analysis_node)
        workflow.add_node("portfolio_manager", self.portfolio_manager_node)
        workflow.set_entry_point("news_sensing")
        workflow.add_edge("news_sensing", "data_ingestion")
        workflow.add_edge("data_ingestion", "sentiment_analysis")
        workflow.add_edge("sentiment_analysis", "technical_analysis")
        workflow.add_edge("technical_analysis", "portfolio_manager")
        workflow.add_edge("portfolio_manager", END)
        return workflow.compile()

    def news_sensing_node(self, state: TradingState) -> TradingState:
        """Node 0: Sentinel News Engine — ingest, deduplicate, score headlines."""
        ticker = state['ticker']
        try:
            results = self.news_engine.run(tickers=[ticker])
            news_result = results.get(ticker, {})
            state['news_alert'] = news_result
            score = news_result.get('score', 0.0)
            count = news_result.get('articles_count', 0)
            direction = news_result.get('direction', 'neutral').upper()
            print(f"  [NewsEngine] {ticker}: score={score:.3f} ({direction}), articles={count}")
            if news_result.get('alert'):
                print(f"\n[Workflow] *** NEWS ALERT for {ticker}: {direction} score={score:.3f} → waking DeepSeek-R1 ***")
        except Exception as e:
            print(f"  [NewsEngine] Warning: {e}")
            state['news_alert'] = {}
        return state

    def data_ingestion_node(self, state: TradingState) -> TradingState:
        """Node 1: Fetch real-time market data and price history."""
        ticker = state['ticker']
        try:
            market_data = self.finnhub.get_quote(ticker)
            if not market_data:
                state['error'] = f"Failed to fetch market data for {ticker}"
                return state
            price_history = self.yfinance.get_price_history(ticker, period="1mo")
            state['market_data'] = market_data
            state['price_history'] = price_history
        except Exception as e:
            state['error'] = f"Data ingestion error: {str(e)}"
        return state

    def sentiment_analysis_node(self, state: TradingState) -> TradingState:
        """Node 2: Build sentiment_data from Sentinel News Engine scores (no re-scoring)."""
        if state.get('error'):
            return state
        try:
            ticker = state['ticker']
            news_result = state.get('news_alert') or {}

            if news_result.get('articles_count', 0) > 0:
                # Use pre-scored results from the news engine — no FinBERT re-run
                sentiment_data = self.sentiment_analyst.from_news_engine(ticker, news_result)
                print(f"  [Sentiment] {ticker}: {sentiment_data['avg_sentiment']} "
                      f"(score={sentiment_data['avg_score']:.3f}, "
                      f"from {sentiment_data['total_headlines']} articles via NewsEngine)")
            else:
                # Fallback: fetch headlines and score with FinBERT directly
                print(f"  [Sentiment] No news engine data for {ticker}, falling back to direct FinBERT scoring...")
                headlines = self.yfinance.get_news(ticker, limit=10)
                sentiment_data = self.sentiment_analyst.analyze_news(ticker, headlines)

            state['sentiment_data'] = sentiment_data
        except Exception as e:
            state['error'] = f"Sentiment analysis error: {str(e)}"
        return state

    def technical_analysis_node(self, state: TradingState) -> TradingState:
        """Node 3: Compute technical indicators using Llama 3.2."""
        if state.get('error'):
            return state
        try:
            ticker = state['ticker']
            market_data = state['market_data']
            price_history = state['price_history']
            if price_history is None or price_history.empty:
                state['error'] = "No price history available for technical analysis"
                return state
            technical_data = self.technical_specialist.analyze(ticker, market_data, price_history)
            state['technical_data'] = technical_data
        except Exception as e:
            state['error'] = f"Technical analysis error: {str(e)}"
        return state

    def portfolio_manager_node(self, state: TradingState) -> TradingState:
        """Node 4: Final decision using DeepSeek-R1 with all context."""
        if state.get('error'):
            return state
        try:
            ticker = state['ticker']
            sentiment_data = state['sentiment_data']
            technical_data = state['technical_data']
            market_data = state['market_data']
            news_alert = state.get('news_alert', {})
            historical_trades = self.db.get_recent_trades(ticker=ticker, limit=5)

            decision = self.portfolio_manager.make_decision(
                ticker, sentiment_data, technical_data, market_data,
                historical_trades, news_alert=news_alert
            )

            self.db.insert_trade(
                ticker=ticker,
                action=decision['decision'],
                price=market_data['current_price'],
                quantity=0,
                reasoning=decision['reasoning'],
                sentiment_avg=sentiment_data['avg_score'],
                rsi=technical_data['indicators']['rsi'],
                macd=technical_data['indicators']['macd']['macd'],
                approved=decision['approved'],
                portfolio_manager_reasoning=decision['thinking_process']
            )
            state['decision'] = decision
        except Exception as e:
            state['error'] = f"Portfolio manager error: {str(e)}"
        return state

    def run(self, ticker: str) -> Dict:
        """Execute the workflow for a single ticker."""
        initial_state = TradingState(
            ticker=ticker,
            market_data={},
            price_history=None,
            headlines=[],
            sentiment_data={},
            technical_data={},
            news_alert={},
            decision={},
            error=""
        )
        return self.graph.invoke(initial_state)

    def run_batch(self, tickers: List[str] = None) -> Dict[str, Dict]:
        """Execute workflow for multiple tickers."""
        if tickers is None:
            tickers = config.STOCKS
        results = {}
        for ticker in tickers:
            print(f"\nProcessing {ticker}...")
            results[ticker] = self.run(ticker)
        return results
