import json
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
from config import GEMINI_API_KEY

# Configure Gemini API
configure(api_key=GEMINI_API_KEY)
model = GenerativeModel('gemini-1.5-pro')

def load_products():
    """Load products from JSON file"""
    try:
        with open('data/products.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("No products.json file found. Please run scraper.py first.")
        return []
    except json.JSONDecodeError:
        print("Error reading products.json file.")
        return []

def format_products_for_context(products):
    """Format products into a readable context string"""
    if not products:
        return "No products available."
    
    import re
    
    def clean_html(text):
        """Remove HTML tags and clean up text"""
        if not text:
            return "No description available"
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text)
        # Remove data attributes
        clean_text = re.sub(r'data-[^=]*="[^"]*"', '', clean_text)
        return clean_text.strip()
    
    context_parts = []
    for i, product in enumerate(products, 1):
        title = product.get('title', 'Unknown Product')
        description = clean_html(product.get('body_html', 'No description available'))
        vendor = product.get('vendor', 'Unknown vendor')
        product_type = product.get('product_type', 'General')
        
        # Get price from variants if available
        price = "Price not available"
        if product.get('variants'):
            variant = product['variants'][0]
            price = variant.get('price', 'Price not available')
            if price != "Price not available":
                price = f"${price}"
        
        # Get tags if available
        tags = product.get('tags', [])
        tags_text = ", ".join(tags) if tags else "No tags"
        
        context_parts.append(f"""
Product {i}: {title}
Price: {price}
Category: {product_type}
Brand: {vendor}
Tags: {tags_text}
Description: {description}
""")
    
    return "\n".join(context_parts)

