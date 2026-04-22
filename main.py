import ccxt
import pandas as pd
import time
import requests
import os
from datetime import datetime

# ====== НАСТРОЙКИ ======
API_TOKEN = os.getenv("8789386024:AAEo78wFGwkWV6WGQLTS90p4xr8wYaakQCI")
CHAT_ID = os.getenv("421535087")

SYMBOLS = ["ETH/USDT", "SOL/USDT"]
TIMEFRAME = "15m"

MAX_SIGNALS_PER_DAY = 5
COOLDOWN_MINUTES = 30

# ====== ПЕРЕМЕННЫЕ ======
last_signal = {}
signals_today = 0
last_reset_day = None
last_signal_time = {}

exchange = ccxt.binance()

# ====== TELEGRAM ======
def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print("Ошибка отправки:", e)

# ====== ДАННЫЕ ======
def get_data(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=100)
    df = pd.DataFrame(ohlcv, columns=["time","open","high","low","close","volume"])
    return df

def indicators(df):
    df["EMA20"] = df["close"].ewm(span=20).mean()
    df["EMA50"] = df["close"].ewm(span=50).mean()
    df["EMA200"] = df["close"].ewm(span=200).mean()

    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    return df

# ====== ЛОГИКА ======
def check_signal(symbol):
    global last_signal, signals_today, last_reset_day, last_signal_time

    try:
        df = get_data(symbol)
        df = indicators(df)

        last = df.iloc[-1]

        price = last["close"]
        ema20 = last["EMA20"]
        ema50 = last["EMA50"]
        ema200 = last["EMA200"]
        rsi = last["RSI"]

        now = datetime.now()
        today = now.date()

        # сброс дня
        if last_reset_day != today:
            signals_today = 0
            last_reset_day = today

        # лимит
        if signals_today >= MAX_SIGNALS_PER_DAY:
            return

        # кулдаун
        if symbol in last_signal_time:
            diff = (now - last_signal_time[symbol]).total_seconds() / 60
            if diff < COOLDOWN_MINUTES:
                return

        signal = None

        # LONG
        if ema20 > ema50 > ema200 and rsi > 55:
            entry = round(price, 2)
            stop = round(price * 0.995, 2)
            take = round(price * 1.015, 2)
            signal = "LONG"

        # SHORT
        elif ema20 < ema50 < ema200 and rsi < 45:
            entry = round(price, 2)
            stop = round(price * 1.005, 2)
            take = round(price * 0.985, 2)
            signal = "SHORT"

        if signal:
            signal_key = f"{symbol}_{signal}_{entry}"

            # анти-дубль
            if symbol in last_signal and last_signal[symbol] == signal_key:
                return

            message = f"""🚀 ФЬЮЧЕРС СИГНАЛ

{symbol.replace("/", "")}
Таймфрейм: {TIMEFRAME}
Тип: {signal}

Вход: {entry}
Стоп: {stop}
Тейк: {take}

RR: ~1:3
"""

            send_telegram(message)

            print("Отправлен сигнал:", symbol, signal)

            last_signal[symbol] = signal_key
            last_signal_time[symbol] = now
            signals_today += 1

    except Exception as e:
        print("Ошибка сигнала:", e)

# ====== СТАРТ ======
print("Бот запущен...")

if not API_TOKEN or not CHAT_ID:
    print("❌ Добавь API_TOKEN и CHAT_ID в Railway Variables")

while True:
    for symbol in SYMBOLS:
        check_signal(symbol)

    time.sleep(60)
