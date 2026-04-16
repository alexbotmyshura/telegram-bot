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
        r = requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": text},
            timeout=10
        )
        print("TG:", r.status_code, r.text)
    except Exception as e:
        print("TG ERROR:", e)

# ---------- BINANCE ----------
def get_data():
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit={LIMIT}"

    for _ in range(3):
        try:
            r = requests.get(url, timeout=10)
            data = r.json()

            if not isinstance(data, list):
                print("BINANCE BAD RESPONSE:", data)
                time.sleep(5)
                continue

            df = pd.DataFrame(data)
            df = df.iloc[:, :6]
            df.columns = ["time", "open", "high", "low", "close", "volume"]

            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)

            df["time"] = df["time"].astype(int)
            return df

        except Exception as e:
            print("BINANCE ERROR:", e)
            time.sleep(5)

    return None

# ---------- INDICATORS ----------
def calculate(df):
    df["EMA20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["close"].ewm(span=50, adjust=False).mean()

    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs()
    ], axis=1).max(axis=1)

    df["ATR"] = tr.rolling(14).mean()
    df["VOL_MA20"] = df["volume"].rolling(20).mean()

    return df

# ---------- SIGNAL ----------
def check_signal(df):
    global last_signal_time

    if len(df) < 60:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    price = float(last["close"])
    open_price = float(last["open"])
    high = float(last["high"])
    low = float(last["low"])

    ema20 = float(last["EMA20"])
    ema50 = float(last["EMA50"])
    rsi = float(last["RSI"])
    atr = float(last["ATR"])
    vol = float(last["volume"])
    vol_ma = float(last["VOL_MA20"])
    candle_time = int(last["time"])

    if pd.isna(rsi) or pd.isna(atr) or pd.isna(vol_ma):
        return None

    # Антидубли
    if last_signal_time == candle_time:
        return None

    # Подтверждение свечи
    bullish_candle = price > open_price
    bearish_candle = price < open_price

    # Объём: умеренный фильтр, чтобы не было слишком редко
    volume_ok = vol >= vol_ma * 0.75

    # Цена рядом с EMA20, но не слишком жёстко
    near_ema_long = price <= ema20 * 1.012
    near_ema_short = price >= ema20 * 0.988

    # LONG: активный VIP
    if (
        ema20 > ema50
        and 42 <= rsi <= 68
        and near_ema_long
        and bullish_candle
        and volume_ok
    ):
        entry = price
        stop = entry - atr * 1.15
        take = entry + (entry - stop) * 2.2
        rr = (take - entry) / (entry - stop) if entry > stop else 0

        last_signal_time = candle_time

        return f"""🟢 VIP LONG

{SYMBOL}
TF: {INTERVAL}

Вход: {entry:.2f}
Стоп: {stop:.2f}
Тейк: {take:.2f}

RR: ~1:{rr:.1f}

EMA20: {ema20:.2f}
EMA50: {ema50:.2f}
RSI: {rsi:.2f}
ATR: {atr:.2f}

Причина: Тренд вверх + активный откат + подтверждающая свеча"""

    # SHORT: активный VIP
    if (
        ema20 < ema50
        and 32 <= rsi <= 58
        and near_ema_short
        and bearish_candle
        and volume_ok
    ):
        entry = price
        stop = entry + atr * 1.15
        take = entry - (stop - entry) * 2.2
        rr = (entry - take) / (stop - entry) if stop > entry else 0

        last_signal_time = candle_time

        return f"""🔻 VIP SHORT

{SYMBOL}
TF: {INTERVAL}

Вход: {entry:.2f}
Стоп: {stop:.2f}
Тейк: {take:.2f}

RR: ~1:{rr:.1f}

EMA20: {ema20:.2f}
EMA50: {ema50:.2f}
RSI: {rsi:.2f}
ATR: {atr:.2f}

Причина: Тренд вниз + активный откат + подтверждающая свеча"""

    return None

# ---------- MAIN ----------
def main():
    send_message("🔥 ACTIVE VIP бот запущен")

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
                time.sleep(90)

            time.sleep(60)

        except Exception as e:
            print("MAIN ERROR:", e)
            time.sleep(60)

main()
