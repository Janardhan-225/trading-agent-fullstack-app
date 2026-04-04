from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter()

@router.get("/wallet")
def get_wallet(db: Session = Depends(get_db)):
    wallet = db.query(models.PortfolioWallet).first()
    if not wallet:
        wallet = models.PortfolioWallet(balance=10000.0)
        db.add(wallet)
        db.commit()
    return {"balance": wallet.balance}

@router.post("/wallet/deposit")
def update_wallet(amount: float, db: Session = Depends(get_db)):
    wallet = db.query(models.PortfolioWallet).first()
    if not wallet:
        wallet = models.PortfolioWallet(balance=10000.0)
        db.add(wallet)
        db.commit()
    
    if amount < 0:
        # User is withdrawing
        withdraw_amt = abs(amount)
        if withdraw_amt > wallet.balance:
            # LIQUIDATION LOGIC REQUIRED
            deficit = withdraw_amt - wallet.balance
            assets = db.query(models.Asset).filter(models.Asset.quantity > 0).all()
            
            # Very simple liquidation: sell off assets until deficit is met, starting from largest holdings.
            # (In production, Deepseek would run a LangGraph emergency sale here)
            assets_sorted = sorted(assets, key=lambda a: a.quantity * a.average_price, reverse=True)
            for asset in assets_sorted:
                if deficit <= 0: break
                asset_value = asset.quantity * asset.average_price
                if asset_value <= deficit:
                    # Sell full asset
                    db.add(models.TransactionOverview(symbol=asset.symbol, transaction_type="SELL", quantity=asset.quantity, price=asset.average_price, reasoning=f"Auto-Liquidation for withdrawal of ${withdraw_amt}"))
                    wallet.balance += asset_value
                    deficit -= asset_value
                    asset.quantity = 0
                else:
                    # Sell partial asset
                    qty_to_sell = deficit / asset.average_price
                    db.add(models.TransactionOverview(symbol=asset.symbol, transaction_type="SELL", quantity=qty_to_sell, price=asset.average_price, reasoning=f"Partial Auto-Liquidation for withdrawal"))
                    wallet.balance += deficit
                    asset.quantity -= qty_to_sell
                    deficit = 0
                    
        if withdraw_amt <= wallet.balance:
            wallet.balance -= withdraw_amt
            db.add(models.TransactionOverview(symbol="USD", transaction_type="WITHDRAWAL", quantity=withdraw_amt, price=1.0, reasoning="User requested withdrawal"))
    else:
        wallet.balance += amount
        db.add(models.TransactionOverview(symbol="USD", transaction_type="DEPOSIT", quantity=amount, price=1.0, reasoning="User added funds"))
        
    db.commit()
    return {"status": "success", "balance": wallet.balance}

@router.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    txs = db.query(models.TransactionOverview).order_by(models.TransactionOverview.timestamp.desc()).limit(50).all()
    return txs

@router.get("/assets")
def get_assets(db: Session = Depends(get_db)):
    assets = db.query(models.Asset).all()
    return assets

@router.post("/strategic-invest")
async def strategic_invest(amount: float, db: Session = Depends(get_db)):
    from trading_engine.loop import process_portfolio_async
    plan = await process_portfolio_async(db, objective="INVEST", target_amount=amount)
    return {
        "status": "success", 
        "message": "Strategic invest deployed.",
        "executed_plan": plan
    }

@router.post("/strategic-withdraw")
async def strategic_withdraw(amount: float, db: Session = Depends(get_db)):
    from trading_engine.loop import process_portfolio_async
    plan = await process_portfolio_async(db, objective="WITHDRAW", target_amount=amount)
    return {
        "status": "success", 
        "message": "Strategic withdraw deployed.",
        "executed_plan": plan
    }

@router.get("/tracked-stocks")
def get_tracked_stocks(db: Session = Depends(get_db)):
    stocks = db.query(models.TrackedStock).all()
    return stocks

@router.post("/tracked-stocks")
def add_tracked_stock(symbol: str, db: Session = Depends(get_db)):
    symbol = symbol.upper()
    stock = db.query(models.TrackedStock).filter(models.TrackedStock.symbol == symbol).first()
    if not stock:
        stock = models.TrackedStock(symbol=symbol, is_active=True)
        db.add(stock)
        db.commit()
    return {"status": "success", "symbol": symbol}

import yfinance as yf

@router.get("/history/{symbol}")
def get_stock_history(symbol: str, range: str = "1mo"):
    # ranges: '1d', '5d', '1wk', '1mo', '3mo', '1y', '5y', 'max'
    # For weekly or older, yfinance handles interval automatically or we can enforce
    interval_map = {
        "1d": "5m",
        "1wk": "1h",
        "1mo": "1d",
        "1y": "1wk",
        "5y": "1mo"
    }
    interval = interval_map.get(range, "1d")
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=range, interval=interval)
        
        data = []
        for index, row in hist.iterrows():
            data.append({
                "time": str(index),
                "price": round(row['Close'], 2) if not import_math_isnan(row['Close']) else 0
            })
            
        return {"symbol": symbol, "range": range, "data": data}
    except Exception as e:
        return {"symbol": symbol, "range": range, "data": []}

def import_math_isnan(val):
    import math
    try:
        return math.isnan(val)
    except:
        return True

import requests
import os
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

@router.get("/predict/{symbol}")
def get_prediction(symbol: str):
    # Retrieve recent data to form prompt
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        latest_price = round(hist.iloc[-1]['Close'], 2) if len(hist) > 0 else 150.0
    except:
        latest_price = 150.0
        
    prompt = f"Analyze stock {symbol} currently at ${latest_price}. Predict the 1-month (next 20 trading days) trajectory mathematically. Provide ONLY a JSON array of 20 floats representing the forecasted daily prices. E.g. [151.2, 155.0, ...]"
    
    try:
        res = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": "llama3.2",
            "prompt": prompt,
            "format": "json",
            "stream": False
        }, timeout=15)
        
        import json
        prediction_arr = json.loads(res.json().get("response", "[]"))
        if not isinstance(prediction_arr, list) or len(prediction_arr) == 0:
            prediction_arr = [latest_price * (1 + (i * 0.005)) for i in range(1, 21)]
    except:
        prediction_arr = [latest_price * (1 + (i * 0.005)) for i in range(1, 21)]
        
    # Format to chart data points
    pred_data = [{"step": i+1, "predicted_price": round(p, 2)} for i, p in enumerate(prediction_arr)]
    return {"symbol": symbol, "current_price": latest_price, "predictions": pred_data}
