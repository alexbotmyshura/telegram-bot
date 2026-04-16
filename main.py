from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 👉 ВСТАВЬ СЮДА СВОИ ДАННЫЕ
BOT_TOKEN = "8789386024:AAGYqKNnmobz2oAruOLcJbcbaASEipgvD9g"
CHAT_ID = "421535087"


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, json=payload)


@app.route("/")
def home():
    return "Bot is running"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.data.decode("utf-8")

    print("DATA:", data)

    if "BUY" in data:
        msg = f"""🚀 СИГНАЛ BUY

Пара: SOLUSDT
Таймфрейм: 15m

Вход: по рынку
Стоп: ~1%
Тейк: ~3%

Причина:
EMA20 > EMA50
RSI сильный
"""
        send_message(msg)

    elif "SELL" in data:
        msg = f"""🔻 СИГНАЛ SELL

Пара: SOLUSDT
Таймфрейм: 15m

Вход: по рынку
Стоп: ~1%
Тейк: ~3%

Причина:
EMA20 < EMA50
RSI слабый
"""
        send_message(msg)

    return "ok"


# 🔥 ВАЖНО — ДЛЯ RAILWAY
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
