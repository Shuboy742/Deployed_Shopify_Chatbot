import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from flask import Flask, request, jsonify
from flask_cors import CORS

# Set your Gemini API Key
api_key = os.getenv("GEMINI_API_KEY")
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=api_key)

# Load the product data
with open('data/shopify_products.json', 'r') as json_file:
    products = json.load(json_file)

def generate_chatbot_response(query, product_data, memory=None):
    context = "\n".join([
f"Product ID: {product.get('id', 'N/A')}\n"
f"Title: {product.get('title', '')}\n"
f"Description: {product.get('body_html', '')}\n"
f"Product Type: {product.get('product_type', 'N/A')}\n"
f"Vendor: {product.get('vendor', 'N/A')}\n"
f"Tags: {', '.join(product.get('tags', [])) if product.get('tags') else 'N/A'}\n"
f"Requires Shipping: {product.get('requires_shipping', 'N/A')}\n"
f"Weight: {product.get('weight', 'N/A')} {product.get('weight_unit', '')}\n"
f"Price: {product.get('variants', [{}])[0].get('price', 'N/A')}\n"
f"Compare at Price: {product.get('variants', [{}])[0].get('compare_at_price', 'N/A')}\n"
f"Inventory Management: {product.get('variants', [{}])[0].get('inventory_management', 'N/A')}\n"
f"Inventory Quantity: {product.get('variants', [{}])[0].get('inventory_quantity', 'N/A')}\n"
f"---"
for product in product_data
])
    prompt_template = PromptTemplate(
        input_variables=["input"],
        template="You are a helpful assistant for Starky Shop. Use the context to answer the user's question.\n\n{input}\n\nAnswer:"
    )
    input_text = f"User question: {query}\nContext:\n{context}"
    chain = prompt_template | model
    response = chain.invoke({"input": input_text})
    return response.content if hasattr(response, "content") else response

# Flask API setup
app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_query = data.get('message', '') if data else ''
    if not user_query:
        return jsonify({'error': 'No message provided'}), 400
    answer = generate_chatbot_response(user_query, products)
    return jsonify({'response': answer})

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'api':
        app.run(host="0.0.0.0", port=5000, debug=True)
    else:
        print("Welcome to Starky Shop Chatbot! Type 'quit' to exit.\n")
        while True:
            user_query = input("You: ").strip()
            if user_query.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break
            answer = generate_chatbot_response(user_query, products)
            print(f"Bot: {answer}\n")