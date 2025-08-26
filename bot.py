import os
import json
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = os.getenv("BOT_TOKEN")  # Токен из переменной окружения
APP_URL = os.getenv("APP_URL")   # URL сервиса Render, например https://my-bot.onrender.com
DATA_FILE = "task_lists.json"

bot = Bot(TOKEN)
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

    # Обработка команд
    if update.message:
        text = update.message.text
        if text.startswith("/newlist"):
            if len(text.split(" ",1)) < 2:
                bot.send_message(chat_id, "Используй: /newlist Название")
                return "ok"
            name = text.split(" ",1)[1]
            if chat_id not in lists:
                lists[chat_id] = {}
            lists[chat_id][name] = {"tasks": [], "status": []}
            save_data()
            bot.send_message(chat_id, f"Создан новый список: {name}")
        elif text.startswith("/add"):
            if len(text.split(" ",1)) < 2:
                bot.send_message(chat_id, "Используй: /add текст задачи")
                return "ok"
            task = text.split(" ",1)[1]
            list_name = list(lists[chat_id].keys())[-1]
            lists[chat_id][list_name]["tasks"].append(task)
            lists[chat_id][list_name]["status"].append(False)
            save_data()
            bot.send_message(chat_id, f"Добавлено: {task}")
        elif text.startswith("/showlist"):
            if len(text.split(" ",1)) < 2:
                bot.send_message(chat_id, "Используй: /showlist Название")
                return "ok"
            list_name = text.split(" ",1)[1]
            if list_name not in lists.get(chat_id, {}):
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
    port = int(os.environ.get("PORT", 5000))
    bot.set_webhook(f"{APP_URL}/{TOKEN}")  # Устанавливаем webhook
    app.run(host="0.0.0.0", port=port)
