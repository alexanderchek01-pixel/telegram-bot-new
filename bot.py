import telebot
import requests
import time
import os
from datetime import datetime, timedelta

# === Настройки ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")

VOLATILITY_THRESHOLD = 5   # % волатильности за 1 час
CHECK_INTERVAL = 300       # каждые 5 минут (в секундах)
DAILY_MESSAGE_INTERVAL = 24 * 60 * 60  # раз в сутки

bot = telebot.TeleBot(TOKEN)
last_daily_message = datetime.now() - timedelta(days=1)  # чтобы отправить в первый день

# === Основная функция ===
def get_volatility():
    url = "https://open-api.coinglass.com/api/pro/v1/futures/volatility"
    headers = {"coinglassSecret": COINGLASS_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        if not data.get("data"):
            return None

        alerts = []
        for coin in data["data"]:
            coin_name = coin["symbol"]
            vol_1h = coin.get("volatility1h", 0)

            if vol_1h and vol_1h > VOLATILITY_THRESHOLD:
                alerts.append(f"⚡ {coin_name}: волатильность за 1ч = {vol_1h:.2f}%")

        return alerts if alerts else None

    except Exception as e:
        print("Ошибка при запросе CoinGlass API:", e)
        return None

# === Запуск бота ===
def run():
    global last_daily_message
    bot.send_message(CHAT_ID, "✅ Бот запущен и следит за волатильностью монет.")
    
    while True:
        alerts = get_volatility()

        if alerts:
            message = "\n".join(alerts)
            bot.send_message(CHAT_ID, f"🚨 Обнаружена высокая волатильность:\n\n{message}")
        else:
            print("Нет значительных изменений.")

        # Отправка ежедневного сообщения
        if datetime.now() - last_daily_message > timedelta(seconds=DAILY_MESSAGE_INTERVAL):
            bot.send_message(CHAT_ID, "📊 Бот активен. Проверяю рынок — пока без значительных изменений.")
            last_daily_message = datetime.now()

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run()
