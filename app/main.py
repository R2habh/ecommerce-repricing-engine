from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import io
import csv
import json
from datetime import datetime
from collections import Counter

from app.models.product import Product
from app.models.competitor import CompetitorPrice
from app.rules.undercut import recommend_undercut_price
from app.services.margin import margin_percent, minimum_allowed_price

app = FastAPI(
    title="E-commerce Repricing Engine",
    description="Rule-based competitive pricing engine for ecommerce products.",
    version="0.1.0",
)

env = Environment(loader=FileSystemLoader("app/templates"))

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


def get_analysis_data(products: list[Product], competitors: list[CompetitorPrice], recommendations: list[dict], 
                      category_filter: Optional[str] = None, brand_filter: Optional[str] = None, 
                      status_filter: Optional[str] = None) -> dict:
    df_products = pd.DataFrame([p.model_dump() for p in products])
    df_comp = pd.DataFrame([{
        'product_id': c.product_id,
        'competitor_name': c.competitor_name,
        'price': c.price,
        'currency': c.currency
    } for c in competitors])
    df_rec = pd.DataFrame(recommendations)
    
    # Apply filters
    if category_filter:
        df_products = df_products[df_products['category'] == category_filter]
        product_ids = df_products['id'].tolist()
        df_rec = df_rec[df_rec['product_id'].isin(product_ids)]
        df_comp = df_comp[df_comp['product_id'].isin(product_ids)]
    
    if brand_filter:
        df_products = df_products[df_products['brand'] == brand_filter]
        product_ids = df_products['id'].tolist()
        df_rec = df_rec[df_rec['product_id'].isin(product_ids)]
        df_comp = df_comp[df_comp['product_id'].isin(product_ids)]
    
    if status_filter == "safe":
        df_rec = df_rec[df_rec['safe_to_apply'] == True]
        product_ids = df_rec['product_id'].tolist()
        df_products = df_products[df_products['id'].isin(product_ids)]
        df_comp = df_comp[df_comp['product_id'].isin(product_ids)]
    elif status_filter == "unsafe":
        df_rec = df_rec[(df_rec['safe_to_apply'] == False) & (df_rec['lowest_competitor_price'].notna())]
        product_ids = df_rec['product_id'].tolist()
        df_products = df_products[df_products['id'].isin(product_ids)]
        df_comp = df_comp[df_comp['product_id'].isin(product_ids)]
    elif status_filter == "no_data":
        df_rec = df_rec[df_rec['lowest_competitor_price'].isna()]
        product_ids = df_rec['product_id'].tolist()
        df_products = df_products[df_products['id'].isin(product_ids)]
        df_comp = df_comp[df_comp['product_id'].isin(product_ids)]
    
    category_stats = []
    for cat in df_products['category'].unique():
        if pd.isna(cat):
            continue
        cat_products = df_products[df_products['category'] == cat]
        cat_recs = df_rec[df_rec['category'] == cat]
        cat_comp = df_comp[df_comp['product_id'].isin(cat_products['id'])]
        
        safe_count = int(cat_recs['safe_to_apply'].sum()) if len(cat_recs) > 0 else 0
        avg_change = float(cat_recs['price_change_percent'].mean()) if len(cat_recs) > 0 else 0
        avg_margin = float(cat_recs['margin_percent'].mean()) if len(cat_recs) > 0 else 0
        competitor_count = len(cat_comp['competitor_name'].unique()) if len(cat_comp) > 0 else 0
        
        category_stats.append({
            "category": cat,
            "product_count": int(len(cat_products)),
            "avg_current_price": round(float(cat_products['current_price'].mean()), 2),
            "avg_recommended_price": round(float(cat_recs['recommended_price'].mean()), 2) if len(cat_recs) > 0 else 0,
            "avg_change_percent": round(avg_change, 1),
            "avg_margin_percent": round(avg_margin, 1),
            "safe_count": safe_count,
            "competitor_count": competitor_count
        })
    
    competitor_stats = []
    for comp in df_comp['competitor_name'].unique():
        if pd.isna(comp):
            continue
        comp_data = df_comp[df_comp['competitor_name'] == comp]
        comp_products = df_products[df_products['id'].isin(comp_data['product_id'])]
        comp_recs = df_rec[df_rec['product_id'].isin(comp_data['product_id'])]
        
        avg_price = float(comp_data['price'].mean())
        price_vs_our = 0
        if len(comp_recs) > 0:
            comp_prices = comp_data.set_index('product_id')['price']
            merged = comp_recs.copy()
            merged['comp_price'] = merged['product_id'].map(comp_prices)
            merged = merged.dropna(subset=['comp_price'])
            if len(merged) > 0:
                price_vs_our = float((((merged['recommended_price'] - merged['comp_price']) / merged['comp_price']) * 100).mean())
        
        competitor_stats.append({
            "competitor": comp,
            "product_count": int(len(comp_data['product_id'].unique())),
            "avg_price": round(avg_price, 2),
            "avg_price_vs_our_percent": round(price_vs_our, 1),
            "currencies": list(comp_data['currency'].unique())
        })
    
    brand_stats = []
    for brand in df_products['brand'].unique():
        if pd.isna(brand) or brand == 'Unknown' or brand == '':
            continue
        brand_products = df_products[df_products['brand'] == brand]
        brand_recs = df_rec[df_rec['brand'] == brand]
        brand_comp = df_comp[df_comp['product_id'].isin(brand_products['id'])]
        
        safe_count = int(brand_recs['safe_to_apply'].sum()) if len(brand_recs) > 0 else 0
        avg_change = float(brand_recs['price_change_percent'].mean()) if len(brand_recs) > 0 else 0
        avg_margin = float(brand_recs['margin_percent'].mean()) if len(brand_recs) > 0 else 0
        
        brand_stats.append({
            "brand": brand,
            "product_count": int(len(brand_products)),
            "avg_current_price": round(float(brand_products['current_price'].mean()), 2),
            "avg_change_percent": round(avg_change, 1),
            "avg_margin_percent": round(avg_margin, 1),
            "safe_count": safe_count,
            "competitor_count": len(brand_comp['competitor_name'].unique()) if len(brand_comp) > 0 else 0
        })
    
    brand_stats.sort(key=lambda x: x['product_count'], reverse=True)
    brand_stats = brand_stats[:20]
    
    price_distribution = []
    bins = [0, 500, 1000, 2000, 5000, 10000, 50000, float('inf')]
    labels = ['0-500', '500-1K', '1K-2K', '2K-5K', '5K-10K', '10K-50K', '50K+']
    for i in range(len(bins)-1):
        count = len(df_products[(df_products['current_price'] >= bins[i]) & (df_products['current_price'] < bins[i+1])])
        price_distribution.append({"range": labels[i], "count": int(count)})
    
    change_distribution = []
    bins_change = [-float('inf'), -20, -10, -5, 0, 5, 10, 20, float('inf')]
    labels_change = ['<-20%', '-20% to -10%', '-10% to -5%', '-5% to 0%', '0% to 5%', '5% to 10%', '10% to 20%', '>20%']
    for i in range(len(bins_change)-1):
        count = len(df_rec[(df_rec['price_change_percent'] >= bins_change[i]) & (df_rec['price_change_percent'] < bins_change[i+1])])
        change_distribution.append({"range": labels_change[i], "count": int(count)})
    
    currency_stats = df_products['currency'].value_counts().to_dict()
    currency_stats = {k: int(v) for k, v in currency_stats.items()}
    
    return {
        "category_stats": category_stats,
        "competitor_stats": competitor_stats,
        "brand_stats": brand_stats,
        "price_distribution": price_distribution,
        "change_distribution": change_distribution,
        "currency_stats": currency_stats,
        "total_products": len(df_products),
        "total_competitors": len(df_comp),
        "total_recommendations": len(df_rec),
        "safe_recommendations": int(df_rec['safe_to_apply'].sum()),
        "avg_price_change": round(float(df_rec['price_change_percent'].mean()), 1) if len(df_rec) > 0 else 0,
        "avg_margin": round(float(df_rec['margin_percent'].mean()), 1) if len(df_rec) > 0 else 0,
    }


