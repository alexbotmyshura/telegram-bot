import requests
import time
import pandas as pd

TELEGRAM_TOKEN = "8789386024:AAEo78wFGwkWV6WGQLTS90p4xr8wYaakQCI"
CHAT_ID = "421535087"

SYMBOLS = ["SOLUSDT", "ETHUSDT"]
TIMEFRAME = "15m"

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message}, timeout=10)
    except Exception as e:
        print("Ошибка отправки:", e)

def get_data(symbol):
    try:
        # ✅ публичный прокси Binance (работает без блокировок)
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={TIMEFRAME}&limit=100"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"{symbol} — ошибка HTTP")
            return None

        data = response.json()

        if not data:
            print(f"{symbol} — пусто")
            return None

        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume",
            "ct","qav","trades","tbbav","tbqav","ignore"
        ])

        df["close"] = df["close"].astype(float)

        return df

    except Exception as e:
        print("Ошибка загрузки:", e)
        return None

def analyze(symbol):
    df = get_data(symbol)

    if df is None or len(df) < 50:
        print(f"{symbol} — пропуск")
        return

    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    last = df.iloc[-1]

    price = last["close"]
    ema20 = last["ema20"]
    ema50 = last["ema50"]
    rsi = last["rsi"]

    signal = None

    if ema20 > ema50 and rsi > 50:
        signal = "LONG"
        entry = price
        stop = price * 0.995
        take = price * 1.015

    elif ema20 < ema50 and rsi < 50:
        signal = "SHORT"
        entry = price
        stop = price * 1.005
        take = price * 0.985

    if signal:
        message = f"""
🚀 ФЬЮЧЕРС СИГНАЛ

{symbol}
Таймфрейм: 15m
Тип: {signal}

Вход: {entry:.2f}
Стоп: {stop:.2f}
Тейк: {take:.2f}

RR: ~1:3
"""
        send_telegram(message)
        print(f"{symbol} сигнал отправлен")
    else:
        print(f"{symbol} — нет сигнала")

while True:
    for symbol in SYMBOLS:
        analyze(symbol)

    time.sleep(60)
