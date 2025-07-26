import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration variables
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SHOP_NAME = os.getenv("SHOP_NAME")