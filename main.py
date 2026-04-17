import requests
import time

BOT_TOKEN = "ТВОЙ_НОВЫЙ_ТОКЕН"
CHAT_ID = "421535087"

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text
    }
    r = requests.post(url, data=data)
    print(r.text)

send_message("✅ Telegram работает")
time.sleep(5)
