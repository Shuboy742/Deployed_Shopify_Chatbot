import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import re
import threading

load_dotenv()

SHOP_NAME = "ecommerce-test-store-demo"
SHOP_URL = f"https://ecommerce-test-store-demo.myshopify.com"
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_API_KEY")
products_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shopify_products.json')
full_export_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shopify_full_export.json')

# Store currency (will be fetched from Shopify)
STORE_CURRENCY = "USD"  # Default fallback

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# Directory to store chat histories
CHAT_HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_histories')
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

# Thread lock for file safety
chat_history_lock = threading.Lock()

def get_chat_history(user_id):
    """Load chat history for a user from file."""
    path = os.path.join(CHAT_HISTORY_DIR, f"{user_id}.json")
    if not os.path.exists(path):
        return []
    with chat_history_lock:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return []

def save_chat_history(user_id, history):
    """Save chat history for a user to file."""
    path = os.path.join(CHAT_HISTORY_DIR, f"{user_id}.json")
    with chat_history_lock:
        with open(path, 'w') as f:
            json.dump(history, f, indent=2)

def load_products_from_disk():
    """Load product data, preferring shopify_full_export.json if present.
    Returns a list of product objects compatible with existing helpers.
    """
    # Try full export first
    try:
        if os.path.exists(full_export_file):
            with open(full_export_file, 'r') as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get('products'), list):
                return data['products']
            if isinstance(data, list):
                return data
    except Exception:
        pass
    # Fallback to products_file
    try:
        if os.path.exists(products_file):
            with open(products_file, 'r') as f:
                data = json.load(f)
            # Legacy file is usually a list already
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and isinstance(data.get('products'), list):
                return data['products']
    except Exception:
        pass
    return []

