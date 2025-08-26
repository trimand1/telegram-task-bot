import os
import json
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.utils.request import Request

TOKEN = os.getenv("BOT_TOKEN")      # токен бота
APP_URL = os.getenv("APP_URL")      # публичный URL Render, например https://telegram-task-bot.onrender.com
DATA_FILE = "task_lists.json"

# Создаём синхронный Bot
bot = Bot(token=TOKEN, request=Request())

# Flask приложение
app = Flask(__name__)

# Загрузка/сохранение списков
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(lists, f, ensure_ascii=False, indent=2)

lists = load_data()

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    chat_id = str(update.effective_chat.id) if update.message else None

    if update.message:
        text = update.message.text

        # /newlist Название
        if text.startswith("/newlist"):
            parts = text.split(" ", 1)
            if len(parts) < 2:
                bot.send_message(chat_id, "Используй: /newlist Название")
                return "ok"
            name = parts[1]
            if chat_id not in lists:
                lists[chat_id] = {}
            lists[chat_id][name] = {"tasks": [], "status": []}
            save_data()
            bot.send_message(chat_id, f"Создан новый список: {name}")

        # /add Текст задачи
        elif text.startswith("/add"):
            parts = text.split(" ", 1)
            if len(parts) < 2:
                bot.send_message(chat_id, "Используй: /add текст задачи")
                return "ok"
            task = parts[1]
            list_name = list(lists[chat_id].keys())[-1]  # последняя созданная
            lists[chat_id][list_name]["tasks"].append(task)
            lists[chat_id][list_name]["status"].append(False)
            save_data()
            bot.send_message(chat_id, f"Добавлено: {task}")

        # /showlist Название
        elif text.startswith("/showlist"):
            parts = text.split(" ", 1)
            if len(parts) < 2:
                bot.send_message(chat_id, "Используй: /showlist Название")
                return "ok"
            list_name = parts[1]
            if chat_id not in lists or list_name not in lists[chat_id]:
                bot.send_message(chat_id, "Такого списка нет")
                return "ok"

            tasks = lists[chat_id][list_name]["tasks"]
            status = lists[chat_id][list_name]["status"]

            keyboard = []
            for i, t in enumerate(tasks):
                text_btn = f"✅ {t}" if status[i] else f"⬜ {t}"
                keyboard.append([InlineKeyboardButton(text_btn, callback_data=f"{chat_id}|{list_name}|{i}")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(chat_id, f"Список: {list_name}", reply_markup=reply_markup)

    return "ok"

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    # Устанавливаем webhook
    bot.set_webhook(f"{APP_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
