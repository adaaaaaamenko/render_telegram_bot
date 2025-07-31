import os
import logging
from fastapi import FastAPI, Request
from telegram.ext import ApplicationBuilder
from telegram import Update
from telegram.ext import ContextTypes
from async_bot import get_handlers  # ты можешь отдельно экспортировать ConversationHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

app = FastAPI()
application = ApplicationBuilder().token(TOKEN).build()
for handler in get_handlers():  # ты определяешь эту функцию в async_bot.py
    application.add_handler(handler)

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}

@app.on_event("startup")
async def on_startup():
    url = os.getenv("WEBHOOK_URL")  # типо https://your-subdomain.onrender.com/webhook
    await application.bot.set_webhook(url)
    logging.info(f"Webhook set to {url}")
