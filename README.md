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

### Adding New Product Fields

To include additional product information, modify the context generation in `data/app.py`:

```python
context = "\n".join([
    f"Product ID: {product.get('id', 'N/A')}\n"
    f"Title: {product.get('title', '')}\n"
    # Add your custom fields here
    f"Custom Field: {product.get('custom_field', 'N/A')}\n"
    for product in product_data
])
```

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

## 📝 Dependencies

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

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

##  Support

For support and questions:
- Check the troubleshooting section above
- Review the configuration requirements
- Ensure all dependencies are properly installed

---

**Note**: This chatbot is designed for development and testing purposes. For production use, consider implementing additional security measures, error handling, and scalability features. 
