import requests
import json
import os
import asyncio
from typing import TypedDict, Annotated, Literal, List, Dict
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

load_dotenv()
FINNHUB_KEY = os.getenv("FINNHUB_API_KEY", "d6psvfpr01qk0cf1ql00d6psvfpr01qk0cf1ql0g")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

class PortfolioState(TypedDict):
    wallet_balance: float
    tracked_symbols: List[str]
    assets: Dict[str, float]
    market_data: Dict[str, dict]
    sentiment_data: Dict[str, dict]
    llama_ta: Dict[str, dict]
    deepseek_plan: List[dict]
    execution_status: str
    objective: str
    objective_amount: float

async def fetch_finnhub_quote(smb: str):
    url = f"https://finnhub.io/api/v1/quote?symbol={smb}&token={FINNHUB_KEY}"
    try:
        res = await asyncio.to_thread(requests.get, url, timeout=10)
        d = res.json()
        return smb, {"price": d.get("c", 0.0), "high": d.get("h", 0.0), "low": d.get("l", 0.0), "open": d.get("o", 0.0), "pc": d.get("pc", 0.0)}
    except:
        return smb, {"price": 0.0, "high": 0.0, "low": 0.0, "open": 0.0, "pc": 0.0}

async def single_llama_eval_swarm(market_data_dict: dict):
    symbols_text = "\n".join([f"- {s}: Price=${d['price']}, Open=${d['open']}, High=${d['high']}, Low=${d['low']}, PrevClose=${d['pc']}, RSI={d['rsi']}, MACD={d['macd']}." for s, d in market_data_dict.items()])
    prompt = f"""Evaluate strictly Technical Indicators locally for these stocks:
{symbols_text}
Output EXACTLY this JSON structure mapping symbols to Technical metrics only.
Format required:
{{
  "AAPL": {{"trend": "bullish|bearish|neutral", "rsi": 60, "macd_signal": "positive|negative"}}
}}"""
    try:
        res = await asyncio.to_thread(requests.post, f"{OLLAMA_URL}/api/generate", json={"model": "llama3.2", "prompt": prompt, "format": "json", "stream": False}, timeout=60)
        return json.loads(res.json().get("response", "{}"))
    except: return {}

# --- Async Nodes ---
async def fetch_market_data(state: PortfolioState) -> PortfolioState:
    state["market_data"] = {}
    tasks = [fetch_finnhub_quote(smb) for smb in state["tracked_symbols"]]
    results = await asyncio.gather(*tasks)
    
    # Pre-generate real technical data concurrently
    import yfinance as yf
    import pandas as pd
    
    def calculate_technical_data():
        metrics = {}
        if not state["tracked_symbols"]: return metrics
        try:
            df = yf.download(state["tracked_symbols"], period="3mo", group_by="ticker", threads=True, progress=False)
            for smb in state["tracked_symbols"]:
                metrics[smb] = {"rsi": 50.0, "macd": 0.0} # Defaults
                try:
                    s_data = df[smb] if len(state["tracked_symbols"]) > 1 else df
                    close = s_data['Close'].squeeze()
                    if close.empty: continue
                    
                    # RSI (14)
                    delta = close.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    
                    # MACD (12, 26)
                    ema12 = close.ewm(span=12, adjust=False).mean()
                    ema26 = close.ewm(span=26, adjust=False).mean()
                    macd = ema12 - ema26
                    
                    metrics[smb]["rsi"] = round(float(rsi.iloc[-1]), 2)
                    metrics[smb]["macd"] = round(float(macd.iloc[-1]), 4)
                    metrics[smb]["yf_price"] = round(float(close.iloc[-1]), 2)
                except Exception:
                    pass
        except Exception:
            pass
        return metrics

    real_technicals = await asyncio.to_thread(calculate_technical_data)

    for smb, quote in results:
        t = real_technicals.get(smb, {"rsi": 50.0, "macd": 0.0, "yf_price": 0.0})
        # If Finnhub failed (0.0) but yfinance succeeded, map the YF price instead of destroying logic!
        true_price = quote["price"] if quote["price"] > 0.0 else t.get("yf_price", 0.0)
        
        state["market_data"][smb] = {
            "price": true_price,
            "high": quote["high"] if quote["high"] > 0.0 else true_price,
            "low": quote["low"] if quote["low"] > 0.0 else true_price,
            "open": quote["open"] if quote["open"] > 0.0 else true_price,
            "pc": quote["pc"] if quote["pc"] > 0.0 else true_price,
            "rsi": t["rsi"], 
            "macd": t["macd"]
        }
    return state

