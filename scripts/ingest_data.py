import pandas as pd
import os
from datetime import datetime

AMAZON_CSV = r"C:\Users\rusha\Downloads\amazon-products.csv"
LAZADA_CSV = r"C:\ALL AI WORKS\eCommerce-dataset-samples-main\eCommerce-dataset-samples-main\lazada-products.csv"
SHEIN_CSV = r"C:\ALL AI WORKS\eCommerce-dataset-samples-main\eCommerce-dataset-samples-main\shein-products.csv"

OUTPUT_PRODUCTS = "data/sample/products.csv"
OUTPUT_COMPETITORS = "data/sample/competitor_prices.csv"

def parse_price(val):
    if pd.isna(val) or val == "" or val == "null" or val == "0":
        return None
    try:
        return float(str(val).replace('"', '').replace(',', ''))
    except:
        return None

def parse_amazon():
    df = pd.read_csv(AMAZON_CSV, low_memory=False)
    products = []
    competitors = []
    
    for i, row in df.iterrows():
        if i >= 50:
            break
        
        final_price = parse_price(row.get('final_price'))
        initial_price = parse_price(row.get('initial_price'))
        
        if not final_price or final_price <= 0:
            continue
            
        cost = final_price * 0.6
        product_id = f"AMZ{str(i+1).zfill(3)}"
        sku = row.get('asin', f"AMZ{i+1}")
        title = str(row.get('title', 'Unknown'))[:100]
        brand = str(row.get('brand', 'Unknown'))[:50]
        categories = str(row.get('categories', ''))
        category = 'Electronics'
        if 'Clothing' in categories or 'Shoes' in categories:
            category = 'Fashion'
        elif 'Home' in categories:
            category = 'Home'
        elif 'Automotive' in categories:
            category = 'Automotive'
        elif 'Tools' in categories:
            category = 'Tools'
        
        products.append({
            'id': product_id,
            'sku': sku,
            'title': title,
            'brand': brand,
            'category': category,
            'cost': round(cost, 2),
            'current_price': final_price,
            'currency': row.get('currency', 'USD'),
            'minimum_margin_percent': 15,
            'maximum_price_change_percent': 20,
            'active': True
        })
        
        competitors.append({
            'product_id': product_id,
            'competitor_name': 'Amazon',
            'competitor_product_id': row.get('asin', ''),
            'product_title': title,
            'price': final_price,
            'currency': row.get('currency', 'USD'),
            'available': True,
            'collected_at': datetime.now().isoformat()
        })
        
        if initial_price and initial_price > final_price:
            competitors.append({
                'product_id': product_id,
                'competitor_name': 'Amazon_List_Price',
                'competitor_product_id': row.get('asin', ''),
                'product_title': title,
                'price': initial_price,
                'currency': row.get('currency', 'USD'),
                'available': True,
                'collected_at': datetime.now().isoformat()
            })
    
    return products, competitors

def parse_lazada():
    df = pd.read_csv(LAZADA_CSV, low_memory=False)
    products = []
    competitors = []
    
    for i, row in df.iterrows():
        if i >= 30:
            break
            
        final_price = parse_price(row.get('final_price'))
        initial_price = parse_price(row.get('initial_price'))
        
        if not final_price or final_price <= 0:
            continue
            
        cost = final_price * 0.65
        product_id = f"LZD{str(i+1).zfill(3)}"
        sku = row.get('sku', f"LZD{i+1}")
        title = str(row.get('title', 'Unknown'))[:100]
        brand = str(row.get('brand', 'Unknown'))[:50]
        breadcrumb = str(row.get('breadcrumb', ''))
        category = 'Electronics'
        if 'Fashion' in breadcrumb or 'Clothing' in breadcrumb:
            category = 'Fashion'
        elif 'Home' in breadcrumb or 'Furniture' in breadcrumb:
            category = 'Home'
        elif 'Beauty' in breadcrumb:
            category = 'Beauty'
        
        products.append({
            'id': product_id,
            'sku': sku,
            'title': title,
            'brand': brand,
            'category': category,
            'cost': round(cost, 2),
            'current_price': final_price,
            'currency': row.get('currency', 'IDR'),
            'minimum_margin_percent': 15,
            'maximum_price_change_percent': 20,
            'active': True
        })
        
        competitors.append({
            'product_id': product_id,
            'competitor_name': 'Lazada',
            'competitor_product_id': sku,
            'product_title': title,
            'price': final_price,
            'currency': row.get('currency', 'IDR'),
            'available': True,
            'collected_at': datetime.now().isoformat()
        })
        
        if initial_price and initial_price > final_price:
            competitors.append({
                'product_id': product_id,
                'competitor_name': 'Lazada_List_Price',
                'competitor_product_id': sku,
                'product_title': title,
                'price': initial_price,
                'currency': row.get('currency', 'IDR'),
                'available': True,
                'collected_at': datetime.now().isoformat()
            })
    
    return products, competitors

