import telebot
import requests
import time
import os

# === Настройки ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")  # добавь этот ключ в Render
VOLATILITY_THRESHOLD = 5  # % волатильности за 1 час
CHECK_INTERVAL = 300  # проверка каждые 5 минут (в секундах)

bot = telebot.TeleBot(TOKEN)

# === Получение данных о волатильности ===
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
            price = coin.get("price", 0)

            if vol_1h and vol_1h > VOLATILITY_THRESHOLD:
                link = f"https://www.coinglass.com/t/{coin_name}"
                msg = (
                    f"🚨 *Обнаружена высокая волатильность!*\n\n"
                    f"⚡ *{coin_name}*\n"
                    f"📈 Волатильность за 1ч: *{vol_1h:.2f}%*\n"
                    f"💰 Текущая цена: *${price:.2f}*\n"
                    f"🔗 [Открыть график CoinGlass]({link})"
                )
                alerts.append(msg)

        return alerts if alerts else None

    except Exception as e:
        print("Ошибка при запросе CoinGlass API:", e)
        return None

# === Основной цикл ===
def run():
    bot.send_message(CHAT_ID, "✅ Бот запущен и следит за волатильностью монет.")
    
    while True:
        alerts = get_volatility()
        if alerts:
            for alert in alerts:
                bot.send_message(CHAT_ID, alert, parse_mode="Markdown", disable_web_page_preview=False)
        else:
            print("Нет значительных изменений.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run()
