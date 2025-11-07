import telebot
import requests
import time
import os

# === Настройки ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")  # добавим этот ключ в Render
VOLATILITY_THRESHOLD = 5  # % волатильности за 1 час
CHECK_INTERVAL = 300  # каждые 5 минут (в секундах)

bot = telebot.TeleBot(TOKEN)

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
    bot.send_message(CHAT_ID, "✅ Бот запущен и следит за волатильностью монет.")
    
    while True:
        alerts = get_volatility()
        if alerts:
            message = "\n".join(alerts)
            bot.send_message(CHAT_ID, f"🚨 Обнаружена высокая волатильность:\n\n{message}")
        else:
            print("Нет значительных изменений.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run()
