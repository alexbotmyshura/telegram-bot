import requests
import pandas as pd
import time

# 🔑 ВСТАВЬ СВОИ ДАННЫЕ
BOT_TOKEN = "ТВОЙ_BOT_TOKEN"
CHAT_ID = "ТВОЙ_CHAT_ID"

SYMBOL = "SOLUSDT"
INTERVALS = ["5m", "15m"]

last_signal_time = {}

# 📊 DATA через proxy (работает в Railway)
def get_data(symbol, interval):
    url = f"https://api.allorigins.win/raw?url=https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"

    try:
        response = requests.get(url, timeout=15)

        if response.status_code != 200:
            print("Ошибка proxy")
            return None

        data = response.json()

        if not isinstance(data, list) or len(data) == 0:
            print("Нет данных")
            return None

        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume",
            "close_time","qav","trades","tbbav","tbqav","ignore"
        ])

        df['close'] = df['close'].astype(float)

        # EMA
        df['ema20'] = df['close'].ewm(span=20).mean()
        df['ema50'] = df['close'].ewm(span=50).mean()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        return df.iloc[-1]

    except Exception as e:
        print("Ошибка:", e)
        return None


# 🚫 Анти-дубли
def can_send(symbol, tf):
    now = time.time()
    key = f"{symbol}_{tf}"

    if key not in last_signal_time or now - last_signal_time[key] > 1800:
        last_signal_time[key] = now
        return True
    return False


# 📩 Telegram
def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text
        }, timeout=10)
    except Exception as e:
        print("Ошибка Telegram:", e)


# 🧠 УМНЫЙ ВХОД
def check_signal(data):
    close = data['close']
    ema20 = data['ema20']
    ema50 = data['ema50']
    rsi = data['rsi']

    distance = abs(close - ema20) / ema20

    # LONG
    if ema20 > ema50 and 45 < rsi < 65 and distance < 0.003:
        return {
            "type": "LONG",
            "entry": round(close, 2),
            "stop": round(close * 0.995, 2),
            "take": round(close * 1.02, 2),
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "rsi": round(rsi, 2),
            "reason": "Откат + тренд вверх"
        }

    # SHORT
    if ema20 < ema50 and 35 < rsi < 55 and distance < 0.003:
        return {
            "type": "SHORT",
            "entry": round(close, 2),
            "stop": round(close * 1.005, 2),
            "take": round(close * 0.98, 2),
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "rsi": round(rsi, 2),
            "reason": "Откат + тренд вниз"
        }

    return None


# 📝 Формат
def format_signal(sig, tf):
    return f"""
🚀 ФЬЮЧЕРС СИГНАЛ

SOLUSDT
Таймфрейм: {tf}
Тип: {sig['type']}

Вход: {sig['entry']}
Стоп: {sig['stop']}
Тейк: {sig['take']}

RR: ~1:3

EMA20: {sig['ema20']}
EMA50: {sig['ema50']}
RSI14: {sig['rsi']}

Причина: {sig['reason']}
"""


# 🔁 Цикл
def run_bot():
    send_telegram("Бот запущен 🚀")

    while True:
        try:
            for tf in INTERVALS:
                time.sleep(2)

                data = get_data(SYMBOL, tf)

                if data is None:
                    continue

                signal = check_signal(data)

                if signal and can_send(SYMBOL, tf):
                    send_telegram(format_signal(signal, tf))
                    print("Сигнал отправлен")

        except Exception as e:
            print("Ошибка:", e)

        time.sleep(90)


# 🚀 СТАРТ
run_bot()
