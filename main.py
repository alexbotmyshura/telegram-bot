import time
import requests
import pandas as pd
import random
from datetime import datetime

# 🔥 ВСТАВЬ СВОИ ДАННЫЕ
BOT_TOKEN = "8789386024:AAEo78wFGwkWV6WGQLTS90p4xr8wYaakQCI"
CHAT_ID = "421535087"

SYMBOL = "SOLUSDT"
INTERVAL = "15m"

last_signal_time = 0


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

    price = round(last["close"], 2)

    # LONG
    if last["ema20"] > last["ema50"]:
        entry = price
        stop = round(price * 0.996, 2)
        take = round(price * 1.01, 2)

        return f"""🚀 LONG

{SYMBOL}
Вход: {entry}
Стоп: {stop}
Тейк: {take}

EMA20 > EMA50
⏰ {datetime.now().strftime('%H:%M')}
"""

    # SHORT
    if last["ema20"] < last["ema50"]:
        entry = price
        stop = round(price * 1.004, 2)
        take = round(price * 0.99, 2)

        return f"""🚀 SHORT

{SYMBOL}
Вход: {entry}
Стоп: {stop}
Тейк: {take}

EMA20 < EMA50
⏰ {datetime.now().strftime('%H:%M')}
"""

    return None


def main():
    global last_signal_time

    print("🤖 Бот 2-5 сигналов запущен")

    while True:
        try:
            signal = generate_signal()
            now = time.time()

            # 🔥 даем сигнал не чаще чем раз в 1–3 часа
            if signal and (now - last_signal_time > random.randint(3600, 10800)):
                print(signal)
                send_telegram(signal)
                last_signal_time = now
            else:
                print("Нет сигнала или ждём таймер...")

            time.sleep(300)  # проверка каждые 5 минут

        except Exception as e:
            print("Ошибка:", e)
            time.sleep(60)


if __name__ == "__main__":
    main()
