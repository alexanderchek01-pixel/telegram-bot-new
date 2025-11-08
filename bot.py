import requests
import time
from datetime import datetime, timedelta
from telegram import Bot

# ==== НАСТРОЙКИ ====
TOKEN = "ВАШ_TELEGRAM_TOKEN"
CHAT_ID = "ВАШ_CHAT_ID"

bot = Bot(token=TOKEN)

CHECK_INTERVAL = 180  # каждые 3 минуты
VOLATILITY_THRESHOLD = 10.0  # % за 15 минут
PERIOD_MINUTES = 15
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1"

# данные для расчёта
last_prices = {}
last_check = {}
daily_signals = {}
daily_reset = datetime.now().date()

def get_gecko_data():
    try:
        response = requests.get(COINGECKO_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print("Ошибка получения данных CoinGecko:", e)
        return []

def reset_daily_if_needed():
    global daily_signals, daily_reset
    today = datetime.now().date()
    if today != daily_reset:
        daily_signals = {}
        daily_reset = today

def analyze_volatility():
    global last_prices, last_check, daily_signals
    alerts = []
    data = get_gecko_data()
    now = datetime.now()

    reset_daily_if_needed()

    for coin in data:
        symbol = coin["symbol"].upper()
        price = coin["current_price"]

        if symbol not in last_prices:
            last_prices[symbol] = price
            last_check[symbol] = now
            daily_signals.setdefault(symbol, 0)
            continue

        time_diff = now - last_check[symbol]
        if time_diff >= timedelta(minutes=PERIOD_MINUTES):
            old_price = last_prices[symbol]
            if old_price == 0:
                continue
            change = ((price - old_price) / old_price) * 100

            if abs(change) >= VOLATILITY_THRESHOLD:
                is_up = change > 0
                emoji = "🟢" if is_up else "🔴"
                direction = "ВЫРОС" if is_up else "УПАЛ"
                coinglass_link = f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?coin={symbol}"

                daily_signals[symbol] += 1

                msg = (
                    f"{emoji} <b>{symbol}</b>\n"
                    f"{direction} на <b>{abs(change):.2f}%</b> за 15 минут\n"
                    f"Сигнал № <b>{daily_signals[symbol]}</b> за сегодня\n"
                    f"<a href='{coinglass_link}'>Открыть карту ликвидаций</a>"
                )
                alerts.append(msg)

            last_prices[symbol] = price
            last_check[symbol] = now

    return alerts

def run():
    print("🚀 Бот запущен. Проверяю рынок CoinGecko...")
    bot.send_message(
        chat_id=CHAT_ID,
        text="🤖 Бот запущен и отслеживает рынок CoinGecko.",
        parse_mode="HTML"
    )

    last_daily_message = datetime.now() - timedelta(hours=24)

    while True:
        try:
            alerts = analyze_volatility()

            if alerts:
                full_message = "\n\n".join(alerts)
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚡ <b>Обнаружена высокая волатильность!</b>\n\n{full_message}",
                    parse_mode="HTML",
                    disable_web_page_preview=False
                )
                print("📨 Сигнал отправлен в Telegram.")
            else:
                print("Нет значительных движений.")

            if datetime.now() - last_daily_message > timedelta(hours=24):
                bot.send_message(
                    chat_id=CHAT_ID,
                    text="🤖 Бот работает стабильно. Проверяю рынок CoinGecko каждые 3 минуты.",
                    parse_mode="HTML"
                )
                last_daily_message = datetime.now()

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Ошибка в основном цикле:", e)
            time.sleep(60)

if __name__ == "__main__":
    run()
