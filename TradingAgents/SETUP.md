# Setup Instructions

## Prerequisites

- Python 3.10+
- PostgreSQL
- Ollama

## Installation Steps

### 1. Clone and Setup Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Ollama Models

```bash
ollama pull llama3.2
ollama pull deepseek-r1
```

### 3. Download FinBERT Model

Download from [HuggingFace](https://huggingface.co/ProsusAI/finbert) and place in `./model/finbert/`

Required files:
- config.json
- pytorch_model.bin
- tokenizer_config.json
- vocab.txt

### 4. Configure Environment

Create a `.env` file with your credentials:
- FINNHUB_API_KEY (get from [finnhub.io](https://finnhub.io))
- Database credentials

### 5. Setup Database

```bash
createdb trading_agents
python main.py --init-db
```

## Verify Installation

```bash
# Test imports
python -c "from graph.trading_workflow import TradingWorkflow; print('OK')"

# Check Ollama
ollama list

# Check database
psql -d trading_agents -c "\dt"
```

## Run

```bash
python main.py
```
