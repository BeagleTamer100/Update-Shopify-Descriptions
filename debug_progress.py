#!/usr/bin/env python3
"""
Debug Progress File Script
Check what's in the progress file and understand the data structure.
"""

import pickle
import csv
import os

def debug_progress():
    """Debug the progress file and CSV structure"""
    
    progress_file = "products_export_June_25_2025.csv_progress.pkl"
    csv_file = "products_export_June_25_2025.csv"
    
    # Check progress file
    print("=== PROGRESS FILE ANALYSIS ===")
    if os.path.exists(progress_file):
        with open(progress_file, 'rb') as f:
            progress_data = pickle.load(f)
        
        processed_handles = set(progress_data.get('processed_handles', []))
        updated_products = progress_data.get('updated_products', {})
        
        print(f"Progress file exists: {progress_file}")
        print(f"Processed handles count: {len(processed_handles)}")
        print(f"Updated products count: {len(updated_products)}")
        
        print("\nFirst 10 processed handles:")
        for i, handle in enumerate(list(processed_handles)[:10], 1):
            print(f"  {i}. {handle}")
        
        if len(processed_handles) > 10:
            print(f"  ... and {len(processed_handles) - 10} more")
            
    else:
        print("Progress file does not exist!")
    
    # Check CSV structure
    print("\n=== CSV ANALYSIS ===")
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, quoting=csv.QUOTE_ALL)
            
            # Count unique products with descriptions
            unique_products = {}
            total_rows = 0
            
            for row in reader:
                total_rows += 1
                handle = row.get('Handle', '').strip()
                title = row.get('Title', '').strip()
                body_html = row.get('Body (HTML)', '').strip()
                
                if handle and title and body_html:
                    if handle not in unique_products:
                        unique_products[handle] = row
            
            print(f"CSV file exists: {csv_file}")
            print(f"Total rows: {total_rows}")
            print(f"Unique products with descriptions: {len(unique_products)}")
            
            print("\nFirst 10 unique products in CSV:")
            for i, (handle, row) in enumerate(list(unique_products.items())[:10], 1):
                print(f"  {i}. {row.get('Title', 'Unknown')} ({handle})")
                
    else:
        print("CSV file does not exist!")
    
    # Check for products not in progress file
    print("\n=== FINDING NEXT PRODUCTS ===")
    if os.path.exists(progress_file) and os.path.exists(csv_file):
        with open(progress_file, 'rb') as f:
            progress_data = pickle.load(f)
        processed_handles = set(progress_data.get('processed_handles', []))
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, quoting=csv.QUOTE_ALL)
            
            next_products = []
            for row in reader:
                handle = row.get('Handle', '').strip()
                title = row.get('Title', '').strip()
                body_html = row.get('Body (HTML)', '').strip()
                
                if handle and title and body_html and handle not in processed_handles:
                    if handle not in [p['handle'] for p in next_products]:
                        next_products.append({
                            'handle': handle,
                            'title': title,
                            'row': row
                        })
                        
                        if len(next_products) >= 10:
                            break
            
            print(f"Found {len(next_products)} next products to process:")
            for i, product in enumerate(next_products, 1):
                print(f"  {i}. {product['title']} ({product['handle']})")

if __name__ == "__main__":
    debug_progress() 