def fetch_store_currency():
    """Fetch the store's currency from Shopify API"""
    global STORE_CURRENCY
    if not SHOPIFY_ACCESS_TOKEN:
        print("Warning: SHOPIFY_ACCESS_TOKEN not set. Using default currency.")
        return STORE_CURRENCY
    
    try:
        url = f"https://{SHOP_NAME}.myshopify.com/admin/api/2023-01/shop.json"
        headers = {
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        shop_data = response.json().get('shop', {})
        currency = shop_data.get('currency', STORE_CURRENCY)
        STORE_CURRENCY = currency
        print(f"Store currency: {currency}")
        return currency
    except Exception as e:
        print(f"Error fetching store currency: {e}")
        return STORE_CURRENCY

def get_currency_symbol(currency_code):
    """Get currency symbol from currency code"""
    currency_symbols = {
        'USD': 'USD',
        'INR': '₹',
        'EUR': '€',
        'GBP': '£',
        'CAD': 'CAD',
        'AUD': 'AUD',
        'JPY': '¥',
        'CNY': '¥',
        'KRW': '₩',
        'RUB': '₽',
        'BRL': 'BRL',
        'MXN': 'MXN',
        'SGD': 'SGD',
        'HKD': 'HKD',
        'NZD': 'NZD',
        'CHF': 'CHF',
        'SEK': 'kr',
        'NOK': 'kr',
        'DKK': 'kr',
        'PLN': 'zł',
        'CZK': 'Kč',
        'HUF': 'Ft',
        'ILS': '₪',
        'TRY': '₺',
        'ZAR': 'R',
        'THB': '฿',
        'MYR': 'RM',
        'PHP': '₱',
        'IDR': 'Rp',
        'VND': '₫'
    }
    return currency_symbols.get(currency_code, currency_code)

def extract_colors_from_product(product):
    """Extract colors directly from product JSON structure"""
    colors = []
    
    # Method 1: Get colors from product options where name is "Color"
    for option in product.get('options', []):
        if option.get('name', '').lower() == 'color':
            colors.extend(option.get('values', []))
    
    # Method 2: Get colors from variants option1 (if not already found)
    if not colors:
        for variant in product.get('variants', []):
            option1 = variant.get('option1')
            if option1 and option1.lower() != 'default title':
                colors.append(option1)
    
    # Filter out currency values and other non-color strings
    filtered_colors = []
    for color in colors:
        # Skip if it contains currency symbols or looks like a price
        if (not re.search(r'[\$€£¥₹₽₩₪₺₫₱₿]', color) and  # No currency symbols
            not re.search(r'\d+\.?\d*', color) and  # No numbers (prices)
            not color.lower() in ['default', 'default title', 'title'] and  # No default values
            len(color.strip()) > 0):  # Not empty
            filtered_colors.append(color)
    
    # Remove duplicates and return
    return list(set(filtered_colors))

def _normalize_text(value):
    try:
        return (value or "").lower()
    except Exception:
        return ""

def _extract_price_range(query: str):
    """Very light heuristic to detect min/max price from free text, returns (min_price,max_price) or (None,None)."""
    q = query.replace(',', ' ')
    nums = [float(x) for x in re.findall(r"\d+\.?\d*", q)]
    if not nums:
        return (None, None)
    if len(nums) == 1:
        # Single number – treat as max
        return (None, nums[0])
    # Multiple numbers – min/max of them
    return (min(nums), max(nums))

def score_product_relevance(query: str, product: dict) -> float:
    """Compute a simple relevance score using keyword overlap, colors, vendor, tags, product_type, and rough price range."""
    score = 0.0
    q = _normalize_text(query)
    words = [w for w in re.findall(r"\w+", q) if len(w) > 2]
    title = _normalize_text(product.get('title'))
    vendor = _normalize_text(product.get('vendor'))
    tags = _normalize_text(product.get('tags'))
    ptype = _normalize_text(product.get('product_type'))
    body = _normalize_text(product.get('body_html'))
    colors = [c.lower() for c in extract_colors_from_product(product)]

    # Keyword matches
    for w in words:
        if w in title:
            score += 5
        if w in vendor:
            score += 2
        if w in tags:
            score += 2
        if w in ptype:
            score += 1.5
        if w in body:
            score += 1

    # Color boosts
    for c in colors:
        if c and c in q:
            score += 6

    # Price range hint
    v = (product.get('variants') or [{}])[0]
    price = v.get('price')
    try:
        price_val = float(str(price)) if price is not None else None
    except Exception:
        price_val = None
    pmin, pmax = _extract_price_range(q)
    if price_val is not None and (pmin is not None or pmax is not None):
        if pmin is not None and price_val < pmin:
            score -= 2
        if pmax is not None and price_val > pmax:
            score -= 2
        if (pmin is None or price_val >= pmin) and (pmax is None or price_val <= pmax):
            score += 4

    return score

def select_top_k_products(query: str, products: list, k: int = 12) -> list:
    if not products:
        return []
    scored = [(score_product_relevance(query, p), p) for p in products]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:k]]

