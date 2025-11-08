import requests
import time
import os
from datetime import datetime
import telebot

# === Настройки ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
VOLATILITY_THRESHOLD = 10.0  # % изменения
CHECK_INTERVAL = 300  # каждые 5 минут (в секундах)

bot = telebot.TeleBot(TOKEN)

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
        "interval": "15",  # 15 минут
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
    bot.send_message(CHAT_ID, "✅ Бот запущен. Следит за фьючерсами Bybit (волатильность > 10%).")

    while True:
        symbols = get_symbols()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Проверяю {len(symbols)} монет...")

        alerts = []

        for sym in symbols:
            change = get_volatility(sym)
            if change is None:
                continue

            if abs(change) >= VOLATILITY_THRESHOLD:
                direction = "🟢 вырос" if change > 0 else "🔴 упал"
                link = f"https://www.bybit.com/trade/usdt/{sym}"
                msg = f"🚨 *Bybit Futures — сильное движение!*\n{direction} **{sym}** на **{change:.2f}%** за 15 мин\n[📊 Открыть на Bybit]({link})"
                alerts.append(msg)
                print(msg)

        if alerts:
            for msg in alerts:
                try:
                    bot.send_message(CHAT_ID, msg, parse_mode="Markdown", disable_web_page_preview=True)
                except Exception as e:
                    print("Ошибка при отправке сообщения:", e)
        else:
            print("Нет монет с изменением > 10%")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run()
