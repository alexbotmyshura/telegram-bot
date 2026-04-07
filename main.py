from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import requests
import asyncio

TOKEN = os.getenv("BOT_TOKEN")

KRAKEN_URL = "https://api.kraken.com/0/public/OHLC"
PAIR = "XBTUSDT"
INTERVAL = 15
CHECK_EVERY_SECONDS = 900  # 15 минут

last_signal_sent = None


def get_kraken_ohlc(pair: str = PAIR, interval: int = INTERVAL):
    params = {
        "pair": pair,
        "interval": interval
    }
    r = requests.get(KRAKEN_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    if data.get("error"):
        raise Exception(f"Kraken error: {data['error']}")

    result = data["result"]

    pair_key = None
    for key in result.keys():
        if key != "last":
            pair_key = key
            break

    if not pair_key:
        raise Exception("Не удалось получить свечи Kraken")

    return result[pair_key]


def closes_from_ohlc(ohlc):
    return [float(candle[4]) for candle in ohlc]


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


def get_signal_data():
    ohlc = get_kraken_ohlc()
    closes = closes_from_ohlc(ohlc)

    current_price = closes[-1]
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    rsi14 = rsi(closes, 14)

    if ema20 is None or ema50 is None or rsi14 is None:
        return None

    if ema20 > ema50 and 50 <= rsi14 <= 68:
        signal = "BUY"
        reason = "EMA20 выше EMA50, RSI в зоне роста"
    elif ema20 < ema50 and 32 <= rsi14 <= 50:
        signal = "SELL"
        reason = "EMA20 ниже EMA50, RSI слабый"
    else:
        signal = "NO TRADE"
        reason = "Нет чистого сигнала"

    message = (
        f"BTCUSDT\n"
        f"Таймфрейм: 15m\n"
        f"Сигнал: {signal}\n"
        f"Цена: {current_price:.2f}\n"
        f"EMA20: {ema20:.2f}\n"
        f"EMA50: {ema50:.2f}\n"
        f"RSI14: {rsi14:.2f}\n"
        f"Причина: {reason}"
    )

    return {
        "signal": signal,
        "message": message
    }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бот сигналов готов.\n"
        "Команды:\n"
        "/check — проверить сигнал\n"
        "/id — показать твой chat_id\n"
        "/setchat — сохранить этот чат для авто-сигналов"
    )


async def check_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = get_signal_data()
        if not data:
            await update.message.reply_text("Недостаточно данных")
            return

        await update.message.reply_text(data["message"])
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")


async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Твой chat_id: {update.effective_chat.id}")


async def set_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    with open("chat_id.txt", "w") as f:
        f.write(chat_id)

    await update.message.reply_text(f"Чат сохранён для авто-сигналов: {chat_id}")


def load_chat_id():
    try:
        with open("chat_id.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


async def auto_signal_loop(app):
    global last_signal_sent

    while True:
        try:
            chat_id = load_chat_id()
            if chat_id:
                data = get_signal_data()
                if data:
                    signal = data["signal"]

                    if signal in ["BUY", "SELL"]:
                        if signal != last_signal_sent:
                            await app.bot.send_message(chat_id=chat_id, text=f"🔔 Авто-сигнал\n\n{data['message']}")
                            last_signal_sent = signal
                    else:
                        last_signal_sent = None

        except Exception as e:
            print("AUTO SIGNAL ERROR:", str(e))

        await asyncio.sleep(CHECK_EVERY_SECONDS)


async def on_startup(app):
    asyncio.create_task(auto_signal_loop(app))
    print("🚀 Auto signal bot started...")


app = ApplicationBuilder().token(TOKEN).post_init(on_startup).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("check", check_signal))
app.add_handler(CommandHandler("id", get_chat_id))
app.add_handler(CommandHandler("setchat", set_chat))

app.run_polling()