async def analyze_sentiment_node(state: PortfolioState) -> PortfolioState:
    from trading_engine.sentiment import SentimentAnalyst
    analyst = SentimentAnalyst.get_instance()
    
    state["sentiment_data"] = {}
    tasks = [analyst.analyze_news_async(smb, limit=5) for smb in state["tracked_symbols"]]
    results = await asyncio.gather(*tasks)
    
    for res in results:
        state["sentiment_data"][res['ticker']] = res
    return state

async def analyze_with_llama_swarm(state: PortfolioState) -> PortfolioState:
    llama_metrics = await single_llama_eval_swarm(state["market_data"])
    state["llama_ta"] = {}
    for smb in state["tracked_symbols"]:
        if smb in llama_metrics:
            state["llama_ta"][smb] = llama_metrics[smb]
        else:
            state["llama_ta"][smb] = {"trend": "neutral", "rsi": 50, "macd_signal": "unknown"}
    return state

async def reason_with_deepseek(state: PortfolioState) -> PortfolioState:
    # Compile the MASSIVE SINGLE GLOBAL REPORT requested by the user
    port_context = f"Wallet: ${state['wallet_balance']:.2f}. Open Positions: {state['assets']}."
    
    global_report = "GLOBAL PORTFOLIO REPORT:\n\n"
    for smb in state["tracked_symbols"]:
        price = state["market_data"][smb]["price"]
        high = state["market_data"][smb]["high"]
        low = state["market_data"][smb]["low"]
        op = state["market_data"][smb]["open"]
        pc = state["market_data"][smb]["pc"]
        
        tec = state["llama_ta"].get(smb, {})
        sen = state["sentiment_data"].get(smb, {})
        
        global_report += f"[{smb}] - Price: ${price:.2f} (H/L: ${high:.2f}/${low:.2f}) (O: ${op:.2f}, PC: ${pc:.2f})\n"
        global_report += f"  - FinBERT Sentiment: {sen.get('avg_sentiment', 'neutral').upper()} (Score: {sen.get('avg_score', 0):.2f}) based on {sen.get('total_headlines', 0)} headlines. Pos: {sen.get('positive_ratio',0):.1%} Neg: {sen.get('negative_ratio',0):.1%}\n"
        global_report += f"  - Technicals (Llama3.2 Specialist): Trend={tec.get('trend', 'neutral')}, RSI={tec.get('rsi', 50)}\n\n"
        
    objective_directive = "Distribute capital strategically across the entire active spectrum to hedge risks while catching momentum."
    override_val = state.get("objective_amount", 0.0)
    
    if state.get("objective") == "INVEST":
        objective_directive = f"CRITICAL OVERRIDE: You must strategically BUY ${override_val} worth of the most undervalued & highly positively-sentimental stocks listed. Distribute percentages matching this EXACT dollar target."
    elif state.get("objective") == "WITHDRAW":
        objective_directive = f"CRITICAL OVERRIDE: You must strategically SELL exactly ${override_val} worth of current holdings, picking the most optimal (maybe negative sentiment or overbought) positions to liquidate."
        
    prompt = f"""You are the Master Portfolio Manager Agent using Deepseek-R1. 
{objective_directive}

{global_report}
Your Current Context: {port_context}

Output ONLY a valid JSON array of objects representing final actions. DO NOT output any conversational text.
Format required: [{{"symbol": "MSFT", "action": "BUY", "percentage": 10, "reasoning": "<Short strict justification against FinBERT/Technicals>"}}]
The percentage is 0-100 indicating how much of available wallet (if BUY) or held stock (if SELL) to allocate to this specific move."""

    try:
        res = await asyncio.to_thread(requests.post, f"{OLLAMA_URL}/api/generate", json={"model": "deepseek-r1:7b", "prompt": prompt, "stream": False}, timeout=300)
        response_text = res.json().get("response", "[]")
        
        import re
        clean_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
        
        array_match = re.search(r'\[.*\]', clean_text, flags=re.DOTALL)
        if array_match:
            data = json.loads(array_match.group(0))
        else:
            dict_match = re.search(r'\{.*\}', clean_text, flags=re.DOTALL)
            if dict_match:
                data = json.loads(dict_match.group(0)).get("actions", [])
            else:
                data = []

        if isinstance(data, list):
            state["deepseek_plan"] = data
        else:
            state["deepseek_plan"] = []
    except Exception as e:
        print("Deepseek Exception:", e)
        state["deepseek_plan"] = []
        
    state["execution_status"] = "PROCEED"
    return state

async def execute_trade(state: PortfolioState) -> PortfolioState:
    state["execution_status"] = "PROCEED"
    return state

def should_execute(state: PortfolioState) -> Literal["execute_trade", "__end__"]:
    if len(state["deepseek_plan"]) > 0:
        return "execute_trade"
    return "__end__"