def parse_shein():
    df = pd.read_csv(SHEIN_CSV, low_memory=False)
    products = []
    competitors = []
    
    for i, row in df.iterrows():
        if i >= 30:
            break
            
        final_price = parse_price(row.get('final_price'))
        initial_price = parse_price(row.get('initial_price'))
        
        if not final_price or final_price <= 0:
            continue
            
        cost = final_price * 0.5
        product_id = f"SHN{str(i+1).zfill(3)}"
        sku = row.get('product_id', f"SHN{i+1}")
        title = str(row.get('product_name', 'Unknown'))[:100]
        brand = str(row.get('brand', 'SHEIN'))[:50]
        category_tree = str(row.get('category_tree', ''))
        category = 'Fashion'
        if 'Home' in category_tree or 'Furniture' in category_tree:
            category = 'Home'
        elif 'Beauty' in category_tree:
            category = 'Beauty'
        elif 'Jewelry' in category_tree:
            category = 'Jewelry'
        
        products.append({
            'id': product_id,
            'sku': sku,
            'title': title,
            'brand': brand,
            'category': category,
            'cost': round(cost, 2),
            'current_price': final_price,
            'currency': row.get('currency', 'USD'),
            'minimum_margin_percent': 20,
            'maximum_price_change_percent': 25,
            'active': True
        })
        
        competitors.append({
            'product_id': product_id,
            'competitor_name': 'SHEIN',
            'competitor_product_id': sku,
            'product_title': title,
            'price': final_price,
            'currency': row.get('currency', 'USD'),
            'available': True,
            'collected_at': datetime.now().isoformat()
        })
        
        if initial_price and initial_price > final_price:
            competitors.append({
                'product_id': product_id,
                'competitor_name': 'SHEIN_List_Price',
                'competitor_product_id': sku,
                'product_title': title,
                'price': initial_price,
                'currency': row.get('currency', 'USD'),
                'available': True,
                'collected_at': datetime.now().isoformat()
            })
    
    return products, competitors

def main():
    print("Parsing Amazon data...")
    amz_products, amz_comp = parse_amazon()
    print(f"  Products: {len(amz_products)}, Competitors: {len(amz_comp)}")
    
    print("Parsing Lazada data...")
    lzd_products, lzd_comp = parse_lazada()
    print(f"  Products: {len(lzd_products)}, Competitors: {len(lzd_comp)}")
    
    print("Parsing SHEIN data...")
    shn_products, shn_comp = parse_shein()
    print(f"  Products: {len(shn_products)}, Competitors: {len(shn_comp)}")
    
    all_products = amz_products + lzd_products + shn_products
    all_competitors = amz_comp + lzd_comp + shn_comp
    
    print(f"\nTotal new products: {len(all_products)}")
    print(f"Total new competitors: {len(all_competitors)}")
    
    existing_products = pd.read_csv(OUTPUT_PRODUCTS)
    existing_comp = pd.read_csv(OUTPUT_COMPETITORS)
    
    new_products_df = pd.DataFrame(all_products)
    new_comp_df = pd.DataFrame(all_competitors)
    
    combined_products = pd.concat([existing_products, new_products_df], ignore_index=True)
    combined_comp = pd.concat([existing_comp, new_comp_df], ignore_index=True)
    
    combined_products = combined_products.drop_duplicates(subset=['id'], keep='first')
    combined_comp = combined_comp.drop_duplicates(subset=['product_id', 'competitor_name', 'competitor_product_id'], keep='first')
    
    combined_products.to_csv(OUTPUT_PRODUCTS, index=False)
    combined_comp.to_csv(OUTPUT_COMPETITORS, index=False)
    
    print(f"\nSaved {len(combined_products)} products to {OUTPUT_PRODUCTS}")
    print(f"Saved {len(combined_comp)} competitor prices to {OUTPUT_COMPETITORS}")

if __name__ == "__main__":
    main()