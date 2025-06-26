#!/usr/bin/env python3
"""
OpenAI-Enhanced Product Description Updater for Wehitpan.com
Uses OpenAI API to generate sophisticated, AI-optimized product descriptions
Only processes products with existing Body (HTML) content
"""

import csv
import json
import re
import requests
from typing import Dict, List, Optional
import time
from dataclasses import dataclass
import html
import openai
import urllib.parse
from bs4 import BeautifulSoup
import signal
import sys
import pickle
import os

@dataclass
class Product:
    handle: str
    title: str
    body_html: str
    vendor: str
    product_category: str
    price: str
    compare_at_price: str
    inventory_qty: str
    image_src: str
    sku: str
    tags: str
    # Additional fields for enhanced data
    top_notes: str = ""
    middle_notes: str = ""
    base_notes: str = ""
    longevity: str = ""
    sillage: str = ""
    season: str = ""
    occasion: str = ""

class OpenAIEnhancedUpdater:
    def __init__(self, csv_file_path: str, openai_api_key: str):
        self.csv_file_path = csv_file_path
        self.products = []  # List[Product]
        self.updated_products = {}  # Dict[handle, updated_html]
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.processed_handles = set()  # To avoid duplicate API calls
        self.progress_file = f"{csv_file_path}_progress.pkl"
        
        # Initialize session for web scraping
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Load existing progress if available
        self.load_progress()
        
        # Set up signal handler for graceful interruption
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle interruption signals gracefully"""
        print(f"\n\nReceived interrupt signal {signum}. Saving progress...")
        self.save_progress()
        self.export_partial_results()
        print("Progress saved. You can resume later or export partial results.")
        sys.exit(0)
    
    def save_progress(self):
        """Save current progress to file"""
        try:
            progress_data = {
                'updated_products': self.updated_products,
                'processed_handles': list(self.processed_handles)
            }
            with open(self.progress_file, 'wb') as f:
                pickle.dump(progress_data, f)
            print(f"Progress saved to {self.progress_file}")
        except Exception as e:
            print(f"Error saving progress: {e}")
    
    def load_progress(self):
        """Load existing progress from file"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'rb') as f:
                    progress_data = pickle.load(f)
                self.updated_products = progress_data.get('updated_products', {})
                self.processed_handles = set(progress_data.get('processed_handles', []))
                print(f"Loaded existing progress: {len(self.updated_products)} products already processed")
        except Exception as e:
            print(f"Error loading progress: {e}")
    
    def export_partial_results(self, output_file: str = None):
        """Export partial results even if not all products are processed"""
        if not output_file:
            output_file = f"{self.csv_file_path}_partial_export.csv"
        
        print(f"Exporting partial results to {output_file}...")
        self.write_updated_csv(output_file)
        print(f"Partial results exported: {len(self.updated_products)} products processed")
    
    def read_csv(self):
        """Read the CSV file and extract only unique product rows (Title and Body (HTML) non-empty)"""
        print("Reading CSV file...")
        with open(self.csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, quoting=csv.QUOTE_ALL)
            for row in reader:
                title = row.get('Title', '').strip()
                body_html = row.get('Body (HTML)', '').strip()
                handle = row.get('Handle', '').strip()
                # Only process unique product rows
                if title and body_html and handle and handle not in self.processed_handles:
                    product = Product(
                        handle=handle,
                        title=title,
                        body_html=body_html,
                        vendor=row.get('Vendor', ''),
                        product_category=row.get('Product Category', ''),
                        price=row.get('Variant Price', ''),
                        compare_at_price=row.get('Variant Compare At Price', ''),
                        inventory_qty=row.get('Variant Inventory Qty', ''),
                        image_src=row.get('Image Src', ''),
                        sku=row.get('Variant SKU', ''),
                        tags=row.get('Tags', ''),
                        top_notes=row.get('Top Notes (product.metafields.custom.top_notes)', ''),
                        middle_notes=row.get('Middle Notes (product.metafields.custom.middle_notes)', ''),
                        base_notes=row.get('Base Notes (product.metafields.custom.base_notes)', ''),
                        longevity=row.get('Longevity', ''),
                        sillage=row.get('Sillage', ''),
                        season=row.get('Season (product.metafields.shopify.season)', ''),
                        occasion=row.get('Occasion (product.metafields.shopify.occasion)', '')
                    )
                    self.products.append(product)
                    self.processed_handles.add(handle)
        print(f"Loaded {len(self.products)} unique products with descriptions.")
    
    def is_perfume(self, product: Product) -> bool:
        """Check if product is a perfume based on title, category, or tags"""
        perfume_keywords = ['perfume', 'fragrance', 'cologne', 'eau de', 'parfum', 'oil', 'scent']
        text_to_check = f"{product.title} {product.product_category} {product.tags}".lower()
        return any(keyword in text_to_check for keyword in perfume_keywords)
    
    def extract_text_description(self, html_content: str) -> str:
        """Extract plain text from HTML content"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        # Decode HTML entities
        text = html.unescape(text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def get_openai_product_research(self, product: Product) -> Dict:
        """Use OpenAI to research product information"""
        try:
            current_desc = self.extract_text_description(product.body_html)
            
            if self.is_perfume(product):
                prompt = f"""