@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(
    request: Request,
    category: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    products = load_products()
    competitors = load_competitors()
    recommendations = calculate_recommendations(products, competitors)
    analysis = get_analysis_data(products, competitors, recommendations, category, brand, status)
    
    # Get unique values for filter dropdowns
    df_products = pd.DataFrame([p.model_dump() for p in products])
    all_categories = sorted([c for c in df_products['category'].unique() if pd.notna(c)])
    all_brands = sorted([b for b in df_products['brand'].unique() if pd.notna(b) and b != 'Unknown' and b != ''])
    
    template = env.get_template("analysis.html")
    html = template.render(
        request={},
        analysis=analysis,
        selected_category=category,
        selected_brand=brand,
        selected_status=status,
        all_categories=all_categories,
        all_brands=all_brands,
    )
    return HTMLResponse(content=html)


@app.get("/api/analysis")
async def get_analysis():
    products = load_products()
    competitors = load_competitors()
    recommendations = calculate_recommendations(products, competitors)
    analysis = get_analysis_data(products, competitors, recommendations)
    return analysis


@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_price: Optional[str] = Query(None),
    max_price: Optional[str] = Query(None),
):
    # Parse numeric filters safely
    try:
        min_price_val = float(min_price) if min_price else None
    except (ValueError, TypeError):
        min_price_val = None
    
    try:
        max_price_val = float(max_price) if max_price else None
    except (ValueError, TypeError):
        max_price_val = None
    
    products = load_products()
    competitors = load_competitors()
    recommendations = calculate_recommendations(products, competitors)
    
    # Apply filters
    if search:
        search_lower = search.lower()
        recommendations = [
            r for r in recommendations
            if search_lower in r["title"].lower()
            or search_lower in r["sku"].lower()
            or (r["brand"] and search_lower in r["brand"].lower())
            or (r["category"] and search_lower in r["category"].lower())
        ]
    
    if category:
        recommendations = [r for r in recommendations if r["category"] == category]
    
    if brand:
        recommendations = [r for r in recommendations if r["brand"] == brand]
    
    if status == "safe":
        recommendations = [r for r in recommendations if r["safe_to_apply"]]
    elif status == "unsafe":
        recommendations = [r for r in recommendations if not r["safe_to_apply"] and r["lowest_competitor_price"] is not None]
    elif status == "no_data":
        recommendations = [r for r in recommendations if r["lowest_competitor_price"] is None]
    
    if min_price_val is not None:
        recommendations = [r for r in recommendations if r["recommended_price"] >= min_price_val]
    
    if max_price_val is not None:
        recommendations = [r for r in recommendations if r["recommended_price"] <= max_price_val]
    
    safe_count = sum(1 for r in recommendations if r["safe_to_apply"])
    products_with_comp = sum(1 for r in recommendations if r["lowest_competitor_price"] is not None)
    products_without_comp = sum(1 for r in recommendations if r["lowest_competitor_price"] is None)
    
    avg_change = 0
    if recommendations:
        avg_change = sum(r["price_change_percent"] for r in recommendations) / len(recommendations)
    
    avg_current = sum(r["current_price"] for r in recommendations) / len(recommendations) if recommendations else 0
    avg_recommended = sum(r["recommended_price"] for r in recommendations) / len(recommendations) if recommendations else 0
    total_savings = sum(r["current_price"] - r["recommended_price"] for r in recommendations)
    
    # Get unique values for filter dropdowns
    all_categories = sorted(set(p.category for p in products if p.category))
    all_brands = sorted(set(p.brand for p in products if p.brand))
    
    products_dict = [p.model_dump() for p in products]
    
    template = env.get_template("dashboard.html")
    html = template.render(
        request={},
        recommendations=recommendations,
        products=products_dict,
        search_query=search,
        selected_category=category,
        selected_brand=brand,
        selected_status=status,
        min_price=min_price,
        max_price=max_price,
        all_categories=all_categories,
        all_brands=all_brands,
        safe_count=safe_count,
        avg_change=round(avg_change, 1),
        products_with_competitors=products_with_comp,
        products_without_competitors=products_without_comp,
        avg_current_price=round(avg_current, 0),
        avg_recommended_price=round(avg_recommended, 0),
        total_savings=round(total_savings, 0),
    )
    return HTMLResponse(content=html)


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