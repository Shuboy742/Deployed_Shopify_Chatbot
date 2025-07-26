# Shopify Chatbot

A comprehensive AI-powered chatbot for Shopify stores that provides intelligent product information, customer support, and shopping assistance using Google's Gemini AI and LangChain.

---

## Features

- **AI-Powered Responses**: Uses Google Gemini for intelligent, contextual responses
- **Product Information**: Detailed product data including pricing, inventory, shipping, and specifications
- **Customer Support**: Handles common customer queries about orders, returns, shipping, and policies
- **Real-time Data**: Fetches live product data from your Shopify store via API and webhooks
- **Interactive Chat Interface**: Simple web API for integration with any frontend

---

## Prerequisites

- Python 3.9 or higher (Tested on 3.12)
- Shopify store with API access
- Google Gemini API key
- [ngrok](https://ngrok.com/) (for public URL/webhooks)
- Git

---

## Setup Instructions

### 1. Clone the Repository

```sh
git clone https://github.com/Shuboy742/EComm_Shopify_Chatbot.git
cd EComm_Shopify_Chatbot
```

---

### 2. Create and Activate a Virtual Environment

#### **Windows:**
```sh
python -m venv venv
venv\Scripts\activate
```

#### **Ubuntu/Linux/Mac:**
```sh
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

```sh
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Create a `.env` file in the project root with:

```
SHOPIFY_API_KEY=your_shopify_api_key
GEMINI_API_KEY=your_gemini_api_key
SHOP_NAME=your_shop_name
```

- Replace values with your actual API keys and Shopify store name (the part before `.myshopify.com`).

---

### 5. Run the Flask Backend

```sh
python app.py api
```
- The app will run on `http://localhost:5000`

---

### 6. Expose Your Backend with ngrok

#### **Windows:**
```sh
cd ngrok-v3-stable-windows-amd64
ngrok.exe http 5000
```

#### **Ubuntu/Linux/Mac:**
```sh
ngrok http 5000
```
#### **Windows:**
```sh
.\ngrok.exe http 5000
```

- Copy the HTTPS forwarding URL (e.g., `https://abcd1234.ngrok-free.app`).

---

### 7. Set Up Shopify Webhooks

- In Shopify Admin:  
  **Settings → Notifications → Webhooks → Create webhook**
- **Event:** Product updates (and optionally creation/deletion)
- **URL:** `https://your-ngrok-url.ngrok-free.app/webhook/products`
- **Format:** JSON

---

### 8. Test the Chatbot

- Use your frontend or Postman to POST to:  
  `https://your-ngrok-url.ngrok-free.app/chat`
- Example JSON body:
  ```json
  {
    "user_id": "testuser",
    "message": "What products do you have?"
  }
  ```

---

## Project Structure

```
EComm_Shopify_Chatbot/
├── app.py                  # Main Flask application
├── config.py               # Configuration loader
├── scraper.py              # Manual product data fetcher (optional)
├── requirements.txt        # Python dependencies
├── shopify_products.json   # Product data (auto-updated)
├── .env                    # Environment variables (not tracked)
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── ngrok.exe / ngrok-v3-stable-windows-amd64/ # ngrok binary/folder
└── venv/                   # Python virtual environment (not tracked)
```

---

## Security

- **Never commit your `.env` file or API keys to GitHub!**
- All API calls use secure HTTPS connections.

---

## Troubleshooting

- **ModuleNotFoundError:** Activate your virtual environment and install dependencies.
- **Webhook not working:** Make sure ngrok is running and the correct URL is set in Shopify.
- **Product data not updating:** Check webhook logs and ensure your backend is running.

---

## License

MIT

---



Designed by Shubham kambale
