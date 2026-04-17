import requests
import time

BOT_TOKEN = "8789386024:AAEo78wFGwkWV6WGQLTS90p4xr8wYaakQCI"
CHAT_ID = "421535087"

last_signal = None
last_signal_time = 0

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text
    }
    r = requests.post(url, data=data)
    print("Telegram:", r.text)

def get_prices():
    url = "https://api.coingecko.com/api/v3/coins/solana/market_chart?vs_currency=usd&days=1"
    data = requests.get(url, timeout=20).json()
    prices = [x[1] for x in data["prices"][-60:]]
    return prices

def ema(data, period):
    k = 2 / (period + 1)
    value = data[0]
    for price in data:
        value = price * k + value * (1 - k)
    return value

def rsi(data, period=14):
    gains = []
    losses = []
    for i in range(1, len(data)):
        diff = data[i] - data[i - 1]
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

def can_send():
    global last_signal_time
    now = time.time()
    if now - last_signal_time > 60 * 60 * 3:   # не чаще 1 сигнала в 3 часа
        last_signal_time = now
        return True
    return False

send_message("🔥 SOL futures бот запущен")

while True:
    try:
        prices = get_prices()
        price = prices[-1]

        ema20 = ema(prices[-30:], 20)
        ema50 = ema(prices[-60:], 50)
        rsi_val = rsi(prices, 14)

        print(f"Цена: {price}, EMA20: {ema20}, EMA50: {ema50}, RSI: {rsi_val}")

        # LONG
        if ema20 > ema50 and 42 <= rsi_val <= 55 and last_signal != "LONG" and can_send():
            entry = round(price, 2)
            stop = round(price * 0.985, 2)
            take1 = round(price * 1.02, 2)
            take2 = round(price * 1.035, 2)

            send_message(
                f"🚀 LONG SOLUSDT\n\n"
                f"Вход: {entry}\n"
                f"Стоп: {stop}\n"
                f"Тейк 1: {take1}\n"
                f"Тейк 2: {take2}\n\n"
                f"RSI: {round(rsi_val, 2)}\n"
                f"EMA20 > EMA50\n"
                f"Логика: тренд вверх + откат"
            )
            last_signal = "LONG"

        # SHORT
        elif ema20 < ema50 and 55 <= rsi_val <= 68 and last_signal != "SHORT" and can_send():
            entry = round(price, 2)
            stop = round(price * 1.015, 2)
            take1 = round(price * 0.98, 2)
            take2 = round(price * 0.965, 2)

            send_message(
                f"🔻 SHORT SOLUSDT\n\n"
                f"Вход: {entry}\n"
                f"Стоп: {stop}\n"
                f"Тейк 1: {take1}\n"
                f"Тейк 2: {take2}\n\n"
                f"RSI: {round(rsi_val, 2)}\n"
                f"EMA20 < EMA50\n"
                f"Логика: тренд вниз + откат"
            )
            last_signal = "SHORT"

        time.sleep(120)

    except Exception as e:
        print("Ошибка:", e)
        time.sleep(30)
