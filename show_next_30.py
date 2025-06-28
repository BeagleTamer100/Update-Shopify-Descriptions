#!/usr/bin/env python3
"""
Show Next 30 Products Script
Shows which 30 products will be processed next to verify no repeats.
"""

import csv
import pickle
import os

def show_next_30_products():
    """Show the next 30 products that will be processed"""
    
    progress_file = "products_export_June_25_2025.csv_progress.pkl"
    csv_file = "products_export_June_25_2025.csv"
    
    print("=== CURRENT PROGRESS STATUS ===")
    
    # Load current progress
    if os.path.exists(progress_file):
        with open(progress_file, 'rb') as f:
            progress_data = pickle.load(f)
        
        updated_products = progress_data.get('updated_products', {})
        processed_handles = set(progress_data.get('processed_handles', []))
        
        print(f"Currently processed: {len(updated_products)} products")
        print(f"Processed handles: {len(processed_handles)}")
        
        print("\nPreviously processed products:")
        for i, handle in enumerate(list(updated_products.keys()), 1):
            print(f"  {i}. {handle}")
            
    else:
        print("No progress file found. Starting fresh.")
        processed_handles = set()
    
    print(f"\n=== NEXT 30 PRODUCTS TO PROCESS ===")
    
    # Find next 30 unprocessed products
    next_products = []
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, quoting=csv.QUOTE_ALL)
        
        for row in reader:
            handle = row.get('Handle', '').strip()
            title = row.get('Title', '').strip()
            body_html = row.get('Body (HTML)', '').strip()
            
            # Only consider rows with all required fields
            if handle and title and body_html:
                # If this is a new unique product handle and not processed
                if handle not in processed_handles and handle not in [p['handle'] for p in next_products]:
                    next_products.append({
                        'handle': handle,
                        'title': title,
                        'vendor': row.get('Vendor', ''),
                        'category': row.get('Product Category', ''),
                        'price': row.get('Variant Price', '')
                    })
                    
                    if len(next_products) >= 30:
                        break
    
    print(f"Found {len(next_products)} products to process next:")
    print()
    
    for i, product in enumerate(next_products, 1):
        print(f"{i:2d}. {product['title']}")
        print(f"     Handle: {product['handle']}")
        print(f"     Brand: {product['vendor']}")
        print(f"     Category: {product['category']}")
        print(f"     Price: ${product['price']}")
        print()
    
    if len(next_products) < 30:
        print(f"⚠️  Only {len(next_products)} products available to process.")
        print("   This means you've processed most or all products in the CSV.")
    
    print("=== VERIFICATION ===")
    print("✅ No duplicates found - all handles are unique")
    print("✅ All products have titles and descriptions")
    print("✅ All products are not in the processed list")
    
    return next_products

if __name__ == "__main__":
    show_next_30_products() 