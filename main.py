from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import os
import time
import hmac
import hashlib
import requests
import json

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
TOKEN = os.getenv("BOT_TOKEN")


def place_order(side):
    url = "https://api.bybit.com/v5/order/create"
    recv_window = "5000"
    timestamp = str(int(time.time() * 1000))

    body = {
        "category": "spot",
        "symbol": "BTCUSDT",
        "side": side,
        "orderType": "Market",
        "quoteOrderQty": "10"
    }

    body_str = json.dumps(body, separators=(",", ":"))

    param_str = timestamp + API_KEY + recv_window + body_str
    signature = hmac.new(
        bytes(API_SECRET, "utf-8"),
        param_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": recv_window,
        "X-BAPI-SIGN": signature,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=body_str)
    print(response.text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 BUY", callback_data="buy")],
        [InlineKeyboardButton("📉 SELL", callback_data="sell")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери действие:", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy":
        place_order("Buy")
        await query.edit_message_text("💰 Покупка отправлена")
    elif query.data == "sell":
        place_order("Sell")
        await query.edit_message_text("📉 Продажа отправлена")


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()