def fetch_latest_products():
    if not SHOPIFY_ACCESS_TOKEN:
        print("Warning: SHOPIFY_ACCESS_TOKEN not set. Using cached data.")
        return []
    try:
        # Fetch store currency first
        fetch_store_currency()
        
        url = f"https://{SHOP_NAME}.myshopify.com/admin/api/2023-01/products.json"
        headers = {
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        products_data = response.json().get('products', [])
        with open(products_file, 'w') as f:
            json.dump(products_data, f, indent=2)
        print(f"Fetched {len(products_data)} products from Shopify (webhook)")
        return products_data
    except Exception as e:
        print(f"Error fetching products from Shopify: {e}")
        return []

def find_products_by_color(query, products):
    """Find products that have the specified color based on JSON data"""
    query_lower = query.lower()
    matching_products = []
    
    for product in products:
        product_colors = extract_colors_from_product(product)
        product_colors_lower = [color.lower() for color in product_colors]
        
        # Check if query color matches any product color
        if query_lower in product_colors_lower:
            matching_products.append(product)
    
    return matching_products

def find_product_by_name(product_name, products):
    """Find a specific product by name"""
    product_name_lower = product_name.lower()
    
    for product in products:
        title = product.get('title', '').lower()
        if product_name_lower in title or title in product_name_lower:
            return product
    return None

def get_product_colors(product):
    """Get colors for a specific product"""
    if not product:
        return []
    
    colors = extract_colors_from_product(product)
    return colors

def find_products_by_keyword(query, products):
    """Find products that match the query keywords"""
    query_lower = query.lower()
    keywords = [w for w in query_lower.split() if len(w) > 2]
    matches = []
    
    # First, try exact product name matching (most specific)
    for product in products:
        title = product.get('title', '').lower()
        # Check if the query contains the exact product title or vice versa
        if title in query_lower or query_lower in title:
            matches.append(product)
            return matches  # Return immediately for exact match
    
    # If no exact match, try partial title matching
    for product in products:
        title = product.get('title', '').lower()
        # Check if any keyword is in the product title
        if any(keyword in title for keyword in keywords):
            matches.append(product)
    
    # If still no matches, try broader matching
    if not matches:
        for product in products:
            title = product.get('title', '').lower()
            tags = product.get('tags', '').lower()
            vendor = product.get('vendor', '').lower()
            product_type = product.get('product_type', '').lower()
            body_html = (product.get('body_html') or '').lower()
            
            if any(k in title or k in tags or k in vendor or k in product_type or k in body_html for k in keywords):
                matches.append(product)
    
    return matches

def extract_products_in_text(text: str, products: list) -> list:
    """Return products whose titles appear in the given text (case-insensitive)."""
    if not text:
        return []
    t = text.lower()
    hits = []
    seen = set()
    for p in products:
        title = (p.get('title') or '').strip()
        if not title:
            continue
        if title.lower() in t and title not in seen:
            hits.append(p)
            seen.add(title)
    return hits

def get_all_available_colors(products):
    """Get all available colors from the product data"""
    all_colors = set()
    
    for product in products:
        colors = extract_colors_from_product(product)
        all_colors.update(colors)
    
    return sorted(list(all_colors))

def find_matching_products(query, products):
    query = query.lower()
    keywords = [w for w in query.split() if len(w) > 2]
    matches = []
    
    # Get all available colors from the data
    all_colors = get_all_available_colors(products)
    all_colors_lower = [color.lower() for color in all_colors]
    
    # Check if query contains any available color
    query_has_colors = any(color in query for color in all_colors_lower)
    
    if query_has_colors:
        # Find products with the specific color
        for color in all_colors:
            if color.lower() in query:
                color_products = find_products_by_color(color, products)
                matches.extend(color_products)
    else:
        # Use the new helper function for keyword matching
        matches = find_products_by_keyword(query, products)
    
    # Remove duplicates
    seen_ids = set()
    unique_matches = []
    for product in matches:
        if product.get('id') not in seen_ids:
            seen_ids.add(product.get('id'))
            unique_matches.append(product)
    
    return unique_matches

def generate_product_link(product):
    """Generate the product URL"""
    handle = product.get('handle', '')
    if handle:
        return f"{SHOP_URL}/products/{handle}"
    return None

def format_product_card(product):
    title = product.get('title', 'Unnamed Product')
    variant = product.get('variants', [{}])[0]
    price = variant.get('price', 'N/A')
    compare_at_price = variant.get('compare_at_price')
    desc = (product.get('body_html') or product.get('product_type', '') or '').strip()
    desc = desc[:90] + ('...' if len(desc) > 90 else '') if desc else 'No description available.'
    tags = product.get('tags', '')
    vendor = product.get('vendor', 'Unknown Vendor')
    
    # Get colors directly from JSON data
    colors = extract_colors_from_product(product)
    color_display = ', '.join(colors) if colors else 'No color options'
    
    link = generate_product_link(product)
    
    # Format price with correct currency and show discount if available
    currency_symbol = get_currency_symbol(STORE_CURRENCY)
    formatted_price = f"{currency_symbol}{price}" if price != 'N/A' else 'N/A'
    discount_line = ''
    try:
        if price not in (None, 'N/A') and compare_at_price:
            p = float(str(price))
            cap = float(str(compare_at_price))
            if cap > p:
                percent = int(round((cap - p) / cap * 100))
                discount_line = f" (was {currency_symbol}{cap}, {percent}% off)"
    except Exception:
        pass
    
    card = f"🛍️ **{title}**\n"
    card += f"💰 Price: {formatted_price}{discount_line}\n"
    card += f"📄 {desc}\n"
    if tags:
        card += f"🏷️ Tags: {tags}\n"
    card += f"🎨 Available colors: {color_display}\n"
    card += f"🏢 Vendor: {vendor}\n"
    if link:
        card += f"🔗 [View Product]({link})"
    return card

def generate_chatbot_response(query, products, memory=None):
    query_lower = query.lower()
    
    # Get all available colors from the data
    all_colors = get_all_available_colors(products)
    all_colors_lower = [color.lower() for color in all_colors]
    
    # Check if query mentions colors
    query_has_colors = any(color in query_lower for color in all_colors_lower)
    query_mentions_color = any(word in query_lower for word in ['color', 'colour', 'coor', 'colors', 'colours'])
    
    # Greetings
    if any(word in query_lower for word in ['hello', 'hi', 'hey']):
        return "👋 Hello! How can I assist you with our products?"
    
    # Product-specific color queries (e.g., "snowboard color options", "complete snowboard colors")
    if query_mentions_color and not query_has_colors:
        # Look for product names in the query
        product_matches = find_products_by_keyword(query, products)
        
        if product_matches:
            # User is asking about colors for specific products
            if len(product_matches) == 1:
                # Single product match - give specific response
                product = product_matches[0]
                product_colors = get_product_colors(product)
                if product_colors:
                    color_list = ', '.join(product_colors)
                    return f"🎨 **{product.get('title', 'Product')}** available colors: {color_list}"
                else:
                    return f"🎨 **{product.get('title', 'Product')}**: Color not available for this product."
            else:
                # Multiple products matched - ask user to be more specific
                product_names = [p.get('title', 'Product') for p in product_matches]
                product_list = ', '.join(product_names)
                return f"🤔 I found multiple products: {product_list}\n\nPlease be more specific. For example:\n• 'What colors does the complete snowboard come in?'\n• 'Show me the draft snowboard colors'"
        
        # If no specific product found, ask user to be more specific
        return "🤔 I couldn't find a specific product in your query. Please ask about a specific product like:\n• 'What colors does the complete snowboard come in?'\n• 'Show me snowboard color options'\n• 'What are the colors for the gift card?'"
    
    # Specific color queries (e.g., "show me ice color products")
    elif query_has_colors:
        matches = find_matching_products(query, products)
        if matches:
            return '\n\n'.join([format_product_card(p) for p in matches])
        else:
            return "Sorry, I couldn't find any products in that color. Try asking about available colors for specific products."
    
    # Show all products
    if 'all products' in query_lower or 'show me' in query_lower or 'list' in query_lower or 'products' in query_lower:
        if not products:
            return "No products found."
        return '\n\n'.join([format_product_card(p) for p in products])
    
    # Price query
    if 'price' in query_lower or 'cost' in query_lower or 'how much' in query_lower:
        matches = find_matching_products(query, products)
        if matches:
            return '\n\n'.join([format_product_card(p) for p in matches])
        else:
            return "Sorry, I couldn't find any product related to that."

    # Discounts / offers / sales
    if any(word in query_lower for word in ['discount', 'offer', 'offers', 'sale', 'deal', 'promotion', 'promo', 'coupon']):
        discounted = []
        for p in products:
            try:
                v = p.get('variants', [{}])[0]
                price = v.get('price')
                compare_at = v.get('compare_at_price')
                if price is not None and compare_at is not None:
                    p_val = float(str(price))
                    cap_val = float(str(compare_at))
                    if cap_val > p_val:
                        discounted.append(p)
            except Exception:
                continue
        if discounted:
            return '\n\n'.join([format_product_card(p) for p in discounted])
        else:
            return "No discounted products right now. Please check again later."
    
    # Vendor
    if 'vendor' in query_lower or 'brand' in query_lower:
        matches = find_matching_products(query, products)
        if matches:
            return '\n\n'.join([format_product_card(p) for p in matches])
        else:
            return "Sorry, I couldn't find any product related to that."
    
    # Tag
    if 'tag' in query_lower:
        matches = find_matching_products(query, products)
        if matches:
            return '\n\n'.join([format_product_card(p) for p in matches])
        else:
            return "Sorry, I couldn't find any product related to that."
    
    # Link to buy
    if 'buy' in query_lower or 'link' in query_lower or 'purchase' in query_lower or 'url' in query_lower:
        matches = find_matching_products(query, products)
        if matches:
            return '\n'.join([f"🔗 {generate_product_link(p)}" for p in matches])
        else:
            return "No matching product found to provide a link."
    
    # Shipping
    if 'shipping' in query_lower or 'delivery' in query_lower:
        return "🚚 We offer delivery on all products. Specific charges and timeframes may vary."
    
    # Name/title
    if 'name' in query_lower or 'title' in query_lower:
        matches = find_matching_products(query, products)
        if matches:
            return '\n\n'.join([format_product_card(p) for p in matches])
        else:
            return "Sorry, I couldn't find any product related to that."
    
    # Default: show a short summary
    matches = find_matching_products(query, products)
    if matches:
        return '\n\n'.join([format_product_card(p) for p in matches])
    return "🤖 I'm here to help with product details, pricing, or availability. Try asking something like: 'Show me snowboards' or 'Price of Gift Card' or 'Show me Ice color snowboards' or 'What colors are available?'"

# Helper to format product data for the prompt

def format_product_data_for_prompt(products):
    entries = []
    currency_symbol = get_currency_symbol(STORE_CURRENCY)
    for product in products:
        variant = (product.get("variants") or [{}])[0]
        price = variant.get("price")
        compare_at = variant.get("compare_at_price")
        discount_pct = None
        try:
            if price is not None and compare_at:
                p_val = float(str(price))
                cap_val = float(str(compare_at))
                if cap_val > p_val:
                    discount_pct = int(round((cap_val - p_val) / cap_val * 100))
        except Exception:
            pass

        colors = extract_colors_from_product(product)
        entry = {
            "title": product.get("title", ""),
            "vendor": product.get("vendor", ""),
            "tags": product.get("tags", ""),
            "collection_titles": [c.get("title") for c in product.get("collections", [])] if product.get("collections") else [],
            "price": f"{currency_symbol}{price}" if price else "",
            "compare_at": f"{currency_symbol}{compare_at}" if compare_at else "",
            "discount_pct": discount_pct,
            "colors": colors,
            "url": generate_product_link(product) or "",
            "description": (product.get("body_html") or product.get("product_type", ""))[:180]
        }
        entries.append(entry)
    return json.dumps(entries, indent=2)

# Gemini 2.0 Flash Request Function

def query_gemini(user_query, context, temperature: float = 0.3):
    # If key is missing, signal caller to fallback
    if not GEMINI_API_KEY:
        return ""
    headers = {
        "Content-Type": "application/json"
    }
    prompt = f"""
You are a helpful ecommerce assistant for a Shopify store.
Rules:
- Answer crisply in natural, human language (2–4 short sentences or a tiny list).
- Use information ONLY from the catalog context provided.
- When mentioning a product, include its current price; mention discounts only if available.
- Prefer the best 1–3 matches, not long lists.
- If colors are asked, list available colors succinctly.

Product Catalog (JSON):
{context}

User Question:
{user_query}

Answer:
"""
    body = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "topK": 32,
            "topP": 0.9,
            "maxOutputTokens": 512
        }
    }
    try:
        res = requests.post(GEMINI_API_URL, headers=headers, json=body)
        res.raise_for_status()
        reply = res.json()['candidates'][0]['content']['parts'][0]['text']
        return reply
    except Exception as e:
        print("Gemini API Error:", e)
        return ""

