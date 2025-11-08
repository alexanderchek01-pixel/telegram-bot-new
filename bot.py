import requests
import telebot
import time
import os
from datetime import datetime, timedelta

# === Настройки ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CHECK_INTERVAL = 300  # каждые 5 минут
VOLATILITY_THRESHOLD = 10.0  # 10% движение
TIMEFRAME_MINUTES = 15  # анализ за 15 минут

bot = telebot.TeleBot(TOKEN)

# === Получаем все пары USDT с Binance Futures ===
def get_futures_symbols():
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "symbols" not in data:
            print("⚠️ Binance API ответил странно:", data)
            return []

        symbols = [
            s["symbol"] for s in data["symbols"]
            if s.get("contractType") == "PERPETUAL" and s["symbol"].endswith("USDT")
        ]
        print(f"✅ Получено {len(symbols)} пар с Binance Futures.")
        return symbols

    except requests.exceptions.RequestException as e:
        print("Ошибка подключения к Binance API:", e)
        return []
    except ValueError:
        print("Ошибка разбора JSON — возможно, пришёл HTML-ответ.")
        return []

# === Получаем изменение цены за выбранный интервал ===
def get_price_change(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1m&limit={TIMEFRAME_MINUTES}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if not isinstance(data, list) or len(data) < 2:
            return None

        open_price = float(data[0][1])
        close_price = float(data[-1][4])
        change = ((close_price - open_price) / open_price) * 100
        return change
    except Exception:
        return None

# === Основной цикл ===
def run():
    print("🚀 Бот запущен. Проверяю рынок Binance Futures...")
    try:
        bot.send_message(CHAT_ID, "✅ Бот запущен. Следит за фьючерсами Binance (волатильность > 10%)")
    except Exception as e:
        print("Ошибка отправки стартового сообщения:", e)

    last_daily_message = datetime.now() - timedelta(hours=24)
    symbols = get_futures_symbols()

    if not symbols:
        bot.send_message(CHAT_ID, "⚠️ Не удалось получить список пар с Binance Futures.")
        return

    while True:
        try:
            alerts = []
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Проверяю данные по {len(symbols)} парам...")

            for symbol in symbols:
                change = get_price_change(symbol)
                if change is None:
                    continue

                direction = "🟢 выросла" if change > 0 else "🔴 упала"
                arrow = "🟢⬆️" if change > 0 else "🔴⬇️"

                if abs(change) >= VOLATILITY_THRESHOLD:
                    msg = (
                        f"🚨 *{symbol}* {arrow}\n"
                        f"{direction} на {abs(change):.2f}% за {TIMEFRAME_MINUTES} минут.\n"
                        f"[Открыть на Binance](https://www.binance.com/en/futures/{symbol})"
                    )
                    alerts.append(msg)

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

            # Ежедневное уведомление
            if datetime.now() - last_daily_message > timedelta(hours=24):
                bot.send_message(CHAT_ID, "🤖 Бот активен. Проверяю рынок Binance Futures.")
                last_daily_message = datetime.now()

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Ошибка в основном цикле:", e)
            time.sleep(60)

if __name__ == "__main__":
    run()