Research this perfume product and provide detailed information:

Product: {product.title}
Brand: {product.vendor}
Current Description: {current_desc[:500]}
Price: ${product.price}
Category: {product.product_category}
Tags: {product.tags}

Please provide:
1. Detailed fragrance notes (top, middle, base notes)
2. Longevity and sillage information
3. Best seasons and occasions to wear
4. Target audience and who would love this fragrance
5. Key benefits and unique selling points
6. 5 frequently asked questions with detailed answers
7. Community insights and popular opinions
8. How to use and apply this fragrance

Format as JSON with these keys:
- fragrance_notes (object with top_notes, middle_notes, base_notes arrays)
- longevity (string)
- sillage (string)
- seasons (array)
- occasions (array)
- target_audience (array)
- benefits (array)
- faqs (array of objects with question and answer)
- community_insights (array)
- usage_tips (array)
- reddit (array of objects with quote, upvotes, author, url, type)
- fragrantica (array of objects with review, upvotes, author, url, type)
- comparisons (array of objects with comparison, upvotes, author, url, type)
- unique_features (string)
"""
            else:
                prompt = f"""
Research this product and provide detailed information:

Product: {product.title}
Brand: {product.vendor}
Current Description: {current_desc[:500]}
Price: ${product.price}
Category: {product.product_category}
Tags: {product.tags}

Please provide:
1. Detailed product features and benefits
2. How to use this product effectively
3. Who this product is perfect for
4. Key benefits and unique selling points
5. 5 frequently asked questions with detailed answers
6. Common use cases and applications
7. Product specifications and details

