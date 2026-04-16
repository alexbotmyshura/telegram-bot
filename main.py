import requests
import time
import os

TELEGRAM_TOKEN = os.getenv("8789386024:AAGYqKNnmobz2oAruOLcJbcbaASEipgvD9g")
CHAT_ID = os.getenv("421535087")

last_signal = None

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})

def get_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
        data = requests.get(url).json()
        return float(data["solana"]["usd"])
    except:
        return None

send_message("✅ Бот запущен")

while True:
    price = get_price()

    if price:
        print("Цена:", price)

        if price > 90 and last_signal != "BUY":
            send_message(f"🚀 BUY SOL\nЦена: {price}")
            last_signal = "BUY"

        elif price < 85 and last_signal != "SELL":
            send_message(f"🔻 SELL SOL\nЦена: {price}")
            last_signal = "SELL"

    time.sleep(60)