# Compile LangGraph
workflow = StateGraph(PortfolioState)
workflow.add_node("fetch_market", fetch_market_data)
workflow.add_node("sentiment_node", analyze_sentiment_node)
workflow.add_node("analyze_llama", analyze_with_llama_swarm)
workflow.add_node("reason_deepseek", reason_with_deepseek)
workflow.add_node("execute_trade", execute_trade)

workflow.add_edge(START, "fetch_market")
workflow.add_edge("fetch_market", "sentiment_node")
workflow.add_edge("sentiment_node", "analyze_llama")
workflow.add_edge("analyze_llama", "reason_deepseek")
workflow.add_conditional_edges("reason_deepseek", should_execute)
workflow.add_edge("execute_trade", END)

app = workflow.compile()

async def process_portfolio_async(db: Session, objective: str = "", target_amount: float = 0.0):
    wallet = db.query(models.PortfolioWallet).first()
    if not wallet: return
    tracked = db.query(models.TrackedStock).filter(models.TrackedStock.is_active == True).all()
    if not tracked: return
    symbols = [t.symbol.upper() for t in tracked]
    assets = db.query(models.Asset).all()
    asset_map = {a.symbol.upper(): a.quantity for a in assets}
    
    initial_state = PortfolioState(
        wallet_balance=wallet.balance, tracked_symbols=symbols, assets=asset_map,
        market_data={}, sentiment_data={}, llama_ta={}, deepseek_plan=[], execution_status="",
        objective=objective, objective_amount=target_amount
    )
    
    final_state = await app.ainvoke(initial_state)
    
    if final_state.get("execution_status") == "PROCEED":
        total_buy_pct = sum(float(d.get("percentage", 0)) for d in final_state.get("deepseek_plan", []) if str(d.get("action", "")).upper() == "BUY")
        total_sell_pct = sum(float(d.get("percentage", 0)) for d in final_state.get("deepseek_plan", []) if str(d.get("action", "")).upper() == "SELL")

        for decision in final_state["deepseek_plan"]:
            action = str(decision.get("action", "HOLD")).upper()
            percentage = float(decision.get("percentage", 0))
            symbol = str(decision.get("symbol", "")).upper()
            reasoning = str(decision.get("reasoning", ""))
            
            if symbol not in symbols or percentage <= 0 or action not in ["BUY", "SELL"]:
                continue
                
            execute_price = final_state["market_data"].get(symbol, {}).get("price", 150.0)
            asset = db.query(models.Asset).filter(models.Asset.symbol == symbol).first()
            
            quantity_to_trade = 0.0
            
            if action == "BUY":
                if objective == "INVEST" and target_amount > 0:
                    cash_to_spend = target_amount * (percentage / total_buy_pct) if total_buy_pct > 0 else 0.0
                else:
                    cash_to_spend = wallet.balance * (percentage / 100.0)
                
                # Check absolute sanity limit
                if cash_to_spend > wallet.balance:
                    cash_to_spend = wallet.balance

                quantity_to_trade = cash_to_spend / execute_price if execute_price > 0 else 0
                if quantity_to_trade > 0:
                    wallet.balance -= cash_to_spend
                    if not asset:
                        asset = models.Asset(symbol=symbol, quantity=0, average_price=0)
                        db.add(asset)
                    total_value = (asset.quantity * asset.average_price) + cash_to_spend
                    asset.quantity += quantity_to_trade
                    asset.average_price = total_value / asset.quantity

            elif action == "SELL" and asset and asset.quantity > 0:
                if objective == "WITHDRAW" and target_amount > 0:
                    cash_to_gain = target_amount * (percentage / total_sell_pct) if total_sell_pct > 0 else 0.0
                    quantity_to_trade = cash_to_gain / execute_price if execute_price > 0 else 0
                    if quantity_to_trade > asset.quantity:
                        quantity_to_trade = asset.quantity
                else:
                    quantity_to_trade = asset.quantity * (percentage / 100.0)
                
                cash_gained = quantity_to_trade * execute_price
                asset.quantity -= quantity_to_trade
                wallet.balance += cash_gained
                if asset.quantity <= 0.001: asset.quantity = 0

            if quantity_to_trade > 0:
                tx = models.TransactionOverview(symbol=symbol, transaction_type=action, quantity=quantity_to_trade, price=execute_price, reasoning=reasoning)
                db.add(tx)
                log = models.SystemLogs(level="INFO", message=f"Full FinBERT + LLaMA + DeepSeek Swarm Executed {action} on {symbol} at ${execute_price:.2f}.")
                db.add(log)
        db.commit()
    return final_state.get("deepseek_plan", [])

def run_trading_cycle():
    db = SessionLocal()
    try:
        asyncio.run(process_portfolio_async(db))
    finally:
        db.close()
