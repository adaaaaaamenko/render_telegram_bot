import asyncio
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from datetime import datetime, timedelta
import os

# Константы этапов диалога
LANGUAGE, DATE, TIME = range(3)

ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # или укажи прямо: ADMIN_CHAT_ID = 123456789
DATA_FILE = "appointments.json"

# Загружаем сохранённые записи
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Сохраняем запись
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Начало диалога
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Русский", callback_data="ru")],
        [InlineKeyboardButton("English", callback_data="en")],
        [InlineKeyboardButton("ქართული", callback_data="ka")],
    ]
    await update.message.reply_text("Выберите язык обслуживания:", reply_markup=InlineKeyboardMarkup(keyboard))
    return LANGUAGE

# Язык выбран
async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["language"] = query.data

    today = datetime.now().date()
    keyboard = [
        [InlineKeyboardButton((today + timedelta(days=i)).strftime("%Y-%m-%d"), callback_data=(today + timedelta(days=i)).isoformat())]
        for i in range(3)
    ]
    await query.edit_message_text("Выберите дату:", reply_markup=InlineKeyboardMarkup(keyboard))
    return DATE

# Дата выбрана
async def date_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["date"] = query.data

    appointments = load_data()
    date_key = context.user_data["date"]
    taken = appointments.get(date_key, {})

    keyboard = []
    for hour in range(12, 22):  # 12:00 – 21:00
        time_str = f"{hour}:00"
        if time_str in taken:
            label = f"{time_str} ❌ {taken[time_str]}"
            callback = "taken"
        else:
            label = f"{time_str}"
            callback = time_str
        keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

    await query.edit_message_text("Выберите время:", reply_markup=InlineKeyboardMarkup(keyboard))
    return TIME

# Время выбрано
async def time_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected_time = query.data

    if selected_time == "taken":
        await query.answer("Это время уже занято. Выберите другое.", show_alert=True)
        return TIME

    context.user_data["time"] = selected_time

    # Сохраняем запись
    date_key = context.user_data["date"]
    time_key = context.user_data["time"]
    lang = context.user_data["language"]
    appointments = load_data()

    if date_key not in appointments:
        appointments[date_key] = {}

    appointments[date_key][time_key] = lang
    save_data(appointments)

    msg = f"✅ Запись подтверждена:\nДата: {date_key}\nВремя: {time_key}\nЯзык: {lang}"
    await query.edit_message_text(msg)

    if ADMIN_CHAT_ID:
        await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=f"🆕 Новая запись:\n{msg}")

    return ConversationHandler.END

# Выход из диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Запись отменена.")
    return ConversationHandler.END

# Главная функция
async def main():
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [CallbackQueryHandler(language_selected)],
            DATE: [CallbackQueryHandler(date_selected)],
            TIME: [CallbackQueryHandler(time_selected)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    await application.run_polling()

# Запуск
if __name__ == "__main__":
    asyncio.run(main())
