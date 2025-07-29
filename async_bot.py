import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
import asyncio
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from datetime import datetime, timedelta

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
URL = os.getenv("RENDER_EXTERNAL_URL")
PORT = int(os.getenv("PORT", "8000"))

# Загрузка/сохранение записей
import json
DATA_FILE = 'appointments.json'
def load_appointments():
    try:
        with open(DATA_FILE) as f: return json.load(f)
    except: return {}
def save_appointments(d): json.dump(d, open(DATA_FILE, 'w'), indent=2)
appointments = load_appointments()

languages = {'ru':'Русский','en':'English','ka':'ქართული'}

def generate_time_slots():
    start = datetime.strptime('12:00','%H:%M')
    end = datetime.strptime('21:00','%H:%M')
    slots=[]
    while start<end:
        slots.append(start.strftime('%H:%M'))
        start+=timedelta(minutes=30)
    return slots

# Handlers
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard=[[{"text":name,"callback_data":f"lang_{code}"}] for code,name in languages.items()]
    await update.message.reply_text("Выберите язык:", reply_markup={"inline_keyboard":keyboard})

async def language_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    ctx.user_data['lang']=q.data.split('_')[1]
    kb=[]
    for t in generate_time_slots():
        if t in appointments:
            label=f"{t} ❌ ({languages[appointments[t]]})"; cd="busy"
        else:
            label=t; cd=f"time_{t}"
        kb.append([{"text":label,"callback_data":cd}])
    await q.edit_message_text("Выберите время:", reply_markup={"inline_keyboard":kb})

async def time_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    t=q.data.split('_')[1]
    if t in appointments:
        await q.edit_message_text(f"❗ Уже занято ({languages[appointments[t]]}).")
    else:
        lang=ctx.user_data['lang']; appointments[t]=lang; save_appointments(appointments)
        await q.edit_message_text(f"✅ Записаны на {t} ({languages[lang]}).")
        await ctx.bot.send_message(chat_id=ADMIN_CHAT_ID,
            text=f"Новая запись:\nВремя: {t}\nЯзык: {languages[lang]}\nПользователь: @{q.from_user.username or q.from_user.full_name}")

async def busy_slot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Занято", show_alert=True)

# Настрой вебхука и веб‑сервер
async def main():
    app = Application.builder().token(BOT_TOKEN).updater(None).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(language_selected, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(time_selected, pattern="^time_"))
    app.add_handler(CallbackQueryHandler(busy_slot, pattern="^busy$"))
    await app.bot.set_webhook(f"{URL}/telegram")

    async def telegram(request: Request) -> Response:
        data = await request.json()
        await app.update_queue.put(Update.de_json(data, app.bot))
        return Response()

    async def health(_: Request):
        return PlainTextResponse("OK")

    starlette_app = Starlette(routes=[
        Route("/telegram", telegram, methods=["POST"]),
        Route("/healthcheck", health, methods=["GET"]),
    ])
    webserver = uvicorn.Server(uvicorn.Config(starlette_app, port=PORT, host="0.0.0.0"))
    async with app:
        await app.start()
        await webserver.serve()
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())

