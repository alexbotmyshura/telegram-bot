import requests
import pandas as pd
import time

# 🔑 ВСТАВЬ СВОИ ДАННЫЕ
BOT_TOKEN = "ТВОЙ_BOT_TOKEN"
CHAT_ID = "ТВОЙ_CHAT_ID"

SYMBOL = "SOLUSDT"
INTERVALS = ["5m", "15m"]

last_signal_time = {}

# 📊 Получение данных (СТАБИЛЬНО)
def get_data(symbol, interval):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        # ❗ защита от пустого ответа
        if not isinstance(data, list) or len(data) == 0:
            print("Нет данных от Binance")
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

        # ❗ защита если мало данных
        if df.empty:
            return None

        return df.iloc[-1]

    except Exception as e:
        print("Ошибка загрузки:", e)
        return None


# 🚫 Анти-дубли (раз в 30 мин)
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


# 🧠 Логика сигналов (2–4 сигнала в день)
def check_signal(data):
    close = data['close']
    ema20 = data['ema20']
    ema50 = data['ema50']
    rsi = data['rsi']

    # LONG
    if ema20 > ema50 and 50 < rsi < 70:
        return {
            "type": "LONG",
            "entry": round(close, 2),
            "stop": round(close * 0.995, 2),
            "take": round(close * 1.015, 2),
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "rsi": round(rsi, 2),
            "reason": "Тренд вверх + импульс"
        }

    # SHORT
    if ema20 < ema50 and 30 < rsi < 50:
        return {
            "type": "SHORT",
            "entry": round(close, 2),
            "stop": round(close * 1.005, 2),
            "take": round(close * 0.985, 2),
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "rsi": round(rsi, 2),
            "reason": "Тренд вниз + импульс"
        }

    return None


# 📝 Формат сообщения
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


# 🔁 Основной цикл
def run_bot():
    while True:
        try:
            for tf in INTERVALS:
                data = get_data(SYMBOL, tf)

                # ❗ если нет данных — пропускаем
                if data is None:
                    continue

                signal = check_signal(data)

                if signal and can_send(SYMBOL, tf):
                    message = format_signal(signal, tf)
                    send_telegram(message)
                    print(f"Сигнал отправлен: {tf}")

        except Exception as e:
            print("Ошибка:", e)

        time.sleep(60)


# 🚀 СТАРТ
run_bot()
