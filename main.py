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
        data = {
            "chat_id": CHAT_ID,
            "text": message
        }
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Ошибка отправки:", e)

def get_data(symbol):
    try:
        # ✅ альтернативный Binance endpoint (работает на Railway)
        url = f"https://api.binance.me/api/v3/klines?symbol={symbol}&interval={TIMEFRAME}&limit=100"
        response = requests.get(url, timeout=10)
        data = response.json()

        if not data or isinstance(data, dict):
            print(f"{symbol} — нет данных от Binance")
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

    # ✅ защита от ошибки
    if df is None or df.empty or len(df) < 50:
        print(f"{symbol} — пропуск (нет данных)")
        return

    # EMA
    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    # RSI
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

    # 🔥 баланс сигналов (2–5 в день)
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
Таймфрейм: {TIMEFRAME}
Тип: {signal}

Вход: {entry:.2f}
Стоп: {stop:.2f}
Тейк: {take:.2f}

RR: ~1:3

EMA20: {ema20:.2f}
EMA50: {ema50:.2f}
RSI: {rsi:.2f}
"""
        send_telegram(message)
        print(f"{symbol} сигнал отправлен")
    else:
        print(f"{symbol} — нет сигнала")

# 🔁 основной цикл
while True:
    for symbol in SYMBOLS:
        try:
            analyze(symbol)
        except Exception as e:
            print("Ошибка анализа:", e)

    time.sleep(60)
