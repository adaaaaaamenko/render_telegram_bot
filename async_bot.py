import json
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пути и токены
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get('PORT', 8443))

LANGUAGE, DATE, TIME = range(3)

# Доступные слоты
AVAILABLE_TIMES = [f"{h}:00" for h in range(12, 22)]
DAYS_FORWARD = 3
FILENAME = "appointments.json"
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # добавь в Render в Variables

def load_appointments():
    if not os.path.exists(FILENAME):
        return {}
    with open(FILENAME, "r") as f:
        return json.load(f)

def save_appointments(appointments):
    with open(FILENAME, "w") as f:
        json.dump(appointments, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        print("⚠️ update.message is None!")
        return ConversationHandler.END
    keyboard = [
        [InlineKeyboardButton("Русский", callback_data='ru')],
        [InlineKeyboardButton("English", callback_data='en')],
        [InlineKeyboardButton("ქართული", callback_data='ka')],
    ]
    await update.message.reply_text("Выберите язык:", reply_markup=InlineKeyboardMarkup(keyboard))
    return LANGUAGE

async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    context.user_data["lang"] = lang

    from datetime import datetime, timedelta
    keyboard = []
    for i in range(DAYS_FORWARD):
        date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        keyboard.append([InlineKeyboardButton(date, callback_data=date)])

    await query.edit_message_text("Выберите дату:", reply_markup=InlineKeyboardMarkup(keyboard))
    return DATE

async def date_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    date = query.data
    context.user_data["date"] = date

    appointments = load_appointments()
    booked_times = [t for t, info in appointments.get(date, {}).items()]
    lang = context.user_data.get("lang", "unknown")

    keyboard = []
    for time in AVAILABLE_TIMES:
        if time in booked_times:
            label = f"{time} ❌ ({appointments[date][time]['lang']})"
            keyboard.append([InlineKeyboardButton(label, callback_data='ignore')])
        else:
            keyboard.append([InlineKeyboardButton(f"{time}", callback_data=time)])

    await query.edit_message_text("Выберите время:", reply_markup=InlineKeyboardMarkup(keyboard))
    return TIME

async def time_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    time = query.data
    if time == 'ignore':
        return TIME

    date = context.user_data["date"]
    lang = context.user_data["lang"]
    user = update.effective_user

    appointments = load_appointments()
    appointments.setdefault(date, {})[time] = {"lang": lang, "user_id": user.id, "username": user.username}
    save_appointments(appointments)

    await query.edit_message_text(f"Запись подтверждена: {date} в {time} ({lang})")

    # Уведомление администратору
    if ADMIN_CHAT_ID:
        await context.bot.send_message(
            chat_id=int(ADMIN_CHAT_ID),
            text=f"Новая запись:\nДата: {date}\nВремя: {time}\nЯзык: {lang}\nПользователь: @{user.username or user.id}"
        )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Запись отменена.")
    return ConversationHandler.END

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Неизвестная команда.")

async def main():
    from telegram.ext import Application

    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [CallbackQueryHandler(language_chosen)],
            DATE: [CallbackQueryHandler(date_chosen)],
            TIME: [CallbackQueryHandler(time_chosen)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Webhook
    render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if render_hostname:
        webhook_url = f"https://{render_hostname}/webhook"
        logger.info(f"Запуск webhook на {webhook_url}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="webhook",
            webhook_url=webhook_url,
        )
    else:
        logger.error("RENDER_EXTERNAL_HOSTNAME не установлен! Webhook не запущен.")
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
def get_handlers():
    return [conv_handler, other_handler_1, ...]  # экспортируй список хендлеров
