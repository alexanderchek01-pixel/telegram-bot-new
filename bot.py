import requests
import time
from datetime import datetime, timedelta
from telegram import Bot, ParseMode
import os

# === Настройки ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

OKX_API_URL = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
CHECK_INTERVAL = 180  # каждые 3 минуты
VOLATILITY_THRESHOLD = 10.0  # 10% и выше
PERIOD_MINUTES = 15  # за 15 минут

# храним данные для расчёта
last_prices = {}
last_check = {}
daily_signals = {}  # счётчик сигналов по каждой монете

def get_okx_data():
    try:
        response = requests.get(OKX_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data.get("data"):
            print("⚠️ Пустой ответ от OKX:", data)
        return data.get("data", [])
    except Exception as e:
        print("Ошибка получения данных с OKX:", e)
        return []

def analyze_volatility():
    global last_prices, last_check, daily_signals
    alerts = []
    data = get_okx_data()
    now = datetime.utcnow()

    for ticker in data:
        symbol = ticker["instId"]  # например BTC-USDT-SWAP
        price = float(ticker["last"])

        if symbol not in last_prices:
            last_prices[symbol] = price
            last_check[symbol] = now
            continue

        # разница во времени
        time_diff = now - last_check[symbol]
        if time_diff >= timedelta(minutes=PERIOD_MINUTES):
            old_price = last_prices[symbol]
            change = ((price - old_price) / old_price) * 100

            if abs(change) >= VOLATILITY_THRESHOLD:
                direction = "🟢 ВЫРОС" if change > 0 else "🔴 УПАЛ"
                color = "<b><font color='green'>" if change > 0 else "<b><font color='red'>"
                coin = symbol.split("-")[0]
                coinglass_link = f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?coin={coin}"

                # считаем количество сигналов за день
                today = now.strftime("%Y-%m-%d")
                key = f"{symbol}_{today}"
                daily_signals[key] = daily_signals.get(key, 0) + 1
                signal_count = daily_signals[key]

                msg = (
                    f"{color}{direction}</font></b>\n"
                    f"⚡ <b>{symbol}</b> изменилась на <b>{abs(change):.2f}%</b> за 15 минут.\n"
                    f"📅 Сигнал № <b>{signal_count}</b> за сегодня.\n"
                    f"<a href='{coinglass_link}'>Открыть карту ликвидаций</a>"
                )
                alerts.append(msg)
                print("🚨 Найден сигнал:", msg)

            last_prices[symbol] = price
            last_check[symbol] = now

    return alerts


def run():
    print("🚀 Бот запущен и следит за волатильностью на OKX...")
    bot.send_message(
        CHAT_ID,
        "✅ Бот запущен и отслеживает волатильность монет на OKX.",
        parse_mode=ParseMode.HTML
    )

    last_daily_message = datetime.utcnow() - timedelta(hours=24)

    while True:
        try:
            alerts = analyze_volatility()

            if alerts:
                full_message = "\n\n".join(alerts)
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"🚨 <b>Обнаружена высокая волатильность!</b>\n\n{full_message}",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=False
                )
                print("📨 Отправлен сигнал в Telegram.")
            else:
                print("Нет значительных изменений на рынке.")

            # ежедневное уведомление
            if datetime.utcnow() - last_daily_message > timedelta(hours=24):
                bot.send_message(
                    CHAT_ID,
                    "🤖 Бот активен и работает стабильно. Проверяю рынок OKX каждые 3 минуты.",
                    parse_mode=ParseMode.HTML
                )
                last_daily_message = datetime.utcnow()

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Ошибка в основном цикле:", e)
            time.sleep(60)

if __name__ == "__main__":
    run()