def handle_specific_prompts(user_input, products):
    user_input_lower = user_input.lower()
    import re

    def clean_html(text):
        if not text:
            return "No description available"
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        return clean_text.strip()

    # 1. What products are currently on sale?
    if "on sale" in user_input_lower or "discounted" in user_input_lower:
        sale_products = [p for p in products if "sale" in p.get("tags", []) or "discount" in p.get("tags", [])]
        if sale_products:
            return "Products currently on sale:\n" + "\n".join(f"- {p['title']}" for p in sale_products)
        else:
            return "Currently, there are no products on sale. Please check back soon for discounts!"

    # 2. How can I track my order status?
    if "track" in user_input_lower and "order" in user_input_lower:
        return "To track your order status, log in to your account and go to 'My Orders'. You'll find real-time updates and tracking information there. If you need help, contact our customer service."

    # 3. What is the return policy for products?
    if "return policy" in user_input_lower or ("return" in user_input_lower and "policy" in user_input_lower):
        return "We offer a customer-friendly return policy. You can return most products within 30 days of delivery for a full refund or exchange. Please ensure the product is unused and in original packaging."

    # 4. Do you offer international shipping?
    if "international shipping" in user_input_lower or ("ship" in user_input_lower and "international" in user_input_lower):
        return "Yes, we offer international shipping to many countries. Shipping fees and delivery times vary by location. You'll see available options at checkout."

    # 5. Can I cancel my order after it's been placed?
    if "cancel" in user_input_lower and "order" in user_input_lower:
        return "You can cancel your order within 1 hour of placing it, as long as it hasn't been processed for shipping. Please contact customer service immediately for assistance."

    # 6. What are the payment methods you accept?
    if "payment methods" in user_input_lower or "how can i pay" in user_input_lower or "accept" in user_input_lower and "payment" in user_input_lower:
        return "We accept credit/debit cards, net banking, UPI, and popular wallets. More payment options will be available at checkout."

    # 7. Can I get a discount for my first purchase?
    if "discount" in user_input_lower and "first purchase" in user_input_lower:
        return "Yes! Use code WELCOME10 at checkout to get 10% off your first purchase."

    # 8. Do you have any promotions or special offers?
    if "promotion" in user_input_lower or "special offer" in user_input_lower or "deal" in user_input_lower:
        return "We regularly run promotions and special offers. Check our homepage or subscribe to our newsletter to stay updated!"

    # 9. How do I apply a coupon code to my order?
    if "apply" in user_input_lower and "coupon" in user_input_lower:
        return "You can enter your coupon code during checkout in the 'Apply Coupon' field. The discount will be applied to your order total."

    # 10. Can I change my delivery address after placing an order?
    if "change" in user_input_lower and "address" in user_input_lower:
        return "If your order hasn't shipped yet, you can change your delivery address by contacting customer service as soon as possible."

    # 11. What’s the estimated delivery time for my order?
    if "delivery time" in user_input_lower or "how long" in user_input_lower and "delivery" in user_input_lower:
        return "Estimated delivery time is 3-7 business days for domestic orders and 7-15 business days for international orders. You'll see a more accurate estimate at checkout."

    # 12. How do I create an account on your website?
    if "create an account" in user_input_lower or "sign up" in user_input_lower:
        return "Click on the 'Sign Up' or 'Create Account' button at the top right of our website and fill in your details to register."

    # 13. Are the prices on your website inclusive of tax?
    if "inclusive of tax" in user_input_lower or "tax included" in user_input_lower:
        return "Yes, all prices displayed on our website are inclusive of applicable taxes unless stated otherwise at checkout."

    # 14. How do I add items to my cart?
    if "add to cart" in user_input_lower or "add items" in user_input_lower:
        return "To add items to your cart, simply click the 'Add to Cart' button on the product page."

    # 15. Is there a warranty on your products?
    if "warranty" in user_input_lower:
        return "Many of our products come with a manufacturer's warranty. Please check the product page for specific warranty details."

    # 16. Can I exchange a product instead of returning it?
    if "exchange" in user_input_lower:
        return "Yes, you can exchange most products within 30 days of delivery, provided they are unused and in original packaging."

    # 17. Are there any new arrivals in the store?
    if "new arrival" in user_input_lower or "latest" in user_input_lower:
        new_arrivals = [p for p in products if "new" in p.get("tags", []) or "latest" in p.get("tags", [])]
        if new_arrivals:
            return "Here are our latest arrivals:\n" + "\n".join(f"- {p['title']}" for p in new_arrivals)
        else:
            return "We update our collection regularly. Check the 'New Arrivals' section on our website for the latest products!"

    # 18. Can I pre-order products that are out of stock?
    if "pre-order" in user_input_lower or "preorder" in user_input_lower:
        return "Pre-order is available for select products. If a product is out of stock but available for pre-order, you'll see a 'Pre-order' button on the product page."

    # 19. Do you offer gift wrapping services?
    if "gift wrap" in user_input_lower or "gift wrapping" in user_input_lower:
        return "Yes, we offer gift wrapping services for a small additional fee. You can select this option during checkout."

    # 20. How do I use loyalty points to get discounts?
    if "loyalty points" in user_input_lower or "reward points" in user_input_lower:
        return "Log in to your account to view your loyalty points. You can redeem them for discounts at checkout."

    # 21. What sizes do you offer for clothing products?
    if "size" in user_input_lower and "clothing" in user_input_lower:
        return "We offer a wide range of sizes for our clothing products. Please refer to the size chart on each product page for details."

    # 22. How do I check the status of my refund?
    if "refund" in user_input_lower and "status" in user_input_lower:
        return "To check your refund status, log in to your account and go to 'My Orders'. Refund updates will also be sent to your registered email."

    # 23. How can I contact customer service for help?
    if "contact" in user_input_lower and "customer service" in user_input_lower:
        return "You can contact our customer service via the chat on our website, by email, or by phone. We're here to help 24/7!"

    # 24. What are the benefits of creating an account with you?
    if "benefit" in user_input_lower and "account" in user_input_lower:
        return "Creating an account lets you track orders, save addresses, earn loyalty points, and get exclusive offers and faster checkout."

    # 25. Can I get a gift card from your store?
    if "gift card" in user_input_lower:
        return "Yes, we offer digital gift cards in various denominations. You can purchase them from the 'Gift Cards' section on our website."

    # 26. How do I know if a product is in stock?
    if "in stock" in user_input_lower or "stock" in user_input_lower:
        return "Product availability is shown on each product page. If an item is out of stock, you'll see an 'Out of Stock' label."

    # 27. What is the best way to care for the products I bought?
    if "care" in user_input_lower or "maintain" in user_input_lower:
        return "Care instructions are provided on each product page. For most items, keep them clean, dry, and store them properly to ensure longevity."

    # 28. Do you offer any bundles or packages for discounts?
    if "bundle" in user_input_lower or "package" in user_input_lower:
        return "Yes, we offer product bundles and packages at discounted rates. Check our 'Bundles' section for current offers."

    # 29. Can I leave a review for a product I purchased?
    if "review" in user_input_lower:
        return "Absolutely! After your purchase, you'll receive an email with a link to leave a review. You can also review products directly on their product pages."

    # 30. What do I do if I received a damaged or incorrect item?
    if "damaged" in user_input_lower or "incorrect" in user_input_lower:
        return "We're sorry for the inconvenience. Please contact customer service immediately with your order details and photos, and we'll resolve the issue promptly."

    # 31. Give me price of leather belts
    if "price" in user_input_lower and "leather belt" in user_input_lower:
        for product in products:
            if "leather belt" in product.get("title", "").lower():
                price = product.get("variants", [{}])[0].get("price", "Price not available")
                return f"The price of {product['title']} is ${price}."
        return "We currently do not have leather belts in stock."

    # 32. Give me products under 4000
    if "under 4000" in user_input_lower or "below 4000" in user_input_lower:
        under_4000 = []
        for product in products:
            try:
                price = float(product.get("variants", [{}])[0].get("price", "0"))
                if price < 4000:
                    under_4000.append(f"{product['title']} - ${price}")
            except Exception:
                continue
        if under_4000:
            return "Products under $4000:\n" + "\n".join(under_4000)
        else:
            return "No products found under $4000."

    return None  # If no specific match, let the main fallback/AI handle it

