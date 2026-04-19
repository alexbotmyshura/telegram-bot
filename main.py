import requests
import pandas as pd
import ta
import time
import telebot

# === НАСТРОЙКИ ===
BOT_TOKEN = "8789386024:AAEo78wFGwkWV6WGQLTS90p4xr8wYaakQCI"
CHAT_ID = "421535087"

symbol = "SOLUSDT"
interval = "15m"
limit = 200

bot = telebot.TeleBot(BOT_TOKEN)

# === ДАННЫЕ 15m ===
def get_data():
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        data = requests.get(url, timeout=10).json()

        if not data or len(data) < 50:
            return None

        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume",
            "close_time","qav","trades","tbav","tqav","ignore"
        ])

        df["close"] = df["close"].astype(float)
        return df
    except:
        return None

# === ТРЕНД 1H ===
def get_trend():
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=200"
        data = requests.get(url, timeout=10).json()

        if not data or len(data) < 200:
            return None

        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume",
            "close_time","qav","trades","tbav","tqav","ignore"
        ])

        df["close"] = df["close"].astype(float)
        df["ema200"] = ta.trend.ema_indicator(df["close"], window=200)

        if pd.isna(df["ema200"].iloc[-1]):
            return None

        if df["close"].iloc[-1] > df["ema200"].iloc[-1]:
            return "LONG"
        else:
            return "SHORT"
    except:
        return None

# === СИГНАЛ ===
def check_signal():
    df = get_data()
    if df is None or len(df) < 50:
        return None

    trend = get_trend()
    if trend is None:
        return None

    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)

    price = df["close"].iloc[-1]
    ema20 = df["ema20"].iloc[-1]
    ema50 = df["ema50"].iloc[-1]
    rsi = df["rsi"].iloc[-1]

    # ❌ фильтр боковика
    if pd.isna(rsi) or 45 < rsi < 55:
        return None

    # 🚀 LONG
    if trend == "LONG" and ema20 > ema50 and rsi > 55 and price <= ema20:
        entry = price
        stop = entry * 0.985
        take1 = entry * 1.02
        take2 = entry * 1.04

        return f"""🚀 LONG {symbol}

Вход: {entry:.2f}
Стоп: {stop:.2f}
Тейк: {take1:.2f} / {take2:.2f}

RSI: {rsi:.2f}
Тренд: ВВЕРХ
"""

    # 🔻 SHORT
    if trend == "SHORT" and ema20 < ema50 and rsi < 45 and price >= ema20:
        entry = price
        stop = entry * 1.015
        take1 = entry * 0.98
        take2 = entry * 0.96

        return f"""🔻 SHORT {symbol}

Вход: {entry:.2f}
Стоп: {stop:.2f}
Тейк: {take1:.2f} / {take2:.2f}

RSI: {rsi:.2f}
Тренд: ВНИЗ
"""

    return None

# === ЗАПУСК ===
print("Бот запущен...")

while True:
    try:
        signal = check_signal()

        if signal:
            bot.send_message(CHAT_ID, signal)
            print("✅ Сигнал отправлен")
            time.sleep(1800)  # пауза 30 мин после сигнала
        else:
            print("⏳ Нет сигнала")
            time.sleep(300)  # проверка каждые 5 мин

    except Exception as e:
        print("❌ Ошибка:", e)
        time.sleep(60)
