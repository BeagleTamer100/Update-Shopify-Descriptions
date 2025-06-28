#!/usr/bin/env python3
"""
Extract Next 10 Products Script
Extracts the next 10 unique products that haven't been processed yet
and outputs them to a new CSV file with their current descriptions.
"""

import csv
import pickle
import os
from typing import Set, List, Dict

def load_progress_file(progress_file: str) -> Set[str]:
    """Load the processed handles from the progress file"""
    try:
        if os.path.exists(progress_file):
            with open(progress_file, 'rb') as f:
                progress_data = pickle.load(f)
            processed_handles = set(progress_data.get('processed_handles', []))
            print(f"Loaded {len(processed_handles)} processed handles from progress file")
            return processed_handles
        else:
            print("No progress file found. Starting from the beginning.")
            return set()
    except Exception as e:
        print(f"Error loading progress file: {e}")
        return set()

def extract_next_10_products(csv_file: str, progress_file: str, output_file: str):
    """Extract the next 10 unique products that haven't been processed"""
    
    # Load processed handles
    processed_handles = load_progress_file(progress_file)
    
    # Read the CSV and collect unique products
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
                # If this is a new unique product handle
                if handle not in unique_products and handle not in processed_handles:
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

def main():
    """Main function"""
    csv_file = "products_export_June_25_2025.csv"
    progress_file = "products_export_June_25_2025.csv_progress.pkl"
    output_file = "next_10_products.csv"
    
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found!")
        return 1
    
    try:
        extract_next_10_products(csv_file, progress_file, output_file)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 