# bot.py (KuCoin Futures, 15m, threshold 10%)
import requests
import time
from datetime import datetime, timedelta
import os
from telegram import Bot

# ========== Настройки ==========
TOKEN = os.getenv("TELEGRAM_TOKEN") or "ВАШ_TELEGRAM_TOKEN"
CHAT_ID = os.getenv("CHAT_ID") or "ВАШ_CHAT_ID"

bot = Bot(token=TOKEN)

CHECK_INTERVAL = 180  # проверка каждые 3 минуты
LOOKBACK_MINUTES = 15  # интервал для сравнения
VOLATILITY_THRESHOLD = 10.0  # % порог для сигнала

# KuCoin Futures Kline API (public)
# Для фьючерсных пар у KuCoin используется символ вида "XBTUSDTM" или "BTCUSDTM" — проверим на месте.
KUCOIN_SYMBOLS_API = "https://api.kucoin.com/api/v1/contracts/active"  # получаем список контрактов
KUCOIN_KLINE_API = "https://api.kucoin.com/api/v1/market/candles?symbol={symbol}&type={interval}&startAt={start}&endAt={end}"

# Храним последние цены и время
last_prices = {}
last_check = {}
daily_signals = {}
daily_reset = datetime.utcnow().date()

def get_kucoin_symbols():
    try:
        r = requests.get(KUCOIN_SYMBOLS_API, timeout=10)
        r.raise_for_status()
        j = r.json()
        # тело: j['data'] список контрактов, у каждого 'symbol' (например "XBTUSDTM")
        syms = [c["symbol"] for c in j.get("data", []) if c.get("symbol")]
        print(f"Получено {len(syms)} контрактов KuCoin.")
        return syms
    except Exception as e:
        print("Ошибка получения списка контрактов KuCoin:", e)
        return []

def get_kucoin_kline(symbol, minutes=15):
    # KuCoin kline type: "1min","3min","5min","15min","30min","1hour" ...
    interval = f"{minutes}min" if minutes in (1,3,5,15,30) else f"{minutes}min"
    # KuCoin expects startAt/endAt in unix seconds
    end = int(time.time())
    start = end - (minutes * 60)
    url = KUCOIN_KLINE_API.format(symbol=symbol, interval=interval, start=start, end=end)
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        j = r.json()
        data = j.get("data") or j.get("data", [])
        # KuCoin returns list of [time, open, high, low, close, volume] strings
        if not data:
            return None
        # take most recent candle (first element may be newest or oldest depending API; ensure correct)
        # KuCoin returns array with newest first historically — we'll parse last element as oldest, first as newest
        newest = data[0]
        open_price = float(newest[1])
        close_price = float(newest[4])
        return open_price, close_price
    except Exception as e:
        # печатаем ошибку для логов
        print(f"Ошибка получения kline для {symbol}:", e)
        return None

def reset_daily_if_needed():
    global daily_reset, daily_signals
    today = datetime.utcnow().date()
    if today != daily_reset:
        daily_signals = {}
        daily_reset = today

def analyze_volatility(symbols):
    alerts = []
    reset_daily_if_needed()
    now = datetime.utcnow()

    for symbol in symbols:
        try:
            k = get_kucoin_kline(symbol, minutes=LOOKBACK_MINUTES)
            if not k:
                continue
            open_price, close_price = k
            if open_price == 0:
                continue
            change = ((close_price - open_price) / open_price) * 100.0
            # если порог превышен
            if abs(change) >= VOLATILITY_THRESHOLD:
                is_up = change > 0
                emoji = "🟢⬆️" if is_up else "🔴⬇️"
                base = symbol.replace("USDTM","").replace("USD","").replace("USDT","")
                coinglass_link = f"https://www.coinglass.com/pro/futures/LiquidationHeatMap?coin={base}&type=pair"
                daily_signals.setdefault(symbol, 0)
                daily_signals[symbol] += 1
                msg = (
                    f"{emoji} *{symbol}*\n"
                    f"{'Выросла' if is_up else 'Упала'} на *{abs(change):.2f}%* за {LOOKBACK_MINUTES} минут.\n"
                    f"Сигнал № *{daily_signals[symbol]}* за сегодня.\n"
                    f"[Открыть CoinGlass Liquidation Map]({coinglass_link})"
                )
                alerts.append(msg)
        except Exception as e:
            print("Ошибка при обработке", symbol, e)
            continue

    return alerts

def run():
    print("🚀 KuCoin futures bot starting...")
    try:
        bot.send_message(CHAT_ID, "✅ Бот запущен. Следит за KuCoin Futures (15m, >10%).")
    except Exception as e:
        print("Ошибка отправки стартового сообщения:", e)

    symbols = get_kucoin_symbols()
    if not symbols:
        print("Не получили список символов KuCoin — попробуйте снова.")
    # для скорости можно сократить список, например взять топ N:
    # symbols = symbols[:150]

    while True:
        try:
            alerts = analyze_volatility(symbols)
            if alerts:
                text = "⚡ *Обнаружена высокая волатильность (KuCoin Futures):*\n\n" + "\n\n".join(alerts)
                bot.send_message(CHAT_ID, text=text, parse_mode="Markdown", disable_web_page_preview=False)
                print("Сигналы отправлены:", len(alerts))
            else:
                print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Нет значительных движений.")

            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print("Ошибка основного цикла:", e)
            time.sleep(60)

if __name__ == "__main__":
    run()
