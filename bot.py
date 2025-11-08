import requests
import telebot
import time
import os
from datetime import datetime, timedelta

# === Настройки ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CHECK_INTERVAL = 180  # каждые 3 минуты
VOLATILITY_THRESHOLD = 10.0  # % волатильности за 15 минут
LOOKBACK_INTERVAL = "15m"  # можно 5m, 15m, 1h

bot = telebot.TeleBot(TOKEN)
last_alerts = {}  # чтобы не спамить повторными сигналами

# === Получаем список фьючерсов OKX ===
def get_okx_symbols():
    url = "https://www.okx.com/api/v5/public/instruments?instType=SWAP"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if "data" not in data:
            print("⚠️ Ошибка: нет данных о парах.")
            return []
        symbols = [x["instId"] for x in data["data"] if x["instId"].endswith("-USDT-SWAP")]
        print(f"✅ Получено {len(symbols)} фьючерсных пар.")
        return symbols
    except Exception as e:
        print("Ошибка при получении списка пар:", e)
        return []

# === Получаем волатильность по конкретной паре ===
def get_volatility(symbol):
    url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}&bar={LOOKBACK_INTERVAL}&limit=2"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if "data" not in data or len(data["data"]) < 2:
            return None

        latest = data["data"][0]
        open_price = float(latest[1])
        close_price = float(latest[4])
        change = ((close_price - open_price) / open_price) * 100
        return change, close_price
    except Exception as e:
        print(f"Ошибка при получении свечей {symbol}: {e}")
        return None

# === Основной цикл ===
def run():
    bot.send_message(CHAT_ID, "✅ Бот запущен. Следит за фьючерсами OKX и присылает сигналы (>10% за 15 минут).")
    symbols = get_okx_symbols()
    if not symbols:
        bot.send_message(CHAT_ID, "⚠️ Не удалось получить список фьючерсов OKX.")
        return

    last_daily_message = datetime.now() - timedelta(hours=24)

    while True:
        try:
            alerts = []
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Проверяю {len(symbols)} пар...")

            for symbol in symbols:
                result = get_volatility(symbol)
                if not result:
                    continue

                change, price = result
                base_coin = symbol.split("-")[0]  # например, BTC из BTC-USDT-SWAP

                # Проверяем антиспам (если сигнал уже был недавно)
                last_time = last_alerts.get(symbol)
                if last_time and (datetime.now() - last_time).total_seconds() < 900:  # 15 минут
                    continue

                if abs(change) >= VOLATILITY_THRESHOLD:
                    direction = "🟢 выросла" if change > 0 else "🔴 упала"
                    arrow = "🟢⬆️" if change > 0 else "🔴⬇️"

                    # ✅ Ссылка на CoinGlass HeatMap
                    coinglass_link = f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?coin={base_coin}&type=pair"

                    msg = (
                        f"🚨 *{symbol}* {arrow}\n"
                        f"{direction} на {abs(change):.2f}% за {LOOKBACK_INTERVAL}.\n"
                        f"💰 Цена сейчас: ${price:.4f}\n"
                        f"[📊 Открыть в CoinGlass HeatMap]({coinglass_link})"
                    )

                    alerts.append(msg)
                    last_alerts[symbol] = datetime.now()

            if alerts:
                full_message = "\n\n".join(alerts)
                bot.send_message(
                    CHAT_ID,
                    f"⚡ Обнаружена высокая волатильность:\n\n{full_message}",
                    parse_mode="Markdown",
                    disable_web_page_preview=False
                )
            else:
                print("Нет значительных движений.")

            # раз в сутки уведомление, что бот жив
            if datetime.now() - last_daily_message > timedelta(hours=24):
                bot.send_message(CHAT_ID, "🤖 Бот активен. Проверяю рынок OKX.")
                last_daily_message = datetime.now()

           
                        time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Ошибка в основном цикле:", e)
            time.sleep(60)

if __name__ == "__main__":
    run()
            
            

        
