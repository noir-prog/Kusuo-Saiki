# ================== IMPORTS ==================

import os
import logging

from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update


# ================== SETTINGS ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "lastmod-secret")


# ================== LOGGING ==================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ================== BOT ==================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ================== FASTAPI ==================

app = FastAPI()


# ================== TELEGRAM UPDATE ==================

@dp.update()
async def handle_update(update: Update):
    logger.info("Telegram update received: %s", update.model_dump())


# ================== WEBHOOK ==================

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "LastMod Business Bot",
    }


@app.post("/webhook")
async def telegram_webhook(request: Request):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")

    if secret != WEBHOOK_SECRET:
        return {"ok": False}

    data = await request.json()

    update = Update.model_validate(data)

    await dp.feed_update(bot, update)

    return {"ok": True}


# ================== STARTUP ==================

@app.on_event("startup")
async def startup():
    webhook_url = "https://kusuo-saiki.onrender.com/webhook"

    await bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
    )

    logger.info("LastMod Business Bot started")
    logger.info("Webhook set: %s", webhook_url)


# ================== SHUTDOWN ==================

@app.on_event("shutdown")
async def shutdown():
    await bot.session.close()
    logger.info("LastMod Business Bot stopped")