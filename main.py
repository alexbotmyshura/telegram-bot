import requests
import time
import os

TELEGRAM_TOKEN = os.getenv("8789386024:AAGYqKNnmobz2oAruOLcJbcbaASEipgvD9g")
CHAT_ID = os.getenv("421535087")

SYMBOL = "SOLUSDT"

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})

def get_price():
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
    try:
        data = requests.get(url).json()
        return float(data["price"])
    except:
        return None

last_signal = None

while True:
    price = get_price()

    if price:
        # ПРОСТАЯ ЛОГИКА
        if price > 90 and last_signal != "BUY":
            send_message(f"🚀 BUY SOL\nЦена: {price}")
            last_signal = "BUY"

        elif price < 85 and last_signal != "SELL":
            send_message(f"🔻 SELL SOL\nЦена: {price}")
            last_signal = "SELL"

    time.sleep(60)
