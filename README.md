# E-commerce Repricing Engine

Rule-based competitive pricing engine for ecommerce products.

## Overview

Given your product cost, current price, competitor prices, margin requirements, and pricing rules, this engine recommends the optimal selling price.

## Features

- Product and competitor price modeling
- Margin calculation with safety floors
- Undercut pricing strategy
- Product matching with fuzzy similarity
- FastAPI REST API
- PostgreSQL persistence
- Docker support

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run API
uvicorn app.main:app --reload
```

### Docker

```bash
docker-compose up --build
```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Service health
- `POST /recommend-price` - Get price recommendation

## Project Structure

```
ecommerce-repricing-engine/
├── app/
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── rules/
│   ├── providers/
│   └── main.py
├── data/
│   ├── raw/
│   └── sample/
├── tests/
├── docs/
└── .github/workflows/
```

## Testing

```bash
pytest
```

## License

MIT