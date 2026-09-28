import os
import logging

from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update


# ================== SETTINGS ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "lastmod-secret")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured")


# ================== LOGGING ==================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ================== TELEGRAM ==================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ================== FASTAPI ==================

app = FastAPI()


# ================== BASIC HANDLER ==================

@dp.message()
async def handle_message(message):
    logger.info(
        "MESSAGE | user=%s | chat=%s | message=%s | text=%s",
        message.from_user.id if message.from_user else None,
        message.chat.id,
        message.message_id,
        message.text,
    )


# ================== WEBHOOK ==================

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Kusuo Saiki",
    }


@app.post("/webhook")
async def webhook(request: Request):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")

    if secret != WEBHOOK_SECRET:
        return {
            "ok": False,
            "error": "invalid secret",
        }

    data = await request.json()
    update = Update.model_validate(data)

    await dp.feed_update(bot, update)

    return {
        "ok": True,
    }


# ================== STARTUP ==================

@app.on_event("startup")
async def startup():
    webhook_url = "https://kusuo-saiki.onrender.com/webhook"

    await bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=False,
    )

    logger.info("BOT STARTED")
    logger.info("WEBHOOK SET | %s", webhook_url)


# ================== SHUTDOWN ==================

@app.on_event("shutdown")
async def shutdown():
    await bot.session.close()
    logger.info("BOT STOPPED")