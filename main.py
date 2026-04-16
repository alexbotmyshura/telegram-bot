import requests
import time
import os

TELEGRAM_TOKEN = os.getenv("8789386024:AAGYqKNnmobz2oAruOLcJbcbaASEipgvD9g")
CHAT_ID = os.getenv("421535087")

last_signal = None

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})

def get_data():
    url = "https://api.coingecko.com/api/v3/coins/solana/market_chart?vs_currency=usd&days=1"
    data = requests.get(url).json()
    prices = [p[1] for p in data["prices"][-50:]]
    return prices

def ema(data, period):
    k = 2 / (period + 1)
    ema_val = data[0]
    for price in data:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val

def rsi(data, period=14):
    gains, losses = [], []
    for i in range(1, len(data)):
        diff = data[i] - data[i-1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

send_message("🚀 Futures бот запущен")

while True:
    try:
        prices = get_data()
        price = prices[-1]

        ema20 = ema(prices, 20)
        ema50 = ema(prices, 50)
        rsi_val = rsi(prices)

        print(f"Цена: {price}, EMA20: {ema20}, EMA50: {ema50}, RSI: {rsi_val}")

        # LONG сигнал
        if ema20 > ema50 and rsi_val < 35 and last_signal != "LONG":
            entry = round(price, 2)
            stop = round(price * 0.98, 2)
            take = round(price * 1.04, 2)

            send_message(
                f"🚀 LONG SOLUSDT\n\n"
                f"Вход: {entry}\n"
                f"Стоп: {stop}\n"
                f"Тейк: {take}\n\n"
                f"RSI: {round(rsi_val,2)}\n"
                f"EMA20 > EMA50\n"
                f"RR ~1:2"
            )
            last_signal = "LONG"

        # SHORT сигнал
        elif ema20 < ema50 and rsi_val > 65 and last_signal != "SHORT":
            entry = round(price, 2)
            stop = round(price * 1.02, 2)
            take = round(price * 0.96, 2)

            send_message(
                f"🔻 SHORT SOLUSDT\n\n"
                f"Вход: {entry}\n"
                f"Стоп: {stop}\n"
                f"Тейк: {take}\n\n"
                f"RSI: {round(rsi_val,2)}\n"
                f"EMA20 < EMA50\n"
                f"RR ~1:2"
            )
            last_signal = "SHORT"

    except Exception as e:
        print("Ошибка:", e)

    time.sleep(120)
