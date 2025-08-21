import requests
import json
import sys
import os
import time
from urllib.parse import urlparse, parse_qs

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SHOPIFY_API_KEY, SHOP_NAME

API_VERSION = "2023-01"
BASE_URL = f"https://{SHOP_NAME}.myshopify.com/admin/api/{API_VERSION}"

session = requests.Session()
session.headers.update({
    "X-Shopify-Access-Token": SHOPIFY_API_KEY,
    "Content-Type": "application/json"
})

def _get(url, params=None, retries=3, timeout=15):
    for attempt in range(retries):
        try:
            resp = session.get(url, params=params, timeout=timeout)
            if resp.status_code == 429:
                # Rate limited – backoff using Retry-After
                retry_after = int(resp.headers.get("Retry-After", "2"))
                time.sleep(retry_after)
                continue
            resp.raise_for_status()
            return resp
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(1 + attempt)

def _iterate_pages(path, root_key, params=None):
    params = dict(params or {})
    url = f"{BASE_URL}/{path}.json"
    while True:
        resp = _get(url, params=params)
        payload = resp.json()
        items = payload.get(root_key, [])
        for item in items:
            yield item

        # Handle cursor pagination via Link header with page_info
        link = resp.headers.get("Link")
        if not link or 'rel="next"' not in link:
            break
        # Extract next page_info
        try:
            parts = [p.strip() for p in link.split(",")]
            next_link = next(p for p in parts if 'rel="next"' in p)
            next_url = next_link[next_link.find("<")+1:next_link.find(">")]
            parsed = urlparse(next_url)
            q = parse_qs(parsed.query)
            params = {"page_info": q.get("page_info", [None])[0]}
            url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        except Exception:
            break

def fetch_price_rules():
    rules = list(_iterate_pages("price_rules", "price_rules"))
    codes_by_rule = {}
    for rule in rules:
        rule_id = rule.get("id")
        try:
            codes = list(_iterate_pages(f"price_rules/{rule_id}/discount_codes", "discount_codes"))
        except Exception:
            codes = []
        codes_by_rule[rule_id] = [c.get("code") for c in codes]
    return rules, codes_by_rule

def fetch_collections_map():
    collections = {}
    # Custom and Smart collections
    for c in _iterate_pages("custom_collections", "custom_collections"):
        collections[c["id"]] = {"id": c["id"], "title": c.get("title"), "type": "custom"}
    for c in _iterate_pages("smart_collections", "smart_collections"):
        collections[c["id"]] = {"id": c["id"], "title": c.get("title"), "type": "smart"}
    # Collects links product to collection
    product_to_collections = {}
    for collect in _iterate_pages("collects", "collects"):
        pid = collect.get("product_id")
        cid = collect.get("collection_id")
        if pid and cid in collections:
            product_to_collections.setdefault(pid, []).append(collections[cid])
    return product_to_collections

def fetch_inventory_levels(inventory_item_ids):
    levels_by_item = {}
    # Shopify supports comma-separated ids up to a limit; chunk requests
    ids = [str(iid) for iid in inventory_item_ids if iid]
    CHUNK = 40
    for i in range(0, len(ids), CHUNK):
        chunk = ids[i:i+CHUNK]
        params = {"inventory_item_ids": ",".join(chunk)}
        resp = _get(f"{BASE_URL}/inventory_levels.json", params=params)
        for lvl in resp.json().get("inventory_levels", []):
            levels_by_item.setdefault(lvl.get("inventory_item_id"), []).append({
                "available": lvl.get("available"),
                "location_id": lvl.get("location_id"),
                "updated_at": lvl.get("updated_at")
            })
    return levels_by_item

def fetch_product_metafields(product_id):
    try:
        mfs = list(_iterate_pages(f"products/{product_id}/metafields", "metafields"))
        # Map by namespace.key for convenience
        return [{
            "id": m.get("id"),
            "namespace": m.get("namespace"),
            "key": m.get("key"),
            "value": m.get("value"),
            "type": m.get("type"),
        } for m in mfs]
    except Exception:
        return []

def fetch_products_comprehensive():
    products_raw = list(_iterate_pages("products", "products", params={"limit": 250}))

    # Build inventory lookup (levels by inventory_item_id)
    all_inventory_item_ids = []
    for p in products_raw:
        for v in p.get("variants", []):
            if v.get("inventory_item_id"):
                all_inventory_item_ids.append(v["inventory_item_id"])
    levels_by_item = fetch_inventory_levels(all_inventory_item_ids) if all_inventory_item_ids else {}

    # Collections map
    product_to_collections = fetch_collections_map()

    # Discounts / price rules
    price_rules, codes_by_rule = fetch_price_rules()

    # Prepare transformed products
    products = []
    for pr in products_raw:
        pid = pr.get("id")
        variants = []
        for v in pr.get("variants", []):
            variants.append({
                "id": v.get("id"),
                "title": v.get("title"),
                "sku": v.get("sku"),
                "price": v.get("price"),
                "compare_at_price": v.get("compare_at_price"),
                "option1": v.get("option1"),
                "option2": v.get("option2"),
                "option3": v.get("option3"),
                "inventory_item_id": v.get("inventory_item_id"),
                "inventory_policy": v.get("inventory_policy"),
                "inventory_management": v.get("inventory_management"),
                "inventory_levels": levels_by_item.get(v.get("inventory_item_id"), []),
                "barcode": v.get("barcode"),
                "weight": v.get("weight"),
                "weight_unit": v.get("weight_unit"),
                "taxable": v.get("taxable"),
            })

        images = []
        for im in pr.get("images", []):
            images.append({
                "id": im.get("id"),
                "src": im.get("src"),
                "alt": im.get("alt"),
                "position": im.get("position"),
                "width": im.get("width"),
                "height": im.get("height"),
            })

        # Attach price rules potentially applicable (basic heuristic)
        applicable_rules = []
        for rule in price_rules:
            entitled_products = rule.get("entitled_product_ids") or []
            target_selection = rule.get("target_selection")
            # If rule targets all products or explicitly includes this product id
            if target_selection == "all" or pid in entitled_products:
                applicable_rules.append({
                    "id": rule.get("id"),
                    "title": rule.get("title"),
                    "value_type": rule.get("value_type"),
                    "value": rule.get("value"),
                    "starts_at": rule.get("starts_at"),
                    "ends_at": rule.get("ends_at"),
                    "codes": codes_by_rule.get(rule.get("id"), []),
                })

        product_obj = {
            "id": pid,
            "title": pr.get("title"),
            "body_html": pr.get("body_html"),
            "vendor": pr.get("vendor"),
            "product_type": pr.get("product_type"),
            "handle": pr.get("handle"),
            "tags": pr.get("tags"),
            "status": pr.get("status"),
            "published_at": pr.get("published_at"),
            "template_suffix": pr.get("template_suffix"),
            "options": pr.get("options", []),
            "variants": variants,
            "images": images,
            "image": pr.get("image"),
            "collections": product_to_collections.get(pid, []),
            "metafields": fetch_product_metafields(pid),
            "discount_rules": applicable_rules,
        }
        products.append(product_obj)

    return {
        "products": products,
        "price_rules_total": len(price_rules)
    }

def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    try:
        result = fetch_products_comprehensive()
        save_json(result.get("products", []), "shopify_products.json")
        print(f"Saved {len(result.get('products', []))} products to shopify_products.json")
        # Optionally also save rules
        save_json(result, "shopify_full_export.json")
        print("Saved full export to shopify_full_export.json")
    except Exception as e:
        print("Error during scraping:", e)
