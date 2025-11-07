import telebot
import requests
import time
import os
import sys
from datetime import datetime, timedelta

# === моментальная запись print() в Render Logs ===
sys.stdout.reconfigure(line_buffering=True)

# === дублирование вывода в файл ===
log_file = open("bot_output.log", "a", buffering=1)
sys.stdout = sys.stderr = log_file

# === настройки ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")

VOLATILITY_THRESHOLD = 0.5
CHECK_INTERVAL = 300
DAILY_MESSAGE_INTERVAL = 86400

bot = telebot.TeleBot(TOKEN)
last_daily_message = datetime.now() - timedelta(seconds=DAILY_MESSAGE_INTERVAL)

def get_volatility():
    url = "https://open-api.coinglass.com/api/pro/v1/futures/volatility"
    headers = {"coinglassSecret": COINGLASS_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Ошибка CoinGlass API: {response.status_code}")
            return None
        data = response.json()
        if not data.get("data"):
            print("⚠️ Нет данных в ответе CoinGlass.")
            return None

        alerts = []
        for coin in data["data"]:
            coin_name = coin["symbol"]
            vol_1h = coin.get("volatility1h", 0)
            price_change = coin.get("changePercent", 0)

            if vol_1h and vol_1h > VOLATILITY_THRESHOLD:
                arrow = "🟢⬆️" if price_change > 0 else "🔴⬇️"
                link = f"https://www.coinglass.com/FutureSyn/{coin_name}"
                alert_msg = (
                    f"{arrow} *{coin_name}*\n"
                    f"Волатильность за 1ч: *{vol_1h:.2f}%*\n"
                    f"Изменение цены: *{price_change:.2f}%*\n"
                    f"[Открыть график]({link})"
                )
                alerts.append((vol_1h, alert_msg))
        alerts.sort(key=lambda x: x[0], reverse=True)
        return [msg for _, msg in alerts] if alerts else None

    except Exception as e:
        print("❌ Ошибка при запросе CoinGlass API:", e)
        return None


def run():
    global last_daily_message
    print("🚀 Бот запущен. Начинаю выполнение run()...")

    try:
        bot.send_message(CHAT_ID, "✅ Бот запущен и следит за волатильностью монет.")
        print("✅ Стартовое сообщение успешно отправлено в Telegram.")
    except Exception as e:
        print("❌ Ошибка при отправке стартового сообщения:", e)

    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Проверяю данные с CoinGlass...")
        alerts = get_volatility()
        if alerts:
            print(f"🚨 Найдены сигналы: {len(alerts)}")
            for alert in alerts:
                try:
                    bot.send_message(CHAT_ID, alert, parse_mode="Markdown", disable_web_page_preview=False)
                    time.sleep(1)
                except Exception as e:
                    print("⚠️ Ошибка при отправке сообщения в Telegram:", e)
        else:
            print("Нет значительных изменений.")

        if datetime.now() - last_daily_message > timedelta(seconds=DAILY_MESSAGE_INTERVAL):
            try:
                bot.send_message(CHAT_ID, "📊 Бот активен. Проверяю рынок — пока без значительных изменений.")
                last_daily_message = datetime.now()
            except Exception as e:
                print("Не удалось отправить ежедневное сообщение:", e)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    print("🧠 Основной блок выполняется — бот начинает запуск.")
    run()
