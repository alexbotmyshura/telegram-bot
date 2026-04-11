import os
import time
import requests

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

KRAKEN_URL = "https://api.kraken.com/0/public/OHLC"
PAIR = "SOLUSD"
INTERVAL = 15

last_signal = None


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)


def get_data():
    params = {"pair": PAIR, "interval": INTERVAL}
    r = requests.get(KRAKEN_URL, params=params)
    data = r.json()

    pair_key = list(data["result"].keys())[0]
    candles = data["result"][pair_key]

    closes = [float(c[4]) for c in candles]
    return closes


def ema(data, period):
    k = 2 / (period + 1)
    ema_val = sum(data[:period]) / period

    for price in data[period:]:
        ema_val = price * k + ema_val * (1 - k)

    return ema_val


def rsi(data, period=14):
    gains, losses = [], []

    for i in range(1, len(data)):
        diff = data[i] - data[i - 1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def check_signal():
    global last_signal

    closes = get_data()
    price = closes[-1]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    rsi14 = rsi(closes)

    signal = None
    reason = ""

    # 🟢 BUY
    if ema20 > ema50 and price > ema20 and rsi14 > 55:
        signal = "BUY"
        reason = "EMA20 выше EMA50, цена выше EMA20, RSI сильный"

    # 🔴 SELL
    elif ema20 < ema50 and price < ema20 and rsi14 < 45:
        signal = "SELL"
        reason = "EMA20 ниже EMA50, цена ниже EMA20, RSI слабый"

    if signal and signal != last_signal:
        last_signal = signal

        stop = price * (0.998 if signal == "BUY" else 1.002)
        take = price * (1.02 if signal == "BUY" else 0.98)

        message = f"""
🔔 Авто-сигнал

SOLUSD
Таймфрейм: 15m
Сигнал: {signal}
Цена: {round(price,2)}
Вход: {round(price,2)}
Стоп: {round(stop,2)}
Тейк: {round(take,2)}
RR: 1:2

EMA20: {round(ema20,2)}
EMA50: {round(ema50,2)}
RSI14: {round(rsi14,2)}

Причина: {reason}
"""
        send_telegram(message)


print("Бот запущен...")

while True:
    try:
        check_signal()
        time.sleep(60)
    except Exception as e:
        print("Ошибка:", e)
        time.sleep(60)
