import os
import time
import requests
import pandas as pd
from datetime import datetime

BOT_TOKEN = os.getenv("8789386024:AAEo78wFGwkWV6WGQLTS90p4xr8wYaakQCI")
CHAT_ID = os.getenv("421535087")

SYMBOL = "SOLUSDT"
INTERVAL = "15m"


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Нет BOT_TOKEN или CHAT_ID")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)


def get_klines():
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=100"
    data = requests.get(url).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])

    df["close"] = df["close"].astype(float)
    return df


def calculate_indicators(df):
    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    return df


def generate_signal():
    df = get_klines()
    df = calculate_indicators(df)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    price = round(last["close"], 2)
    ema20 = round(last["ema20"], 2)
    ema50 = round(last["ema50"], 2)
    rsi = round(last["rsi"], 2)

    signal = None

    # LONG
    if ema20 > ema50 and rsi > 55 and last["close"] > prev["close"]:
        entry = price
        stop = round(price * 0.995, 2)
        take = round(price * 1.02, 2)

        signal = f"""
🚀 <b>PRO СИГНАЛ</b>

{SYMBOL}
Таймфрейм: 15m
Тип: <b>LONG</b>

Вход: {entry}
Стоп: {stop}
Тейк: {take}

EMA20: {ema20}
EMA50: {ema50}
RSI: {rsi}

Причина: Восходящий тренд + импульс
⏰ {datetime.now().strftime('%H:%M')}
"""

    # SHORT
    elif ema20 < ema50 and rsi < 45 and last["close"] < prev["close"]:
        entry = price
        stop = round(price * 1.005, 2)
        take = round(price * 0.98, 2)

        signal = f"""
🚀 <b>PRO СИГНАЛ</b>

{SYMBOL}
Таймфрейм: 15m
Тип: <b>SHORT</b>

Вход: {entry}
Стоп: {stop}
Тейк: {take}

EMA20: {ema20}
EMA50: {ema50}
RSI: {rsi}

Причина: Нисходящий тренд + давление
⏰ {datetime.now().strftime('%H:%M')}
"""

    return signal


def main():
    print("🤖 PRO бот запущен")

    while True:
        signal = generate_signal()

        if signal:
            print(signal)
            send_telegram(signal)
            time.sleep(3600)  # пауза после сигнала
        else:
            print("Нет сигнала...")
            time.sleep(300)  # проверка каждые 5 мин


if __name__ == "__main__":
    main()
