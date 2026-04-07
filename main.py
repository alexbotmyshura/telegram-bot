def place_order(side):
    url = "https://api.bybit.com/v5/order/create"

    recv_window = "5000"
    timestamp = str(int(time.time() * 1000))

    body = {
        "category": "spot",
        "symbol": "BTCUSDT",
        "side": side,
        "orderType": "Market",
        "qty": "10",
        "marketUnit": "quoteCoin"
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
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": recv_window,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=body_str, timeout=20)

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)

    return response.text
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("🚀 Bot started...")

app.run_polling()
