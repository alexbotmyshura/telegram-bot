from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import requests

TOKEN = os.getenv("BOT_TOKEN")

BINANCE_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "15m"
LIMIT = 120


def get_klines(symbol: str = SYMBOL, interval: str = INTERVAL, limit: int = LIMIT):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }
    r = requests.get(BINANCE_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data


def closes_from_klines(klines):
    return [float(k[4]) for k in klines]


def ema(values, period: int):
    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)
    ema_value = sum(values[:period]) / period

    for price in values[period:]:
        ema_value = (price - ema_value) * multiplier + ema_value

    return ema_value


def rsi(values, period: int = 14):
    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, period + 1):
        delta = values[i] - values[i - 1]
        if delta >= 0:
            gains.append(delta)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(delta))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    for i in range(period + 1, len(values)):
        delta = values[i] - values[i - 1]
        gain = max(delta, 0)
        loss = max(-delta, 0)

        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def build_signal():
    klines = get_klines()
    closes = closes_from_klines(klines)

    current_price = closes[-1]
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    rsi14 = rsi(closes, 14)

    if ema20 is None or ema50 is None or rsi14 is None:
        return "Недостаточно данных"

    # Простая осторожная логика
    if ema20 > ema50 and 50 <= rsi14 <= 68:
        signal = "BUY"
        reason = "EMA20 выше EMA50, RSI в нормальной зоне роста"
    elif ema20 < ema50 and 32 <= rsi14 <= 50:
        signal = "SELL"
        reason = "EMA20 ниже EMA50, RSI слабый"
    else:
        signal = "NO TRADE"
        reason = "Нет чистого сигнала"

    return (
        f"BTCUSDT\n"
        f"Таймфрейм: 15m\n"
        f"Сигнал: {signal}\n"
        f"Цена: {current_price:.2f}\n"
        f"EMA20: {ema20:.2f}\n"
        f"EMA50: {ema50:.2f}\n"
        f"RSI14: {rsi14:.2f}\n"
        f"Причина: {reason}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бот сигналов готов.\n"
        "Команды:\n"
        "/check — проверить сигнал по BTCUSDT"
    )


async def check_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = build_signal()
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("check", check_signal))

print("Signal bot started...")

app.run_polling()
