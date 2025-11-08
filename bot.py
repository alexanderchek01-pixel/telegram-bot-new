import requests
import time
import os
from datetime import datetime, date
import telebot

# === Настройки ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
VOLATILITY_THRESHOLD = 10.0  # % изменения
CHECK_INTERVAL = 300  # каждые 5 минут
INTERVAL = "15"  # анализ за 15 минут

bot = telebot.TeleBot(TOKEN)

# === Учёт сигналов за день ===
daily_signals = {}
current_day = date.today()

# === Получение списка фьючерсов ===
def get_symbols():
    url = "https://api.bybit.com/v5/market/instruments-info?category=linear"
    try:
        res = requests.get(url)
        data = res.json()
        symbols = [x["symbol"] for x in data["result"]["list"] if "USDT" in x["symbol"]]
        return symbols
    except Exception as e:
        print("Ошибка при получении списка монет:", e)
        return []

# === Проверка волатильности ===
def get_volatility(symbol):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": INTERVAL,
        "limit": 2
    }
    try:
        r = requests.get(url, params=params)
        data = r.json()
        kline = data["result"]["list"][0]
        open_price = float(kline[1])
        close_price = float(kline[4])
        change = (close_price - open_price) / open_price * 100
        return change
    except Exception as e:
        print(f"Ошибка при получении данных для {symbol}:", e)
        return None

# === Основной цикл ===
def run():
    global current_day, daily_signals

    bot.send_message(CHAT_ID, "✅ Бот запущен. Следит за фьючерсами Bybit (волатильность > 10%).")

    while True:
        # Сброс сигналов в начале нового дня
        if date.today() != current_day:
            daily_signals = {}
            current_day = date.today()
            bot.send_message(CHAT_ID, "🌅 Новый день — счётчики сигналов обнулены.")

        symbols = get_symbols()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Проверяю {len(symbols)} монет...")

        for sym in symbols:
            change = get_volatility(sym)
            if change is None:
                continue

            if abs(change) >= VOLATILITY_THRESHOLD:
                # Обновляем счётчик сигналов
                daily_signals[sym] = daily_signals.get(sym, 0) + 1
                signal_count = daily_signals[sym]

                direction = "🟢 вырос" if change > 0 else "🔴 упал"
                link = f"https://www.bybit.com/trade/usdt/{sym}"

                msg = (
                    f"🚨 *Bybit Futures — сильное движение!*\n"
                    f"{direction} **{sym}** на **{change:.2f}%** за 15 минут\n"
                    f"[📊 Открыть на Bybit]({link})\n\n"
                    f"📈 Это *{signal_count}-й сигнал* по **{sym}** сегодня."
                )

                print(msg)
                try:
                    bot.send_message(CHAT_ID, msg, parse_mode="Markdown", disable_web_page_preview=True)
                except Exception as e:
                    print("Ошибка при отправке сообщения:", e)

        print("✅ Проверка завершена. Ожидаю следующую итерацию...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()
