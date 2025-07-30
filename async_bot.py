import json
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder, CallbackContext, CallbackQueryHandler,
    CommandHandler, ConversationHandler
)
from dotenv import load_dotenv
import asyncio

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not BOT_TOKEN or not ADMIN_CHAT_ID:
    raise ValueError("BOT_TOKEN or ADMIN_CHAT_ID not set in environment variables")

ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)

LANGUAGE, DATE, TIME = range(3)

translations = {
    "ru": {
        "choose_language": "Пожалуйста, выберите язык обслуживания:",
        "choose_date": "Выберите дату:",
        "choose_time": "Выберите время:",
        "already_booked": "Это время уже занято. Язык записи: {}",
        "confirm": "Вы записаны на {} в {} ({} язык). Спасибо!",
    },
    "en": {
        "choose_language": "Please choose a service language:",
        "choose_date": "Choose a date:",
        "choose_time": "Choose a time:",
        "already_booked": "This slot is already booked. Language: {}",
        "confirm": "You are booked for {} at {} (language: {}). Thank you!",
    },
    "ka": {
        "choose_language": "გთხოვთ, აირჩიოთ მომსახურების ენა:",
        "choose_date": "აირჩიეთ თარიღი:",
        "choose_time": "აირჩიეთ დრო:",
        "already_booked": "ეს დრო უკვე დაკავებულია. ენა: {}",
        "confirm": "თქვენ დაჯავშნეთ {} - {} (ენა: {}). მადლობა!",
    }
}

def load_appointments():
    if os.path.exists("appointments.json"):
        with open("appointments.json", "r") as f:
            return json.load(f)
    return {}

def save_appointment(date, time, lang):
    appointments = load_appointments()
    if date not in appointments:
        appointments[date] = {}
    appointments[date][time] = lang
    with open("appointments.json", "w") as f:
        json.dump(appointments, f)

def is_booked(date, time):
    appointments = load_appointments()
    return date in appointments and time in appointments[date]

def get_language_text(lang, key):
    return translations.get(lang, translations["en"]).get(key)

async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Русский 🇷🇺", callback_data="ru")],
        [InlineKeyboardButton("English 🇬🇧", callback_data="en")],
        [InlineKeyboardButton("ქართული 🇬🇪", callback_data="ka")],
    ]
    await update.message.reply_text(
        "Пожалуйста, выберите язык обслуживания:\nPlease choose a service language:\nგთხოვთ, აირჩიოთ მომსახურების ენა:",
        reply_markup=InlineKeyboardMarkup(keyboard))
    return LANGUAGE

async def choose_language(update: Update, context: CallbackContext):
    lang = update.callback_query.data
    context.user_data["lang"] = lang
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton((datetime.now() + timedelta(days=i)).strftime("%d.%m.%Y"), callback_data=str(i))]
        for i in range(3)
    ]
    await update.callback_query.edit_message_text(
        get_language_text(lang, "choose_date"),
        reply_markup=InlineKeyboardMarkup(keyboard))
    return DATE

async def choose_date(update: Update, context: CallbackContext):
    lang = context.user_data["lang"]
    days_from_now = int(update.callback_query.data)
    chosen_date = (datetime.now() + timedelta(days=days_from_now)).strftime("%Y-%m-%d")
    context.user_data["date"] = chosen_date

    keyboard = [
        [InlineKeyboardButton(f"{hour:02d}:00", callback_data=f"{hour:02d}:00")]
        for hour in range(12, 22)
    ]
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        get_language_text(lang, "choose_time"),
        reply_markup=InlineKeyboardMarkup(keyboard))
    return TIME

async def choose_time(update: Update, context: CallbackContext):
    lang = context.user_data["lang"]
    date = context.user_data["date"]
    time = update.callback_query.data

    if is_booked(date, time):
        booked_lang = load_appointments()[date][time]
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(get_language_text(lang, "already_booked").format(booked_lang))
        return ConversationHandler.END

    save_appointment(date, time, lang)
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID,
                                   text=f"Запись: {update.effective_user.full_name} — {date} {time} ({lang})")
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(get_language_text(lang, "confirm").format(date, time, lang))
    return ConversationHandler.END

async def main():
    bot = Bot(token=BOT_TOKEN)
    try:
    await bot.delete_webhook(drop_pending_updates=True)
except Exception as e:
    print(f'Failed to delete webhook: {e}')
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [CallbackQueryHandler(choose_language)],
            DATE: [CallbackQueryHandler(choose_date)],
            TIME: [CallbackQueryHandler(choose_time)],
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    await application.initialize()
    await application.start()
    await application.bot.initialize()
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    import sys

    async def safe_main():
        try:
            await main()
        except Exception as e:
            print(f"Main crashed with error: {e}", file=sys.stderr)

    try:
        asyncio.run(safe_main())
    except RuntimeError as e:
        if "already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.create_task(safe_main())
            loop.run_forever()
        else:
            raise



if __name__ == '__main__':
    import asyncio
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e).startswith("This event loop is already running"):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
