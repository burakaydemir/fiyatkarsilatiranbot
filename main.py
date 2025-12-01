import os
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, request

TOKEN = os.environ.get("BOT_TOKEN")  # Render ortam değişkeninden gelecek
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Render domainin

DATA_FILE = "products.json"

# ------------------------- DATA UTILS -------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ------------------------- SCRAPER -------------------------
headers = {
    "User-Agent": "Mozilla/5.0"
}

def get_price(url):
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # Amazon
        if "amazon" in url:
            price = soup.select_one("#priceblock_ourprice, #priceblock_dealprice")
            if price:
                return price.text.strip()

        # Trendyol
        if "trendyol" in url:
            price = soup.select_one(".prc-dsc, .prc-slg")
            if price:
                return price.text.strip()

        # Hepsiburada
        if "hepsiburada" in url:
            price = soup.select_one(".price-list .price-value")
            if price:
                return price.text.strip()

        # MediaMarkt
        if "mediamarkt" in url:
            price = soup.select_one(".PriceBlock__PriceText")
            if price:
                return price.text.strip()

        # Vatan
        if "vatanbilgisayar" in url:
            price = soup.select_one(".product-list__price")
            if price:
                return price.text.strip()

    except Exception:
        return None

    return None


# ------------------------- TELEGRAM SEND MESSAGE -------------------------
def send_message(chat_id, text):
    requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text})


# ------------------------- FLASK (WEBHOOK) -------------------------
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Bot is running"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()

    if "message" not in update:
        return "ok"

    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    data = load_data()

    # ------------------------- /start -------------------------
    if text.startswith("/start"):
        send_message(chat_id, 
            "📊 *Fiyat Botuna Hoş Geldin*\n"
            "/urunekle [isim] [url]\n"
            "/liste\n"
            "/sil [isim]\n"
            "/fiyat [isim]"
        )
        return "ok"

    # ------------------------- /urunekle -------------------------
    if text.startswith("/urunekle"):
        try:
            parts = text.split(" ", 2)
            name = parts[1]
            url = parts[2]

            if name not in data:
                data[name] = []

            data[name].append(url)
            save_data(data)

            send_message(chat_id, f"👍 *{name}* ürünü kaydedildi.")
        except:
            send_message(chat_id, "❌ Kullanım: /urunekle tv https://...")
        return "ok"

    # ------------------------- /liste -------------------------
    if text.startswith("/liste"):
        if not data:
            send_message(chat_id, "📭 Hiç ürün yok.")
            return "ok"

        msg = "📦 Takip Edilen Ürünler:\n\n"
        for name in data:
            msg += f"• {name} ({len(data[name])} link)\n"

        send_message(chat_id, msg)
        return "ok"

    # ------------------------- /sil -------------------------
    if text.startswith("/sil"):
        try:
            name = text.split(" ")[1]
            if name in data:
                del data[name]
                save_data(data)
                send_message(chat_id, f"🗑️ *{name}* silindi.")
            else:
                send_message(chat_id, "❌ Böyle bir ürün yok.")
        except:
            send_message(chat_id, "❌ Kullanım: /sil tv")
        return "ok"

    # ------------------------- /fiyat -------------------------
    if text.startswith("/fiyat"):
        try:
            name = text.split(" ")[1]

            if name not in data:
                send_message(chat_id, "❌ Bu ürün bulunamadı.")
                return "ok"

            links = data[name]
            results = []

            for url in links:
                price = get_price(url)
                if price:
                    results.append((url, price))

            if not results:
                send_message(chat_id, "❌ Hiçbir siteden fiyat alınamadı.")
                return "ok"

            msg = f"📊 *{name}* Fiyat Karşılaştırma:\n\n"
            for url, price in results:
                msg += f"{price}\n{url}\n\n"

            send_message(chat_id, msg)

        except:
            send_message(chat_id, "❌ Kullanım: /fiyat tv")

        return "ok"

    return "ok"


# ------------------------- SET WEBHOOK -------------------------
def set_webhook():
    url = f"{BASE_URL}/setWebhook?url={WEBHOOK_URL}/{TOKEN}"
    requests.get(url)

set_webhook()

# ------------------------- RUN -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))