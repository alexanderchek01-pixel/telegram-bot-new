import requests
import time
from datetime import datetime, timedelta
from telegram import Bot

# ==== НАСТРОЙКИ ====
TOKEN = "ВАШ_TELEGRAM_TOKEN"
CHAT_ID = "ВАШ_CHAT_ID"

bot = Bot(token=TOKEN)

CHECK_INTERVAL = 180  # Проверка каждые 3 минуты
VOLATILITY_THRESHOLD = 10.0  # % изменения за 15 минут
OKX_API_URL = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"

# Храним последние цены для вычисления изменений
last_prices = {}
last_check = {}

def get_okx_data():
    try:
        response = requests.get(OKX_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["data"]
    except Exception as e:
        print("Ошибка получения данных с OKX:", e)
        return []

def analyze_volatility():
    global last_prices, last_check
    alerts = []
    data = get_okx_data()
    now = datetime.now()

    for ticker in data:
        symbol = ticker["instId"]  # Например BTC-USDT-SWAP
        price = float(ticker["last"])

        # Игнорируем если только начали
        if symbol not in last_prices:
            last_prices[symbol] = price
            last_check[symbol] = now
            continue

        time_diff = now - last_check[symbol]
        if time_diff >= timedelta(minutes=15):
            old_price = last_prices[symbol]
            change = ((price - old_price) / old_price) * 100

            if abs(change) >= VOLATILITY_THRESHOLD:
                direction = "📈 ВЫРОС" if change > 0 else "📉 УПАЛ"
                coinglass_link = f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?coin={symbol.split('-')[0]}"
                msg = (
                    f"⚡ {symbol}\n"
                    f"{direction} на {change:.2f}% за 15 минут!\n"
                    f"[Открыть в CoinGlass]({coinglass_link})"
                )
                alerts.append(msg)

            # Обновляем данные
            last_prices[symbol] = price
            last_check[symbol] = now

    return alerts

def run():
    print("🚀 Бот запущен. Проверяю рынок OKX...")
    last_daily_message = datetime.now() - timedelta(hours=24)

    while True:
        try:
            alerts = analyze_volatility()

            if alerts:
                full_message = "\n\n".join(alerts)
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚡ Обнаружена высокая волатильность:\n\n{full_message}",
                    parse_mode="Markdown",
                    disable_web_page_preview=False
                )
                print("📨 Отправлен сигнал в Telegram.")
            else:
                print("Нет значительных движений.")

            # Ежедневное сообщение о статусе
            if datetime.now() - last_daily_message > timedelta(hours=24):
                bot.send_message(
                    CHAT_ID,
                    "🤖 Бот активен. Проверяю рынок OKX.",
                )
                last_daily_message = datetime.now()

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Ошибка в основном цикле:", e)
            time.sleep(60)

if __name__ == "__main__":
    run()
