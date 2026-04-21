import os
import time
import requests
import pandas as pd
import ta
import logging
import telebot

# Настройки логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Безопасность: токены и параметры через окружение
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")  # строка, например "123456789"

# Параметры сигнала и рисков
SYMBOLS = [
    "SOLUSDT_PERP",
    "BTCUSDT_PERP",
    # добавляйте по желанию
]
INTERVAL = "15m"
LIMIT = 200

# Расчёты SL/TP (процент от цены входа)
SL_PCT = 0.02   # 2% stop loss
TP_PCT = 0.04   # 4% take profit

if not BOT_TOKEN or not CHAT_ID:
    logging.error("BOT_TOKEN и CHAT_ID должны быть заданы как переменные окружения.")
    raise SystemExit(1)

bot = telebot.TeleBot(BOT_TOKEN)

def fetch_klines(symbol: str, interval: str, limit: int):
    # REST API Binance Futures (fapi)
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

def parse_df(data):
    df = pd.DataFrame(data, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","quote_asset_volume","trades","taker_buy_base","taker_buy_quote","ignore"
    ])
    df["close"] = df["close"].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    return df

def compute_signal(df: pd.DataFrame):
    # Добавим индикаторы
    d
f["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)

    price = df["close"].iloc[-1]
    ema20 = df["ema20"].iloc[-1]
    ema50 = df["ema50"].iloc[-1]
    rsi = df["rsi"].iloc[-1]

    # Фильтр: избегаем узких рамок РСИ вокруг 50
    if pd.isna(rsi) or 48 < rsi < 52:
        return None

    # LONG
    if price > ema20 and ema20 > ema50 and rsi > 52:
        entry = price
        sl = entry * (1 - SL_PCT)
        tp = entry * (1 + TP_PCT)
        return {
            "type": "LONG",
            "symbol": SYMBOL,
            "price": entry,
            "rsi": rsi,
            "sl": sl,
            "tp": tp
        }

    # SHORT
    if price < ema20 and ema20 < ema50 and rsi < 48:
        entry = price
        sl = entry * (1 + SL_PCT)
        tp = entry * (1 - TP_PCT)
        return {
            "type": "SHORT",
            "symbol": SYMBOL,
            "price": entry,
            "rsi": rsi,
            "sl": sl,
            "tp": tp
        }

    return None

def format_signal_message(info):
    if not info:
        return None
    direction = "LONG" if info["type"] == "LONG" else "SHORT"
    return (
        f"{direction} {info['symbol']} | Цена: {info['price']:.2f} | RSI: {info['rsi']:.2f} | "
        f"SL: {info['sl']:.2f} TP: {info['tp']:.2f}"
    )

def main_loop():
    logging.info("Старт цикла сигналов с несколькими инструментами...")
    while True:
        for symbol in SYMBOLS:
            try:
                data = fetch_klines(symbol, INTERVAL, LIMIT)
                if not data or len(data) < 50:
                    logging.warning(f"Недостаточно данных для {symbol}.")
                    continue

                df = parse_df(data)
                # Привязка сигнала к конкретному символу
                # Об
