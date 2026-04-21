import os
import time
import requests
import pandas as pd
from datetime import datetime

BOT_TOKEN = os.getenv("8789386024:AAEo78wFGwkWV6WGQLTS90p4xr8wYaakQCI")
CHAT_ID = os.getenv("421535087")

SYMBOL = "SOLUSDT"
INTERVAL = "15m"
CHECK_EVERY_SEC = 300  # проверка каждые 5 минут
PAUSE_AFTER_SIGNAL_SEC = 3600  # пауза после сигнала 1 час


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Нет BOT_TOKEN или CHAT_ID")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        r = requests.post(url, data=data, timeout=15)
        print("Telegram status:", r.status_code, r.text)
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)


def get_klines():
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=120"

    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()

        if not isinstance(data, list):
            print("❌ Binance вернул не список:", data)
            return pd.DataFrame()

        if len(data) < 60:
            print("❌ Слишком мало свечей:", len(data))
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=[
            "time", "open", "high", "low", "close", "volume",
            "close_time", "qav", "trades", "tbbav", "tbqav", "ignore"
        ])

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna().reset_index(drop=True)

        if df.empty:
            print("❌ DataFrame пустой после очистки")
            return pd.DataFrame()

        return df

    except Exception as e:
        print("Ошибка загрузки Binance данных:", e)
        return pd.DataFrame()


def calculate_indicators(df):
    if df.empty or len(df) < 60:
        return pd.DataFrame()

    df = df.copy()

    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()

    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    df = df.dropna().reset_index(drop=True)
    return df


def generate_signal():
    df = get_klines()
    if df.empty:
        print("Нет данных по свечам")
        return None

    df = calculate_indicators(df)
    if df.empty or len(df) < 2:
        print("Недостаточно данных после индикаторов")
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    price = round(float(last["close"]), 2)
    ema20 = round(float(last["ema20"]), 2)
    ema50 = round(float(last["ema50"]), 2)
    rsi = round(float(last["rsi"]), 2)
    volume = float(last["volume"])
    prev_volume = float(prev["volume"])

    # фильтр объема
    volume_ok_long = volume > prev_volume * 1.05
    volume_ok_short = volume > prev_volume * 1.05

    # LONG
    if (
        ema20 > ema50 and
        rsi > 55 and
        last["close"] > prev["close"] and
        volume_ok_long
    ):
        entry = price
        stop = round(price * 0.995, 2)
        take = round(price * 1.02, 2)
        rr = round((take - entry) / (entry - stop), 2)

        return f"""🚀 <b>PRO СИГНАЛ</b>

{SYMBOL}
Таймфрейм: {INTERVAL}
Тип: <b>LONG</b>

Вход: {entry}
Стоп: {stop}
Тейк: {take}
RR: ~1:{rr}

EMA20: {ema20}
EMA50: {ema50}
RSI14: {rsi}

Причина: Тренд вверх + импульс + объем
⏰ {datetime.now().strftime('%H:%M:%S')}"""

    # SHORT
    if (
        ema20 < ema50 and
        rsi < 45 and
        last["close"] < prev["close"] and
        volume_ok_short
    ):
        entry = price
        stop = round(price * 1.005, 2)
        take = round(price
