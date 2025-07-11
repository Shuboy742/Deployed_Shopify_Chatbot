SHOPIFY_API_KEY= "Your shopify API Key"
GEMINI_API_KEY = "Your Gemini API Key"
SHOP_NAME = "Your Shop Name"

import os
from dotenv import load_dotenv

load_dotenv()

import json
with open('data/products.json', 'w') as f:
    json.dump([{"test": "ok"}], f)
