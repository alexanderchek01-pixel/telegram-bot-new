import telebot
import time
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот запущен и работает!")

def run():
    while True:
        try:
            bot.polling(non_stop=True, timeout=60)
        except Exception as e:
            print("Ошибка:", e)
            time.sleep(10)

if __name__ == "__main__":
    bot.send_message(CHAT_ID, "✅ Render запустил бота!")
    run()
