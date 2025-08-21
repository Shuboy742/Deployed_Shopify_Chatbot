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
- Git
- Render account (free) for a stable HTTPS backend URL

---

## Setup Instructions

### 1. Clone the Repository

```sh
git clone https://github.com/Shuboy742/Deployed_Shopify_Chatbot.git
cd Deployed_Shopify_Chatbot
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

### 5. Run the Flask Backend (local development)

```sh
python app.py api
```
- The app will run on `http://localhost:5000`

---

### 6. Deploy Backend on Render (recommended, free)

Render provides a stable HTTPS URL (no rotating links).

1) Push the repo to GitHub
2) Render Dashboard → New → Web Service → Connect your repo
3) Settings:
   - Name: `deployed-shopify-chatbot` (URL becomes `https://deployed-shopify-chatbot.onrender.com`)
   - Build Command:
```sh
     pip install --upgrade pip && pip install -r requirements.txt
```
   - Start Command:
```sh
     python app.py api
     ```
   - Environment Variables:
     - `SHOPIFY_API_KEY` = your value
     - `GEMINI_API_KEY` = your value
     - `SHOP_NAME` = ecommerce-test-store-demo
     - `ALLOWED_ORIGIN` = `https://ecommerce-test-store-demo.myshopify.com`
4) Create & deploy. The URL will be shown in Render.

Notes:
- Free plan sleeps on inactivity; first request can be slow (cold start).
- Manual redeploy: Deploys tab → Manual Deploy → Deploy latest commit.

---

### 7. Set Up Shopify Webhooks

- In Shopify Admin:  
  **Settings → Notifications → Webhooks → Create webhook**
- **Event:** Product updates (and optionally creation/deletion)
- **URL:** `https://deployed-shopify-chatbot.onrender.com/webhook/products`
- **Format:** JSON

---

### 8. Integrate the Frontend Widget (Shopify theme) & Test

- Add the widget code (`Chatbot.html` content) into your theme, e.g., `footer.liquid`.
- Configure the API base once:
  ```html
  <script>
    const API_BASE = "https://deployed-shopify-chatbot.onrender.com";
  </script>
  ```
- The widget will POST to `${API_BASE}/chat` and shows a visible "🤖 Thinking..." indicator while replying.
- Or test via Postman/curl:  
  `https://deployed-shopify-chatbot.onrender.com/chat`
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
Deployed_Shopify_Chatbot/
├── app.py                  # Main Flask application
├── config.py               # Configuration loader
├── scraper.py              # Manual product data fetcher (optional)
├── requirements.txt        # Python dependencies
├── shopify_products.json   # Product data (auto-updated)
├── .env                    # Environment variables (not tracked)
├── .gitignore              # Git ignore rules
├── README.md               # This file
└── venv/                   # Python virtual environment (not tracked)
```

---

## Security

- **Never commit your `.env` file or API keys to GitHub!**
- All API calls use secure HTTPS connections.

---

## Troubleshooting

- **ModuleNotFoundError:** Activate your virtual environment and install dependencies.
- **Webhook not working:** Ensure the Render URL is correct in Shopify webhook settings and your service is live.
- **CORS blocked:** Set `ALLOWED_ORIGIN` in Render to your Shopify store domain.
- **Cold start delay:** Free Render instances sleep on inactivity; first request may take a few seconds.
- **favicon 404 in console:** Handled by a `/favicon.ico` 204 endpoint in the backend.

---

## License

MIT

---

## Results
<img width="1920" height="969" alt="Screenshot (79)" src="https://github.com/user-attachments/assets/90f53b84-4339-4868-bed6-e69df79aa7ab" />

<img width="1920" height="968" alt="Screenshot (80)" src="https://github.com/user-attachments/assets/f23ee428-3a85-4e1d-9b46-830563b87ee1" />

<img width="1920" height="980" alt="Screenshot (81)" src="https://github.com/user-attachments/assets/5590b143-6cf4-404c-8329-2179fd4f2d62" />

<img width="1920" height="973" alt="Screenshot (82)" src="https://github.com/user-attachments/assets/90422440-47b9-4f5e-8c73-2c76ccc76cb4" />

<img width="1920" height="966" alt="Screenshot (83)" src="https://github.com/user-attachments/assets/5c6f7710-752c-4f83-b423-ea5cadd0d107" />

<img width="1920" height="966" alt="Screenshot (84)" src="https://github.com/user-attachments/assets/4e564b26-39dc-4df6-a915-2330dd0571be" />

<img width="1920" height="976" alt="Screenshot (85)" src="https://github.com/user-attachments/assets/06cf18c6-173f-4166-bbed-9ce64864669e" />



Designed by Shubham Kambale
