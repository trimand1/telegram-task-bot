import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

import os
TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "task_lists.json"

# Загружаем списки из файла
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

# Сохраняем списки в файл
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(lists, f, ensure_ascii=False, indent=2)

# Загружаем данные при старте
lists = load_data()

# /newlist название
async def new_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if len(context.args) == 0:
        await update.message.reply_text("Используй: /newlist Название списка")
        return
    list_name = " ".join(context.args)

    if chat_id not in lists:
        lists[chat_id] = {}

    lists[chat_id][list_name] = {
        "tasks": [],
        "status": []
    }
    save_data()
    await update.message.reply_text(f"Создан новый список: *{list_name}*\nДобавь задачи через /add", parse_mode="Markdown")

# /add текст задачи
async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id not in lists or not lists[chat_id]:
        await update.message.reply_text("Сначала создай список: /newlist Название")
        return
    task = " ".join(context.args)
    if not task:
        await update.message.reply_text("Используй: /add текст задачи")
        return

    list_name = list(lists[chat_id].keys())[-1]  # последняя созданная
    lists[chat_id][list_name]["tasks"].append(task)
    lists[chat_id][list_name]["status"].append(False)
    save_data()
    await update.message.reply_text(f"Добавлено в *{list_name}*: {task}", parse_mode="Markdown")

# /showlist название
async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if len(context.args) == 0:
        await update.message.reply_text("Используй: /showlist Название списка")
        return
    list_name = " ".join(context.args)

    if chat_id not in lists or list_name not in lists[chat_id]:
        await update.message.reply_text("Такого списка нет")
        return

    tasks = lists[chat_id][list_name]["tasks"]
    status = lists[chat_id][list_name]["status"]

    keyboard = []
    for i, task in enumerate(tasks):
        text = f"✅ {task}" if status[i] else f"⬜ {task}"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"{chat_id}|{list_name}|{i}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Список: *{list_name}*", reply_markup=reply_markup, parse_mode="Markdown")

# обработка нажатий
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id, list_name, idx = query.data.split("|")
    idx = int(idx)

    lists[chat_id][list_name]["status"][idx] = not lists[chat_id][list_name]["status"][idx]
    save_data()

    tasks = lists[chat_id][list_name]["tasks"]
    status = lists[chat_id][list_name]["status"]

    keyboard = []
    for i, task in enumerate(tasks):
        text = f"✅ {task}" if status[i] else f"⬜ {task}"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"{chat_id}|{list_name}|{i}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_reply_markup(reply_markup=reply_markup)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("newlist", new_list))
    app.add_handler(CommandHandler("add", add_task))
    app.add_handler(CommandHandler("showlist", show_list))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == "__main__":
    main()