Format as JSON with these keys:
- features (array)
- benefits (array)
- usage_instructions (array)
- target_audience (array)
- faqs (array of objects with question and answer)
- use_cases (array)
- specifications (string)
- unique_features (string)
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-2024-11-20",  # Latest free tier model - best for product descriptions
                messages=[
                    {"role": "system", "content": "You are a product research expert specializing in e-commerce and AI search optimization. You want to provide helpful accurate information to the consumer. Provide accurate, detailed information in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500  # Reduced for cost efficiency
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content
            # Extract JSON from the response (in case there's extra text)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
                
        except Exception as e:
            print(f"Error getting OpenAI research for {product.title}: {e}")
            return {}
    
    def generate_openai_description(self, product: Product, research_data: Dict, community_data: Dict) -> str:
        """Use OpenAI to generate the final optimized description"""
        try:
            current_desc = self.extract_text_description(product.body_html)
            
            if self.is_perfume(product):
                prompt = f"""
You are creating a product description for {product.title}. You MUST use the research data and community data provided below to fill in the sections.

RESEARCH DATA (use this data):
{json.dumps(research_data, indent=2)}

COMMUNITY DATA (use this data):
{json.dumps(community_data, indent=2)}

AVAILABLE DATA FIELDS:
- Research data contains: {list(research_data.keys()) if research_data else 'No research data'}
- Community data contains: {list(community_data.keys()) if community_data else 'No community data'}

Create the description in this EXACT format, filling in the brackets with real data from the research and community data above:

<div class="product-description">
    <h2>{product.title}</h2>
    
    <p><strong>Spiritual. Smoky. Sacred.</strong> [Write a compelling opening paragraph using the research data]</p>

    <h3>Fragrance Notes</h3>
    <ul>
        <li><strong>Top:</strong> [Use the top_notes from research data]</li>
        <li><strong>Heart:</strong> [Use the middle_notes from research data]</li>
        <li><strong>Base:</strong> [Use the base_notes from research data]</li>
    </ul>

    <h3>Product Characteristics</h3>
    <ul>
        <li><strong>Longevity:</strong> [Use the longevity from research data]</li>
        <li><strong>Sillage:</strong> [Use the sillage from research data]</li>
        <li><strong>Best Seasons:</strong> [Use the seasons from research data]</li>
        <li><strong>Unisex:</strong> [Use the target_audience from research data]</li>
        <li><strong>Vibe:</strong> [Use the unique_features from research data]</li>
    </ul>

    <h3>Reddit & Community Tips</h3>
    <ul>
        <li>[Use the first Reddit quote from community_data['reddit'] if available - these are formatted as "quote" - u/username (X upvotes)]</li>
        <li>[Use the second Reddit quote if available]</li>
        <li>[Use the usage_tips from research_data if available]</li>
    </ul>

    <h3>Who It's For</h3>
    <p>[Use the target_audience from research data to write this section]</p>

    <h3>Product Features</h3>
    <ul>
        <li>[Use the benefits from research data]</li>
        <li>[Use the features from research data]</li>
    </ul>

    <h3>How to Use</h3>
    <p>[Use the usage_instructions from research data]</p>

    <div class="schema-markup" style="display: none;">
        <script type="application/ld+json">
        {{
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "{product.title}",
            "brand": {{
                "@type": "Brand",
                "name": "{product.vendor}"
            }},
            "description": "[extract key description from research data]",
            "sku": "{product.sku}",
            "image": "{product.image_src}",
            "offers": {{
                "@type": "Offer",
                "price": "{product.price}",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
                "url": "https://wehitpan.com/products/{product.handle}"
            }}
        }}
        </script>
    </div>
</div>

CRITICAL: You MUST replace the [bracketed text] with actual data from the JSON objects above. Do not leave brackets empty. If data is not available, write "Information not available" or skip that section entirely.
"""
            else:
                prompt = f"""
Create a product description for this non-perfume product that will help it appear in ChatGPT shopping and AI search results.

Product: {product.title}
Brand: {product.vendor}
Current Description: {current_desc[:300]}
Price: ${product.price}

Research Data: {json.dumps(research_data, indent=2)}
Community Data: {json.dumps(community_data, indent=2)}

Create an HTML description that includes:
1. Compelling product overview that starts with what the product does
2. Key features and benefits section
3. How to use section
4. Target audience section
5. FAQ section with the provided questions and answers
6. Use cases and applications
7. Schema.org structured data markup (hidden)

Requirements:
- Write in natural, conversational language like speaking to a curious shopper
- Include Schema.org markup for Product, Offer, and AggregateRating
- Make it descriptive and benefit-driven
- Avoid keyword stuffing
- Include unique use cases and key differentiators
- Use customer questions as headers where appropriate
- Optimize for AI search and ChatGPT shopping visibility
- Focus specifically on this product, not generic content
- Do NOT use emojis or special characters

Format the response as clean HTML with proper structure and styling.
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-2024-11-20",  # Latest free tier model - best for product descriptions
                messages=[
                    {"role": "system", "content": "You are an expert e-commerce copywriter specializing in AI-optimized product descriptions. Create compelling, natural content that ranks well in AI search and appears in ChatGPT shopping. Always focus on the specific product provided. Do NOT use emojis or special characters - keep the content clean and professional."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2000  # Reduced for cost efficiency
            )
            
            # Clean the generated content to remove emojis and fix encoding issues
            cleaned_content = self.clean_html_content(response.choices[0].message.content)
            
            return cleaned_content
            
        except Exception as e:
            print(f"Error generating OpenAI description for {product.title}: {e}")
            return self.generate_fallback_description(product)
    
    def generate_fallback_description(self, product: Product) -> str:
        """Generate a fallback description if OpenAI fails"""
        current_desc = self.extract_text_description(product.body_html)
        
        return f"""
<div class="product-description">
    <h2>{product.title}</h2>
    
    <div class="product-overview">
        <p><strong>What it does:</strong> {current_desc[:200]}...</p>
    </div>
    
    <div class="benefits">
        <h3>Key Benefits</h3>
        <ul>
            <li>High-quality product from {product.vendor}</li>
            <li>Trusted brand with proven effectiveness</li>
            <li>Perfect for your needs</li>
        </ul>
    </div>
    
    <div class="usage">
        <h3>How to Use</h3>
        <p>Follow the manufacturer's instructions for best results.</p>
    </div>
    
    <div class="target-audience">
        <h3>Perfect For</h3>
        <ul>
            <li>Anyone looking for a high-quality product</li>
            <li>Those who appreciate attention to detail</li>
        </ul>
    </div>
    
    <div class="schema-markup" style="display: none;">
        <script type="application/ld+json">
        {{
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "{product.title}",
            "brand": {{
                "@type": "Brand",
                "name": "{product.vendor}"
            }},
            "description": "{current_desc[:200]}",
            "sku": "{product.sku}",
            "image": "{product.image_src}",
            "offers": {{
                "@type": "Offer",
                "price": "{product.price}",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
                "url": "https://wehitpan.com/products/{product.handle}"
            }}
        }}
        </script>
    </div>
</div>
        """
    
    def update_product_descriptions(self):
        """Update only unique product descriptions using OpenAI, cache by handle"""
        print("Updating product descriptions with OpenAI...")
        print(f"Starting with {len(self.updated_products)} products already processed")
        
        for i, product in enumerate(self.products):
            print(f"Processing {i+1}/{len(self.products)}: {product.title}")
            
            # Only process each handle once
            if product.handle in self.updated_products:
                print(f"  Skipping {product.title} - already processed")
                continue
            
            try:
                # Gather community data for perfumes
                community_data = {}
                if self.is_perfume(product):
                    print(f"  Gathering community data for perfume...")
                    community_data['reddit'] = self.search_reddit_fragrance(product.title, product.vendor)
                    print(f"  Community data gathered: {len(community_data.get('reddit', []))} Reddit items")
                    time.sleep(1)  # Be respectful to external APIs
                
                research_data = self.get_openai_product_research(product)
                print(f"  Research data gathered: {len(research_data)} items")
                if research_data:
                    print(f"  Research data keys: {list(research_data.keys())}")
                
                optimized_html = self.generate_openai_description(product, research_data, community_data)
                self.updated_products[product.handle] = optimized_html
                self.processed_handles.add(product.handle)
                
                # Save progress after each product
                self.save_progress()
                
                print(f"  ✓ Completed {product.title}")
                time.sleep(2)  # Respect API rate limits
                
            except Exception as e:
                print(f"  ✗ Error processing {product.title}: {e}")
                # Continue with next product instead of stopping
                continue
        
        print(f"\nCompleted processing. Total products updated: {len(self.updated_products)}")
    
    def write_updated_csv(self, output_file: str):
        """Write updated products to a new CSV file, updating only Body (HTML) for unique product rows"""
        print(f"Writing updated CSV to {output_file}...")
        with open(self.csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, quoting=csv.QUOTE_ALL)
            fieldnames = reader.fieldnames
        with open(self.csv_file_path, 'r', encoding='utf-8') as input_file, \
             open(output_file, 'w', encoding='utf-8', newline='') as output_file:
            reader = csv.DictReader(input_file, quoting=csv.QUOTE_ALL)
            writer = csv.DictWriter(output_file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for row in reader:
                handle = row.get('Handle', '').strip()
                title = row.get('Title', '').strip()
                body_html = row.get('Body (HTML)', '').strip()
                # Only update if this is a unique product row
                if handle in self.updated_products and title and body_html:
                    row['Body (HTML)'] = self.updated_products[handle]
                writer.writerow(row)
        print(f"Updated CSV saved to {output_file}")

    def clean_html_content(self, html_content: str) -> str:
        """Clean HTML content by removing emojis, markdown formatting, and fixing encoding issues"""
        import re
        
        # Remove markdown code blocks and HTML tags that shouldn't be there
        cleaned_content = html_content
        
        # Remove markdown code blocks
        cleaned_content = re.sub(r'```html\s*', '', cleaned_content)
        cleaned_content = re.sub(r'```\s*', '', cleaned_content)
        
        # Remove DOCTYPE and html/head/body tags if they exist
        cleaned_content = re.sub(r'<!DOCTYPE html>.*?<body>', '', cleaned_content, flags=re.DOTALL)
        cleaned_content = re.sub(r'</body>.*?</html>', '', cleaned_content, flags=re.DOTALL)
        cleaned_content = re.sub(r'<html.*?>', '', cleaned_content, flags=re.DOTALL)
        cleaned_content = re.sub(r'</html>', '', cleaned_content)
        cleaned_content = re.sub(r'<head>.*?</head>', '', cleaned_content, flags=re.DOTALL)
        cleaned_content = re.sub(r'<body>', '', cleaned_content)
        cleaned_content = re.sub(r'</body>', '', cleaned_content)
        
        # Remove emojis and special characters that cause encoding issues
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"  # enclosed characters
            "]+", flags=re.UNICODE
        )
        
        # Remove emojis
        cleaned_content = emoji_pattern.sub('', cleaned_content)
        
        # Fix common encoding issues
        cleaned_content = cleaned_content.replace('Äô', "'")
        cleaned_content = cleaned_content.replace('Äù', '"')
        cleaned_content = cleaned_content.replace('Äú', '"')
        cleaned_content = cleaned_content.replace('Äì', '-')
        cleaned_content = cleaned_content.replace('Äî', '—')
        cleaned_content = cleaned_content.replace('Äö', '✓')
        cleaned_content = cleaned_content.replace('úà', '♥')
        cleaned_content = cleaned_content.replace('Ô∏è', '')
        cleaned_content = cleaned_content.replace('üåø', '')
        cleaned_content = cleaned_content.replace('üéâ', '')
        cleaned_content = cleaned_content.replace('üåü', '')
        cleaned_content = cleaned_content.replace('‚Äô', "'")
        cleaned_content = cleaned_content.replace('‚Äù', '"')
        cleaned_content = cleaned_content.replace('‚Äú', '"')
        cleaned_content = cleaned_content.replace('‚Äì', '-')
        cleaned_content = cleaned_content.replace('‚Äî', '—')
        
        # Remove any remaining weird characters
        cleaned_content = re.sub(r'[^\x00-\x7F\u00A0-\uFFFF]', '', cleaned_content)
        
        # Clean up extra whitespace
        cleaned_content = re.sub(r'\n\s*\n', '\n\n', cleaned_content)
        cleaned_content = cleaned_content.strip()
        
        return cleaned_content
    
    def search_reddit_fragrance(self, product_name: str, brand: str) -> List[Dict]:
        """Search Reddit r/fragrance for community discussions with upvotes"""
        try:
            # Clean product name
            clean_product_name = product_name.replace(' - 2 Pack ($25 value)', '').replace(' – 2 Pack ($27 value)', '').replace(' (Limited Release)', '')
            
            # Try multiple search strategies
            search_queries = []
            
            # Avoid duplication if brand is already in product name
            if brand.lower() in clean_product_name.lower():
                search_queries = [
                    clean_product_name,
                    f'"{clean_product_name}"',
                    clean_product_name.replace('-', ' ').replace('_', ' ')
                ]
            else:
                search_queries = [
                    f"{brand} {clean_product_name}",
                    f"{clean_product_name} {brand}",
                    f'"{brand}" "{clean_product_name}"',
                    clean_product_name.replace('-', ' ').replace('_', ' '),
                    brand
                ]
            
            all_quotes = []
            
            for search_query in search_queries:
                print(f"  Searching Reddit for: {search_query}")
                
                # Try Reddit API search
                search_url = "https://www.reddit.com/r/fragrance/search.json"
                params = {
                    'q': search_query,
                    'restrict_sr': 'on',
                    'sort': 'top',  # Sort by top to get most upvoted
                    't': 'year',    # Last year for better relevance
                    'limit': 10
                }
                
                response = self.session.get(search_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for post in posts:
                        post_data = post.get('data', {})
                        title = post_data.get('title', '')
                        selftext = post_data.get('selftext', '')
                        upvotes = post_data.get('ups', 0)
                        url = post_data.get('url', '')
                        author = post_data.get('author', '')
                        
                        # Only include posts with significant upvotes
                        if upvotes >= 5:
                            quote_data = {
                                'text': '',
                                'upvotes': upvotes,
                                'author': author,
                                'url': url,
                                'type': 'post'
                            }
                            
                            # Extract meaningful content
                            if title and len(title) > 20:
                                quote_data['text'] = title
                                all_quotes.append(quote_data)
                            
                            if selftext and len(selftext) > 50:
                                # Extract the most meaningful sentence
                                sentences = re.split(r'[.!?]', selftext)
                                meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 30 and len(s.strip()) < 200]
                                if meaningful_sentences:
                                    quote_data['text'] = meaningful_sentences[0]
                                    all_quotes.append(quote_data)
                
                # Also try r/fragrance subreddit directly
                subreddit_url = f"https://www.reddit.com/r/fragrance.json"
                response = self.session.get(subreddit_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for post in posts:
                        post_data = post.get('data', {})
                        title = post_data.get('title', '')
                        selftext = post_data.get('selftext', '')
                        upvotes = post_data.get('ups', 0)
                        
                        # Check if post mentions our product
                        search_terms = [brand.lower(), clean_product_name.lower().replace('-', ' ')]
                        if any(term in title.lower() or term in selftext.lower() for term in search_terms):
                            if upvotes >= 3:
                                quote_data = {
                                    'text': title if len(title) > 20 else selftext[:150] + "..." if len(selftext) > 150 else selftext,
                                    'upvotes': upvotes,
                                    'author': post_data.get('author', ''),
                                    'url': post_data.get('url', ''),
                                    'type': 'subreddit'
                                }
                                all_quotes.append(quote_data)
                
                # Limit to avoid too many requests
                if len(all_quotes) >= 5:
                    break
                
                time.sleep(1)  # Be respectful to Reddit API
            
            # Sort by upvotes and return top quotes
            all_quotes.sort(key=lambda x: x['upvotes'], reverse=True)
            
            # Format quotes for display
            formatted_quotes = []
            for quote in all_quotes[:5]:  # Top 5 quotes
                if quote['text']:
                    formatted_text = f"\"{quote['text']}\" - u/{quote['author']} ({quote['upvotes']} upvotes)"
                    formatted_quotes.append(formatted_text)
            
            print(f"  Found {len(formatted_quotes)} Reddit quotes with upvotes")
            return formatted_quotes
            
        except Exception as e:
            print(f"  Error searching Reddit: {e}")
            return []

def main():
    """Main function to run the OpenAI-enhanced product description updater"""
    csv_file = "products_export_June_25_2025.csv"
    output_file = "products_export_openai_enhanced.csv"
    
    # OpenAI API key - use environment variable or placeholder
    openai_api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
    
    if openai_api_key == "YOUR_OPENAI_API_KEY_HERE":
        print("Error: Please set your OpenAI API key as an environment variable:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return 1
    
    updater = OpenAIEnhancedUpdater(csv_file, openai_api_key)
    
    try:
        # Read the CSV
        updater.read_csv()
        
        # Update descriptions with OpenAI
        updater.update_product_descriptions()
        
        # Write updated CSV
        updater.write_updated_csv(output_file)
        
        print("OpenAI-enhanced product description update completed successfully!")
        print(f"Original file: {csv_file}")
        print(f"Updated file: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 