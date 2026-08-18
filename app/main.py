from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import io
import csv
from datetime import datetime

from app.models.product import Product
from app.models.competitor import CompetitorPrice
from app.rules.undercut import recommend_undercut_price
from app.services.margin import margin_percent, minimum_allowed_price

app = FastAPI(
    title="E-commerce Repricing Engine",
    description="Rule-based competitive pricing engine for ecommerce products.",
    version="0.1.0",
)

templates = Jinja2Templates(directory="app/templates")

PRODUCTS_CSV = "data/sample/products.csv"
COMPETITORS_CSV = "data/sample/competitor_prices.csv"


def load_products() -> list[Product]:
    df = pd.read_csv(PRODUCTS_CSV)
    products = []
    for _, row in df.iterrows():
        if row.get("active", True):
            products.append(Product(
                id=row["id"],
                sku=row["sku"],
                title=row["title"],
                brand=row.get("brand"),
                category=row.get("category"),
                cost=float(row["cost"]),
                current_price=float(row["current_price"]),
                currency=row.get("currency", "INR"),
                minimum_margin_percent=float(row.get("minimum_margin_percent", 15)),
                maximum_price_change_percent=float(row.get("maximum_price_change_percent", 20)),
            ))
    return products


def load_competitors() -> list[CompetitorPrice]:
    df = pd.read_csv(COMPETITORS_CSV)
    competitors = []
    for _, row in df.iterrows():
        if row.get("available", True):
            competitors.append(CompetitorPrice(
                product_id=row["product_id"],
                competitor_name=row["competitor_name"],
                competitor_product_id=row.get("competitor_product_id"),
                product_title=row["product_title"],
                price=float(row["price"]),
                currency=row.get("currency", "INR"),
                available=True,
                collected_at=pd.to_datetime(row["collected_at"]),
            ))
    return competitors


def get_competitors_for_product(product_id: str, competitors: list[CompetitorPrice]) -> list[CompetitorPrice]:
    return [c for c in competitors if c.product_id == product_id]


def calculate_recommendations(products: list[Product], competitors: list[CompetitorPrice]) -> list[dict]:
    results = []
    for product in products:
        product_competitors = get_competitors_for_product(product.id, competitors)
        result = recommend_undercut_price(product, product_competitors, undercut_amount=1.0)
        
        min_price = minimum_allowed_price(product.cost, product.minimum_margin_percent)
        margin = margin_percent(product.cost, result["recommended_price"])
        
        lowest_comp = None
        if product_competitors:
            available = [c.price for c in product_competitors if c.available and c.price > 0]
            if available:
                lowest_comp = min(available)
        
        results.append({
            "product_id": product.id,
            "sku": product.sku,
            "title": product.title,
            "brand": product.brand,
            "category": product.category,
            "cost": product.cost,
            "current_price": product.current_price,
            "lowest_competitor_price": lowest_comp,
            "recommended_price": result["recommended_price"],
            "price_change_percent": ((result["recommended_price"] - product.current_price) / product.current_price) * 100,
            "margin_percent": margin,
            "minimum_allowed_price": min_price,
            "reason": result["reason"],
            "safe_to_apply": result["safe_to_apply"],
        })
    return results


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, search: Optional[str] = Query(None)):
    products = load_products()
    competitors = load_competitors()
    recommendations = calculate_recommendations(products, competitors)
    
    if search:
        search_lower = search.lower()
        recommendations = [
            r for r in recommendations
            if search_lower in r["title"].lower()
            or search_lower in r["sku"].lower()
            or (r["brand"] and search_lower in r["brand"].lower())
            or (r["category"] and search_lower in r["category"].lower())
        ]
    
    safe_count = sum(1 for r in recommendations if r["safe_to_apply"])
    products_with_comp = sum(1 for r in recommendations if r["lowest_competitor_price"] is not None)
    products_without_comp = sum(1 for r in recommendations if r["lowest_competitor_price"] is None)
    
    avg_change = 0
    if recommendations:
        avg_change = sum(r["price_change_percent"] for r in recommendations) / len(recommendations)
    
    avg_current = sum(r["current_price"] for r in recommendations) / len(recommendations) if recommendations else 0
    avg_recommended = sum(r["recommended_price"] for r in recommendations) / len(recommendations) if recommendations else 0
    total_savings = sum(r["current_price"] - r["recommended_price"] for r in recommendations)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "recommendations": recommendations,
        "products": products,
        "search_query": search,
        "safe_count": safe_count,
        "avg_change": round(avg_change, 1),
        "products_with_competitors": products_with_comp,
        "products_without_competitors": products_without_comp,
        "avg_current_price": round(avg_current, 0),
        "avg_recommended_price": round(avg_recommended, 0),
        "total_savings": round(total_savings, 0),
    })


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/recommendations")
async def get_recommendations_api():
    products = load_products()
    competitors = load_competitors()
    recommendations = calculate_recommendations(products, competitors)
    return {"recommendations": recommendations, "count": len(recommendations)}


@app.post("/api/recalculate")
async def recalculate():
    return {"status": "recalculated", "timestamp": datetime.now().isoformat()}


@app.get("/api/export")
async def export_csv():
    products = load_products()
    competitors = load_competitors()
    recommendations = calculate_recommendations(products, competitors)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Product ID", "SKU", "Title", "Brand", "Category",
        "Cost", "Current Price", "Lowest Competitor",
        "Recommended Price", "Change %", "Margin %",
        "Min Allowed Price", "Safe to Apply", "Reason"
    ])
    for r in recommendations:
        writer.writerow([
            r["product_id"], r["sku"], r["title"], r["brand"] or "", r["category"] or "",
            r["cost"], r["current_price"],
            r["lowest_competitor_price"] or "",
            r["recommended_price"], round(r["price_change_percent"], 1),
            round(r["margin_percent"], 1),
            r["minimum_allowed_price"],
            "Yes" if r["safe_to_apply"] else "No",
            r["reason"]
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=repricing-recommendations.csv"}
    )