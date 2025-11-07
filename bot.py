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
last_daily_message = datetime.now() - timedelta(days=1)

# === Получение данных о волатильности ===
def get_volatility():
    url = "https://open-api.coinglass.com/api/pro/v1/futures/volatility"
    headers = {"coinglassSecret": COINGLASS_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        if not data.get("data"):
            return None

        alerts = []
        for coin in data["data"]:
            coin_name = coin.get("symbol")
            vol_1h = coin.get("volatility1h", 0)
            price = coin.get("price", 0)

            if vol_1h and vol_1h > VOLATILITY_THRESHOLD:
                # Ссылка на график CoinGlass
                coinglass_link = f"https://www.coinglass.com/t/{coin_name}"
                msg = (
                    f"🚨 *Обнаружена высокая волатильность!*\n\n"
                    f"⚡ *{coin_name}*\n"
                    f"📈 Волатильность за 1ч: *{vol_1h:.2f}%*\n"
                    f"💰 Текущая цена: *${price:.2f}*\n"
                    f"🔗 [Открыть график CoinGlass]({coinglass_link})"
                )
                alerts.append(msg)

        return alerts if alerts else None

    except Exception as e:
        print("Ошибка при запросе CoinGlass API:", e)
        return None

# === Основной цикл ===
def run():
    global last_daily_message
    try:
        bot.send_message(CHAT_ID, "✅ Бот запущен и следит за волатильностью монет.")
    except Exception as e:
        print("Не удалось отправить стартовое сообщение:", e)

    while True:
        alerts = get_volatility()

        if alerts:
            for alert in alerts:
                # Используем Markdown, включаем превью встраиваемой ссылки
                bot.send_message(CHAT_ID, alert, parse_mode="Markdown", disable_web_page_preview=False)
        else:
            print("Нет значительных изменений.")

        # Ежедневное уведомление о том, что бот активен
        if datetime.now() - last_daily_message > timedelta(seconds=DAILY_MESSAGE_INTERVAL):
            try:
                bot.send_message(CHAT_ID, "📊 Бот активен. Проверяю рынок — пока без значительных изменений.")
            except Exception as e:
                print("Не удалось отправить ежедневное сообщение:", e)
            last_daily_message = datetime.now()

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run()
