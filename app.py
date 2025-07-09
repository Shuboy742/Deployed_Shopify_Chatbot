import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Set your Gemini API Key
api_key = os.getenv("GEMINI_API_KEY")
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=api_key)

# Load the product data
with open('shopify_products.json', 'r') as json_file:
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
    # Compose the input
    input_text = f"User question: {query}\nContext:\n{context}"
    # Use the new RunnableSequence API
    chain = prompt_template | model
    # Optionally, you can add memory if you want to keep conversation history
    response = chain.invoke({"input": input_text})
    return response.content if hasattr(response, "content") else response

if __name__ == "__main__":
    print("Welcome to Starky Shop Chatbot! Type 'quit' to exit.\n")
    while True:
        user_query = input("You: ").strip()
        if user_query.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
        answer = generate_chatbot_response(user_query, products)
        print(f"Bot: {answer}\n")

