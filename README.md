# 📈 AI-Powered Portfolio Management System

This is the central codebase for your smart AI-driven portfolio analyzer and trading agent. It is built using a modern **React (Vite) + Vanilla CSS** frontend and a **FastAPI + LangGraph + PosgreSQL** python backend.

## Prerequisites

Before starting the project, ensure you have the following installed and running:
1. **PostgreSQL**: Running on `localhost:5432`. Ensure you have created a database named `minor-project-ai-trading-antigravity` with user `postgres` and password `1234` (or update `.env`/`database.py`).
2. **Ollama**: Installed locally with the models running.
   - Run `ollama run llama3.2` and `ollama run deepseek-r1` in your terminal to ensure you've pulled the models.
3. **Finnhub API Key**: (Already pre-configured in `loop.py`).

## Step 1: Start the Backend (FastAPI + AI Trading Engine)
The Python backend manages the database, API endpoints, and the LangGraph looping engine.

1. Open a new terminal.
2. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
3. Activate the virtual environment:
   ```bash
   # Windows PowerShell
   ..\venv\Scripts\activate
   ```
4. Start the FastAPI Application:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   *The backend will automatically create the PostgreSQL tables upon starting.*
   *API Swagger documentation will be available at http://localhost:8000/docs.*

## Step 2: Start the Frontend (React + Vite)
The frontend serves the beautiful glassmorphism dashboard.

1. Open a second new terminal.
2. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open the displayed local URL (typically `http://localhost:5173`) in your browser to view your AI Portfolio application.
