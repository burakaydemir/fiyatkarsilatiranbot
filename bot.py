import telebot
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = "TOKEN_BURAYA"

bot = telebot.TeleBot(BOT_TOKEN)

# Kullanıcının kayıtlı ürünleri
user_products = {}  # chat_id -> ["TCL 75C855", "PS5", ...]

# ----------- FİYAT ÇEKME FONKSİYONLARI -----------

def get_trendyol_price(query):
    url = f"https://www.trendyol.com/sr?q={query}"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    price = soup.select_one("div.prc-box-dscntd, span.prc-dsc")
    if price:
        return "Trendyol", int(price.text.replace(".", "").replace(",", "").replace("TL", "").strip())
    return None

def get_hepsiburada_price(query):
    url = f"https://www.hepsiburada.com/ara?q={query}"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    price = soup.select_one("span.priceValue")
    if price:
        return "Hepsiburada", int(price.text.replace(".", "").replace(",", "").replace("TL", "").strip())
    return None

def get_amazon_price(query):
    url = f"https://www.amazon.com.tr/s?k={query}"
    html = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "html.parser")
    price = soup.select_one("span.a-price-whole")
    if price:
        return "Amazon", int(price.text.replace(".", "").replace(",", "").strip())
    return None

def get_vatan_price(query):
    url = f"https://www.vatanbilgisayar.com/arama/?q={query}"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    price = soup.select_one("span.product-list__price")
    if price:
        return "Vatan", int(price.text.split("TL")[0].replace(".", "").replace(",", "").strip())
    return None

def get_mediamarkt_price(query):
    url = f"https://www.mediamarkt.com.tr/tr/search.html?query={query}"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    price = soup.select_one("div.price, span.whole")
    if price:
        return "MediaMarkt", int(price.text.replace(".", "").replace(",", "").replace("TL", "").strip())
    return None

# Toplu kontrol function
def get_all_prices(query):
    query_encoded = query.replace(" ", "+")
    
    results = []
    for func in [
        get_trendyol_price,
        get_hepsiburada_price,
        get_amazon_price,
        get_vatan_price,
        get_mediamarkt_price
    ]:
        try:
            r = func(query_encoded)
            if r:
                results.append(r)
        except:
            pass

    return sorted(results, key=lambda x: x[1])

# ------------------- TELEGRAM KOMUTLARI -------------------

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "/ekle <ürün adı>\n/kontrol\n/liste")

@bot.message_handler(commands=["ekle"])
def add_product(message):
    chat_id = message.chat.id
    query = message.text.split(" ", 1)[1].strip()

    if chat_id not in user_products:
        user_products[chat_id] = []

    user_products[chat_id].append(query)
    bot.reply_to(message, f"Ürün eklendi: {query}\n/kontrol yazarak fiyatları görebilirsin.")

@bot.message_handler(commands=["liste"])
def list_products(message):
    chat_id = message.chat.id
    if chat_id not in user_products or len(user_products[chat_id]) == 0:
        bot.reply_to(message, "Henüz ürün eklemedin.")
        return

    text = "Kayıtlı ürünler:\n\n"
    for p in user_products[chat_id]:
        text += f"- {p}\n"
    bot.reply_to(message, text)

@bot.message_handler(commands=["kontrol"])
def control_prices(message):
    chat_id = message.chat.id

    if chat_id not in user_products or len(user_products[chat_id]) == 0:
        bot.reply_to(message, "Önce ürün eklemelisin.")
        return

    for q in user_products[chat_id]:
        prices = get_all_prices(q)
        if not prices:
            bot.send_message(chat_id, f"❌ Fiyat bulunamadı: {q}")
            continue

        text = f"📊 *{q}* fiyat karşılaştırması:\n\n"
        for name, price in prices:
            text += f"• *{name}*: {price} TL\n"

        bot.send_message(chat_id, text, parse_mode="Markdown")

# Botu çalıştır
bot.infinity_polling()