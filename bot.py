import requests
import telebot
import time
import os
from datetime import datetime, timedelta

# === Настройки ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CHECK_INTERVAL = 300  # каждые 5 минут
VOLATILITY_THRESHOLD = 10.0  # 10% движение за 24 часа

bot = telebot.TeleBot(TOKEN)

# === Получаем данные с CoinGecko ===
def get_market_data():
    try:
        url = (
            "https://api.coingecko.com/api/v3/coins/markets"
            "?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&price_change_percentage=24h"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Ошибка при получении данных с CoinGecko:", e)
        return None

# === Проверяем волатильность монет ===
def get_volatile_coins():
    data = get_market_data()
    if not data:
        return []

    alerts = []
    for coin in data:
        try:
            change = coin.get("price_change_percentage_24h", 0)
            name = coin.get("name", "Unknown")
            symbol = coin.get("symbol", "").upper()
            price = coin.get("current_price", 0)

            if change is None:
                continue

            if abs(change) >= VOLATILITY_THRESHOLD:
                direction = "🟢 выросла" if change > 0 else "🔴 упала"
                arrow = "🟢⬆️" if change > 0 else "🔴⬇️"
                alert = (
                    f"🚨 *{name}* ({symbol}) {arrow}\n"
                    f"{direction} на {abs(change):.2f}% за 24 часа.\n"
                    f"💰 Текущая цена: ${price:.4f}\n"
                    f"[Открыть на CoinGecko](https://www.coingecko.com/en/coins/{coin['id']})"
                )
                alerts.append(alert)
        except Exception:
            continue

    return alerts

# === Основной цикл ===
def run():
    print("🚀 Бот запущен. Проверяю рынок через CoinGecko...")
    try:
        bot.send_message(CHAT_ID, "✅ Бот запущен. Следит за волатильностью монет через CoinGecko (24h > 10%).")
    except Exception as e:
        print("Ошибка отправки стартового сообщения:", e)

    last_daily_message = datetime.now() - timedelta(hours=24)

    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Проверяю данные с CoinGecko...")
            alerts = get_volatile_coins()

            if alerts:
                full_message = "\n\n".join(alerts)
                bot.send_message(
                    CHAT_ID,
                    f"⚡ Обнаружена сильная волатильность:\n\n{full_message}",
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
            else:
                print("Нет значительных изменений.")

            # Каждые 24 часа пишет, что бот активен
            if datetime.now() - last_daily_message > timedelta(hours=24):
                bot.send_message(CHAT_ID, "🤖 Бот активен. Проверяю рынок CoinGecko.")
                last_daily_message = datetime.now()

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Ошибка в основном цикле:", e)
            time.sleep(60)

if __name__ == "__main__":
    run()
