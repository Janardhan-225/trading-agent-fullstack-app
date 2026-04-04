from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import os
from dotenv import load_dotenv

load_dotenv()
from database import engine, Base
from routers import portfolio, llm_chat, knowledge, news
import models

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Portfolio Management API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    from database import SessionLocal
    db = SessionLocal()
    # Seed core stocks requested by user
    core_stocks = ["MSFT", "GOOGL", "ADBE", "JPM", "BAC", "XOM", "LMT", "NOC", "JNJ", "PFE"]
    buffer_stocks = ["AMZN", "INTC"] # buffers
    
    all_stocks = core_stocks + buffer_stocks
    for symbol in all_stocks:
        if not db.query(models.TrackedStock).filter(models.TrackedStock.symbol == symbol).first():
            is_active = symbol in core_stocks
            db.add(models.TrackedStock(symbol=symbol, is_active=is_active))
    db.commit()
    db.close()

    from trading_engine.loop import run_trading_cycle
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_trading_cycle, 'interval', minutes=30)
    scheduler.start()

app.include_router(portfolio.router, prefix="/api/portfolio")
app.include_router(llm_chat.router, prefix="/api/chat")
app.include_router(knowledge.router, prefix="/api/knowledge")
app.include_router(news.router, prefix="/api/news")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "API Running"}


