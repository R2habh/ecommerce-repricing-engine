# E-commerce Repricing Engine

Rule-based competitive pricing engine for ecommerce products. Given your product cost, current price, competitor prices, margin requirements, and pricing rules, this engine recommends the optimal selling price.

## Features

- **Product & Competitor Modeling** - Structured data models for products and competitor prices
- **Margin Safety Floors** - Never recommends prices below minimum margin threshold
- **Undercut Pricing Strategy** - Beat lowest competitor by configurable amount (default ₹1)
- **Multi-source Data Ingestion** - Parse Amazon, Lazada, SHEIN CSV exports
- **Currency Normalization** - Auto-convert USD/IDR to INR
- **Interactive Dashboard** - Search, filter, and view recommendations
- **Analysis & Visualization** - Charts for price distribution, category performance, competitor comparison, brand analysis
- **FastAPI REST API** - JSON endpoints for integration
- **CSV Export** - Download recommendations for bulk upload
- **Docker Support** - Containerized deployment with PostgreSQL

## Screenshots

### Dashboard
![Dashboard](docs/images/dashboard.svg)
*Main dashboard with filterable product recommendations table*

### Analysis - Overview
![Analysis Overview](docs/images/analysis-overview.svg)
*Price distribution, change distribution, currency breakdown, category performance*

### Analysis - Categories
![Analysis Categories](docs/images/analysis-categories.svg)
*Category-wise performance metrics with safe/unsafe counts*

### Analysis - Competitors
![Analysis Competitors](docs/images/analysis-competitors.svg)
*Competitor price comparison vs our recommended prices*

### Analysis - Brands
![Analysis Brands](docs/images/analysis-brands.svg)
*Top brands by product count with performance details*

## Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/R2habh/ecommerce-repricing-engine.git
cd ecommerce-repricing-engine

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run API server
uvicorn app.main:app --reload
```

Open in browser:
- **Dashboard**: http://127.0.0.1:8000
- **Analysis**: http://127.0.0.1:8000/analysis
- **API Docs**: http://127.0.0.1:8000/docs

### Docker

```bash
docker-compose up --build
```

## Data Ingestion

Ingest external ecommerce CSV data (Amazon, Lazada, SHEIN):

```bash
python scripts/ingest_data.py
```

This will:
1. Parse CSV files from configured paths
2. Convert all prices to INR (USD→₹83, IDR→₹0.0052)
3. Calculate cost as percentage of selling price (60% Amazon, 65% Lazada, 50% SHEIN)
4. Merge with existing sample data
5. Output to `data/sample/products.csv` and `data/sample/competitor_prices.csv`

**Current dataset**: 219 products, 364 competitor prices across 13 categories

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard HTML (with filters) |
| `/analysis` | GET | Analysis page with charts |
| `/health` | GET | Health check |
| `/api/recommendations` | GET | All recommendations as JSON |
| `/api/analysis` | GET | Analysis data as JSON |
| `/api/export` | GET | Download recommendations CSV |
| `/api/recalculate` | POST | Trigger recalculation |

### Query Parameters

**Dashboard (`/`)**:
- `search` - Search title, SKU, brand, category
- `category` - Filter by category
- `brand` - Filter by brand
- `status` - Filter by `safe`, `unsafe`, `no_data`
- `min_price` - Minimum recommended price
- `max_price` - Maximum recommended price

**Analysis (`/analysis`)**:
- `category` - Filter by category
- `brand` - Filter by brand
- `status` - Filter by `safe`, `unsafe`, `no_data`

### Example API Response

```json
{
  "recommendations": [
    {
      "product_id": "P001",
      "sku": "SKU001",
      "title": "Wireless Bluetooth Headphones",
      "brand": "SoundMax",
      "category": "Electronics",
      "cost": 700,
      "current_price": 999,
      "lowest_competitor_price": 949,
      "recommended_price": 948,
      "price_change_percent": -5.1,
      "margin_percent": 26.2,
      "minimum_allowed_price": 805,
      "reason": "Targeting ₹1.00 below lowest competitor.",
      "safe_to_apply": true
    }
  ],
  "count": 219
}
```

## Pricing Logic

### Margin Floor (Safety)
```
Minimum Price = Cost × (1 + Minimum Margin %)
```
Example: Cost ₹700, Margin 15% → Minimum ₹805

### Undercut Rule
```
Target Price = Lowest Competitor Price - Undercut Amount
Recommended = max(Target Price, Minimum Price)
```
Example: Lowest competitor ₹949, Undercut ₹1 → Target ₹948

If competitor price is below margin floor, engine recommends margin floor (doesn't compete at a loss).

## Project Structure

```
ecommerce-repricing-engine/
├── app/
│   ├── api/              # API routes (future)
│   ├── models/           # Pydantic models
│   │   ├── product.py
│   │   ├── competitor.py
│   │   └── recommendation.py
│   ├── services/         # Business logic
│   │   ├── margin.py
│   │   └── competitor.py
│   ├── rules/            # Pricing rules
│   │   └── undercut.py
│   ├── providers/        # Data providers (future)
│   ├── templates/        # Jinja2 templates
│   │   ├── dashboard.html
│   │   └── analysis.html
│   └── main.py           # FastAPI app
├── data/
│   ├── raw/              # Raw data files
│   └── sample/           # Sample CSV data
├── scripts/
│   └── ingest_data.py    # Data ingestion script
├── tests/
│   └── test_pricing.py
├── docs/
│   └── images/           # Screenshots
├── .github/workflows/
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Configuration

Environment variables (`.env`):

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/repricing

# API
API_HOST=0.0.0.0
API_PORT=8000

# Debug
DEBUG=true
```

Currency conversion rates (in `scripts/ingest_data.py`):
```python
USD_TO_INR = 83.0
IDR_TO_INR = 0.0052
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_pricing.py::test_undercuts_lowest_competitor -v
```

## Extending the Engine

### Add New Pricing Rule

Create `app/rules/my_rule.py`:
```python
from app.models.product import Product
from app.models.competitor import CompetitorPrice

def recommend_my_rule(product: Product, competitors: list[CompetitorPrice]):
    # Your logic here
    return {
        "recommended_price": price,
        "reason": "Description",
        "safe_to_apply": bool
    }
```

Register in `app/main.py`:
```python
from app.rules.my_rule import recommend_my_rule
```

### Add Data Provider

Create `app/providers/my_provider.py`:
```python
class MyProvider:
    def fetch_competitor_prices(self, product_ids: list[str]):
        # Fetch from API, scrape, etc.
        return competitor_prices
```

## Performance Notes

- Analysis page loads filtered data only (server-side filtering)
- Charts lazy-loaded on tab activation
- 219 products render in ~50ms
- For production: add Redis caching, database indexing, async DB

## License

MIT