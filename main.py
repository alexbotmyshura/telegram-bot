import requests
import time
from binance.client import Client

# 🔑 ВСТАВЬ СВОИ ДАННЫЕ
TELEGRAM_TOKEN = "ТВОЙ_ТОКЕН"
CHAT_ID = "ТВОЙ_CHAT_ID"

client = Client()

SYMBOL = "SOLUSDT"
TIMEFRAME = Client.KLINE_INTERVAL_15MINUTE

last_signal = None


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)


def get_data():
    klines = client.get_klines(symbol=SYMBOL, interval=TIMEFRAME, limit=100)
    closes = [float(k[4]) for k in klines]
    return closes


def ema(data, period):
    ema_values = []
    k = 2 / (period + 1)
    for i in range(len(data)):
        if i < period:
            ema_values.append(sum(data[:period]) / period)
        else:
            ema_values.append(data[i] * k + ema_values[-1] * (1 - k))
    return ema_values


def rsi(data, period=14):
    gains = []
    losses = []

    for i in range(1, len(data)):
        change = data[i] - data[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def check_signal():
    global last_signal

    closes = get_data()

    ema20 = ema(closes, 20)[-1]
    ema50 = ema(closes, 50)[-1]
    rsi_value = rsi(closes)
    price = closes[-1]

    signal = None
    reason = ""

    # 🔴 SELL
    if ema20 < ema50 and price < ema20 and rsi_value < 45:
        signal = "SELL"
        reason = "EMA20 ниже EMA50, цена ниже EMA20, RSI слабый"

    # 🟢 BUY
    elif ema20 > ema50 and price > ema20 and rsi_value > 55:
        signal = "BUY"
        reason = "EMA20 выше EMA50, цена выше EMA20, RSI сильный"

    # ❗ чтобы не спамил одинаковыми сигналами
    if signal and signal != last_signal:
        last_signal = signal

        stop = price * (1.002 if signal == "SELL" else 0.998)
        take = price * (0.98 if signal == "SELL" else 1.02)

        message = f"""
🔔 SOLUSDT Сигнал

Таймфрейм: 15m
Сигнал: {signal}
Цена: {round(price, 2)}
Вход: {round(price, 2)}
Стоп: {round(stop, 2)}
Тейк: {round(take, 2)}
RR: 1:2

EMA20: {round(ema20, 2)}
EMA50: {round(ema50, 2)}
RSI14: {round(rsi_value, 2)}

Причина: {reason}
"""
        send_telegram(message)


while True:
    try:
        check_signal()
        time.sleep(60)
    except Exception as e:
        print("Ошибка:", e)
        time.sleep(60)
