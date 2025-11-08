import os
import requests
import time
from datetime import datetime, timedelta
from telegram import Bot

# ==== НАСТРОЙКИ ====
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")  # можно строкой

if not TOKEN or not CHAT_ID:
    raise SystemExit("TELEGRAM_TOKEN или TELEGRAM_CHAT_ID не выставлены в окружении")

bot = Bot(token=TOKEN)

CHECK_INTERVAL = 180  # проверка каждые 3 минуты
VOLATILITY_THRESHOLD = 10.0  # % изменения за 15 минут
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"
PARAMS = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250, "page": 1, "sparkline": "false", "price_change_percentage": "15m"}

# Храним последние цены и счётчики
last_prices = {}
last_check = {}
daily_signals = {}  # счетчик сигналов по монете за день
daily_reset = datetime.now()

def get_coingecko_data():
    try:
        r = requests.get(COINGECKO_API_URL, params=PARAMS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Ошибка Coingecko:", e)
        return []

def analyze_volatility():
    global last_prices, last_check, daily_signals, daily_reset
    alerts = []
    data = get_coingecko_data()
    now = datetime.now()

    # сброс счётчиков раз в сутки
    if now - daily_reset > timedelta(hours=24):
        daily_signals = {}
        daily_reset = now

    for coin in data:
        # Coingecko возвращает 'id' и 'symbol' и 'current_price'
        coin_id = coin.get("id")
        symbol = coin.get("symbol", "").upper()
        price = coin.get("current_price")

        if coin_id is None or price is None:
            continue

        # стартовая инициализация
        if coin_id not in last_prices:
            last_prices[coin_id] = price
            last_check[coin_id] = now
            continue

        time_diff = now - last_check[coin_id]
        if time_diff >= timedelta(minutes=15):
            old_price = last_prices[coin_id]
            if old_price == 0:
                last_prices[coin_id] = price
                last_check[coin_id] = now
                continue

            change = ((price - old_price) / old_price) * 100

            if abs(change) >= VOLATILITY_THRESHOLD:
                # счётчик за день
                daily_signals[coin_id] = daily_signals.get(coin_id, 0) + 1

                direction_emoji = "🟢" if change > 0 else "🔴"
                direction_text = "ВЫРОС" if change > 0 else "УПАЛ"
                # сделать ссылку CoinGlass; CoinGlass принимает тикер (например BTC). Возьмём symbol
                coinglass_link = f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?coin={symbol}"

                msg = (
                    f"{direction_emoji} *{symbol}* ({coin_id}) {direction_text} на *{abs(change):.2f}%* за 15 минут\n"
                    f"🔢 Сигналов за сегодня: *{daily_signals[coin_id]}*\n"
                    f"🔗 [CoinGlass Liquidation Map]({coinglass_link})"
                )
                alerts.append(msg)

            # обновляем
            last_prices[coin_id] = price
            last_check[coin_id] = now

    return alerts

def run():
    print("🚀 Бот запущен. Проверяю Coingecko...")
    last_daily_message = datetime.now() - timedelta(hours=24)

    while True:
        try:
            alerts = analyze_volatility()

            if alerts:
                full_message = "\n\n".join(alerts)
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚡ *Обнаружена высокая волатильность:*\n\n{full_message}",
                    parse_mode="Markdown",
                    disable_web_page_preview=False
                )
                print("📨 Отправлен сигнал в Telegram.")
            else:
                print("Нет значительных движений.")

            # ежедневное сообщение о статусе
            if datetime.now() - last_daily_message > timedelta(hours=24):
                bot.send_message(
                    CHAT_ID,
                    "🤖 Бот активен. Проверяю рынок Coingecko.",
                )
                last_daily_message = datetime.now()

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Ошибка в основном цикле:", e)
            time.sleep(60)

if __name__ == "__main__":
    run()
