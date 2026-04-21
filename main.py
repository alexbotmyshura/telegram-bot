import os
import time
import logging
import requests
import pandas as pd
import ta
import telebot

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Переменные окружения
BOT_TOKEN = os.environ.get("8789386024:AAEo78wFGwkWV6WGQLTS90p4xr8wYaakQCI")
CHAT_ID = os.environ.get("421535087")

# Настройки
SYMBOLS = ["SOLUSDT", "BTCUSDT", "ETHUSDT"]
INTERVAL = "15m"
LIMIT = 200
SL_PCT = 0.02
TP_PCT = 0.04

if not BOT_TOKEN or not CHAT_ID:
    logging.error("Нужно задать BOT_TOKEN и CHAT_ID в переменных окружения Railway.")
    raise SystemExit(1)

bot = telebot.TeleBot(BOT_TOKEN)


def fetch_klines(symbol: str, interval: str, limit: int):
    url = (
        f"https://fapi.binance.com/fapi/v1/klines"
        f"?symbol={symbol}&interval={interval}&limit={limit}"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def parse_df(data):
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    return df


def compute_signal(df: pd.DataFrame, symbol: str):
    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)

    price = df["close"].iloc[-1]
    ema20 = df["ema20"].iloc[-1]
    ema50 = df["ema50"].iloc[-1]
    rsi = df["rsi"].iloc[-1]

    if pd.isna(rsi) or pd.isna(ema20) or pd.isna(ema50):
        return None

    if 48 < rsi < 52:
        return None

    if price > ema20 and ema20 > ema50 and rsi > 52:
        entry = price
        return {
            "type": "LONG",
            "symbol": symbol,
            "price": entry,
            "rsi": rsi,
            "sl": entry * (1 - SL_PCT),
            "tp": entry * (1 + TP_PCT)
        }

    if price < ema20 and ema20 < ema50 and rsi < 48:
        entry = price
        return {
            "type": "SHORT",
            "symbol": symbol,
            "price": entry,
            "rsi": rsi,
            "sl": entry * (1 + SL_PCT),
            "tp": entry * (1 - TP_PCT)
        }

    return None


def format_message(info: dict) -> str:
    emoji = "🟢" if info["type"] == "LONG" else "🔴"
    return (
        f"{emoji} *{info['type']}* | `{info['symbol']}`\n"
        f"💰 Цена входа: `{info['price']:.4f}`\n"
        f"📊 RSI: `{info['rsi']:.2f}`\n"
        f"🛑 Stop Loss: `{info['sl']:.4f}`\n"
        f"✅ Take Profit: `{info['tp']:.4f}`"
    )


def main_loop():
    logging.info("Бот запущен. Начинаю сканирование рынка...")
    bot.send_message(CHAT_ID, "🤖 Бот запущен и сканирует рынок...")

    while True:
        for symbol in SYMBOLS:
            try:
                data = fetch_klines(symbol, INTERVAL, LIMIT)

                if not data or len(data) < 60:
                    logging.warning(f"Мало данных для {symbol}")
                    continue

                df = parse_df(data)
                info = compute_signal(df, symbol)

                if info:
                    msg = format_message(info)
                    bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                    logging.info(f"Сигнал отправлен: {info['type']} {symbol}")
                    time.sleep(1800)
                else:
                    logging.info(f"Нет сигнала для {symbol}")

            except Exception as e:
                logging.error(f"Ошибка при обработке {symbol}: {e}")
                time.sleep(30)

        time.sleep(300)


if __name__ == "__main__":
    main_loop()
