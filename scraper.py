import requests
import json
from config import SHOPIFY_API_KEY, SHOP_NAME

def fetch_products_from_api():
    url = f"https://{SHOP_NAME}.myshopify.com/admin/api/2023-01/products.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Failed to fetch products: {response.status_code}")
            print(f"Response text: {response.text}")
            print("Please check your Shopify API key and permissions.")
            return []

        data = response.json()
        products = []
        for product in data.get("products", []):
            products.append({
                "id": product.get("id"),
                "title": product.get("title"),
                "body_html": product.get("body_html"),
                "vendor": product.get("vendor"),
                "product_type": product.get("product_type"),
                "handle": product.get("handle"),
                "tags": product.get("tags"),
                "variants": product.get("variants"),
                "images": product.get("images"),
                "image": product.get("image"),
            })

        with open("data/products.json", "w") as f:
            json.dump(products, f, indent=4)
        print(f"Successfully saved {len(products)} products to data/shopify_products.json")
        return products
        
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []

if __name__ == "__main__":
    fetch_products_from_api()
