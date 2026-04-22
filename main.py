import ccxt
import pandas as pd
import time
import requests
from datetime import datetime

# ====== НАСТРОЙКИ ======
API_TOKEN = "8789386024:AAEo78wFGwkWV6WGQLTS90p4xr8wYaakQCI"
CHAT_ID = "421535087"

SYMBOLS = ["ETH/USDT", "SOL/USDT"]
TIMEFRAME = "15m"

MAX_SIGNALS_PER_DAY = 5
COOLDOWN_MINUTES = 30

# ====== ПЕРЕМЕННЫЕ ======
last_signal = {}
signals_today = 0
last_reset_day = None
last_signal_time = {}

# ====== БИРЖА ======
exchange = ccxt.binance()

# ====== ФУНКЦИИ ======
def send_telegram(text):
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

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

def check_signal(symbol):
    global last_signal, signals_today, last_reset_day, last_signal_time

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

    # лимит сигналов
    if signals_today >= MAX_SIGNALS_PER_DAY:
        return

    # кулдаун
    if symbol in last_signal_time:
        diff = (now - last_signal_time[symbol]).total_seconds() / 60
        if diff < COOLDOWN_MINUTES:
            return

    signal = None

    # ===== LONG =====
    if ema20 > ema50 > ema200 and rsi > 55:
        entry = round(price, 2)
        stop = round(price * 0.995, 2)
        take = round(price * 1.015, 2)
        signal = "LONG"

    # ===== SHORT =====
    elif ema20 < ema50 < ema200 and rsi < 45:
        entry = round(price, 2)
        stop = round(price * 1.005, 2)
        take = round(price * 0.985, 2)
        signal = "SHORT"

    if signal:
        signal_key = f"{symbol}_{signal}_{entry}"

        # защита от дубля
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

EMA20: {round(ema20,2)}
EMA50: {round(ema50,2)}
EMA200: {round(ema200,2)}
RSI14: {round(rsi,2)}
"""

        send_telegram(message)

        last_signal[symbol] = signal_key
        last_signal_time[symbol] = now
        signals_today += 1

# ====== ЦИКЛ ======
while True:
    try:
        for symbol in SYMBOLS:
            check_signal(symbol)

        time.sleep(60)  # проверка раз в минуту

    except Exception as e:
        print("Ошибка:", e)
        time.sleep(60)
