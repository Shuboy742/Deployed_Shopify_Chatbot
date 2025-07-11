# Shopify_Chatbot

A comprehensive AI-powered chatbot for Shopify stores that provides intelligent product information, customer support, and shopping assistance using Google's Gemini AI and LangChain.

##  Features

- **AI-Powered Responses**: Uses Google Gemini 2.0 Flash for intelligent, contextual responses
- **Product Information**: Detailed product data including pricing, inventory, shipping, and specifications
- **Customer Support**: Handles common customer queries about orders, returns, shipping, and policies
- **Real-time Data**: Fetches live product data from your Shopify store via API
- **Comprehensive Context**: Includes product ID, title, description, vendor, tags, pricing, inventory, and more
- **Interactive Chat Interface**: Simple command-line interface for testing and development

##  Prerequisites

- Python 3.9 or higher
- Shopify store with API access
- Google Gemini API key
- Virtual environment (recommended)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Shuboy742/Shopify_Chatbot
   cd Shopify_chatbot
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys:**
   Edit `config.py` and add your API keys:
   ```python
   SHOPIFY_API_KEY = "your_shopify_api_key_here"
   GEMINI_API_KEY = "your_gemini_api_key_here"
   SHOP_NAME = "your_shop_name_here"
   ```

## 🔧 Configuration

### Required API Keys

1. **Shopify API Key**: 
   - Get from your Shopify admin → Apps → Private apps
   - Requires `read_products` permission

2. **Google Gemini API Key**:
   - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Free tier available

### Environment Variables

The project uses `python-dotenv` for environment variable management. You can create a `.env` file:

```env
SHOPIFY_API_KEY=your_shopify_api_key
GEMINI_API_KEY=your_gemini_api_key
SHOP_NAME=your_shop_name
```

##  Project Structure

```
Shopify_chatbot/
├── config.py                 # Configuration and API keys
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── data/
│   ├── scraper.py           # Shopify API data fetcher
│   ├── app.py              # Main chatbot application
│   └── shopify_products.json # Cached product data
└── venv/                    # Virtual environment
```

##  Usage

### 1. Fetch Product Data

First, fetch the latest product data from your Shopify store:

```bash
# From project root directory
PYTHONPATH=. python3 data/scraper.py
```

This will create/update `data/shopify_products.json` with your store's product information.

### 2. Run the Chatbot

Start the interactive chatbot:

```bash
# From project root directory
python3 data/app.py
```

### 3. Chat Interface

The chatbot supports various types of queries:

- **Product Information**: "What products do you have?"
- **Pricing**: "What's the price of leather belts?"
- **Inventory**: "Do you have jackets in stock?"
- **Customer Support**: "What's your return policy?"
- **Store Information**: "Tell me about your store"

Type `quit`, `exit`, or `bye` to exit the chatbot.

##  Product Data Fields

The chatbot has access to comprehensive product information:

- **Basic Info**: Product ID, Title, Description, Product Type
- **Vendor & Branding**: Vendor, Tags
- **Pricing**: Price, Compare at Price
- **Inventory**: Inventory Management, Inventory Quantity
- **Shipping**: Requires Shipping, Weight, Weight Unit
- **Variants**: All variant-specific information

##  AI Capabilities

The chatbot uses Google Gemini 2.0 Flash with LangChain to provide:

- **Contextual Responses**: Understands product context and user intent
- **Natural Language**: Conversational, human-like responses
- **Comprehensive Knowledge**: Access to all product and store information
- **Flexible Queries**: Handles various question formats and topics

##  Security

- API keys are stored in configuration files (consider using environment variables for production)
- No sensitive customer data is stored locally
- All API calls use secure HTTPS connections

## 🔧 Customization


### Modifying AI Prompts

Edit the prompt template in `data/app.py` to customize the AI's behavior:

```python
prompt_template = PromptTemplate(
    input_variables=["input"],
    template="Your custom prompt template here.\n\n{input}\n\nAnswer:"
)
```

##  Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'config'**
   - Run scripts from the project root directory
   - Use: `PYTHONPATH=. python3 data/scraper.py`

2. **FileNotFoundError: No such file or directory: 'data/shopify_products.json'**
   - Run the scraper first: `PYTHONPATH=. python3 data/scraper.py`

3. **API Key Errors**
   - Verify your API keys in `config.py`
   - Check API key permissions and validity

4. **Import Errors**
   - Ensure virtual environment is activated
   - Install missing packages: `pip install package_name`

##  Dependencies

- `langchain-google-genai`: Google Gemini AI integration
- `langchain-core`: Core LangChain functionality
- `requests`: HTTP requests for Shopify API
- `python-dotenv`: Environment variable management
- `beautifulsoup4`: HTML parsing (if needed)
- `pandas`: Data manipulation (if needed)

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

##  Support

For support and questions:
- Check the troubleshooting section above
- Review the configuration requirements
- Ensure all dependencies are properly installed

---

## INTEGRATING CHATBOT TO SHOPIFY DUMMY WEBSITE 
# Shopify Chatbot Integration Guide

This guide will help you integrate your Flask-based Shopify chatbot with your dummy website and make API calls to interact with it.

---

## 1. Start the Chatbot Backend

1. **Activate your virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Run the Flask app:**
   ```bash
   python data/app.py
   ```
   By default, this will start your chatbot backend on `http://localhost:5000`.

---

## 2. Expose the Backend to the Internet (Optional, for public access)

If you want your website to access the backend from anywhere (not just localhost), use ngrok:

1. **Install your ngrok authtoken** (if you haven’t already):
   ```bash
   ngrok config add-authtoken YOUR_AUTHTOKEN
   ```

3. **To fetch The API Run this command**
    ```bash
   python data/app.py api
   ```

2. **Expose port 5000:**
   ```bash
   ngrok http 5000
   ```
   Copy the HTTPS URL ngrok provides (e.g., `https://abcd1234.ngrok.io`).
---

## 3. Add Chatbot UI to Your Dummy Website
Add html,css,js (event handling) code in the dummy shopify website in the footer.liquid 


**Note:**  - Replace `API_URL` with your ngrok URL if you are using ngrok (e.g., `https://abcd1234.ngrok.io/chat`).

**Note**: This chatbot is designed for development and testing purposes. For production use, consider implementing additional security measures, error handling, and scalability features. 

**Commands to run webhooks**
python3 data/app.py api
ngrok http 5000

Paste this url in frontend api and shopify webhook
everytime the ngrok url gets changed 
https://your-ngrok-link/webhook/products


**Results**
![Screenshot from 2025-07-09 15-11-50](https://github.com/user-attachments/assets/72f43358-29fe-4637-94df-d584cd52daae)

![Screenshot from 2025-07-09 15-12-47](https://github.com/user-attachments/assets/c1886954-30d6-4262-999d-9962eb0dba3e)

![cb](https://github.com/user-attachments/assets/2c647789-3cd4-4cea-be8e-39a3ad8a4af1)

<img width="1291" height="670" alt="cb" src="https://github.com/user-attachments/assets/8915b323-121f-4674-a23c-78bd4cea0faf" />

<img width="1293" height="625" alt="cb1" src="https://github.com/user-attachments/assets/e7b2170f-9697-4968-9842-f75fb76ddfa3" />





