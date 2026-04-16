import requests
import time
import pandas as pd

TOKEN = "8789386024:AAGYqKNnmobz2oAruOLcJbcbaASEipgvD9g"
CHAT_ID = "421535087"

SYMBOL = "SOLUSDT"
INTERVAL = "15m"
LIMIT = 200

last_signal_time = None

# ---------- TELEGRAM ----------
def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text
        }, timeout=10)
        print("TG:", r.status_code)
    except Exception as e:
        print("TG ERROR:", e)

# ---------- BINANCE ----------
def get_data():
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit={LIMIT}"

    for _ in range(3):
        try:
            r = requests.get(url, timeout=10)
            data = r.json()

            df = pd.DataFrame(data)
            df = df.iloc[:, :6]
            df.columns = ["time", "open", "high", "low", "close", "volume"]

            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)

            df["time"] = df["time"].astype(int)
            return df

        except Exception as e:
            print("Binance error:", e)
            time.sleep(5)

    return None

# ---------- INDICATORS ----------
def calculate(df):
    df["EMA20"] = df["close"].ewm(span=20).mean()
    df["EMA50"] = df["close"].ewm(span=50).mean()

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # ATR
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs()
    ], axis=1).max(axis=1)

    df["ATR"] = tr.rolling(14).mean()

    return df

# ---------- SIGNAL ----------
def check_signal(df):
    global last_signal_time

    last = df.iloc[-1]

    price = last["close"]
    ema20 = last["EMA20"]
    ema50 = last["EMA50"]
    rsi = last["RSI"]
    atr = last["ATR"]
    candle_time = last["time"]

    if last_signal_time == candle_time:
        return None

    # LONG
    if ema20 > ema50 and rsi > 45 and price < ema20 * 1.01:
        entry = price
        stop = price - atr * 1.2
        take = price + (entry - stop) * 2.5

        last_signal_time = candle_time

        return f"""🟢 VIP LONG

{SYMBOL}
TF: {INTERVAL}

Вход: {entry:.2f}
Стоп: {stop:.2f}
Тейк: {take:.2f}

EMA20: {ema20:.2f}
EMA50: {ema50:.2f}
RSI: {rsi:.2f}
"""

    # SHORT
    if ema20 < ema50 and rsi < 55 and price > ema20 * 0.99:
        entry = price
        stop = price + atr * 1.2
        take = price - (stop - entry) * 2.5

        last_signal_time = candle_time

        return f"""🔻 VIP SHORT

{SYMBOL}
TF: {INTERVAL}

Вход: {entry:.2f}
Стоп: {stop:.2f}
Тейк: {take:.2f}

EMA20: {ema20:.2f}
EMA50: {ema50:.2f}
RSI: {rsi:.2f}
"""

    return None

# ---------- MAIN LOOP ----------
def main():
    send_message("🔥 VIP бот запущен")

    while True:
        try:
            df = get_data()

            if df is None:
                time.sleep(60)
                continue

            df = calculate(df)
            signal = check_signal(df)

            if signal:
                send_message(signal)
                time.sleep(120)

            time.sleep(60)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(60)

# ---------- START ----------
main()
