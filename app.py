import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import markdown
from dotenv import load_dotenv
import re
import threading

load_dotenv()

SHOP_NAME = "ecommerce-test-store-demo"
SHOP_URL = f"https://ecommerce-test-store-demo.myshopify.com"
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_API_KEY")
products_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'products.json')

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
        'USD': '$',
        'INR': '₹',
        'EUR': '€',
        'GBP': '£',
        'CAD': 'C$',
        'AUD': 'A$',
        'JPY': '¥',
        'CNY': '¥',
        'KRW': '₩',
        'RUB': '₽',
        'BRL': 'R$',
        'MXN': '$',
        'SGD': 'S$',
        'HKD': 'HK$',
        'NZD': 'NZ$',
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

def find_product_by_name(query, product_data):
    """Find products that match the search query"""
    query_lower = query.lower()
    matching_products = []
    
    # Common words to remove from search
    stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'link', 'url', 'buy', 'purchase', 'provide', 'give', 'me', 'please', 'can', 'you']
    
    # Clean the query
    words = query_lower.split()
    search_terms = [word for word in words if word not in stop_words and len(word) > 2]
    
    for product in product_data:
        title_lower = product.get('title', '').lower()
        
        # Check if any search term matches the product title
        for term in search_terms:
            if term in title_lower:
                matching_products.append(product)
                break
    
    return matching_products

def generate_product_link(product):
    """Generate the product URL"""
    handle = product.get('handle', '')
    if handle:
        return f"{SHOP_URL}/products/{handle}"
    return None

def format_product_card(product):
    title = product.get('title', 'Unnamed Product')
    price = product.get('variants', [{}])[0].get('price', 'N/A')
    desc = (product.get('body_html') or product.get('product_type', '') or '').strip()
    desc = desc[:90] + ('...' if len(desc) > 90 else '') if desc else 'No description available.'
    tags = product.get('tags', '')
    vendor = product.get('vendor', 'Unknown Vendor')
    # Try to get color from options
    color = None
    for opt in product.get('options', []):
        if 'color' in opt.get('name', '').lower():
            color = ', '.join(opt.get('values', []))
    link = generate_product_link(product)
    
    # Format price with correct currency
    currency_symbol = get_currency_symbol(STORE_CURRENCY)
    formatted_price = f"{currency_symbol}{price}" if price != 'N/A' else 'N/A'
    
    card = f"🛍️ **{title}**\n"
    card += f"💰 Price: {formatted_price}\n"
    card += f"📄 {desc}\n"
    if tags:
        card += f"🏷️ Tags: {tags}\n"
    if color:
        card += f"🎨 Available colors: {color}\n"
    card += f"🏢 Vendor: {vendor}\n"
    if link:
        card += f"🔗 [View Product]({link})"
    return card

def find_matching_products(query, products):
    query = query.lower()
    keywords = [w for w in query.split() if len(w) > 2]
    matches = []
    for product in products:
        title = product.get('title', '').lower()
        tags = product.get('tags', '').lower()
        vendor = product.get('vendor', '').lower()
        options = ' '.join([str(opt.get('values', '')) for opt in product.get('options', [])]).lower()
        if any(k in title or k in tags or k in vendor or k in options for k in keywords):
            matches.append(product)
    return matches

def generate_chatbot_response(query, products, memory=None):
    query_lower = query.lower()
    # Greetings
    if any(word in query_lower for word in ['hello', 'hi', 'hey']):
        return "👋 Hello! How can I assist you with our products?"
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
    # Color (try to find in options)
    if 'color' in query_lower:
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
    return "🤖 I'm here to help with product details, pricing, or availability. Try asking something like: 'Show me snowboards' or 'Price of Gift Card'."

# Helper to format product data for the prompt

def format_product_data_for_prompt(products):
    entries = []
    currency_symbol = get_currency_symbol(STORE_CURRENCY)
    for product in products:
        price = product.get("variants", [{}])[0].get("price", "")
        formatted_price = f"{currency_symbol}{price}" if price else ""
        entry = {
            "title": product.get("title", ""),
            "vendor": product.get("vendor", ""),
            "tags": product.get("tags", ""),
            "handle": product.get("handle", ""),
            "price": formatted_price,
            "description": (product.get("body_html") or product.get("product_type", ""))[:200]
        }
        entries.append(entry)
    return json.dumps(entries, indent=2)

# Gemini 2.0 Flash Request Function

def query_gemini(user_query, context):
    headers = {
        "Content-Type": "application/json"
    }
    prompt = f"""You are a helpful ecommerce assistant for a Shopify store.\nAnswer ONLY the user's question using the product catalog below.\nRespond in a friendly and human-like tone with relevant product names, prices, vendors, tags, delivery info, etc.\n\nProduct Catalog:\n{context}\n\nUser Question:\n{user_query}\n\nAnswer:"""
    body = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }
    try:
        res = requests.post(GEMINI_API_URL, headers=headers, json=body)
        res.raise_for_status()
        reply = res.json()['candidates'][0]['content']['parts'][0]['text']
        return reply
    except Exception as e:
        print("Gemini API Error:", e)
        return "Sorry, something went wrong while processing your request."

app = Flask(__name__)
CORS(app)

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
@app.route('/chat', methods=['POST'])
def chat():
    try:
        with open(products_file, 'r') as json_file:
            products_latest = json.load(json_file)
        data = request.get_json(silent=True)
        user_query = data.get('message', '') if data else ''
        user_id = data.get('user_id', 'default_user') if data else 'default_user'
        if not user_query:
            return jsonify({'error': 'No message provided'}), 400

        # Load chat history
        chat_history = get_chat_history(user_id)
        # Append new user message
        chat_history.append({'role': 'user', 'message': user_query})

        # Prepare context for Gemini: last 5 messages (user+bot)
        context_messages = []
        for msg in chat_history[-10:]:
            prefix = 'User:' if msg['role'] == 'user' else 'Bot:'
            context_messages.append(f"{prefix} {msg['message']}")
        context = format_product_data_for_prompt(products_latest)
        # Add chat history context to prompt
        if context_messages:
            context = f"Chat History:\n{chr(10).join(context_messages)}\n\nProduct Catalog:\n{context}"

        answer = query_gemini(user_query, context)

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
        app.run(host="0.0.0.0", port=5000)
    else:
        print("Welcome to Starky Shop Chatbot! Type 'quit' to exit.\n")
        while True:
            user_query = input("You: ").strip()
            if user_query.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break
            # Always use the latest products.json
            try:
                with open(products_file, 'r') as json_file:
                    products_latest = json.load(json_file)
            except Exception as e:
                print("Error loading products:", e)
                products_latest = []
            answer = generate_chatbot_response(user_query, products_latest)
            print(f"Bot: {answer}\n")
