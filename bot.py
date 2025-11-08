import requests
import telebot
import time
import os
from datetime import datetime, timedelta

# === Настройки ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CHECK_INTERVAL = 180  # каждые 3 минуты
VOLATILITY_THRESHOLD = 10.0  # движение в % за 15 минут
LOOKBACK_MINUTES = 15  # интервал анализа (в минутах)

bot = telebot.TeleBot(TOKEN)
price_history = {}  # сохраняем цену и время последнего обновления для каждой монеты

def get_market_data():
    """Получение текущих данных с CoinGecko"""
    try:
        url = (
            "https://api.coingecko.com/api/v3/coins/markets"
            "?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Ошибка при получении данных с CoinGecko:", e)
        return None

def analyze_volatility():
    """Сравнение текущих цен с ценами 15 минут назад"""
    data = get_market_data()
    if not data:
        return []

    now = datetime.now()
    alerts = []

    for coin in data:
        try:
            coin_id = coin["id"]
            name = coin["name"]
            symbol = coin["symbol"].upper()
            price = coin["current_price"]

            # если монета уже есть в истории — проверяем изменение
            if coin_id in price_history:
                old_price, timestamp = price_history[coin_id]
                elapsed = (now - timestamp).total_seconds() / 60

                if elapsed >= LOOKBACK_MINUTES:
                    change = ((price - old_price) / old_price) * 100

                    if abs(change) >= VOLATILITY_THRESHOLD:
                        direction = "🟢 выросла" if change > 0 else "🔴 упала"
                        arrow = "🟢⬆️" if change > 0 else "🔴⬇️"
                        alerts.append(
                            f"🚨 *{name}* ({symbol}) {arrow}\n"
                            f"{direction} на {abs(change):.2f}% за {LOOKBACK_MINUTES} минут.\n"
                            f"💰 Цена сейчас: ${price:.4f}\n"
                            f"[Открыть график на CoinGecko](https://www.coingecko.com/en/coins/{coin_id})"
                        )

                    # обновляем данные после проверки
                    price_history[coin_id] = (price, now)
            else:
                # добавляем монету в историю, если её ещё нет
                price_history[coin_id] = (price, now)

        except Exception:
            continue

    return alerts

def run():
    print("🚀 Бот запущен. Проверяю рынок CoinGecko каждые 3 минуты...")
    try:
        bot.send_message(CHAT_ID, "✅ Бот запущен и следит за волатильностью монет (15 мин, >10%).")
    except Exception as e:
        print("Ошибка отправки стартового сообщения:", e)

    last_daily_message = datetime.now() - timedelta(hours=24)

    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Проверяю рынок...")
            alerts = analyze_volatility()

            if alerts:
                message = "\n\n".join(alerts)
                bot.send_message(
                    CHAT_ID,
                    f"⚡ Обнаружено сильное движение (15 мин, >10%):\n\n{message}",
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
            else:
                print("Нет резких изменений за последние 15 минут.")

            # ежедневное напоминание, что бот активен
            if datetime.now() - last_daily_message > timedelta(hours=24):
                bot.send_message(CHAT_ID, "🤖 Бот активен. Проверяю рынок CoinGecko.")
                last_daily_message = datetime.now()

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Ошибка в основном цикле:", e)
            time.sleep(60)

if __name__ == "__main__":
    run()

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Ошибка в основном цикле:", e)
            time.sleep(60)

if __name__ == "__main__":
    run()