def get_comprehensive_response(user_input, products):
    """Comprehensive response system that can handle any question"""
    import re
    
    def clean_html(text):
        if not text:
            return "No description available"
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = re.sub(r'data-[^=]*="[^"]*"', '', clean_text)
        return clean_text.strip()
    
    user_input_lower = user_input.lower()
    
    # Store knowledge base
    store_info = {
        "name": "Starky Shop",
        "website": "https://mffws4-kk.myshopify.com",
        "status": "Opening Soon",
        "platform": "Shopify",
        "focus": "Premium quality products",
        "mission": "Provide exceptional customer experience with carefully curated products",
        "values": ["Quality", "Customer Satisfaction", "Innovation", "Integrity"],
        "contact": "Available through this chatbot",
        "shipping": "Available once store launches",
        "payment": "Multiple secure payment options",
        "returns": "Customer-friendly return policy",
        "support": "24/7 chatbot assistance"
    }
    
    # Product-specific queries
    if any(word in user_input_lower for word in ['list', 'products', 'show', 'what do you have', 'available']):
        if 'list' in user_input_lower or 'products' in user_input_lower:
            product_names = []
            for i, product in enumerate(products, 1):
                title = product.get('title', 'Unknown Product')
                product_names.append(f"{i}. {title}")
            return "Product List:\n" + "\n".join(product_names)
        else:
            return format_products_for_context(products)
    
    if any(word in user_input_lower for word in ['price', 'cost', 'how much', 'pricing']):
        price_info = []
        for product in products:
            title = product.get('title', 'Unknown')
            if product.get('variants'):
                price = product['variants'][0].get('price', 'Price not available')
                price_info.append(f"{title}: ${price}")
        return "Product prices:\n" + "\n".join(price_info)
    
    # Search for specific product
    for product in products:
        if product.get('title', '').lower() in user_input_lower:
            title = product.get('title', 'Unknown')
            description = clean_html(product.get('body_html', 'No description'))
            if product.get('variants'):
                price = product['variants'][0].get('price', 'Price not available')
                return f"📦 {title}\n💰 Price: ${price}\n📝 Description: {description}"
    
    # Store information queries
    if any(word in user_input_lower for word in ['store', 'shop', 'website', 'starky']):
        return f"""Welcome to {store_info['name']}! 🛍️

We're a premium online store offering high-quality products including:
- Fashion accessories (belts, etc.)
- Electronics and gadgets
- Clothing and apparel

Our store is currently in "{store_info['status']}" mode, but we're excited to serve you with our carefully curated selection of products.

Store Details:
- Brand: {store_info['name']}
- Status: {store_info['status']}
- Focus: {store_info['focus']}
- Customer Service: {store_info['support']}

Feel free to ask about our products, pricing, or any other questions!"""
    
    # Contact and support queries
    if any(word in user_input_lower for word in ['contact', 'support', 'help', 'customer service', 'email', 'phone']):
        return f"""Customer Support Information:

📧 Contact: {store_info['contact']}
🛍️ Store: {store_info['name']} ({store_info['status']})
📍 Status: Currently in pre-launch phase
💬 Support: {store_info['support']}

For immediate assistance, you can ask me about:
- Product information and pricing
- Store policies and details
- General inquiries about {store_info['name']}

I'm your 24/7 shopping assistant! 😊"""
    
    # Shipping and delivery queries
    if any(word in user_input_lower for word in ['shipping', 'delivery', 'when will i get', 'how long']):
        return f"""Shipping & Delivery Information:

🚚 Shipping: {store_info['shipping']}
⏰ Delivery Time: Will be announced at launch
📦 Packaging: Secure and professional packaging
🌍 Locations: Shipping details coming soon

Since we're currently in "{store_info['status']}" mode, specific shipping details will be available when we officially launch. Stay tuned for updates!"""
    
    # Payment and checkout queries
    if any(word in user_input_lower for word in ['payment', 'pay', 'checkout', 'buy', 'purchase', 'order']):
        return f"""Payment & Checkout Information:

💳 Payment Methods: {store_info['payment']}
🔒 Security: Secure payment processing
📱 Checkout: Easy and user-friendly process
🛡️ Protection: Buyer protection guaranteed

Our payment and checkout system is being finalized for launch. We'll offer multiple secure payment options for your convenience!"""
    
    # Store policies queries
    if any(word in user_input_lower for word in ['return', 'refund', 'policy', 'warranty', 'guarantee']):
        return f"""Store Policies:

🔄 Returns: {store_info['returns']}
💰 Refunds: Hassle-free refund process
🛡️ Warranty: Product warranties available
✅ Guarantee: Customer satisfaction guaranteed

Our detailed policies will be available when we launch. We're committed to providing excellent customer service and satisfaction!"""
    
    # General greeting and conversation
    if any(word in user_input_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
        return f"""Hello! 👋 Welcome to {store_info['name']}!

I'm your personal shopping assistant, ready to help you discover our amazing products. We're currently in "{store_info['status']}" mode, but I can tell you all about what we have to offer!

What would you like to know about our products or store? 😊"""
    
    # About the store/brand
    if any(word in user_input_lower for word in ['about', 'who are you', 'what is starky', 'brand', 'company']):
        return f"""About {store_info['name']}:

🏪 We are {store_info['name']}, a premium online retailer committed to bringing you high-quality products that enhance your lifestyle.

Our Mission: {store_info['mission']}

Our Values: {', '.join(store_info['values'])}

We're excited to launch soon and can't wait to serve you! 🌟"""
    
    # Technical and website queries
    if any(word in user_input_lower for word in ['website', 'site', 'online', 'web', 'url', 'link']):
        return f"""Website Information:

🌐 Website: {store_info['website']}
📱 Status: {store_info['status']}
🔧 Platform: {store_info['platform']}-powered
📊 Features: Secure, mobile-friendly, fast loading
🎨 Design: Modern, user-friendly interface

Our website is built on {store_info['platform']}'s reliable platform, ensuring security and performance. We're currently in pre-launch mode, preparing for an amazing shopping experience!"""
    
    # Business and partnership queries
    if any(word in user_input_lower for word in ['business', 'partnership', 'wholesale', 'bulk', 'reseller', 'affiliate']):
        return """Business Inquiries:

🤝 Partnerships: We're open to business opportunities
📦 Wholesale: Bulk purchasing options available
🔄 Reseller: Partnership programs coming soon
💼 Corporate: Business accounts and solutions
📈 Growth: Expanding our network

For business inquiries, please contact us through this chatbot. We'll get back to you with detailed information about our partnership opportunities!"""
    
    # Product recommendations and advice
    if any(word in user_input_lower for word in ['recommend', 'suggestion', 'advice', 'best', 'popular', 'trending']):
        return """Product Recommendations:

Based on our current inventory, here are some highlights:

🔥 Popular Items:
- Premium Leather Belts (High quality, versatile)
- [Other trending products from your inventory]

💡 Shopping Tips:
- Consider your style preferences
- Check product descriptions for details
- Look at pricing and value
- Read customer reviews when available

I can provide specific recommendations based on your needs. What type of product are you looking for?"""
    
    # Store hours and availability
    if any(word in user_input_lower for word in ['hours', 'open', 'close', 'available', 'when', 'time']):
        return f"""Store Availability:

🕒 Status: {store_info['status']} (Pre-launch phase)
🌍 Online: 24/7 website access
💬 Support: {store_info['support']}
📅 Launch: Coming soon - stay tuned!

While we're in "{store_info['status']}" mode, our website and chatbot are available 24/7. Once we launch, we'll have regular business hours and enhanced customer service!"""
    
    # Quality and standards
    if any(word in user_input_lower for word in ['quality', 'standard', 'certification', 'authentic', 'genuine']):
        return """Quality Standards:

✅ Quality Assurance: All products meet high standards
🔍 Authenticity: Genuine products only
📋 Certifications: Industry-standard compliance
🎯 Selection: Carefully curated inventory
💎 Premium: Focus on quality over quantity

We're committed to offering only the best products. Every item in our store is selected for quality, authenticity, and customer satisfaction!"""
    
    # Future plans and updates
    if any(word in user_input_lower for word in ['future', 'plan', 'update', 'new', 'coming', 'launch']):
        return """Future Plans & Updates:

🚀 Launch: Official store opening coming soon
🆕 New Products: Expanding inventory regularly
📱 Features: Enhanced shopping experience
🎁 Promotions: Special offers and deals
📈 Growth: Continuous improvement and expansion

We're constantly working to improve and expand our offerings. Stay connected for the latest updates and exciting new products!"""
    
    # Environmental and social responsibility
    if any(word in user_input_lower for word in ['environmental', 'eco', 'green', 'sustainable', 'social', 'responsibility']):
        return """Environmental & Social Responsibility:

🌱 Sustainability: Committed to eco-friendly practices
♻️ Packaging: Environmentally conscious materials
🤝 Community: Supporting local and global initiatives
💚 Values: Responsible business practices
🌍 Impact: Minimizing environmental footprint

We believe in responsible business practices and are committed to making a positive impact on our community and environment!"""
    
    # Gift and special occasions
    if any(word in user_input_lower for word in ['gift', 'present', 'birthday', 'anniversary', 'holiday', 'special']):
        return """Gift & Special Occasions:

🎁 Gift Options: Perfect presents for any occasion
🎂 Birthdays: Thoughtful birthday gifts
💕 Anniversaries: Romantic anniversary presents
🎄 Holidays: Seasonal gift selections
🎉 Special Events: Customized gift solutions

We offer a variety of products perfect for gifting. From fashion accessories to electronics, we have something special for every occasion and recipient!"""
    
    # International and global
    if any(word in user_input_lower for word in ['international', 'global', 'worldwide', 'country', 'region']):
        return """International Information:

🌍 Global Reach: Serving customers worldwide
🌐 International Shipping: Available at launch
💱 Currency: Multiple payment options
🌎 Regions: Shipping to most countries
📦 Customs: International shipping support

We're excited to serve customers globally! International shipping details and supported regions will be available when we officially launch."""
    
    # General knowledge and miscellaneous
    if any(word in user_input_lower for word in ['what', 'how', 'why', 'when', 'where', 'who']):
        return f"""I'm here to help you with everything about {store_info['name']}! 

You can ask me about:
• Our products and pricing
• Store information and policies
• Shipping and delivery
• Payment and checkout
• Customer support
• General questions about our brand
• Business inquiries
• Technical questions
• And much more!

What specific information are you looking for? 😊"""
    
    # Default comprehensive response
    return f"""I'm your comprehensive {store_info['name']} assistant! 

I can help you with absolutely anything related to our store:

📦 **Products**: Information, pricing, recommendations
🏪 **Store**: Policies, shipping, returns, payment
💬 **Support**: Customer service, contact info
🌐 **Website**: Technical details, features
🤝 **Business**: Partnerships, wholesale, corporate
🎁 **Gifts**: Special occasions, recommendations
🌍 **Global**: International shipping, regions
🔮 **Future**: Plans, updates, new features

No matter what you ask, I'll do my best to provide helpful, accurate information about {store_info['name']}!

What would you like to know? 😊"""

def get_chatbot_response(user_input, products):
    """Get response from Gemini AI about the products"""
    if not products:
        return "I don't have any product information available. Please make sure the scraper has been run successfully."
    
    try:
        context = format_products_for_context(products)
        
        prompt = f"""
You are a comprehensive Shopify store assistant for Starky Shop. You have access to the following product information:

{context}

You can answer ANY type of question about:
- Products: details, pricing, features, comparisons
- Store information: policies, shipping, returns, payment methods
- Customer service: contact info, support, help
- Store status: currently "Opening Soon" mode
- Brand information: about Starky Shop, mission, values
- General shopping: recommendations, advice, tips
- Technical questions: website, ordering process
- Business inquiries: partnerships, wholesale, etc.
- Environmental and social responsibility
- Gift and special occasions
- International shipping and global reach
- Quality standards and certifications
- Future plans and updates
- ANY OTHER TOPIC related to the store or business

Be helpful, friendly, and comprehensive. If you don't have specific information, provide general guidance or redirect appropriately. Always maintain a professional yet warm tone.

Customer question: {user_input}

Response:"""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            return get_comprehensive_response(user_input, products)
        else:
            return f"Sorry, I encountered an error: {error_msg}"

def main():
    print("Loading products...")
    products = load_products()
    
    if not products:
        print("No products found. Please run scraper.py first to fetch products.")
        return
    
    print(f"Loaded {len(products)} products.")
    print("\nShopify Chatbot is ready! Ask me about the products.")
    print("Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        response = get_chatbot_response(user_input, products)
        print(f"Bot: {response}\n")

if __name__ == "__main__":
    main()