def rewrite_with_gemini(text: str) -> str:
    """Use Gemini to crispen/shorten a draft answer if API is available; otherwise return original."""
    if not GEMINI_API_KEY or not text:
        return text
    prompt = f"""
Rewrite the following answer to be crisp, human, and at most 3 short sentences. Keep prices/discounts intact and include links if present.

Answer:
{text}
"""
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 256}
    }
    try:
        res = requests.post(GEMINI_API_URL, headers=headers, json=body)
        res.raise_for_status()
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("Gemini rewrite Error:", e)
        return text

app = Flask(__name__)

# Lock CORS to your Shopify store (override via ALLOWED_ORIGIN env if needed)
ALLOWED_ORIGIN = os.getenv('ALLOWED_ORIGIN', 'https://ecommerce-test-store-demo.myshopify.com')
CORS(
    app,
    resources={
        r"/chat": {"origins": [ALLOWED_ORIGIN]},
        r"/history": {"origins": [ALLOWED_ORIGIN]},
        r"/webhook/*": {"origins": "*"}
    },
    supports_credentials=False
)

@app.after_request
def add_cors_headers(response):
    # Ensure headers are always present (including preflight 204)
    response.headers.setdefault('Access-Control-Allow-Origin', ALLOWED_ORIGIN)
    response.headers.setdefault('Vary', 'Origin')
    response.headers.setdefault('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.setdefault('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.setdefault('Access-Control-Max-Age', '3600')
    return response

# Silence favicon 404s
@app.route('/favicon.ico')
def _favicon():
    return ('', 204)

@app.route('/webhook/products', methods=['POST'])
def shopify_webhook():
    try:
        print("Webhook received, about to fetch products")
        latest_products = fetch_latest_products()
        print("Fetched and wrote products:", len(latest_products))
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500

# Update chat endpoint to use Gemini
@app.route('/chat', methods=['OPTIONS', 'POST'])
def chat():
    try:
        # Handle CORS preflight
        if request.method == 'OPTIONS':
            return ('', 204)
        products_latest = load_products_from_disk()
        data = request.get_json(silent=True)
        user_query = data.get('message', '') if data else ''
        user_id = data.get('user_id', 'default_user') if data else 'default_user'
        if not user_query:
            return jsonify({'error': 'No message provided'}), 400

        # Load chat history
        chat_history = get_chat_history(user_id)
        # Append new user message
        chat_history.append({'role': 'user', 'message': user_query})

        # Check if this is a color-related query
        query_lower = user_query.lower()
        color_keywords = [
            'black', 'white', 'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 
            'brown', 'gray', 'grey', 'silver', 'gold', 'navy', 'maroon', 'olive', 'teal',
            'cyan', 'magenta', 'lime', 'indigo', 'violet', 'coral', 'salmon', 'turquoise',
            'beige', 'cream', 'ivory', 'charcoal', 'burgundy', 'emerald', 'sapphire', 'ruby',
            'amber', 'bronze', 'copper', 'platinum', 'rose', 'lavender', 'mint', 'peach',
            'ice', 'dawn', 'powder', 'electric', 'sunset', 'hydrogen', 'liquid', 'brew'
        ]
        query_has_colors = any(color in query_lower for color in color_keywords)
        query_mentions_color = any(word in query_lower for word in ['color', 'colour', 'coor', 'colors', 'colours'])

        # Infer focus products from the last bot message to support pronouns like "it/this/that"
        focus_products = []
        if chat_history:
            for past in reversed(chat_history):
                if past.get('role') == 'bot':
                    focus_products = extract_products_in_text(past.get('message', ''), products_latest)
                    if focus_products:
                        break

        # Use Gemini (with top-K product selection) as primary, with local fallback
        if query_has_colors or query_mentions_color:
            context_messages = []
            for msg in chat_history[-10:]:
                prefix = 'User:' if msg['role'] == 'user' else 'Bot:'
                context_messages.append(f"{prefix} {msg['message']}")
            top_k = select_top_k_products(user_query, products_latest, k=12)
            # Put focus products first (if any), then the rest of top-k
            if focus_products:
                focus_ids = {p.get('id') for p in focus_products}
                merged = focus_products + [p for p in top_k if p.get('id') not in focus_ids]
                context = format_product_data_for_prompt(merged[:12])
            else:
                context = format_product_data_for_prompt(top_k)
            if context_messages:
                focus_titles = ', '.join([p.get('title','') for p in focus_products]) if focus_products else ''
                focus_line = f"\nCurrent focus products (for pronouns): {focus_titles}\n" if focus_titles else ''
                context = f"Chat History:\n{chr(10).join(context_messages)}{focus_line}\nProduct Catalog:\n{context}"

            answer = query_gemini(user_query, context, temperature=0.25)
            # Fallback to local logic if Gemini fails or returns too little
            if not answer or len(answer.strip()) < 5 or 'went wrong' in answer.lower():
                # Minimal pronoun-aware local handling
                if any(tok in query_lower for tok in [' it ', ' this ', ' that ']) and focus_products:
                    fp = focus_products[0]
                    if any(k in query_lower for k in ['vendor','brand']):
                        answer = f"Vendor for {fp.get('title','product')}: {fp.get('vendor','Unknown Vendor')}"
                    elif query_mentions_color:
                        cols = extract_colors_from_product(fp)
                        ctext = ', '.join(cols) if cols else 'No color options'
                        answer = f"Colors for {fp.get('title','product')}: {ctext}"
                    else:
                        answer = generate_chatbot_response(user_query, products_latest)
                else:
                    answer = generate_chatbot_response(user_query, products_latest)
                answer = rewrite_with_gemini(answer)
            else:
                # Linkify product names in Gemini answer
                for product in products_latest:
                    title = product.get('title', '')
                    title_lower = title.lower()
                    link = generate_product_link(product)
                    if title and link and title_lower in answer.lower():
                        answer = re.sub(rf'(?<!\[){re.escape(title)}(?!\])', f'[{title}]({link})', answer)
        else:
            # Use Gemini for non-color queries
            context_messages = []
            for msg in chat_history[-10:]:
                prefix = 'User:' if msg['role'] == 'user' else 'Bot:'
                context_messages.append(f"{prefix} {msg['message']}")
            top_k = select_top_k_products(user_query, products_latest, k=12)
            if focus_products:
                focus_ids = {p.get('id') for p in focus_products}
                merged = focus_products + [p for p in top_k if p.get('id') not in focus_ids]
                context = format_product_data_for_prompt(merged[:12])
            else:
                context = format_product_data_for_prompt(top_k)
            # Add chat history context to prompt
            if context_messages:
                focus_titles = ', '.join([p.get('title','') for p in focus_products]) if focus_products else ''
                focus_line = f"\nCurrent focus products (for pronouns): {focus_titles}\n" if focus_titles else ''
                context = f"Chat History:\n{chr(10).join(context_messages)}{focus_line}\nProduct Catalog:\n{context}"

            answer = query_gemini(user_query, context, temperature=0.3)
            # Fallback to local logic if Gemini unavailable/failed
            if not answer or len(answer.strip()) < 5:
                answer = generate_chatbot_response(user_query, products_latest)
                answer = rewrite_with_gemini(answer)
            else:
                # Replace product name with clickable markdown link, and do not show the raw link
                for product in products_latest:
                    title = product.get('title', '')
                    title_lower = title.lower()
                    link = generate_product_link(product)
                    if title and link and title_lower in answer.lower():
                        answer = re.sub(rf'(?<!\[){re.escape(title)}(?!\])', f'[{title}]({link})', answer)

        # Append bot response to chat history and save
        chat_history.append({'role': 'bot', 'message': answer})
        save_chat_history(user_id, chat_history)

        return jsonify({'response': answer})
    except Exception as e:
        print('Unexpected error:', e)
        return jsonify({'error': 'An unexpected error occurred.'}), 500

# (Optional) Endpoint to fetch chat history for a user
@app.route('/history', methods=['POST'])
def get_history():
    data = request.get_json(silent=True)
    user_id = data.get('user_id', 'default_user') if data else 'default_user'
    history = get_chat_history(user_id)
    return jsonify({'history': history})

if __name__ == "__main__":
    import sys
    print("Fetching initial product data...")
    fetch_latest_products()
    print("Initial product data loaded.")

    # If 'api' is passed as an argument, run Flask API
    if len(sys.argv) > 1 and sys.argv[1] == 'api':
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
    else:
        print("Welcome to Starky Shop Chatbot! Type 'quit' to exit.\n")
        chat_history = []
        while True:
            user_query = input("You: ").strip()
            if user_query.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break
            try:
                products_latest = load_products_from_disk()
            except Exception as e:
                print("Error loading products:", e)
                products_latest = []

            # Build minimal context and use Gemini first
            context_messages = []
            for msg in chat_history[-10:]:
                prefix = 'User:' if msg['role'] == 'user' else 'Bot:'
                context_messages.append(f"{prefix} {msg['message']}")
            context = format_product_data_for_prompt(products_latest)
            if context_messages:
                context = f"Chat History:\n{chr(10).join(context_messages)}\n\nProduct Catalog:\n{context}"

            answer = query_gemini(user_query, context)
            if not answer or len(answer.strip()) < 5:
                answer = generate_chatbot_response(user_query, products_latest)

            chat_history.append({'role': 'user', 'message': user_query})
            chat_history.append({'role': 'bot', 'message': answer})
            print(f"Bot: {answer}\n")
