#!/usr/bin/env python3
"""
Fix Progress and Extract Next 10 Products
Fixes the progress file to only include actually processed products,
then extracts the next 10 unprocessed products.
"""

import csv
import pickle
import os
from typing import Set, List, Dict

def fix_progress_and_extract():
    """Fix the progress file and extract next 10 products"""
    
    progress_file = "products_export_June_25_2025.csv_progress.pkl"
    csv_file = "products_export_June_25_2025.csv"
    output_file = "next_10_products.csv"
    
    print("=== FIXING PROGRESS FILE ===")
    
    # Load current progress
    if os.path.exists(progress_file):
        with open(progress_file, 'rb') as f:
            progress_data = pickle.load(f)
        
        updated_products = progress_data.get('updated_products', {})
        processed_handles = set(progress_data.get('processed_handles', []))
        
        print(f"Current state:")
        print(f"  - Updated products: {len(updated_products)}")
        print(f"  - Processed handles: {len(processed_handles)}")
        
        # Fix: Only keep handles that were actually updated
        fixed_processed_handles = set(updated_products.keys())
        
        print(f"Fixed state:")
        print(f"  - Actually processed: {len(fixed_processed_handles)}")
        
        # Update progress file
        progress_data['processed_handles'] = list(fixed_processed_handles)
        
        with open(progress_file, 'wb') as f:
            pickle.dump(progress_data, f)
        
        print("✅ Progress file fixed!")
        
    else:
        print("No progress file found. Starting fresh.")
        fixed_processed_handles = set()
    
    print("\n=== EXTRACTING NEXT 10 PRODUCTS ===")
    
    # Read CSV and find next 10 unprocessed products
    unique_products = {}  # handle -> first row with that handle
    all_rows = []  # all rows for output
    
    print(f"Reading CSV file: {csv_file}")
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, quoting=csv.QUOTE_ALL)
        fieldnames = reader.fieldnames
        
        for row in reader:
            handle = row.get('Handle', '').strip()
            title = row.get('Title', '').strip()
            body_html = row.get('Body (HTML)', '').strip()
            
            # Only consider rows with all required fields
            if handle and title and body_html:
                # If this is a new unique product handle and not processed
                if handle not in unique_products and handle not in fixed_processed_handles:
                    unique_products[handle] = row
                    print(f"Found unique product {len(unique_products)}: {title}")
                
                # Add all rows for this handle to our output
                all_rows.append(row)
                
                # Stop when we have 10 unique products
                if len(unique_products) >= 10:
                    break
    
    print(f"\nFound {len(unique_products)} unique products to extract:")
    for i, (handle, row) in enumerate(unique_products.items(), 1):
        print(f"  {i}. {row.get('Title', 'Unknown')} ({handle})")
    
    if len(unique_products) == 0:
        print("❌ No more products to process!")
        return
    
    # Filter all_rows to only include rows for the 10 unique products we found
    output_rows = []
    target_handles = set(unique_products.keys())
    
    for row in all_rows:
        handle = row.get('Handle', '').strip()
        if handle in target_handles:
            output_rows.append(row)
    
    # Write to output CSV
    print(f"\nWriting {len(output_rows)} rows to {output_file}")
    with open(output_file, 'w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(output_rows)
    
    print(f"✅ Successfully extracted next 10 products to: {output_file}")
    print(f"📊 Summary:")
    print(f"   - Unique products: {len(unique_products)}")
    print(f"   - Total rows (including variants): {len(output_rows)}")
    print(f"   - Output file: {output_file}")

if __name__ == "__main__":
    fix_progress_and_extract() 