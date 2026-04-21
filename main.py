import time
import requests
import pandas as pd
from datetime import datetime

# 🔥 ВСТАВЬ СЮДА СВОИ ДАННЫЕ
BOT_TOKEN = "8789386024:AAEo78wFGwkWV6WGQLTS90p4xr8wYaakQCI"
CHAT_ID = "421535087"

SYMBOL = "SOLUSDT"
INTERVAL = "15m"


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, data=data)
        print("✅ Отправлено в Telegram")
    except Exception as e:
        print("❌ Ошибка Telegram:", e)


def get_price():
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
    data = requests.get(url).json()
    return float(data["price"])


def get_klines():
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=100"
    data = requests.get(url).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])

    df["close"] = df["close"].astype(float)
    return df


def generate_signal():
    df = get_klines()

    if len(df) < 50:
        return None

    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    price = round(last["close"], 2)

    # LONG
    if last["ema20"] > last["ema50"] and last["close"] > prev["close"]:
        entry = price
        stop = round(price * 0.995, 2)
        take = round(price * 1.02, 2)

        return f"""🚀 LONG

{SYMBOL}
Вход: {entry}
Стоп: {stop}
Тейк: {take}

⏰ {datetime.now().strftime('%H:%M')}
"""

    # SHORT
    if last["ema20"] < last["ema50"] and last["close"] < prev["close"]:
        entry = price
        stop = round(price * 1.005, 2)
        take = round(price * 0.98, 2)

        return f"""🚀 SHORT

{SYMBOL}
Вход: {entry}
Стоп: {stop}
Тейк: {take}

⏰ {datetime.now().strftime('%H:%M')}
"""

    return None


def main():
    print("🤖 Бот запущен")

    while True:
        try:
            signal = generate_signal()

            if signal:
                print(signal)
                send_telegram(signal)
                time.sleep(3600)
            else:
                print("Нет сигнала...")
                time.sleep(300)

        except Exception as e:
            print("Ошибка:", e)
            time.sleep(60)


if __name__ == "__main__":
    main()
