# ================== IMPORTS ==================

import os
import logging
from datetime import datetime, timezone
import asyncpg
import hashlib
import hmac

from fastapi import FastAPI, Request
from urllib.parse import parse_qsl
from fastapi.middleware.cors import CORSMiddleware

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    MenuButtonWebApp,
    WebAppInfo,

)

# ================== SETTINGS ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "lastmod-secret")
DATABASE_URL = os.getenv("DATABASE_URL")

CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
D1_DATABASE_ID = os.getenv("D1_DATABASE_ID")
OWNER_ID = 6925580275

# ================== D1 ROUTER ==================

D1_DATABASES = {
    # ================== D1.1 ==================

    "D1.1.1": {
        "account_id": "a5cbd8bb1cd52eea0b38b21c40106d53",
        "database_id": D1_DATABASE_ID,
        "token_env": "CLOUDFLARE_API_TOKEN_1",
    },

    "D1.1.2": {
        "account_id": "a5cbd8bb1cd52eea0b38b21c40106d53",
        "database_id": "7e101e0b-9426-458b-92b2-b08cde11378c",
        "token_env": "CLOUDFLARE_API_TOKEN_1",
    },

    "D1.1.3": {
        "account_id": "a5cbd8bb1cd52eea0b38b21c40106d53",
        "database_id": "e7c828de-a078-4f47-98d1-7e308e0652b5",
        "token_env": "CLOUDFLARE_API_TOKEN_1",
    },

    "D1.1.4": {
        "account_id": "a5cbd8bb1cd52eea0b38b21c40106d53",
        "database_id": "7a82b7fa-b0c4-4887-bfa5-a9b3cf961eb9",
        "token_env": "CLOUDFLARE_API_TOKEN_1",
    },

    "D1.1.5": {
        "account_id": "a5cbd8bb1cd52eea0b38b21c40106d53",
        "database_id": "ae4f4daf-4b95-4b64-9a38-d4fde305141d",
        "token_env": "CLOUDFLARE_API_TOKEN_1",
    },

    "D1.1.6": {
        "account_id": "a5cbd8bb1cd52eea0b38b21c40106d53",
        "database_id": "d0500f4c-7c55-433e-add7-c87b296dfcd8",
        "token_env": "CLOUDFLARE_API_TOKEN_1",
    },

    "D1.1.7": {
        "account_id": "a5cbd8bb1cd52eea0b38b21c40106d53",
        "database_id": "a2d714ab-f7ca-451a-bfb6-098a1af1312c",
        "token_env": "CLOUDFLARE_API_TOKEN_1",
    },

    "D1.1.8": {
        "account_id": "a5cbd8bb1cd52eea0b38b21c40106d53",
        "database_id": "05a42544-6886-4e72-9d37-731233c79820",
        "token_env": "CLOUDFLARE_API_TOKEN_1",
    },

    "D1.1.9": {
        "account_id": "a5cbd8bb1cd52eea0b38b21c40106d53",
        "database_id": "28670110-b025-4bc1-af15-45b58e58565f",
        "token_env": "CLOUDFLARE_API_TOKEN_1",
    },

    "D1.1.10": {
        "account_id": "a5cbd8bb1cd52eea0b38b21c40106d53",
        "database_id": "99d131db-69bc-418d-ba33-6c28a44d46f3",
        "token_env": "CLOUDFLARE_API_TOKEN_1",
    },


    # ================== D1.2 ==================

    "D1.2.1": {
        "account_id": "b7bd135a9fb318c159851e18b38610ce",
        "database_id": "fab77f46-362e-4e63-9f42-cf6139968c6b",
        "token_env": "CLOUDFLARE_API_TOKEN_2",
    },

    "D1.2.2": {
        "account_id": "b7bd135a9fb318c159851e18b38610ce",
        "database_id": "3f91cacc-17e8-46b6-b891-fde9c5d9004e",
        "token_env": "CLOUDFLARE_API_TOKEN_2",
    },

    "D1.2.3": {
        "account_id": "b7bd135a9fb318c159851e18b38610ce",
        "database_id": "121ba3de-6215-40b1-bcdf-c27e364d753f",
        "token_env": "CLOUDFLARE_API_TOKEN_2",
    },

    "D1.2.4": {
        "account_id": "b7bd135a9fb318c159851e18b38610ce",
        "database_id": "04dd45ac-800d-45ed-8f13-7928ff6b0df8",
        "token_env": "CLOUDFLARE_API_TOKEN_2",
    },

    "D1.2.5": {
        "account_id": "b7bd135a9fb318c159851e18b38610ce",
        "database_id": "2f7f4592-d755-483f-884f-300fd6ab6200",
        "token_env": "CLOUDFLARE_API_TOKEN_2",
    },

    "D1.2.6": {
        "account_id": "b7bd135a9fb318c159851e18b38610ce",
        "database_id": "6157bec3-7298-40f9-ba63-b87dbb5b18cd",
        "token_env": "CLOUDFLARE_API_TOKEN_2",
    },

    "D1.2.7": {
        "account_id": "b7bd135a9fb318c159851e18b38610ce",
        "database_id": "36aac910-96f9-44a1-820d-60cf9dea72f5",
        "token_env": "CLOUDFLARE_API_TOKEN_2",
    },

    "D1.2.8": {
        "account_id": "b7bd135a9fb318c159851e18b38610ce",
        "database_id": "6024a1b1-e17c-45e5-b899-0f5ba4246087",
        "token_env": "CLOUDFLARE_API_TOKEN_2",
    },

    "D1.2.9": {
        "account_id": "b7bd135a9fb318c159851e18b38610ce",
        "database_id": "17c4f304-d733-413e-b858-f9b3033e79c1",
        "token_env": "CLOUDFLARE_API_TOKEN_2",
    },

    "D1.2.10": {
        "account_id": "b7bd135a9fb318c159851e18b38610ce",
        "database_id": "5c93444c-792b-4423-b0a9-437772e6e388",
        "token_env": "CLOUDFLARE_API_TOKEN_2",
    },


    # ================== D1.3 ==================

    "D1.3.1": {
        "account_id": "f2bf38f76018c112bffc762e4b67bfff",
        "database_id": "8b96ef57-d63d-47b1-bcd3-f7dee8ac9634",
        "token_env": "CLOUDFLARE_API_TOKEN_3",
    },

    "D1.3.2": {
        "account_id": "f2bf38f76018c112bffc762e4b67bfff",
        "database_id": "16fe894c-9316-41c2-915a-6d317b27bce7",
        "token_env": "CLOUDFLARE_API_TOKEN_3",
    },

    "D1.3.3": {
        "account_id": "f2bf38f76018c112bffc762e4b67bfff",
        "database_id": "b46644ac-f405-4545-ba61-9b2379619c79",
        "token_env": "CLOUDFLARE_API_TOKEN_3",
    },

    "D1.3.4": {
        "account_id": "f2bf38f76018c112bffc762e4b67bfff",
        "database_id": "e2fe703b-e07b-4cee-9118-4075a261a9ea",
        "token_env": "CLOUDFLARE_API_TOKEN_3",
    },

    "D1.3.5": {
        "account_id": "f2bf38f76018c112bffc762e4b67bfff",
        "database_id": "c096fa0f-78fb-428d-adc5-50fb4d66c2c0",
        "token_env": "CLOUDFLARE_API_TOKEN_3",
    },

    "D1.3.6": {
        "account_id": "f2bf38f76018c112bffc762e4b67bfff",
        "database_id": "a701f494-bc40-462c-bdf7-5e2fea09847e",
        "token_env": "CLOUDFLARE_API_TOKEN_3",
    },

    "D1.3.7": {
        "account_id": "f2bf38f76018c112bffc762e4b67bfff",
        "database_id": "6464544a-793c-474e-bb9c-52a6f11b056a",
        "token_env": "CLOUDFLARE_API_TOKEN_3",
    },

    "D1.3.8": {
        "account_id": "f2bf38f76018c112bffc762e4b67bfff",
        "database_id": "5e922691-72bd-4dd9-b909-c55db3af7548",
        "token_env": "CLOUDFLARE_API_TOKEN_3",
    },

    "D1.3.9": {
        "account_id": "f2bf38f76018c112bffc762e4b67bfff",
        "database_id": "0aa787aa-317b-4bcc-aeb2-9cda666ecf91",
        "token_env": "CLOUDFLARE_API_TOKEN_3",
    },

    "D1.3.10": {
        "account_id": "f2bf38f76018c112bffc762e4b67bfff",
        "database_id": "8ad226e1-a3d9-4d77-bd40-c54133286746",
        "token_env": "CLOUDFLARE_API_TOKEN_3",
    },
}

# ================== D1 ROUTER ORDER ==================

D1_ORDER = [
    # D1.1
    "D1.1.1",
    "D1.1.2",
    "D1.1.3",
    "D1.1.4",
    "D1.1.5",
    "D1.1.6",
    "D1.1.7",
    "D1.1.8",
    "D1.1.9",
    "D1.1.10",

    # D1.2
    "D1.2.1",
    "D1.2.2",
    "D1.2.3",
    "D1.2.4",
    "D1.2.5",
    "D1.2.6",
    "D1.2.7",
    "D1.2.8",
    "D1.2.9",
    "D1.2.10",

    # D1.3
    "D1.3.1",
    "D1.3.2",
    "D1.3.3",
    "D1.3.4",
    "D1.3.5",
    "D1.3.6",
    "D1.3.7",
    "D1.3.8",
    "D1.3.9",
    "D1.3.10",
]


# ================== D1 ROUTER CHECK ==================

if len(D1_ORDER) != 30:

    raise RuntimeError(
        f"D1 ROUTER ORDER INVALID: "
        f"expected 30 databases, got {len(D1_ORDER)}"
    )


missing_d1 = [
    d1_name
    for d1_name in D1_ORDER
    if d1_name not in D1_DATABASES
]


if missing_d1:

    raise RuntimeError(
        f"D1 ROUTER ORDER HAS MISSING DATABASES: "
        f"{missing_d1}"
    )

# ================== USER ACTIONS STATE ==================

trial_days_waiting = {}


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


# ================== CORS ==================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kusuo-miniapp.onrender.com",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================== USER INTERFACE ==================

def main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 МЕНЮ",
                    callback_data="open_menu",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛟 Поддержка",
                    callback_data="support",
                ),
                InlineKeyboardButton(
                    text="⚙️ Настройки",
                    callback_data="settings",
                ),
            ],
        ]
    )


# ================== REQUIRED SUBSCRIPTION CHECK ==================

async def get_required_subscriptions():

    if db_pool is None:
        logger.error(
            "REQUIRED SUBSCRIPTION CHECK | DATABASE POOL IS NONE"
        )
        return []

    try:

        async with db_pool.acquire() as conn:

            rows = await conn.fetch(
                """
                SELECT
                    id,
                    chat_id,
                    title,
                    username,
                    invite_link
                FROM required_subscriptions
                WHERE is_active = TRUE
                ORDER BY id ASC
                """
            )

        return rows

    except Exception as e:

        logger.exception(
            "REQUIRED SUBSCRIPTION LOAD ERROR | error=%s",
            e,
        )

        return []


async def get_unsubscribed_required_chats(user_id):

    subscriptions = await get_required_subscriptions()

    if not subscriptions:
        return []

    unsubscribed = []

    for subscription in subscriptions:

        try:

            member = await bot.get_chat_member(
                chat_id=subscription["chat_id"],
                user_id=user_id,
            )

            if member.status not in (
                "member",
                "administrator",
                "creator",
            ):

                unsubscribed.append(subscription)

        except Exception as e:

            logger.warning(
                "REQUIRED SUBSCRIPTION CHECK ERROR | "
                "user=%s | chat_id=%s | error=%s",
                user_id,
                subscription["chat_id"],
                e,
            )

            unsubscribed.append(subscription)

    return unsubscribed


async def show_required_subscription_screen(
    message,
    user_id,
):

    subscriptions = await get_unsubscribed_required_chats(
        user_id
    )

    if not subscriptions:
        return False

    keyboard = []

    for subscription in subscriptions:

        if subscription["invite_link"]:

            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"📢 {subscription['title']}",
                        url=subscription["invite_link"],
                    )
                ]
            )

        elif subscription["username"]:

            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"📢 {subscription['title']}",
                        url=f"https://t.me/{subscription['username']}",
                    )
                ]
            )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔄 ПРОВЕРИТЬ ПОДПИСКУ",
                callback_data="check_required_subscription",
            )
        ]
    )

    text = (
        "📢 ОБЯЗАТЕЛЬНАЯ ПОДПИСКА\n\n"
        "Чтобы пользоваться Kusuo Saiki, "
        "необходимо подписаться на следующие "
        "группы или каналы:\n\n"
        "После подписки нажмите "
        "«🔄 ПРОВЕРИТЬ ПОДПИСКУ»."
    )

    markup = InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

    # ================== MESSAGE FROM USER ==================

    if message.from_user is not None:

        await message.answer(
            text,
            reply_markup=markup,
        )

    # ================== MESSAGE FROM BOT ==================

    else:

        await message.edit_text(
            text,
            reply_markup=markup,
        )

    return True


@dp.message(CommandStart())
async def start_command(message):

    # ================== OWNER ==================

    if message.from_user.id == OWNER_ID:

        await message.answer(
            "👋 Добро пожаловать в Kusuo Saiki!\n\n"
            "Умный помощник для управления "
            "сообщениями вашего Telegram Business.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👑 АДМИН",
                            callback_data="admin_panel",
                        ),
                        InlineKeyboardButton(
                            text="👤 ПОЛЬЗОВАТЕЛЬ",
                            callback_data="user_mode",
                        ),
                    ]
                ]
            ),
        )

        return

    # ================== REQUIRED SUBSCRIPTION ==================

    has_unsubscribed = await show_required_subscription_screen(
        message,
        message.from_user.id,
    )

    if has_unsubscribed:
        return

    # ================== USER ==================

    await message.answer(
        "👋 Добро пожаловать в Kusuo Saiki!\n\n"
        "Умный помощник для управления "
        "сообщениями вашего Telegram Business.",
        reply_markup=main_menu_keyboard(),
    )
    
    
# ================== USERS SEARCH STATE ==================

users_search_waiting = set()


# ================== USER ACTIONS STATE ==================

trial_days_waiting = {}


# ================== UI CALLBACKS ==================

@dp.callback_query()
async def handle_ui_callback(callback: CallbackQuery):

    # ================== TRIAL OK ==================

    if callback.data == "trial_ok":

        try:

            await callback.answer()

        except Exception as e:

            logger.warning(
                "TRIAL OK ANSWER ERROR | error=%s",
                e,
            )

        try:

            await callback.message.delete()

            logger.info(
                "TRIAL OK MESSAGE DELETED | user=%s",
                callback.from_user.id,
            )

        except Exception as e:

            logger.exception(
                "TRIAL OK DELETE ERROR | user=%s | error=%s",
                callback.from_user.id,
                e,
            )

        return

    # ================== CALLBACK CONFIRM ==================

    if callback.data == "instruction":

        try:
            await callback.answer(
                "📖 ИНСТРУКЦИЯ\n\n"
                "1. Нажмите на кнопку «НАСТРОЙКИ АККАУНТА» в боте.\n\n"
                "2. Нажмите «АВТОМАТИЗАЦИЯ ЧАТОВ».\n\n"
                "3. Добавьте бота @KusuoSaikibot.",
                show_alert=True,
            )
        except Exception as e:
            logger.warning(
                "INSTRUCTION CALLBACK ERROR | error=%s",
                e,
            )

        return

        # ================== BUSINESS CONNECTION STATUS ==================

    async def get_business_connection_status(
        business_connection_id
    ):

        try:

            connection = await bot.get_business_connection(
                business_connection_id=business_connection_id
            )

            logger.info(
                "BUSINESS CONNECTION STATUS | "
                "connection=%s | enabled=%s",
                business_connection_id,
                connection.is_enabled,
            )

            return connection.is_enabled

        except Exception as e:

            logger.exception(
                "BUSINESS CONNECTION STATUS ERROR | "
                "connection=%s | error=%s",
                business_connection_id,
                e,
            )

            return False


    # ================== CHECK BUSINESS CONNECTION ==================

    async def is_business_connected(user_id):

        if db_pool is None:

            logger.error(
                "BUSINESS CONNECTION CHECK | DATABASE POOL IS NONE"
            )

            return False

        try:

            async with db_pool.acquire() as conn:

                row = await conn.fetchrow(
                    """
                    SELECT business_connection_id
                    FROM business_accounts
                    WHERE telegram_user_id = $1
                    """,
                    user_id,
                )

            if not row:

                logger.info(
                    "BUSINESS CONNECTION CHECK | "
                    "user=%s | no database record",
                    user_id,
                )

                return False

            business_connection_id = row[
                "business_connection_id"
            ]

            return await get_business_connection_status(
                business_connection_id
            )

        except Exception as e:

            logger.exception(
                "BUSINESS CONNECTION CHECK ERROR | "
                "user=%s | error=%s",
                user_id,
                e,
            )

            return False
            

    # ================== GET ALL BUSINESS USERS ==================

    async def get_all_business_users():

        if db_pool is None:

            logger.error(
                "GET BUSINESS USERS | DATABASE POOL IS NONE"
            )

            return []

        try:

            async with db_pool.acquire() as conn:

                rows = await conn.fetch(
                    """
                    SELECT
                        telegram_user_id,
                        business_connection_id,
                        first_name,
                        last_name,
                        username
                    FROM business_accounts
                    ORDER BY first_name ASC, last_name ASC
                    """
                )

            users = []

            for row in rows:

                is_connected = await get_business_connection_status(
                    row["business_connection_id"]
                )

                first_name = row["first_name"] or ""
                last_name = row["last_name"] or ""

                full_name = (
                    f"{first_name} {last_name}"
                    .strip()
                )

                if not full_name:

                    full_name = "Без имени"

                users.append(
                    {
                        "telegram_user_id": row["telegram_user_id"],
                        "first_name": first_name,
                        "last_name": last_name,
                        "username": row["username"],
                        "name": full_name,
                        "is_connected": is_connected,
                    }
                )

            logger.info(
                "GET BUSINESS USERS | total=%s",
                len(users),
            )

            return users

        except Exception as e:

            logger.exception(
                "GET BUSINESS USERS ERROR | error=%s",
                e,
            )

            return []
            
            
    # ================== START SCREEN ==================

    async def show_start_screen():
        await callback.message.edit_text(
            "👋 Добро пожаловать в Kusuo Saiki!\n\n"
            "Умный помощник для управления "
            "сообщениями вашего Telegram Business.\n\n"
            "Подключите бота к Telegram Business, "
            "чтобы открыть все функции.",
            reply_markup=main_menu_keyboard(),
        )

    # ================== SETTINGS ==================

    async def show_settings():
        connected = await is_business_connected(
            callback.from_user.id
        )

        if connected:
            status_text = "🟢 Бот подключён"
        else:
            status_text = "🔴 Бот не подключён"

        await callback.message.edit_text(
            "⚙️ НАСТРОЙКИ\n\n"
            "Статус подключения:\n"
            f"{status_text}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📖 ИНСТРУКЦИЯ",
                            callback_data="instruction",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⚙️ НАСТРОЙКИ АККАУНТА",
                            url="tg://settings/edit",
                        ),
                        InlineKeyboardButton(
                            text="🔄 ПРОВЕРИТЬ",
                            callback_data="check_connection",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ НАЗАД",
                            callback_data="back_start",
                        )
                    ],
                ]
            ),
        )


    # ================== CHECK REQUIRED SUBSCRIPTION ==================

    if callback.data == "check_required_subscription":

        # ================== OWNER ==================

        if callback.from_user.id == OWNER_ID:

            await callback.answer(
                "👑 Для владельца обязательная подписка не требуется.",
                show_alert=True,
            )

            return

        # ================== CHECK SUBSCRIPTION ==================

        unsubscribed = await get_unsubscribed_required_chats(
            callback.from_user.id
        )

        # ================== NOT SUBSCRIBED ==================

        if unsubscribed:

            await callback.answer(
                "😏 Ты ещё не подписался...\n\n"
                "Не выйдет зайти и пользоваться мной 😉💔\n\n"
                "Подпишись на все группы и каналы выше "
                "и попробуй ещё раз.",
                show_alert=True,
            )

            return

        # ================== SUCCESS ==================

        await callback.answer(
            "🎉 Всё отлично!\n\n"
            "Ты подписался на все обязательные каналы. "
            "Добро пожаловать ❤️",
            show_alert=True,
        )

           # ================== OPEN WELCOME SCREEN ==================

        await callback.message.edit_text(
            "👋 Добро пожаловать в Kusuo Saiki!\n\n"
            "Умный помощник для управления "
            "сообщениями вашего Telegram Business.\n\n"
            "Подключите бота к Telegram Business, "
            "чтобы открыть все функции.",
            reply_markup=main_menu_keyboard(),
        )

        return
        
        
            # ================== ADMIN PANEL ==================

    if callback.data == "admin_panel":

        if callback.from_user.id != OWNER_ID:
            return

        await callback.message.edit_text(
            "👑 АДМИН-ПАНЕЛЬ\n\n"
            "Выберите раздел:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📢 ОБЯЗАТЕЛЬНАЯ ПОДПИСКА",
                            callback_data="admin_subscription",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="👥 ПОЛЬЗОВАТЕЛИ",
                            callback_data="admin_users",
                        ),
                        InlineKeyboardButton(
                            text="💰 ЦЕНЫ",
                            callback_data="admin_prices",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="🆓 БЕСПЛАТНЫЙ ДОСТУП",
                            callback_data="admin_free_access",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ НАЗАД",
                            callback_data="admin_start",
                        )
                    ],
                ]
            ),
        )

        return


        # ================== ADMIN USERS ==================

    elif callback.data == "admin_users":

        if callback.from_user.id != OWNER_ID:
            return

        users_search_waiting.discard(
            callback.from_user.id
        )

        users = await get_all_business_users()

        # ================== EMPTY LIST ==================

        if not users:

            await callback.message.edit_text(
                "👥 ПОЛЬЗОВАТЕЛИ\n\n"
                "Пока нет пользователей, "
                "подключавших Telegram Business.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⬅️ НАЗАД",
                                callback_data="admin_panel",
                            )
                        ]
                    ]
                ),
            )

            return

        # ================== PAGINATION ==================

        page = 1
        users_per_page = 20

        total_pages = (
            len(users) + users_per_page - 1
        ) // users_per_page

        start_index = (
            page - 1
        ) * users_per_page

        end_index = (
            start_index + users_per_page
        )

        page_users = users[
            start_index:end_index
        ]

        # ================== USER BUTTONS ==================

        keyboard = []

        for index in range(
            0,
            len(page_users),
            2,
        ):

            row = []

            first_user = page_users[index]

            first_status = (
                "✅"
                if first_user["is_connected"]
                else "❌"
            )

            row.append(
                InlineKeyboardButton(
                    text=(
                        f"{first_status} "
                        f"{first_user['name']}"
                    ),
                    callback_data=(
                        f"user_manage:"
                        f"{first_user['telegram_user_id']}"
                    ),
                )
            )

            if index + 1 < len(page_users):

                second_user = page_users[
                    index + 1
                ]

                second_status = (
                    "✅"
                    if second_user["is_connected"]
                    else "❌"
                )

                row.append(
                    InlineKeyboardButton(
                        text=(
                            f"{second_status} "
                            f"{second_user['name']}"
                        ),
                        callback_data=(
                            f"user_manage:"
                            f"{second_user['telegram_user_id']}"
                        ),
                    )
                )

            keyboard.append(row)

        # ================== SEARCH ==================

        keyboard.insert(
            0,
            [
                InlineKeyboardButton(
                    text="🔎 ПОИСК",
                    callback_data="users_search",
                )
            ],
        )

        # ================== PAGE NAVIGATION ==================

        navigation = []

        if page > 1:

            navigation.append(
                InlineKeyboardButton(
                    text="◀️",
                    callback_data=(
                        f"users_page:{page - 1}"
                    ),
                )
            )

        else:

            navigation.append(
                InlineKeyboardButton(
                    text="◀️",
                    callback_data="users_page_disabled",
                )
            )

        navigation.append(
            InlineKeyboardButton(
                text=f"{page} / {total_pages}",
                callback_data="users_page_current",
            )
        )

        if page < total_pages:

            navigation.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data=(
                        f"users_page:{page + 1}"
                    ),
                )
            )

        else:

            navigation.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data="users_page_disabled",
                )
            )

        keyboard.append(navigation)

        # ================== BACK ==================

        keyboard.append(
            [
                InlineKeyboardButton(
                    text="⬅️ НАЗАД",
                    callback_data="admin_panel",
                )
            ]
        )

        # ================== SHOW USERS ==================

        await callback.message.edit_text(
            "👥 ПОЛЬЗОВАТЕЛИ\n\n"
            f"Всего пользователей: {len(users)}\n\n"
            "Выберите пользователя:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard
            ),
        )

        return
        
        
            # ================== USERS SEARCH ==================

    elif callback.data == "users_search":

        if callback.from_user.id != OWNER_ID:
            return

        users_search_waiting.add(
            callback.from_user.id
        )

        await callback.message.edit_text(
            "🔎 ПОИСК ПОЛЬЗОВАТЕЛЯ\n\n"
            "Введите имя, фамилию или username "
            "пользователя:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="❌ ОТМЕНА",
                            callback_data="admin_users",
                        )
                    ]
                ]
            ),
        )

        return
        
        
               # ================== USER MANAGEMENT ==================

    elif callback.data.startswith("user_manage:"):

        if callback.from_user.id != OWNER_ID:
            return

        try:
            target_user_id = int(
                callback.data.split(":", 1)[1]
            )

        except (ValueError, IndexError):

            await callback.answer(
                "❌ Некорректный пользователь.",
                show_alert=True,
            )

            return

        if db_pool is None:

            await callback.answer(
                "❌ База данных недоступна.",
                show_alert=True,
            )

            return

        async with db_pool.acquire() as conn:

            user = await conn.fetchrow(
                """
                SELECT
                    telegram_user_id,
                    business_connection_id,
                    first_name,
                    last_name,
                    username,
                    topic_id
                FROM business_accounts
                WHERE telegram_user_id = $1
                """,
                target_user_id,
            )

        if not user:

            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )

            return

        # ================== USER NAME ==================

        name_parts = []

        if user["first_name"]:
            name_parts.append(
                user["first_name"]
            )

        if user["last_name"]:
            name_parts.append(
                user["last_name"]
            )

        user_name = " ".join(
            name_parts
        ).strip()

        if not user_name:
            user_name = "Без имени"

        # ================== USERNAME ==================

        username = user["username"]

        if username:

            username_text = (
                f"@{username.lstrip('@')}"
            )

        else:

            username_text = "Не указан"

        # ================== CONNECTION STATUS ==================

        is_connected = False

        try:

            connection = await bot.get_business_connection(
                user["business_connection_id"]
            )

            is_connected = connection.is_enabled

        except Exception as e:

            logger.warning(
                "USER MANAGEMENT CONNECTION ERROR | "
                "user=%s | error=%s",
                target_user_id,
                e,
            )

        connection_status = (
            "🟢 Подключён"
            if is_connected
            else "🔴 Отключён"
        )

        # ================== USER MENU ==================

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👤 ИНФОРМАЦИЯ",
                        callback_data=(
                            f"user_info:{target_user_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔌 BUSINESS",
                        callback_data=(
                            f"user_business:{target_user_id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        text="📢 ОБЯЗАТЕЛЬНЫЕ ПОДПИСКИ",
                        callback_data=(
                            f"user_subscription:{target_user_id}"
                        ),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🛠 ДЕЙСТВИЯ",
                        callback_data=(
                            f"user_actions:{target_user_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ НАЗАД",
                        callback_data="admin_users",
                    )
                ],
            ]
        )

        await callback.message.edit_text(
            "👤 УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЕМ\n\n"
            f"Имя: {user_name}\n"
            f"Username: {username_text}\n"
            f"ID: {user['telegram_user_id']}\n\n"
            f"Статус: {connection_status}\n"
            f"Топик: {user['topic_id']}\n\n"
            "Выберите действие:",
            reply_markup=keyboard,
        )

        await callback.answer()

        return


    # ================== USER ACTIONS ==================

    elif callback.data.startswith("user_actions:"):

        if callback.from_user.id != OWNER_ID:
            return

        try:

            target_user_id = int(
                callback.data.split(":", 1)[1]
            )

        except (ValueError, IndexError):

            await callback.answer(
                "❌ Некорректный пользователь.",
                show_alert=True,
            )

            return

        if db_pool is None:

            await callback.answer(
                "❌ База данных недоступна.",
                show_alert=True,
            )

            return

        async with db_pool.acquire() as conn:

            user = await conn.fetchrow(
                """
                SELECT
                    telegram_user_id,
                    first_name,
                    last_name
                FROM business_accounts
                WHERE telegram_user_id = $1
                """,
                target_user_id,
            )

        if not user:

            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )

            return

        # ================== USER NAME ==================

        name_parts = []

        if user["first_name"]:
            name_parts.append(
                user["first_name"]
            )

        if user["last_name"]:
            name_parts.append(
                user["last_name"]
            )

        user_name = " ".join(
            name_parts
        ).strip()

        if not user_name:
            user_name = "Без имени"

        # ================== ACTIONS KEYBOARD ==================

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎁 ВЫДАТЬ ПРОБНЫЙ ПЕРИОД",
                        callback_data=(
                            f"action_trial:"
                            f"{target_user_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🆓 ВЫДАТЬ ПОЛНЫЙ ДОСТУП БЕСПЛАТНО",
                        callback_data=(
                            f"action_free:"
                            f"{target_user_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💸 СДЕЛАТЬ СКИДКУ",
                        callback_data=(
                            f"action_discount:"
                            f"{target_user_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🚫 ЗАБЛОКИРОВАТЬ",
                        callback_data=(
                            f"action_block:"
                            f"{target_user_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔓 РАЗБЛОКИРОВАТЬ",
                        callback_data=(
                            f"action_unblock:"
                            f"{target_user_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🗑 УДАЛИТЬ ПОЛЬЗОВАТЕЛЯ",
                        callback_data=(
                            f"action_delete:"
                            f"{target_user_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ НАЗАД",
                        callback_data=(
                            f"user_manage:"
                            f"{target_user_id}"
                        ),
                    )
                ],
            ]
        )

        await callback.message.edit_text(
            "🛠 ДЕЙСТВИЯ\n\n"
            f"Пользователь: {user_name}\n"
            f"Telegram ID: {target_user_id}\n\n"
            "Выберите действие:",
            reply_markup=keyboard,
        )

        await callback.answer()

        return


    # ================== GIVE TRIAL ==================

    elif callback.data.startswith("action_trial:"):

        if callback.from_user.id != OWNER_ID:
            await callback.answer(
                "🚫 Недостаточно прав.",
                show_alert=True,
            )
            return

        try:
            target_user_id = int(
                callback.data.split(":")[1]
            )

        except (IndexError, ValueError):

            await callback.answer(
                "❌ Не удалось определить пользователя.",
                show_alert=True,
            )

            return

        trial_days_waiting[
            callback.from_user.id
        ] = target_user_id

        await callback.message.edit_text(
            "🎁 ВЫДАЧА ПРОБНОГО ПЕРИОДА\n\n"
            f"Пользователь: {target_user_id}\n\n"
            "Введите количество дней, на которое "
            "выдать пробный период.\n\n"
            "Например:\n"
            "1 — 1 день\n"
            "7 — 7 дней\n"
            "30 — 30 дней\n"
            "100 — 100 дней",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ НАЗАД",
                            callback_data=(
                                f"user_manage:"
                                f"{target_user_id}"
                            ),
                        )
                    ]
                ]
            ),
        )

        await callback.answer()

        return


    # ================== USER SUBSCRIPTION ==================

    elif callback.data.startswith("user_subscription:"):

        if callback.from_user.id != OWNER_ID:
            return

        try:

            target_user_id = int(
                callback.data.split(":", 1)[1]
            )

        except (ValueError, IndexError):

            await callback.answer(
                "❌ Некорректный пользователь.",
                show_alert=True,
            )

            return

        if db_pool is None:

            await callback.answer(
                "❌ База данных недоступна.",
                show_alert=True,
            )

            return

        # ================== USER ==================

        async with db_pool.acquire() as conn:

            user = await conn.fetchrow(
                """
                SELECT
                    telegram_user_id,
                    first_name,
                    last_name
                FROM business_accounts
                WHERE telegram_user_id = $1
                """,
                target_user_id,
            )

        if not user:

            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )

            return

        # ================== REQUIRED SUBSCRIPTIONS ==================

        subscriptions = await get_required_subscriptions()

        # ================== USER NAME ==================

        name_parts = []

        if user["first_name"]:
            name_parts.append(
                user["first_name"]
            )

        if user["last_name"]:
            name_parts.append(
                user["last_name"]
            )

        user_name = " ".join(
            name_parts
        ).strip()

        if not user_name:
            user_name = "Без имени"

        # ================== NO SUBSCRIPTIONS ==================

        if not subscriptions:

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ НАЗАД",
                            callback_data=(
                                f"user_manage:"
                                f"{target_user_id}"
                            ),
                        )
                    ]
                ]
            )

            await callback.message.edit_text(
                "📢 ОБЯЗАТЕЛЬНЫЕ ПОДПИСКИ\n\n"
                f"Пользователь: {user_name}\n\n"
                "Обязательных подписок пока нет.",
                reply_markup=keyboard,
            )

            await callback.answer()

            return

        # ================== CHECK USER ==================

        subscribed_count = 0
        not_subscribed_count = 0

        subscription_lines = []

        for subscription in subscriptions:

            chat_id = subscription["chat_id"]
            title = subscription["title"]

            try:

                member = await bot.get_chat_member(
                    chat_id=chat_id,
                    user_id=target_user_id,
                )

                status = member.status

                is_subscribed = status in (
                    "creator",
                    "administrator",
                    "member",
                )

            except Exception as e:

                logger.warning(
                    "USER SUBSCRIPTION CHECK ERROR | "
                    "user=%s | chat=%s | error=%s",
                    target_user_id,
                    chat_id,
                    e,
                )

                is_subscribed = False

            if is_subscribed:

                subscribed_count += 1

                subscription_lines.append(
                    f"✅ {title}"
                )

            else:

                not_subscribed_count += 1

                subscription_lines.append(
                    f"❌ {title}"
                )

        # ================== KEYBOARD ==================

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 ПРОВЕРИТЬ",
                        callback_data=(
                            f"user_subscription:"
                            f"{target_user_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ НАЗАД",
                        callback_data=(
                            f"user_manage:"
                            f"{target_user_id}"
                        ),
                    )
                ],
            ]
        )

                # ================== SHOW SUBSCRIPTIONS ==================

        text = (
            "📢 ОБЯЗАТЕЛЬНЫЕ ПОДПИСКИ\n\n"
            f"Пользователь: {user_name}\n\n"
            + "\n".join(subscription_lines)
            + "\n\n"
            f"✅ Подписан: {subscribed_count}\n"
            f"❌ Не подписан: {not_subscribed_count}"
        )

        try:

            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
            )

        except Exception as e:

            if "message is not modified" not in str(e):

                logger.exception(
                    "USER SUBSCRIPTION EDIT ERROR"
                )

                await callback.answer(
                    "❌ Не удалось обновить информацию.",
                    show_alert=True,
                )

                return

        await callback.answer(
            "🔄 Проверка выполнена."
        )

        return
        
        
    # ================== USER BUSINESS ==================

    elif callback.data.startswith("user_business:"):

        if callback.from_user.id != OWNER_ID:
            return

        try:

            target_user_id = int(
                callback.data.split(":", 1)[1]
            )

        except (ValueError, IndexError):

            await callback.answer(
                "❌ Некорректный пользователь.",
                show_alert=True,
            )

            return

        if db_pool is None:

            await callback.answer(
                "❌ База данных недоступна.",
                show_alert=True,
            )

            return

        async with db_pool.acquire() as conn:

            user = await conn.fetchrow(
                """
                SELECT
                    telegram_user_id,
                    business_connection_id,
                    trial_until,
                    subscription_until
                FROM business_accounts
                WHERE telegram_user_id = $1
                """,
                target_user_id,
            )

        if not user:

            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )

            return

        # ================== BUSINESS STATUS ==================

        is_connected = False

        try:

            connection = await bot.get_business_connection(
                user["business_connection_id"]
            )

            is_connected = connection.is_enabled

        except Exception as e:

            logger.warning(
                "BUSINESS STATUS ERROR | "
                "user=%s | error=%s",
                target_user_id,
                e,
            )

        connection_status = (
            "🟢 Подключён"
            if is_connected
            else "🔴 Отключён"
        )

        # ================== TRIAL ==================

        trial_until = user["trial_until"]

        if trial_until:

            trial_text = trial_until.strftime(
                "%d.%m.%Y %H:%M"
            )

        else:

            trial_text = "Не выдан"

        # ================== SUBSCRIPTION ==================

        subscription_until = user["subscription_until"]

        if subscription_until:

            subscription_text = subscription_until.strftime(
                "%d.%m.%Y %H:%M"
            )

        else:

            subscription_text = "Не активна"

        # ================== BUSINESS KEYBOARD ==================

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 ОБНОВИТЬ СТАТУС",
                        callback_data=(
                            f"user_business:"
                            f"{target_user_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ НАЗАД",
                        callback_data=(
                            f"user_manage:"
                            f"{target_user_id}"
                        ),
                    )
                ],
            ]
        )

                # ================== SHOW BUSINESS ==================

        text = (
            "🔌 BUSINESS\n\n"
            f"Статус подключения: {connection_status}\n\n"
            "🎁 Пробный период:\n"
            f"{trial_text}\n\n"
            "💳 Подписка:\n"
            f"{subscription_text}"
        )

        try:

            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
            )

        except Exception as e:

            if "message is not modified" not in str(e):

                logger.exception(
                    "USER BUSINESS EDIT ERROR"
                )

                await callback.answer(
                    "❌ Не удалось обновить информацию.",
                    show_alert=True,
                )

                return

        await callback.answer(
            "🔄 Статус обновлён."
        )

        return
        
        
    # ================== USER INFO ==================

    elif callback.data.startswith("user_info:"):

        if callback.from_user.id != OWNER_ID:
            return

        try:

            target_user_id = int(
                callback.data.split(":", 1)[1]
            )

        except (ValueError, IndexError):

            await callback.answer(
                "❌ Некорректный пользователь.",
                show_alert=True,
            )

            return

        if db_pool is None:

            await callback.answer(
                "❌ База данных недоступна.",
                show_alert=True,
            )

            return

        async with db_pool.acquire() as conn:

            user = await conn.fetchrow(
                """
                SELECT
                    telegram_user_id,
                    business_connection_id,
                    first_name,
                    last_name,
                    username,
                    topic_id,
                    created_at,
                    updated_at
                FROM business_accounts
                WHERE telegram_user_id = $1
                """,
                target_user_id,
            )

        if not user:

            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )

            return

        # ================== USER NAME ==================

        name_parts = []

        if user["first_name"]:
            name_parts.append(
                user["first_name"]
            )

        if user["last_name"]:
            name_parts.append(
                user["last_name"]
            )

        user_name = " ".join(
            name_parts
        ).strip()

        if not user_name:
            user_name = "Без имени"

        # ================== USERNAME ==================

        username = user["username"]

        if username:

            username_text = (
                f"@{username.lstrip('@')}"
            )

        else:

            username_text = "Не указан"

        # ================== DATES ==================

        created_at = user["created_at"]

        if created_at:

            created_text = created_at.strftime(
                "%d.%m.%Y %H:%M"
            )

        else:

            created_text = "Неизвестно"

        updated_at = user["updated_at"]

        if updated_at:

            updated_text = updated_at.strftime(
                "%d.%m.%Y %H:%M"
            )

        else:

            updated_text = "Неизвестно"

        # ================== USER INFO KEYBOARD ==================

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ НАЗАД",
                        callback_data=(
                            f"user_manage:{target_user_id}"
                        ),
                    )
                ]
            ]
        )

        # ================== SHOW USER INFO ==================

        await callback.message.edit_text(
            "👤 ИНФОРМАЦИЯ\n\n"
            f"Имя: {user_name}\n"
            f"Username: {username_text}\n"
            f"Telegram ID: {user['telegram_user_id']}\n\n"
            f"📅 Добавлен: {created_text}\n"
            f"🔄 Обновлён: {updated_text}\n\n"
            "🔌 Business connection:\n"
            f"{user['business_connection_id']}\n\n"
            f"🗂 Топик LOG: {user['topic_id']}",
            reply_markup=keyboard,
        )

        await callback.answer()

        return


    # ================== USERS PAGE ==================

    elif callback.data.startswith("users_page:"):

        if callback.from_user.id != OWNER_ID:
            return

        try:

            page = int(
                callback.data.split(":", 1)[1]
            )

        except (ValueError, IndexError):

            return

        users = await get_all_business_users()

        if not users:

            await callback.message.edit_text(
                "👥 ПОЛЬЗОВАТЕЛИ\n\n"
                "Пока нет пользователей, "
                "подключавших Telegram Business.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⬅️ НАЗАД",
                                callback_data="admin_panel",
                            )
                        ]
                    ]
                ),
            )

            return

        # ================== PAGINATION ==================

        users_per_page = 20

        total_pages = (
            len(users) + users_per_page - 1
        ) // users_per_page

        if page < 1:
            page = 1

        if page > total_pages:
            page = total_pages

        start_index = (
            page - 1
        ) * users_per_page

        end_index = (
            start_index + users_per_page
        )

        page_users = users[
            start_index:end_index
        ]

        # ================== USER BUTTONS ==================

        keyboard = []

        for index in range(
            0,
            len(page_users),
            2,
        ):

            row = []

            first_user = page_users[index]

            first_status = (
                "✅"
                if first_user["is_connected"]
                else "❌"
            )

            row.append(
                InlineKeyboardButton(
                    text=(
                        f"{first_status} "
                        f"{first_user['name']}"
                    ),
                    callback_data=(
                        f"user_manage:"
                        f"{first_user['telegram_user_id']}"
                    ),
                )
            )

            if index + 1 < len(page_users):

                second_user = page_users[
                    index + 1
                ]

                second_status = (
                    "✅"
                    if second_user["is_connected"]
                    else "❌"
                )

                row.append(
                    InlineKeyboardButton(
                        text=(
                            f"{second_status} "
                            f"{second_user['name']}"
                        ),
                        callback_data=(
                            f"user_manage:"
                            f"{second_user['telegram_user_id']}"
                        ),
                    )
                )

            keyboard.append(row)

        # ================== SEARCH ==================

        keyboard.insert(
            0,
            [
                InlineKeyboardButton(
                    text="🔎 ПОИСК",
                    callback_data="users_search",
                )
            ],
        )

        # ================== PAGE NAVIGATION ==================

        navigation = []

        if page > 1:

            navigation.append(
                InlineKeyboardButton(
                    text="◀️",
                    callback_data=(
                        f"users_page:{page - 1}"
                    ),
                )
            )

        else:

            navigation.append(
                InlineKeyboardButton(
                    text="◀️",
                    callback_data="users_page_disabled",
                )
            )

        navigation.append(
            InlineKeyboardButton(
                text=f"{page} / {total_pages}",
                callback_data="users_page_current",
            )
        )

        if page < total_pages:

            navigation.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data=(
                        f"users_page:{page + 1}"
                    ),
                )
            )

        else:

            navigation.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data="users_page_disabled",
                )
            )

        keyboard.append(navigation)

        # ================== BACK ==================

        keyboard.append(
            [
                InlineKeyboardButton(
                    text="⬅️ НАЗАД",
                    callback_data="admin_panel",
                )
            ]
        )

        # ================== SHOW PAGE ==================

        await callback.message.edit_text(
            "👥 ПОЛЬЗОВАТЕЛИ\n\n"
            f"Всего пользователей: {len(users)}\n\n"
            "Выберите пользователя:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard
            ),
        )

        return


    # ================== ADMIN SUBSCRIPTION ==================

    elif callback.data == "admin_subscription":

        if callback.from_user.id != OWNER_ID:
            return

        await callback.message.edit_text(
            "📢 ОБЯЗАТЕЛЬНАЯ ПОДПИСКА\n\n"
            "Здесь будут находиться группы и каналы, "
            "на которые пользователь должен подписаться "
            "для доступа к Kusuo Saiki.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="➕ ДОБАВИТЬ",
                            callback_data="subscription_add",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="📋 СПИСОК",
                            callback_data="subscription_list",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🗑 УДАЛИТЬ",
                            callback_data="subscription_delete",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ НАЗАД",
                            callback_data="admin_panel",
                        )
                    ],
                ]
            ),
        )

        return
                # ================== SUBSCRIPTION ADD ==================

    elif callback.data == "subscription_add":

        if callback.from_user.id != OWNER_ID:
            return

        subscription_add_waiting.add(
            callback.from_user.id
        )

        await callback.message.edit_text(
            "➕ ДОБАВЛЕНИЕ ПОДПИСКИ\n\n"
            "Пришлите ссылку на группу или канал, "
            "который пользователь должен будет "
            "обязательно посетить.\n\n"
            "⚠️ Бот обязательно должен быть добавлен "
            "в группу или канал и иметь статус администратора.\n\n"
            "Например:\n"
            "https://t.me/example",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ НАЗАД",
                            callback_data="admin_subscription",
                        )
                    ]
                ]
            ),
        )

        return


    # ================== SUBSCRIPTION LIST ==================

    elif callback.data == "subscription_list":

        if callback.from_user.id != OWNER_ID:
            return

        if db_pool is None:

            await callback.message.edit_text(
                "❌ Ошибка подключения к базе данных.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⬅️ НАЗАД",
                                callback_data="admin_subscription",
                            )
                        ]
                    ]
                ),
            )

            return

        try:

            async with db_pool.acquire() as conn:

                rows = await conn.fetch(
                    """
                    SELECT
                        id,
                        chat_id,
                        title,
                        username,
                        invite_link,
                        is_active
                    FROM required_subscriptions
                    ORDER BY id ASC
                    """
                )

        except Exception as e:

            logger.exception(
                "SUBSCRIPTION LIST ERROR | error=%s",
                e,
            )

            await callback.message.edit_text(
                "❌ Не удалось получить список подписок.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⬅️ НАЗАД",
                                callback_data="admin_subscription",
                            )
                        ]
                    ]
                ),
            )

            return

        # ================== EMPTY LIST ==================

        if not rows:

            await callback.message.edit_text(
                "📋 СПИСОК ПОДПИСОК\n\n"
                "Пока нет добавленных групп или каналов.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⬅️ НАЗАД",
                                callback_data="admin_subscription",
                            )
                        ]
                    ]
                ),
            )

            return

        # ================== BUILD LIST ==================

        text = "📋 СПИСОК ПОДПИСОК\n\n"

        for index, row in enumerate(rows, start=1):

            status = (
                "🟢 Активна"
                if row["is_active"]
                else "🔴 Выключена"
            )

            if row["username"]:
                chat_link = f"@{row['username']}"
            else:
                chat_link = row["invite_link"]

            text += (
                f"{index}. 📢 {row['title']}\n"
                f"   {chat_link}\n"
                f"   {status}\n\n"
            )

        # ================== SHOW LIST ==================

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ НАЗАД",
                            callback_data="admin_subscription",
                        )
                    ]
                ]
            ),
        )

        return


    # ================== SUBSCRIPTION DELETE CONFIRM ==================

    elif callback.data.startswith("subscription_delete_confirm:"):

        if callback.from_user.id != OWNER_ID:
            return

        try:

            subscription_id = int(
                callback.data.split(":", 1)[1]
            )

        except (ValueError, IndexError):

            await callback.message.answer(
                "❌ Некорректный ID подписки."
            )

            return

        if db_pool is None:

            await callback.message.edit_text(
                "❌ Ошибка подключения к базе данных.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⬅️ НАЗАД",
                                callback_data="admin_subscription",
                            )
                        ]
                    ]
                ),
            )

            return

        try:

            async with db_pool.acquire() as conn:

                deleted = await conn.fetchrow(
                    """
                    DELETE FROM required_subscriptions
                    WHERE id = $1
                    RETURNING title
                    """,
                    subscription_id,
                )

        except Exception as e:

            logger.exception(
                "SUBSCRIPTION DELETE ERROR | "
                "id=%s | error=%s",
                subscription_id,
                e,
            )

            await callback.message.edit_text(
                "❌ Не удалось удалить подписку.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⬅️ НАЗАД",
                                callback_data="admin_subscription",
                            )
                        ]
                    ]
                ),
            )

            return

        if not deleted:

            await callback.message.edit_text(
                "❌ Подписка не найдена.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⬅️ НАЗАД",
                                callback_data="admin_subscription",
                            )
                        ]
                    ]
                ),
            )

            return

        logger.info(
            "SUBSCRIPTION DELETED | id=%s | title=%s",
            subscription_id,
            deleted["title"],
        )

        await callback.message.edit_text(
            "✅ ПОДПИСКА УДАЛЕНА!\n\n"
            f"📢 {deleted['title']}\n\n"
            "Она больше не будет использоваться "
            "для обязательной подписки.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ НАЗАД",
                            callback_data="admin_subscription",
                        )
                    ]
                ]
            ),
        )

        return
        
        
    # ================== OWNER USER MODE ==================
    
    if callback.data == "user_mode":

        await callback.message.edit_text(
            "👋 Добро пожаловать в Kusuo Saiki!\n\n"
            "Умный помощник для управления "
            "сообщениями вашего Telegram Business.\n\n"
            "Подключите бота к Telegram Business, "
            "чтобы открыть все функции.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📋 МЕНЮ",
                            callback_data="open_menu",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🛟 Поддержка",
                            callback_data="support",
                        ),
                        InlineKeyboardButton(
                            text="⚙️ Настройки",
                            callback_data="settings",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ НАЗАД",
                            callback_data="admin_start",
                        )
                    ],
                ]
            ),
        )

        return
        

    # ================== SUBSCRIPTION DELETE ==================

    elif callback.data == "subscription_delete":

        if callback.from_user.id != OWNER_ID:
            return

        if db_pool is None:

            await callback.message.edit_text(
                "❌ Ошибка подключения к базе данных.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⬅️ НАЗАД",
                                callback_data="admin_subscription",
                            )
                        ]
                    ]
                ),
            )

            return

        try:

            async with db_pool.acquire() as conn:

                rows = await conn.fetch(
                    """
                    SELECT
                        id,
                        title,
                        username
                    FROM required_subscriptions
                    WHERE is_active = TRUE
                    ORDER BY id ASC
                    """
                )

        except Exception as e:

            logger.exception(
                "SUBSCRIPTION DELETE LIST ERROR | error=%s",
                e,
            )

            await callback.message.edit_text(
                "❌ Не удалось получить список подписок.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⬅️ НАЗАД",
                                callback_data="admin_subscription",
                            )
                        ]
                    ]
                ),
            )

            return

        # ================== EMPTY LIST ==================

        if not rows:

            await callback.message.edit_text(
                "🗑 УДАЛЕНИЕ ПОДПИСКИ\n\n"
                "Нет активных подписок для удаления.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⬅️ НАЗАД",
                                callback_data="admin_subscription",
                            )
                        ]
                    ]
                ),
            )

            return

        # ================== DELETE BUTTONS ==================

        keyboard = []

        for row in rows:

            title = row["title"]

            if row["username"]:
                title = f"📢 {title} (@{row['username']})"
            else:
                title = f"📢 {title}"

            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=title,
                        callback_data=f"subscription_delete_confirm:{row['id']}",
                    )
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    text="⬅️ НАЗАД",
                    callback_data="admin_subscription",
                )
            ]
        )

        await callback.message.edit_text(
            "🗑 УДАЛЕНИЕ ПОДПИСКИ\n\n"
            "Выберите группу или канал, "
            "который хотите удалить:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard
            ),
        )

        return
        
        
    # ================== OWNER USER MODE ==================
    
    if callback.data == "user_mode":

        await callback.message.edit_text(
            "👋 Добро пожаловать в Kusuo Saiki!\n\n"
            "Умный помощник для управления "
            "сообщениями вашего Telegram Business.\n\n"
            "Подключите бота к Telegram Business, "
            "чтобы открыть все функции.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📋 МЕНЮ",
                            callback_data="open_menu",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🛟 Поддержка",
                            callback_data="support",
                        ),
                        InlineKeyboardButton(
                            text="⚙️ Настройки",
                            callback_data="settings",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ НАЗАД",
                            callback_data="admin_start",
                        )
                    ],
                ]
            ),
        )

        return
        
        
    # ================== MAIN MENU ==================

    if callback.data == "open_menu":

        logger.info(
            "OPEN MENU | user=%s | owner=%s",
            callback.from_user.id,
            OWNER_ID,
        )

        access = await get_user_access_status(
            callback.from_user.id
        )

        logger.info(
            "OPEN MENU ACCESS | user=%s | access=%s",
            callback.from_user.id,
            access,
        )

        # ================== BLOCKED ==================

        if access["blocked"]:

            logger.info(
                "OPEN MENU | USER BLOCKED | user=%s",
                callback.from_user.id,
            )

            await callback.answer(
                "🚫 Доступ к Kusuo Saiki заблокирован.",
                show_alert=True,
            )

            return

        # ================== NO ACCESS ==================

        if not access["has_access"]:

            logger.info(
                "OPEN MENU | ACCESS DENIED | user=%s",
                callback.from_user.id,
            )

            # ================== TRIAL EXPIRED ==================

            if access["trial_expired"]:

                await callback.answer(
                    "🥺 Твой пробный период закончился.\n\n"
                    "Чтобы продолжить пользоваться Kusuo Saiki, "
                    "оформи подписку.",
                    show_alert=True,
                )

                logger.info(
                    "OPEN MENU | TRIAL EXPIRED POPUP SENT | user=%s",
                    callback.from_user.id,
                )

                return

            # ================== OTHER ACCESS ERROR ==================

            await callback.answer(
                "🚫 У тебя сейчас нет доступа к Kusuo Saiki.",
                show_alert=True,
            )

            logger.info(
                "OPEN MENU | NO ACCESS POPUP SENT | user=%s",
                callback.from_user.id,
            )

            return

        # ================== CALLBACK CONFIRM ==================

        await callback.answer()

        # ================== BUSINESS CONNECTION ==================

        connected = await is_business_connected(
            callback.from_user.id
        )

        if not connected:

            await show_settings()
            return

        # ================== MENU ==================

        await callback.message.edit_text(
            "📋 МЕНЮ\n\n"
            "Добро пожаловать в Kusuo Saiki!\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📨 Сообщения",
                            callback_data="menu_messages",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🗑 Удалённые",
                            callback_data="menu_deleted",
                        ),
                        InlineKeyboardButton(
                            text="✏️ Изменённые",
                            callback_data="menu_edited",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="👤 Мой аккаунт",
                            callback_data="menu_account",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⚙️ Настройки",
                            callback_data="settings",
                        )
                    ],
                ]
            ),
        )
        # ================== SUPPORT ==================
        
    elif callback.data == "support":
        
        await callback.message.edit_text(
            "🛟 ПОДДЕРЖКА\n\n"
            "Если у вас возникли вопросы или проблемы "
            "с Kusuo Saiki — наша поддержка всегда готова помочь.\n\n"
            "Нажмите кнопку ниже, чтобы обратиться в поддержку.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="💬 ОБРАТИТЬСЯ В ПОДДЕРЖКУ",
                            url="https://t.me/kusuosaiki290?direct",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ НАЗАД",
                            callback_data="back_start",
                        )
                    ],
                ]
            ),
        )
        
        
    # ================== SETTINGS ==================
    
    elif callback.data == "settings":
        
        await show_settings()

        # ================== CHECK CONNECTION ==================

    elif callback.data == "check_connection":

        connected = await is_business_connected(
            callback.from_user.id
        )

        try:

            if connected:

                await callback.message.edit_text(
                    "🟢 ПОДКЛЮЧЕНИЕ НАЙДЕНО\n\n"
                    "Kusuo Saiki успешно подключён "
                    "к Telegram Business.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="📋 ОТКРЫТЬ МЕНЮ",
                                    callback_data="open_menu",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    text="⬅️ НАЗАД",
                                    callback_data="back_start",
                                )
                            ],
                        ]
                    ),
                )

            else:

                await callback.message.edit_text(
                    "🔴 БОТ НЕ ПОДКЛЮЧЁН\n\n"
                    "Kusuo Saiki пока не подключён "
                    "к Telegram Business.\n\n"
                    "Подключите бота в настройках аккаунта, "
                    "а затем нажмите «Проверить подключение».",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="⚙️ НАСТРОЙКИ АККАУНТА",
                                    url="tg://settings/edit",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    text="🔄 ПРОВЕРИТЬ",
                                    callback_data="check_connection",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    text="⬅️ НАЗАД",
                                    callback_data="back_start",
                                )
                            ],
                        ]
                    ),
                )

        except Exception as e:

            if "message is not modified" in str(e):
                logger.info(
                    "CHECK CONNECTION | message already up to date | user=%s",
                    callback.from_user.id,
                )
            else:
                logger.exception(
                    "CHECK CONNECTION MESSAGE ERROR | user=%s | error=%s",
                    callback.from_user.id,
                    e,
                )


        # ================== ADMIN START ==================

    elif callback.data == "admin_start":

        await callback.message.edit_text(
            "👋 Добро пожаловать в Kusuo Saiki!\n\n"
            "Умный помощник для управления "
            "сообщениями вашего Telegram Business.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👑 АДМИН",
                            callback_data="admin_panel",
                        ),
                        InlineKeyboardButton(
                            text="👤 ПОЛЬЗОВАТЕЛЬ",
                            callback_data="user_mode",
                        ),
                    ]
                ]
            ),
        )

        return
        
        
        # ================== BACK TO START ==================

    elif callback.data == "back_start":

        if callback.from_user.id == OWNER_ID:

            await callback.message.edit_text(
                "👋 Добро пожаловать в Kusuo Saiki!\n\n"
                "Умный помощник для управления "
                "сообщениями вашего Telegram Business.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="📋 МЕНЮ",
                                callback_data="open_menu",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🛟 Поддержка",
                                callback_data="support",
                            ),
                            InlineKeyboardButton(
                                text="⚙️ Настройки",
                                callback_data="settings",
                            ),
                        ],
                        [
                            InlineKeyboardButton(
                                text="⬅️ НАЗАД",
                                callback_data="admin_start",
                            )
                        ],
                    ]
                ),
            )

        else:

            await show_start_screen()
            
            
# ================== SEARCH USERS FROM DATABASE ==================

async def get_all_business_users_for_search():

    if db_pool is None:
        logger.error("DATABASE POOL IS NOT INITIALIZED")
        return []

    async with db_pool.acquire() as conn:

        rows = await conn.fetch(
            """
            SELECT
                telegram_user_id,
                business_connection_id,
                first_name,
                last_name,
                username
            FROM business_accounts
            ORDER BY created_at ASC
            """
        )

    users = []

    for row in rows:

        name_parts = []

        if row["first_name"]:
            name_parts.append(row["first_name"])

        if row["last_name"]:
            name_parts.append(row["last_name"])

        name = " ".join(name_parts).strip()

        if not name:
            name = "Без имени"

        is_connected = False

        try:

            connection = await bot.get_business_connection(
                row["business_connection_id"]
            )

            is_connected = connection.is_enabled

        except Exception as e:

            logger.warning(
                "SEARCH USER CONNECTION CHECK ERROR | "
                "user=%s | connection=%s | error=%s",
                row["telegram_user_id"],
                row["business_connection_id"],
                e,
            )

        users.append(
            {
                "telegram_user_id": row["telegram_user_id"],
                "name": name,
                "username": row["username"] or "",
                "is_connected": is_connected,
            }
        )

    logger.info(
        "SEARCH USERS | total=%s",
        len(users),
    )

    return users
    
    
 # ================== USERS SEARCH HANDLER ==================

@dp.message(
    lambda message:
        message.from_user
        and message.from_user.id in users_search_waiting
)
async def handle_users_search(message):

    if message.from_user.id != OWNER_ID:
        users_search_waiting.discard(
            message.from_user.id
        )
        return

    search_text = (message.text or "").strip()

    logger.info(
        "USER SEARCH REQUEST | user=%s | text=%r",
        message.from_user.id,
        search_text,
    )

    if not search_text:

        await message.answer(
            "🔎 Введите имя, фамилию или username пользователя."
        )

        return

    # ================== NORMALIZE SEARCH ==================

    search_lower = search_text.lower().strip()

    # Убираем @ перед username
    search_username = search_lower.lstrip("@")

    users_search_waiting.discard(
        message.from_user.id
    )

    # ================== GET USERS ==================

    try:

        users = await get_all_business_users_for_search()

        logger.info(
            "USER SEARCH DATA | total=%s",
            len(users),
        )

    except Exception as e:

        logger.exception(
            "USER SEARCH DATABASE ERROR | error=%s",
            e,
        )

        await message.answer(
            "❌ Не удалось выполнить поиск.\n\n"
            "Попробуйте ещё раз."
        )

        return

    # ================== SEARCH ==================

    found_users = []

    for user in users:

        name = (user["name"] or "").strip()
        username = (user["username"] or "").strip()

        name_lower = name.lower()
        username_lower = username.lower().lstrip("@")

        logger.info(
            "USER SEARCH CHECK | name=%r | username=%r",
            name,
            username,
        )

        if (
            search_lower in name_lower
            or search_username in username_lower
        ):
            found_users.append(user)

    logger.info(
        "USER SEARCH RESULT | query=%r | found=%s",
        search_text,
        len(found_users),
    )

    # ================== KEYBOARD ==================

    keyboard = []

    for user in found_users:

        status = (
            "✅"
            if user["is_connected"]
            else "❌"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{status} {user['name']}",
                    callback_data=(
                        f"user_manage:{user['telegram_user_id']}"
                    ),
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔎 НОВЫЙ ПОИСК",
                callback_data="users_search",
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅️ К ПОЛЬЗОВАТЕЛЯМ",
                callback_data="admin_users",
            )
        ]
    )

    # ================== SHOW RESULT ==================

    if found_users:

        await message.answer(
            "🔎 РЕЗУЛЬТАТЫ ПОИСКА\n\n"
            f"Найдено пользователей: {len(found_users)}\n\n"
            "Выберите пользователя:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard
            ),
        )

    else:

        await message.answer(
            "🔎 РЕЗУЛЬТАТЫ ПОИСКА\n\n"
            f"По запросу «{search_text}» "
            "пользователи не найдены.\n\n"
            "Проверьте имя, фамилию или username.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard
            ),
        )


# ================== MESSAGE STORAGE ==================

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
        # ================== ACCESS CONTROL COLUMNS ==================

        await conn.execute("""
            ALTER TABLE business_accounts
            ADD COLUMN IF NOT EXISTS blocked BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS free_access BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS trial_until TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS subscription_until TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS trial_expired_notified BOOLEAN NOT NULL DEFAULT FALSE
        """)
        
    logger.info("DATABASE INITIALIZED")
    
    
# ================== ACCESS CONTROL ==================

async def get_user_access_status(user_id):

    if db_pool is None:

        logger.error(
            "ACCESS CHECK | DATABASE POOL IS NOT INITIALIZED"
        )

        return {
            "blocked": False,
            "free_access": False,
            "trial_active": False,
            "trial_expired": False,
            "subscription_active": False,
            "has_access": False,
        }

    if user_id == OWNER_ID:

        return {
            "blocked": False,
            "free_access": True,
            "trial_active": False,
            "trial_expired": False,
            "subscription_active": False,
            "has_access": True,
        }

    async with db_pool.acquire() as conn:

        user = await conn.fetchrow(
            """
            SELECT
                blocked,
                free_access,
                trial_until,
                subscription_until
            FROM business_accounts
            WHERE telegram_user_id = $1
            """,
            user_id,
        )

    # ================== USER NOT FOUND ==================

    if not user:

        return {
            "blocked": False,
            "free_access": False,
            "trial_active": False,
            "trial_expired": False,
            "subscription_active": False,
            "has_access": False,
        }

    now = datetime.now(timezone.utc)

    # ================== USER STATUS ==================

    blocked = bool(
        user["blocked"]
    )

    free_access = bool(
        user["free_access"]
    )

    trial_active = (
        user["trial_until"] is not None
        and user["trial_until"] > now
    )

    trial_expired = (
        user["trial_until"] is not None
        and user["trial_until"] <= now
    )

    subscription_active = (
        user["subscription_until"] is not None
        and user["subscription_until"] > now
    )

    has_access = (
        not blocked
        and (
            free_access
            or subscription_active
            or trial_active
        )
    )

    return {
        "blocked": blocked,
        "free_access": free_access,
        "trial_active": trial_active,
        "trial_expired": trial_expired,
        "subscription_active": subscription_active,
        "has_access": has_access,
    }
    

# ================== TRIAL EXPIRATION CHECKER ==================

async def check_expired_trials():

    if db_pool is None:
        logger.error(
            "TRIAL EXPIRATION CHECK | DATABASE POOL IS NOT INITIALIZED"
        )
        return

    async with db_pool.acquire() as conn:

        users = await conn.fetch(
            """
            SELECT
                telegram_user_id,
                first_name,
                last_name
            FROM business_accounts
            WHERE
                trial_until IS NOT NULL
                AND trial_until <= NOW()
                AND trial_expired_notified = FALSE
            """
        )

    for user in users:

        user_id = user["telegram_user_id"]

        try:

            await bot.send_message(
                user_id,
                (
                    "🥺 Твой пробный период подошёл к концу.\n\n"
                    "Очень жаль… Но ты можешь продлить мою жизнь — "
                    "и я продолжу помогать тебе дальше. ❤️\n\n"
                    "Если хочешь продолжить пользоваться ботом, "
                    "ты можешь приобрести подписку."
                )
            )

            async with db_pool.acquire() as conn:

                await conn.execute(
                    """
                    UPDATE business_accounts
                    SET
                        trial_expired_notified = TRUE,
                        updated_at = NOW()
                    WHERE telegram_user_id = $1
                    """,
                    user_id,
                )

            logger.info(
                "TRIAL EXPIRED NOTIFICATION SENT | user=%s",
                user_id,
            )

        except Exception as e:

            logger.exception(
                "TRIAL EXPIRED NOTIFICATION ERROR | user=%s | error=%s",
                user_id,
                e,
            )
            
            
# ================== CLOUDFLARE D1 ==================

import httpx

# ================== D1 STORAGE CHECK ==================

D1_MAX_STORAGE_BYTES = 500 * 1024 * 1024

# ================== D1 DAILY WRITE LIMIT ==================

D1_DAILY_WRITE_LIMIT = 100000

CLOUDFLARE_GRAPHQL_URL = (
    "https://api.cloudflare.com/client/v4/graphql"
)


async def get_d1_account_rows_written(
    account_id: str,
    token_env: str
):

    api_token = os.getenv(
        token_env
    )

    if not api_token:

        raise RuntimeError(
            f"{token_env} is not configured"
        )

    # Cloudflare D1 daily limits reset at 00:00 UTC.
    # GraphQL Date filters use UTC dates.

    from datetime import datetime, timezone

    today_utc = datetime.now(
        timezone.utc
    ).date().isoformat()

    query = """
    query D1DailyRowsWritten(
        $accountTag: string!
        $start: Date
        $end: Date
    ) {
        viewer {
            accounts(
                filter: {
                    accountTag: $accountTag
                }
            ) {
                d1AnalyticsAdaptiveGroups(
                    limit: 10000
                    filter: {
                        date_geq: $start
                        date_leq: $end
                    }
                ) {
                    sum {
                        rowsWritten
                    }
                }
            }
        }
    }
    """

    variables = {
        "accountTag": account_id,
        "start": today_utc,
        "end": today_utc,
    }

    headers = {
        "Authorization": (
            f"Bearer {api_token}"
        ),
        "Content-Type": "application/json",
    }

    payload = {
        "query": query,
        "variables": variables,
    }

    async with httpx.AsyncClient() as client:

        response = await client.post(
            CLOUDFLARE_GRAPHQL_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )

    if response.status_code != 200:

        raise RuntimeError(
            f"CLOUDFLARE GRAPHQL HTTP ERROR "
            f"{response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    if data.get("errors"):

        raise RuntimeError(
            f"CLOUDFLARE GRAPHQL ERROR: "
            f"{data['errors']}"
        )

    accounts = (
        data
        .get("data", {})
        .get("viewer", {})
        .get("accounts", [])
    )

    if not accounts:

        return 0

    analytics = (
        accounts[0]
        .get(
            "d1AnalyticsAdaptiveGroups",
            []
        )
    )

    total_rows_written = 0

    for group in analytics:

        rows_written = (
            group
            .get("sum", {})
            .get("rowsWritten")
        )

        if rows_written is not None:

            total_rows_written += int(
                rows_written
            )

    return total_rows_written
    
    # ================== D1 DAILY WRITE TEST ==================

async def test_d1_daily_write_usage():

    accounts = [
        (
            "D1.1",
            "a5cbd8bb1cd52eea0b38b21c40106d53",
            "CLOUDFLARE_API_TOKEN_1",
        ),
        (
            "D1.2",
            "b7bd135a9fb318c159851e18b38610ce",
            "CLOUDFLARE_API_TOKEN_2",
        ),
        (
            "D1.3",
            "f2bf38f76018c112bffc762e4b67bfff",
            "CLOUDFLARE_API_TOKEN_3",
        ),
    ]

    for group_name, account_id, token_env in accounts:

        try:

            rows_written = (
                await get_d1_account_rows_written(
                    account_id,
                    token_env,
                )
            )

            remaining = max(
                0,
                D1_DAILY_WRITE_LIMIT
                - rows_written,
            )

            logger.info(
                "D1 DAILY WRITE USAGE | "
                "group=%s | "
                "rows_written=%s | "
                "remaining=%s",
                group_name,
                rows_written,
                remaining,
            )

        except Exception as e:

            logger.exception(
                "D1 DAILY WRITE TEST ERROR | "
                "group=%s | error=%s",
                group_name,
                e,
            )
            
# ================== D1 DAILY WRITE ROUTER ==================

D1_GROUPS = {
    "D1.1": [
        "D1.1.1",
        "D1.1.2",
        "D1.1.3",
        "D1.1.4",
        "D1.1.5",
        "D1.1.6",
        "D1.1.7",
        "D1.1.8",
        "D1.1.9",
        "D1.1.10",
    ],
    "D1.2": [
        "D1.2.1",
        "D1.2.2",
        "D1.2.3",
        "D1.2.4",
        "D1.2.5",
        "D1.2.6",
        "D1.2.7",
        "D1.2.8",
        "D1.2.9",
        "D1.2.10",
    ],
    "D1.3": [
        "D1.3.1",
        "D1.3.2",
        "D1.3.3",
        "D1.3.4",
        "D1.3.5",
        "D1.3.6",
        "D1.3.7",
        "D1.3.8",
        "D1.3.9",
        "D1.3.10",
    ],
}


D1_GROUP_ACCOUNTS = {
    "D1.1": (
        "a5cbd8bb1cd52eea0b38b21c40106d53",
        "CLOUDFLARE_API_TOKEN_1",
    ),
    "D1.2": (
        "b7bd135a9fb318c159851e18b38610ce",
        "CLOUDFLARE_API_TOKEN_2",
    ),
    "D1.3": (
        "f2bf38f76018c112bffc762e4b67bfff",
        "CLOUDFLARE_API_TOKEN_3",
    ),
}


async def get_available_d1_group():

    for group_name in (
        "D1.1",
        "D1.2",
        "D1.3",
    ):

        account_id, token_env = (
            D1_GROUP_ACCOUNTS[group_name]
        )

        try:

            rows_written = (
                await get_d1_account_rows_written(
                    account_id,
                    token_env,
                )
            )

            if rows_written < D1_DAILY_WRITE_LIMIT:

                remaining = (
                    D1_DAILY_WRITE_LIMIT
                    - rows_written
                )

                logger.info(
                    "D1 ROUTER GROUP AVAILABLE | "
                    "group=%s | "
                    "rows_written=%s | "
                    "remaining=%s",
                    group_name,
                    rows_written,
                    remaining,
                )

                return group_name

            logger.info(
                "D1 ROUTER GROUP DAILY LIMIT | "
                "group=%s | "
                "rows_written=%s",
                group_name,
                rows_written,
            )

        except Exception as e:

            logger.exception(
                "D1 ROUTER GROUP CHECK ERROR | "
                "group=%s | error=%s",
                group_name,
                e,
            )

            continue

    raise RuntimeError(
        "D1 ROUTER: "
        "NO DATABASE GROUP WITH AVAILABLE DAILY WRITE LIMIT"
    )
    
    # ================== D1 COMBINED ROUTER ==================

async def get_available_d1_from_router():

    selected_group = await get_available_d1_group()

    group_databases = D1_GROUPS.get(
        selected_group
    )

    if not group_databases:

        raise RuntimeError(
            f"D1 ROUTER: "
            f"DATABASE GROUP NOT FOUND: {selected_group}"
        )

    for d1_name in group_databases:

        try:

            size_bytes = await get_d1_storage_size(
                d1_name
            )

            if size_bytes < D1_MAX_STORAGE_BYTES:

                available_bytes = (
                    D1_MAX_STORAGE_BYTES
                    - size_bytes
                )

                available_mb = (
                    available_bytes
                    / 1024
                    / 1024
                )

                logger.info(
                    "D1 COMBINED ROUTER AVAILABLE | "
                    "group=%s | "
                    "d1=%s | "
                    "size_bytes=%s | "
                    "available_mb=%.2f",
                    selected_group,
                    d1_name,
                    size_bytes,
                    available_mb,
                )

                return d1_name

            logger.info(
                "D1 COMBINED ROUTER STORAGE FULL | "
                "group=%s | "
                "d1=%s | "
                "size_bytes=%s",
                selected_group,
                d1_name,
                size_bytes,
            )

        except Exception as e:

            logger.exception(
                "D1 COMBINED ROUTER STORAGE CHECK ERROR | "
                "group=%s | "
                "d1=%s | error=%s",
                selected_group,
                d1_name,
                e,
            )

            continue

    raise RuntimeError(
        f"D1 ROUTER: "
        f"NO DATABASE WITH AVAILABLE STORAGE "
        f"IN GROUP {selected_group}"
    )
    
    # ================== D1 COMBINED ROUTER TEST ==================

async def test_d1_combined_router():

    try:

        selected_d1 = (
            await get_available_d1_from_router()
        )

        logger.info(
            "D1 COMBINED ROUTER TEST SUCCESS | "
            "selected_d1=%s",
            selected_d1,
        )

    except Exception as e:

        logger.exception(
            "D1 COMBINED ROUTER TEST ERROR | %s",
            e,
        )

async def get_d1_storage_size(
    d1_name: str
):

    d1_config = D1_DATABASES.get(
        d1_name
    )

    if not d1_config:

        raise RuntimeError(
            f"D1 STORAGE CHECK: "
            f"database config not found: {d1_name}"
        )

    account_id = d1_config.get(
        "account_id"
    )

    database_id = d1_config.get(
        "database_id"
    )

    token_env = d1_config.get(
        "token_env"
    )

    if not account_id:

        raise RuntimeError(
            f"D1 STORAGE CHECK: "
            f"account id not configured: {d1_name}"
        )

    if not database_id:

        raise RuntimeError(
            f"D1 STORAGE CHECK: "
            f"database id not configured: {d1_name}"
        )

    if not token_env:

        raise RuntimeError(
            f"D1 STORAGE CHECK: "
            f"token env not configured: {d1_name}"
        )

    api_token = os.getenv(
        token_env
    )

    if not api_token:

        raise RuntimeError(
            f"D1 STORAGE CHECK: "
            f"{token_env} is not configured"
        )

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/d1/database/"
        f"{database_id}/query"
    )

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "sql": "SELECT 1 AS storage_check",
        "params": [],
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
            f"D1 STORAGE CHECK HTTP ERROR "
            f"{d1_name}: "
            f"{response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    if not data.get("success"):

        raise RuntimeError(
            f"D1 STORAGE CHECK QUERY ERROR "
            f"{d1_name}: "
            f"{data}"
        )

    result_data = data.get(
        "result",
        []
    )

    if not result_data:

        raise RuntimeError(
            f"D1 STORAGE CHECK EMPTY RESULT: "
            f"{d1_name}"
        )

    meta = result_data[0].get(
        "meta",
        {}
    )

    size_after = meta.get(
        "size_after"
    )

    if size_after is None:

        raise RuntimeError(
            f"D1 STORAGE SIZE NOT RETURNED: "
            f"{d1_name}"
        )

    size_after = int(
        size_after
    )

    return size_after
    
# ================== D1 AVAILABLE DATABASE ==================

async def get_available_d1():

    for d1_name in D1_ORDER:

        try:

            size_bytes = await get_d1_storage_size(
                d1_name
            )

            if size_bytes < D1_MAX_STORAGE_BYTES:

                available_bytes = (
                    D1_MAX_STORAGE_BYTES
                    - size_bytes
                )

                available_mb = (
                    available_bytes
                    / 1024
                    / 1024
                )

                logger.info(
                    "D1 ROUTER STORAGE AVAILABLE | "
                    "d1=%s | "
                    "size_bytes=%s | "
                    "available_mb=%.2f",
                    d1_name,
                    size_bytes,
                    available_mb,
                )

                return d1_name

            logger.info(
                "D1 ROUTER STORAGE FULL | "
                "d1=%s | "
                "size_bytes=%s",
                d1_name,
                size_bytes,
            )

        except Exception as e:

            logger.exception(
                "D1 ROUTER STORAGE CHECK ERROR | "
                "d1=%s | error=%s",
                d1_name,
                e,
            )

            continue

    raise RuntimeError(
        "D1 ROUTER: "
        "NO DATABASE WITH AVAILABLE STORAGE"
    )

# ================== D1 ROUTER STORAGE TEST ==================

async def test_d1_router_storage():

    try:

        selected_d1 = await get_available_d1()

        logger.info(
            "D1 ROUTER STORAGE TEST SUCCESS | "
            "selected=%s",
            selected_d1,
        )

    except Exception as e:

        logger.exception(
            "D1 ROUTER STORAGE TEST ERROR | %s",
            e,
        )


# ================== TEST D1.1.2 ==================

async def test_d1_1_2():

    d1_name = "D1.1.2"

    d1_config = D1_DATABASES.get(
        d1_name
    )

    if not d1_config:

        logger.error(
            "D1.1.2 TEST ERROR | database config not found"
        )

        return

    account_id = d1_config.get(
        "account_id"
    )

    database_id = d1_config.get(
        "database_id"
    )

    token_env = d1_config.get(
        "token_env"
    )

    if not token_env:

        logger.error(
            "D1.1.2 TEST ERROR | token env not configured"
        )

        return

    api_token = os.getenv(
        token_env
    )

    if not api_token:

        logger.error(
            "D1.1.2 TEST ERROR | %s is not configured",
            token_env,
        )

        return

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/d1/database/"
        f"{database_id}/query"
    )

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "sql": "SELECT 1 AS test",
        "params": [],
    }

    try:

        async with httpx.AsyncClient() as client:

            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=30,
            )

        if response.status_code != 200:

            raise RuntimeError(
                f"HTTP {response.status_code}: "
                f"{response.text}"
            )

        data = response.json()

        if not data.get("success"):

            raise RuntimeError(
                f"D1.1.2 QUERY ERROR: {data}"
            )

        logger.info(
            "D1.1.2 CONNECTION SUCCESS | "
            "account=%s | database=%s | token=%s | result=%s",
            account_id,
            database_id,
            token_env,
            data,
        )

    except Exception as e:

        logger.exception(
            "D1.1.2 CONNECTION ERROR | %s",
            e,
        )
        
# ================== D1 STORAGE TEST ==================

async def test_d1_storage():

    test_databases = [
        "D1.1.1",
        "D1.1.2",
        "D1.2.1",
        "D1.3.1",
    ]

    for d1_name in test_databases:

        try:

            size_bytes = await get_d1_storage_size(
                d1_name
            )

            size_mb = (
                size_bytes
                / 1024
                / 1024
            )

            available_bytes = (
                D1_MAX_STORAGE_BYTES
                - size_bytes
            )

            available_mb = (
                available_bytes
                / 1024
                / 1024
            )

            logger.info(
                "D1 STORAGE TEST | "
                "d1=%s | "
                "size_bytes=%s | "
                "size_mb=%.2f | "
                "available_mb=%.2f",
                d1_name,
                size_bytes,
                size_mb,
                available_mb,
            )

        except Exception as e:

            logger.exception(
                "D1 STORAGE TEST ERROR | "
                "d1=%s | error=%s",
                d1_name,
                e,
            )
            
# ================== D1 DAILY WRITE ROUTER TEST ==================

async def test_d1_daily_write_router():

    try:

        selected_group = (
            await get_available_d1_group()
        )

        logger.info(
            "D1 DAILY WRITE ROUTER TEST SUCCESS | "
            "selected_group=%s",
            selected_group,
        )

    except Exception as e:

        logger.exception(
            "D1 DAILY WRITE ROUTER TEST ERROR | %s",
            e,
        )


# ================== D1 MESSAGE BUFFER ==================

import asyncio
import json
import time


MESSAGE_BATCH_SIZE = 100
MESSAGE_BATCH_TIMEOUT = 90

D1_RETRY_DELAY = 15

d1_message_batches = {}
d1_batch_tasks = {}
d1_retry_tasks = {}


# ================== FLUSH D1 BATCH ==================

async def flush_d1_batch(batch_key):

    batch = d1_message_batches.get(batch_key)

    if not batch:
        return

    messages = batch["messages"]

    if not messages:
        d1_message_batches.pop(
            batch_key,
            None,
        )
        return

    business_connection_id = batch_key[0]
    chat_id = batch_key[1]

    batch_id = (
        f"{business_connection_id}:"
        f"{chat_id}:"
        f"{int(time.time() * 1000)}"
    )

    logger.info(
        "D1 BATCH WRITE START | "
        "connection=%s | chat=%s | messages=%s",
        business_connection_id,
        chat_id,
        len(messages),
    )

    try:

        # ================== SELECT D1 ==================

        selected_d1 = (
            await get_available_d1_from_router()
        )

        logger.info(
            "D1 BATCH ROUTER SELECTED | "
            "connection=%s | chat=%s | d1=%s",
            business_connection_id,
            chat_id,
            selected_d1,
        )

        # ================== GET D1 CONFIG ==================

        d1_config = D1_DATABASES.get(
            selected_d1
        )

        if not d1_config:

            raise RuntimeError(
                f"D1 CONFIG NOT FOUND: "
                f"{selected_d1}"
            )

        account_id = d1_config.get(
            "account_id"
        )

        database_id = d1_config.get(
            "database_id"
        )

        token_env = d1_config.get(
            "token_env"
        )

        if not account_id:

            raise RuntimeError(
                f"D1 ACCOUNT ID NOT CONFIGURED: "
                f"{selected_d1}"
            )

        if not database_id:

            raise RuntimeError(
                f"D1 DATABASE ID NOT CONFIGURED: "
                f"{selected_d1}"
            )

        if not token_env:

            raise RuntimeError(
                f"D1 TOKEN ENV NOT CONFIGURED: "
                f"{selected_d1}"
            )

        api_token = os.getenv(
            token_env
        )

        if not api_token:

            raise RuntimeError(
                f"{token_env} is not configured"
            )

        # ================== D1 API ==================

        url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{account_id}/d1/database/"
            f"{database_id}/query"
        )

        headers = {
            "Authorization": (
                f"Bearer {api_token}"
            ),
            "Content-Type": "application/json",
        }

        payload = {
            "sql": """
                INSERT INTO message_batches (
                    business_connection_id,
                    chat_id,
                    batch_id,
                    messages_json
                )
                VALUES (?, ?, ?, ?)
            """,
            "params": [
                business_connection_id,
                chat_id,
                batch_id,
                json.dumps(
                    messages,
                    ensure_ascii=False,
                ),
            ],
        }

        logger.info(
            "D1 BATCH WRITE REQUEST | "
            "d1=%s | account=%s | database=%s | token=%s",
            selected_d1,
            account_id,
            database_id,
            token_env,
        )

        async with httpx.AsyncClient() as client:

            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=30,
            )

        if response.status_code != 200:

            raise RuntimeError(
                f"D1 API ERROR "
                f"{response.status_code}: "
                f"{response.text}"
            )

        data = response.json()

        if not data.get("success"):

            raise RuntimeError(
                f"D1 QUERY ERROR: "
                f"{data}"
            )

        # ================== D1 WRITE SUCCESS ==================

        logger.info(
            "D1 BATCH WRITE SUCCESS | "
            "connection=%s | chat=%s | "
            "messages=%s | batch_id=%s | d1=%s",
            business_connection_id,
            chat_id,
            len(messages),
            batch_id,
            selected_d1,
        )

        # После успешной записи D1
        # удаляем сообщения из RAM.

        d1_message_batches.pop(
            batch_key,
            None,
        )

        # Если существовала задача повторной попытки —
        # она больше не нужна.

        retry_task = d1_retry_tasks.pop(
            batch_key,
            None,
        )

        if (
            retry_task is not None
            and retry_task is not asyncio.current_task()
        ):
            retry_task.cancel()

    except Exception as e:

        logger.exception(
            "D1 BATCH WRITE ERROR | "
            "connection=%s | chat=%s | "
            "messages=%s | error=%s",
            business_connection_id,
            chat_id,
            len(messages),
            e,
        )

        # ВАЖНО:
        # сообщения НЕ удаляем из RAM.
        # Они останутся в d1_message_batches
        # до успешной записи.

        if batch_key not in d1_retry_tasks:

            d1_retry_tasks[batch_key] = asyncio.create_task(
                retry_d1_batch(batch_key)
            )
            
# ================== D1 RETRY ==================

async def retry_d1_batch(batch_key):

    current_task = asyncio.current_task()

    try:

        while True:

            await asyncio.sleep(
                D1_RETRY_DELAY
            )

            if batch_key not in d1_message_batches:
                return

            logger.info(
                "D1 RETRY | connection=%s | chat=%s",
                batch_key[0],
                batch_key[1],
            )

            await flush_d1_batch(
                batch_key
            )

            # Если запись прошла успешно,
            # flush_d1_batch удалит batch из RAM.

            if batch_key not in d1_message_batches:
                return

    except asyncio.CancelledError:

        logger.info(
            "D1 RETRY TASK CANCELLED | "
            "connection=%s | chat=%s",
            batch_key[0],
            batch_key[1],
        )

        raise

    except Exception as e:

        logger.exception(
            "D1 RETRY LOOP ERROR | "
            "connection=%s | chat=%s | error=%s",
            batch_key[0],
            batch_key[1],
            e,
        )

    finally:

        existing_task = d1_retry_tasks.get(
            batch_key
        )

        if existing_task is current_task:

            d1_retry_tasks.pop(
                batch_key,
                None,
            )


# ================== ADD MESSAGE TO D1 BUFFER ==================

async def add_message_to_d1_batch(
    business_connection_id,
    chat_id,
    message_data,
):

    batch_key = (
        business_connection_id,
        chat_id,
    )

    # ================== CREATE BATCH ==================

    if batch_key not in d1_message_batches:

        d1_message_batches[
            batch_key
        ] = {
            "messages": [],
            "created_at": time.time(),
        }

    # ================== ADD MESSAGE ==================

    d1_message_batches[
        batch_key
    ]["messages"].append(
        message_data
    )

    current_size = len(
        d1_message_batches[
            batch_key
        ]["messages"]
    )

    logger.info(
        "D1 MESSAGE BUFFERED | "
        "connection=%s | chat=%s | messages_in_buffer=%s",
        business_connection_id,
        chat_id,
        current_size,
    )

    # ================== BATCH SIZE ==================

    if current_size >= MESSAGE_BATCH_SIZE:

        existing_task = d1_batch_tasks.pop(
            batch_key,
            None,
        )

        if existing_task is not None:

            existing_task.cancel()

        await flush_d1_batch(
            batch_key
        )

        return

    # ================== BATCH TIMEOUT ==================

    if batch_key not in d1_batch_tasks:

        async def delayed_flush():

            try:

                await asyncio.sleep(
                    MESSAGE_BATCH_TIMEOUT
                )

                if batch_key in d1_message_batches:

                    await flush_d1_batch(
                        batch_key
                    )

            except asyncio.CancelledError:

                pass

            except Exception as e:

                logger.exception(
                    "D1 DELAYED FLUSH ERROR | "
                    "connection=%s | chat=%s | error=%s",
                    business_connection_id,
                    chat_id,
                    e,
                )

            finally:

                current_task = asyncio.current_task()

                if d1_batch_tasks.get(
                    batch_key
                ) is current_task:

                    d1_batch_tasks.pop(
                        batch_key,
                        None,
                    )

        d1_batch_tasks[
            batch_key
        ] = asyncio.create_task(
            delayed_flush()
        )


# ================== SAVE MESSAGE TO D1 ==================

async def save_message_to_d1(
    business_connection_id,
    chat_id,
    message_data,
):

    try:

        await add_message_to_d1_batch(
            business_connection_id=business_connection_id,
            chat_id=chat_id,
            message_data=message_data,
        )

    except Exception as e:

        logger.exception(
            "SAVE MESSAGE TO D1 ERROR | "
            "connection=%s | chat=%s | error=%s",
            business_connection_id,
            chat_id,
            e,
        )
        
 
# ================== ADMIN SUBSCRIPTION STATE ==================

subscription_add_waiting = set()


@dp.message()
async def handle_subscription_add(message):

    if message.from_user.id != OWNER_ID:
        return

    # ================== GIVE TRIAL ==================

    if message.from_user.id in trial_days_waiting:

        if not message.text:
            await message.answer(
                "❌ Введите количество дней числом.\n\n"
                "Например: 1, 7, 30 или 100."
            )
            return

        try:
            days = int(
                message.text.strip()
            )

        except ValueError:

            await message.answer(
                "❌ Количество дней должно быть числом.\n\n"
                "Например: 1, 7, 30 или 100."
            )
            return

        if days <= 0:

            await message.answer(
                "❌ Количество дней должно быть больше нуля."
            )
            return

        target_user_id = trial_days_waiting.get(
            message.from_user.id
        )

        if target_user_id is None:

            await message.answer(
                "❌ Пользователь для выдачи "
                "пробного периода не найден."
            )
            return

        if db_pool is None:

            await message.answer(
                "❌ Ошибка подключения к базе данных."
            )

            logger.error(
                "GIVE TRIAL ERROR | DATABASE POOL IS NONE"
            )

            return

        try:

            async with db_pool.acquire() as conn:

                updated_user = await conn.fetchval(
                    """
                    UPDATE business_accounts
                    SET
                        trial_until = NOW() + ($1::INTEGER * INTERVAL '1 day'),
                        trial_expired_notified = FALSE,
                        updated_at = NOW()
                    WHERE telegram_user_id = $2
                    RETURNING telegram_user_id
                    """,
                    days,
                    target_user_id,
                )

            if updated_user is None:

                await message.answer(
                    "❌ Пользователь не найден в базе данных."
                )
                return

        except Exception as e:

            logger.exception(
                "GIVE TRIAL ERROR | "
                "user=%s | days=%s | error=%s",
                target_user_id,
                days,
                e,
            )

            await message.answer(
                "❌ Не удалось выдать пробный период."
            )

            return

        trial_days_waiting.pop(
            message.from_user.id,
            None,
        )
        
                # ================== NOTIFY USER ==================

        try:

            await bot.send_message(
                target_user_id,
                "🎁 ТЕБЕ ВЫДАН ПРОБНЫЙ ПЕРИОД!\n\n"
                f"Администратор предоставил тебе доступ "
                f"на {days} дн.\n\n"
                "Теперь ты снова можешь пользоваться "
                "Kusuo Saiki. ❤️",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="✅ ОК",
                                callback_data="trial_ok",
                            )
                        ]
                    ]
                ),
            )

        except Exception as e:

            logger.warning(
                "TRIAL USER NOTIFICATION ERROR | "
                "user=%s | error=%s",
                target_user_id,
                e,
            )
            
        sent_message = await message.answer(
            "🎁 ПРОБНЫЙ ПЕРИОД ВЫДАН\n\n"
            f"Пользователь: {target_user_id}\n"
            f"Срок: {days} дн.\n\n"
            "Доступ пользователя обновлён."
        )

        async def delete_trial_message():

            await asyncio.sleep(10)

            try:

                await sent_message.delete()

            except Exception as e:

                logger.warning(
                    "GIVE TRIAL MESSAGE DELETE ERROR | error=%s",
                    e,
                )

        asyncio.create_task(
            delete_trial_message()
        )

        logger.info(
            "TRIAL GIVEN | user=%s | days=%s | admin=%s",
            target_user_id,
            days,
            message.from_user.id,
        )

        return

    # ================== SUBSCRIPTION ADD ==================

    if message.from_user.id not in subscription_add_waiting:
        return

    if not message.text:
        await message.answer(
            "❌ Пришлите ссылку на группу или канал текстом."
        )
        return

    link = message.text.strip()

    await message.answer(
        "🔄 Получил ссылку.\n\n"
        "Проверяю группу или канал..."
    )

    # ================== PARSE TELEGRAM LINK ==================

    chat_identifier = link

    if link.startswith("https://t.me/"):
        chat_identifier = link.replace(
            "https://t.me/",
            "",
            1,
        )

    elif link.startswith("http://t.me/"):
        chat_identifier = link.replace(
            "http://t.me/",
            "",
            1,
        )

    elif link.startswith("t.me/"):
        chat_identifier = link.replace(
            "t.me/",
            "",
            1,
        )

    # Убираем возможные параметры ссылки
    chat_identifier = chat_identifier.split("?")[0]
    chat_identifier = chat_identifier.split("/")[0]

    # Публичный username Telegram должен начинаться с @
    if not chat_identifier.startswith("@"):
        chat_identifier = f"@{chat_identifier}"

    # ================== CHECK CHAT ==================

    try:
        chat = await bot.get_chat(
            chat_identifier
        )

    except Exception as e:

        logger.exception(
            "SUBSCRIPTION CHAT CHECK ERROR | "
            "link=%s | error=%s",
            link,
            e,
        )

        await message.answer(
            "❌ Не удалось найти эту группу или канал.\n\n"
            "Проверьте ссылку и убедитесь, "
            "что бот уже добавлен туда."
        )

        return

    # ================== CHECK BOT RIGHTS ==================

    try:
        me = await bot.get_me()

        member = await bot.get_chat_member(
            chat_id=chat.id,
            user_id=me.id,
        )

    except Exception as e:

        logger.exception(
            "SUBSCRIPTION BOT RIGHTS ERROR | "
            "chat_id=%s | error=%s",
            chat.id,
            e,
        )

        await message.answer(
            "❌ Не удалось проверить права бота.\n\n"
            "Убедитесь, что бот добавлен в эту группу "
            "или канал."
        )

        return

    # ================== REQUIRE ADMIN ==================

    if member.status not in (
        "administrator",
        "creator",
    ):

        await message.answer(
            "❌ Бот добавлен, но он не является "
            "администратором.\n\n"
            "Сделайте бота администратором "
            "и попробуйте ещё раз."
        )

        return

    # ================== SAVE TO NEON ==================

    if db_pool is None:

        await message.answer(
            "❌ Ошибка подключения к базе данных."
        )

        logger.error(
            "SUBSCRIPTION SAVE ERROR | DATABASE POOL IS NONE"
        )

        return

    try:

        username = getattr(
            chat,
            "username",
            None,
        )

        await db_pool.execute(
            """
            INSERT INTO required_subscriptions (
                chat_id,
                title,
                username,
                invite_link,
                is_active,
                updated_at
            )
            VALUES (
                $1,
                $2,
                $3,
                $4,
                TRUE,
                NOW()
            )
            ON CONFLICT (chat_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                username = EXCLUDED.username,
                invite_link = EXCLUDED.invite_link,
                is_active = TRUE,
                updated_at = NOW()
            """,
            chat.id,
            chat.title or "Без названия",
            username,
            link,
        )

    except Exception as e:

        logger.exception(
            "SUBSCRIPTION NEON SAVE ERROR | "
            "chat_id=%s | error=%s",
            chat.id,
            e,
        )

        await message.answer(
            "❌ Не удалось сохранить подписку в базе данных."
        )

        return

    # ================== CLEAR WAITING STATE ==================

    subscription_add_waiting.discard(
        message.from_user.id
    )

    # ================== SUCCESS ==================

    logger.info(
        "SUBSCRIPTION ADDED | "
        "chat_id=%s | title=%s | username=%s | link=%s",
        chat.id,
        chat.title,
        getattr(chat, "username", None),
        link,
    )

    await message.answer(
        "✅ ПОДПИСКА ДОБАВЛЕНА!\n\n"
        f"📢 {chat.title}\n"
        f"🆔 ID: {chat.id}\n\n"
        "Бот является администратором.\n"
        "Группа/канал сохранён в Neon."
    )
    
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
        "BUSINESS CONNECTION | id=%s | user_id=%s | name=%s %s | enabled=%s",
        business_connection_id,
        user.id,
        user.first_name,
        user.last_name or "",
        connection.is_enabled,
    )

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

            await conn.execute(
                """
                UPDATE business_accounts
                SET
                    business_connection_id = $1,
                    first_name = $2,
                    last_name = $3,
                    username = $4,
                    updated_at = NOW()
                WHERE telegram_user_id = $5
                """,
                business_connection_id,
                user.first_name,
                user.last_name,
                user.username,
                user.id,
            )

            business_topics[business_connection_id] = topic_id

            logger.info(
                "BUSINESS CONNECTION UPDATED | "
                "user=%s | connection=%s | topic_id=%s | enabled=%s",
                user.id,
                business_connection_id,
                topic_id,
                connection.is_enabled,
            )

        else:

            logger.info(
                "BUSINESS CONNECTION NOT IN DATABASE | "
                "user=%s | connection=%s",
                user.id,
                business_connection_id,
            )

    # ================== CONNECTION MESSAGE ==================

    try:

        if connection.is_enabled:

            await bot.send_message(
                chat_id=user.id,
                text=(
                    "🎉 УРА! У ВАС ВСЁ ПОЛУЧИЛОСЬ!\n\n"
                    "Kusuo Saiki успешно подключён "
                    "к вашему Telegram Business.\n\n"
                    "Теперь вы можете пользоваться "
                    "всеми возможностями бота."
                ),
            )

            logger.info(
                "CONNECTION SUCCESS MESSAGE SENT | user=%s",
                user.id,
            )

        else:

            await bot.send_message(
                chat_id=user.id,
                text=(
                    "😢 КАК ЖАЛЬ, ЧТО ВЫ УШЛИ...\n\n"
                    "Kusuo Saiki больше не подключён "
                    "к вашему Telegram Business.\n\n"
                    "Если захотите вернуться — мы будем ждать вас ❤️"
                ),
            )

            logger.info(
                "DISCONNECTION MESSAGE SENT | user=%s",
                user.id,
            )

    except Exception as e:

        logger.exception(
            "CONNECTION MESSAGE ERROR | user=%s | error=%s",
            user.id,
            e,
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
        
        
# ================== LOG CHAT HEADER ==================
import html
async def ensure_log_chat_header(
    business_connection_id,
    topic_id,
    chat_id,
    business_user,
):
    """
    Формирует визуальный заголовок чата
    для добавления перед каждым архивным сообщением.
    """
    try:
        # ================== GET CHAT USER ==================
        chat = await bot.get_chat(
            chat_id=chat_id
        )
        peer_name = (
            chat.full_name
            if getattr(chat, "full_name", None)
            else getattr(chat, "first_name", None)
            or getattr(chat, "title", None)
            or "Неизвестный пользователь"
        )
        peer_name = html.escape(
            peer_name
        )
        # ================== BUSINESS USER NAME ==================
        business_name = (
            business_user.first_name
            or "Пользователь"
        )
        if business_user.last_name:
            business_name += (
                f" {business_user.last_name}"
            )
        business_name = html.escape(
            business_name
        )
        # ================== HEADER ==================
        header_text = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 {business_name}\n"
            f"💬 {peer_name}\n"
            f"🆔 Chat ID: <code>{chat_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
        )
        logger.info(
            "LOG CHAT HEADER CREATED | "
            "connection=%s | topic=%s | chat=%s | peer=%s",
            business_connection_id,
            topic_id,
            chat_id,
            peer_name,
        )
        return header_text
    except Exception as e:
        logger.exception(
            "LOG CHAT HEADER ERROR | "
            "connection=%s | topic=%s | chat=%s | error=%s",
            business_connection_id,
            topic_id,
            chat_id,
            e,
        )
        return ""
        
# ================== LOG PROFILE KEYBOARD ==================

def create_profile_keyboard(
    sender_id,
    recipient_id,
):
    return InlineKeyboardMarkup(
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
    
# ================== LOG MESSAGE PROFILE KEYBOARD ==================

def create_message_profile_keyboard(
    message,
    business_user,
):
    sender_id = message.from_user.id

    if sender_id == business_user.id:
        recipient_id = message.chat.id
    else:
        recipient_id = business_user.id

    return create_profile_keyboard(
        sender_id=sender_id,
        recipient_id=recipient_id,
    )
    
# ================== LOG MEDIA CAPTION ==================

def create_log_media_caption(
    header_text,
    message_type,
    caption=None,
):
    text = (
        header_text
        + "\n"
        + message_type
    )

    if caption:
        text += (
            "\n📝 Подпись:\n"
            + caption
        )

    return text
    
# ================== LOG TEXT MESSAGE ==================

async def send_log_text(
    topic_id,
    text,
    reply_markup=None,
):
    return await bot.send_message(
        chat_id=int(LOG_CHAT_ID),
        message_thread_id=topic_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    
# ================== LOG PHOTO ==================

async def send_log_photo(
    topic_id,
    photo,
    caption,
    reply_markup=None,
):
    return await bot.send_photo(
        chat_id=int(LOG_CHAT_ID),
        message_thread_id=topic_id,
        photo=photo,
        caption=caption,
        reply_markup=reply_markup,
    )
    
# ================== LOG VIDEO ==================

async def send_log_video(
    topic_id,
    video,
    caption,
    reply_markup=None,
):
    return await bot.send_video(
        chat_id=int(LOG_CHAT_ID),
        message_thread_id=topic_id,
        video=video,
        caption=caption,
        reply_markup=reply_markup,
    )
    
# ================== LOG AUDIO ==================

async def send_log_audio(
    topic_id,
    audio,
    caption,
    reply_markup=None,
):
    return await bot.send_audio(
        chat_id=int(LOG_CHAT_ID),
        message_thread_id=topic_id,
        audio=audio,
        caption=caption,
        reply_markup=reply_markup,
    )


# ================== LOG VOICE ==================

async def send_log_voice(
    topic_id,
    voice,
    caption,
    reply_markup=None,
):
    return await bot.send_voice(
        chat_id=int(LOG_CHAT_ID),
        message_thread_id=topic_id,
        voice=voice,
        caption=caption,
        reply_markup=reply_markup,
    )
    
# ================== LOG DOCUMENT ==================

async def send_log_document(
    topic_id,
    document,
    caption,
    reply_markup=None,
):
    return await bot.send_document(
        chat_id=int(LOG_CHAT_ID),
        message_thread_id=topic_id,
        document=document,
        caption=caption,
        reply_markup=reply_markup,
    )
    
# ================== LOG STICKER ==================

async def send_log_sticker(
    topic_id,
    sticker,
):
    return await bot.send_sticker(
        chat_id=int(LOG_CHAT_ID),
        message_thread_id=topic_id,
        sticker=sticker,
    )
    
# ================== LOG ANIMATION ==================

async def send_log_animation(
    topic_id,
    animation,
    caption,
    reply_markup=None,
):
    return await bot.send_animation(
        chat_id=int(LOG_CHAT_ID),
        message_thread_id=topic_id,
        animation=animation,
        caption=caption,
        reply_markup=reply_markup,
    )
    
# ================== LOG VIDEO NOTE ==================

async def send_log_video_note(
    topic_id,
    video_note,
):
    return await bot.send_video_note(
        chat_id=int(LOG_CHAT_ID),
        message_thread_id=topic_id,
        video_note=video_note,
    )
    
# ================== LOG LOCATION ==================

async def send_log_location(
    topic_id,
    latitude,
    longitude,
):
    return await bot.send_location(
        chat_id=int(LOG_CHAT_ID),
        message_thread_id=topic_id,
        latitude=latitude,
        longitude=longitude,
    )
    
# ================== LOG CONTACT ==================

async def send_log_contact(
    topic_id,
    phone_number,
    first_name,
    last_name=None,
    vcard=None,
):
    return await bot.send_contact(
        chat_id=int(LOG_CHAT_ID),
        message_thread_id=topic_id,
        phone_number=phone_number,
        first_name=first_name,
        last_name=last_name,
        vcard=vcard,
    )
    
# ================== LOG REPLY MESSAGE ==================

async def send_log_reply(
    topic_id,
    text,
):
    return await bot.send_message(
        chat_id=int(LOG_CHAT_ID),
        message_thread_id=topic_id,
        text=(
            "💬 ОТВЕТ НА СООБЩЕНИЕ\n\n"
            f"📝 {text}"
        ),
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

    text = message.text or message.caption or ""

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
                        username,
                        trial_until
                    )
                    VALUES (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5,
                        $6,
                        NOW() + INTERVAL '7 days'
                    )
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
    # ================== ENSURE CHAT HEADER ==================
    header_text = await ensure_log_chat_header(
        business_connection_id=message.business_connection_id,
        topic_id=topic_id,
        chat_id=message.chat.id,
        business_user=user,
    )
    
    try:

        # ================== PROFILE BUTTONS ==================

        profile_keyboard = create_message_profile_keyboard(
            message=message,
            business_user=user,
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

                await send_log_photo(
                    topic_id=topic_id,
                    photo=photo_file,
                    caption=create_log_media_caption(
                        header_text=header_text,
                        message_type="🖼 Самоудаляющееся фото",
                        caption=original.caption,
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
                await send_log_reply(
                    topic_id=topic_id,
                    text=message.text,
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

                await send_log_video(
                    topic_id=topic_id,
                    video=video_file,
                    caption=create_log_media_caption(
                        header_text=header_text,
                        message_type="🎥 Самоудаляющееся видео",
                        caption=original.caption,
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
                await send_log_reply(
                    topic_id=topic_id,
                    text=message.text,
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

                await send_log_voice(
                    topic_id=topic_id,
                    voice=voice_file,
                    caption=create_log_media_caption(
                        header_text=header_text,
                        message_type="🎤 Самоудаляющееся голосовое сообщение",
                    ),
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
                await send_log_reply(
                    topic_id=topic_id,
                    text=message.text,
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

                await send_log_video_note(
                    topic_id=topic_id,
                    video_note=video_note_file,
                )

                await send_log_text(
                    topic_id=topic_id,
                    text=create_log_media_caption(
                        header_text=header_text,
                        message_type="⭕ Самоудаляющийся кружок",
                        ),
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
                await send_log_reply(
                    topic_id=topic_id,
                    text=message.text,
                )
                
        # ================== TEXT ==================

        elif message.text:
            full_text = (
                header_text
                + "\n"
                + f"📝 {message.text}"
            )

            sent_message = await send_log_text(
                topic_id=topic_id,
                text=full_text,
                reply_markup=profile_keyboard,
            )

            await save_message_to_d1(
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
            sent_message = await send_log_photo(
                topic_id=topic_id,
                photo=message.photo[-1].file_id,
                caption=create_log_media_caption(
                    header_text=header_text,
                    message_type="🖼 Фото",
                    caption=message.caption,
                ),
                reply_markup=profile_keyboard,
            )

            await save_message_to_d1(
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
            sent_message = await send_log_video(
                topic_id=topic_id,
                video=message.video.file_id,
                caption=create_log_media_caption(
                    header_text=header_text,
                    message_type="🎥 Видео",
                    caption=message.caption,
                ),
                reply_markup=profile_keyboard,
            )

            await save_message_to_d1(
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
            sent_message = await send_log_audio(
                topic_id=topic_id,
                audio=message.audio.file_id,
                caption=create_log_media_caption(
                    header_text=header_text,
                    message_type="🎵 Аудио",
                    caption=message.caption,
                ),
                reply_markup=profile_keyboard,
            )

            await save_message_to_d1(
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
            sent_message = await send_log_voice(
                topic_id=topic_id,
                voice=message.voice.file_id,
                caption=create_log_media_caption(
                    header_text=header_text,
                    message_type="🎤 Голосовое сообщение",
                ),
                reply_markup=profile_keyboard,
            )

            await save_message_to_d1(
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
            sent_message = await send_log_document(
                topic_id=topic_id,
                document=message.document.file_id,
                caption=create_log_media_caption(
                    header_text=header_text,
                    message_type="📎 Документ",
                    caption=message.caption,
                ),
                reply_markup=profile_keyboard,
            )

            await save_message_to_d1(
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
            sent_message = await send_log_text(
                topic_id=topic_id,
                text=create_log_media_caption(
                    header_text=header_text,
                    message_type="😀 Стикер",
                ),
                reply_markup=profile_keyboard,
            )

            await send_log_sticker(
                topic_id=topic_id,
                sticker=message.sticker.file_id,
            )

            await save_message_to_d1(
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
            sent_message = await send_log_animation(
                topic_id=topic_id,
                animation=message.animation.file_id,
                caption=create_log_media_caption(
                    header_text=header_text,
                    message_type="🎞 GIF / Анимация",
                    caption=message.caption,
                ),
                reply_markup=profile_keyboard,
            )

            await save_message_to_d1(
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
            sent_message = await send_log_text(
                topic_id=topic_id,
                text=create_log_media_caption(
                    header_text=header_text,
                    message_type="📹 Видеосообщение",
                ),
                reply_markup=profile_keyboard,
            )
            
            await send_log_video_note(
                topic_id=topic_id,
                video_note=message.video_note.file_id,
            )

            await save_message_to_d1(
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
            sent_message = await send_log_text(
                topic_id=topic_id,
                text=create_log_media_caption(
                    header_text=header_text,
                    message_type="📍 Геолокация",
                ),
                reply_markup=profile_keyboard,
            )

            await send_log_location(
                topic_id=topic_id,
                latitude=message.location.latitude,
                longitude=message.location.longitude,
            ) 

            await save_message_to_d1(
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
            sent_message = await send_log_text(
                topic_id=topic_id,
                text=create_log_media_caption(
                    header_text=header_text,
                    message_type="👤 Контакт",
                ),
                reply_markup=profile_keyboard,
            )

            await send_log_contact(
                topic_id=topic_id,
                phone_number=message.contact.phone_number,
                first_name=message.contact.first_name,
                last_name=message.contact.last_name,
                vcard=message.contact.vcard,
            )

            await save_message_to_d1(
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
            sent_message = await send_log_text(
                topic_id=topic_id,
                text=create_log_media_caption(
                    header_text=header_text,
                    message_type="❓ Неподдерживаемый тип сообщения",
                ),
                reply_markup=profile_keyboard,
            )

            await save_message_to_d1(
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

    business_connection_id = (
        message.business_connection_id
    )

    chat_id = message.chat.id
    message_id = message.message_id

    new_text = (
        message.text
        or message.caption
        or ""
    )

    logger.info(
        "MESSAGE EDITED | "
        "connection=%s | chat=%s | message=%s | new_text=%s",
        business_connection_id,
        chat_id,
        message_id,
        new_text,
    )

    # ================== FIND OLD MESSAGE IN D1 ==================

    old_text = None
    log_message_id = None
    found_d1 = None

    for d1_name in D1_ORDER:

        try:

            d1_config = D1_DATABASES.get(
                d1_name
            )

            if not d1_config:

                logger.warning(
                    "EDIT D1 CONFIG NOT FOUND | "
                    "d1=%s | connection=%s | chat=%s | message=%s",
                    d1_name,
                    business_connection_id,
                    chat_id,
                    message_id,
                )

                continue

            account_id = d1_config.get(
                "account_id"
            )

            database_id = d1_config.get(
                "database_id"
            )

            token_env = d1_config.get(
                "token_env"
            )

            if not account_id:

                logger.warning(
                    "EDIT D1 ACCOUNT ID NOT CONFIGURED | "
                    "d1=%s",
                    d1_name,
                )

                continue

            if not database_id:

                logger.warning(
                    "EDIT D1 DATABASE ID NOT CONFIGURED | "
                    "d1=%s",
                    d1_name,
                )

                continue

            if not token_env:

                logger.warning(
                    "EDIT D1 TOKEN ENV NOT CONFIGURED | "
                    "d1=%s",
                    d1_name,
                )

                continue

            api_token = os.getenv(
                token_env
            )

            if not api_token:

                logger.warning(
                    "EDIT D1 TOKEN NOT CONFIGURED | "
                    "d1=%s | token=%s",
                    d1_name,
                    token_env,
                )

                continue

            url = (
                f"https://api.cloudflare.com/client/v4/accounts/"
                f"{account_id}/d1/database/"
                f"{database_id}/query"
            )

            headers = {
                "Authorization": (
                    f"Bearer {api_token}"
                ),
                "Content-Type": "application/json",
            }

            payload = {
                "sql": """
                    SELECT
                        json_extract(
                            value,
                            '$.text_content'
                        ) AS text_content,
                        json_extract(
                            value,
                            '$.log_message_id'
                        ) AS log_message_id
                    FROM message_batches,
                         json_each(
                             message_batches.messages_json
                         )
                    WHERE
                        message_batches.business_connection_id = ?
                        AND message_batches.chat_id = ?
                        AND CAST(
                            json_extract(
                                value,
                                '$.message_id'
                            )
                            AS INTEGER
                        ) = ?
                    ORDER BY
                        message_batches.rowid DESC
                    LIMIT 1
                """,
                "params": [
                    business_connection_id,
                    chat_id,
                    message_id,
                ],
            }

            logger.info(
                "EDIT D1 SEARCH | "
                "d1=%s | connection=%s | chat=%s | message=%s",
                d1_name,
                business_connection_id,
                chat_id,
                message_id,
            )

            async with httpx.AsyncClient() as client:

                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=30,
                )

            if response.status_code != 200:

                logger.warning(
                    "EDIT D1 SEARCH HTTP ERROR | "
                    "d1=%s | status=%s | response=%s",
                    d1_name,
                    response.status_code,
                    response.text,
                )

                continue

            result = response.json()

            if not result.get("success"):

                logger.warning(
                    "EDIT D1 SEARCH QUERY ERROR | "
                    "d1=%s | result=%s",
                    d1_name,
                    result,
                )

                continue

            result_data = result.get(
                "result",
                []
            )

            rows = (
                result_data[0].get(
                    "results",
                    []
                )
                if result_data
                else []
            )

            if rows:

                row = rows[0]

                old_text = row.get(
                    "text_content"
                )

                log_message_id = row.get(
                    "log_message_id"
                )

                found_d1 = d1_name

                logger.info(
                    "EDIT OLD MESSAGE LOADED FROM D1 | "
                    "d1=%s | connection=%s | chat=%s | message=%s",
                    found_d1,
                    business_connection_id,
                    chat_id,
                    message_id,
                )

                break

        except Exception as e:

            logger.exception(
                "EDIT D1 SEARCH ERROR | "
                "d1=%s | connection=%s | chat=%s | "
                "message=%s | error=%s",
                d1_name,
                business_connection_id,
                chat_id,
                message_id,
                e,
            )

            continue

    # ================== IF NOT IN D1 — CHECK RAM ==================

    if old_text is None:

        batch_key = (
            business_connection_id,
            chat_id,
        )

        batch = d1_message_batches.get(
            batch_key
        )

        if batch:

            for item in reversed(
                batch["messages"]
            ):

                if item.get(
                    "message_id"
                ) == message_id:

                    old_text = item.get(
                        "text_content"
                    )

                    log_message_id = item.get(
                        "log_message_id"
                    )

                    logger.info(
                        "EDIT OLD MESSAGE LOADED FROM RAM | "
                        "connection=%s | chat=%s | message=%s",
                        business_connection_id,
                        chat_id,
                        message_id,
                    )

                    break

    if old_text is None:

        old_text = (
            "[старый текст не найден]"
        )

        logger.warning(
            "EDIT OLD MESSAGE NOT FOUND | "
            "connection=%s | chat=%s | message=%s",
            business_connection_id,
            chat_id,
            message_id,
        )

    # ================== GET BUSINESS OWNER ==================

    try:

        business_connection = (
            await bot.get_business_connection(
                business_connection_id
            )
        )

        user = business_connection.user

    except Exception as e:

        logger.exception(
            "EDIT BUSINESS OWNER ERROR | "
            "connection=%s | error=%s",
            business_connection_id,
            e,
        )

        return

    # ================== GET EDITED MESSAGE TOPIC ==================

    topic_id = business_topics.get(
        business_connection_id
    )

    if topic_id is None and db_pool is not None:

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

            business_topics[
                business_connection_id
            ] = topic_id

    if topic_id is None:

        logger.error(
            "EDITED MESSAGE TOPIC NOT FOUND | "
            "connection=%s | chat=%s | message=%s",
            business_connection_id,
            chat_id,
            message_id,
        )

        return

    # ================== GET CHAT USER ==================

    try:

        chat = await bot.get_chat(
            chat_id=chat_id
        )

        peer_name = (
            chat.full_name
            if getattr(chat, "full_name", None)
            else getattr(chat, "first_name", None)
            or getattr(chat, "title", None)
            or "Неизвестный пользователь"
        )

    except Exception:

        peer_name = (
            "Неизвестный пользователь"
        )

    # ================== ESCAPE HTML ==================

    business_name = (
        user.first_name
        or "Пользователь"
    )

    if user.last_name:

        business_name += (
            f" {user.last_name}"
        )

    business_name = html.escape(
        business_name
    )

    peer_name = html.escape(
        peer_name
    )

    old_text_escaped = html.escape(
        old_text
    )

    new_text_escaped = html.escape(
        new_text
    )

    # ================== PROFILE BUTTONS ==================

    sender_id = message.from_user.id

    if sender_id == user.id:

        recipient_id = chat_id

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

    # ================== SAVE EDIT TO LOG ==================

    edited_text = (
        "✏️ <b>СООБЩЕНИЕ ИЗМЕНЕНО</b>\n\n"
        f"👤 {business_name}\n"
        f"💬 {peer_name}\n"
        f"🆔 Chat ID: <code>{chat_id}</code>\n\n"
        "⬅️ <b>БЫЛО:</b>\n"
        f"<code>{old_text_escaped}</code>\n\n"
        "➡️ <b>СТАЛО:</b>\n"
        f"<code>{new_text_escaped}</code>"
    )

    try:

        sent_edit = await bot.send_message(
            chat_id=int(LOG_CHAT_ID),
            message_thread_id=topic_id,
            text=edited_text,
            parse_mode="HTML",
            reply_markup=profile_keyboard,
            reply_parameters=(
                {
                    "message_id": log_message_id
                }
                if log_message_id
                else None
            ),
        )

        logger.info(
            "EDIT LOG SAVED | "
            "connection=%s | topic=%s | message=%s",
            business_connection_id,
            topic_id,
            message_id,
        )

    except Exception as e:

        logger.exception(
            "EDIT LOG ERROR | "
            "connection=%s | message=%s | error=%s",
            business_connection_id,
            message_id,
            e,
        )

        sent_edit = None

    # ================== SAVE NEW VERSION TO D1 ==================

    await save_message_to_d1(
        business_connection_id=business_connection_id,
        chat_id=chat_id,
        message_data={
            "message_id": message_id,
            "log_message_id": (
                sent_edit.message_id
                if sent_edit
                else log_message_id
            ),
            "message_type": "text",
            "file_id": None,
            "text_content": new_text,
            "event_type": "edit",
        },
    )

    logger.info(
        "EDIT NEW VERSION BUFFERED | "
        "connection=%s | chat=%s | message=%s",
        business_connection_id,
        chat_id,
        message_id,
    )

# ================== DELETED BUSINESS MESSAGES ==================

@dp.deleted_business_messages()
async def handle_deleted_business_messages(message):
    logger.info(
        "BUSINESS MESSAGES DELETED | connection=%s | chat=%s | messages=%s",
        message.business_connection_id,
        message.chat.id,
        message.message_ids,
    )

    # ================== GET BUSINESS OWNER ==================

    business_connection = await bot.get_business_connection(
        business_connection_id=message.business_connection_id
    )

    user = business_connection.user

    # ================== GET USER LOG TOPIC ==================

    topic_id = business_topics.get(
        message.business_connection_id
    )

    if topic_id is None and db_pool is not None:
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

            business_topics[
                message.business_connection_id
            ] = topic_id

            logger.info(
                "DELETED MESSAGE TOPIC LOADED FROM DATABASE | "
                "user=%s | topic_id=%s",
                user.id,
                topic_id,
            )

    if topic_id is None:
        logger.error(
            "DELETED MESSAGE TOPIC NOT FOUND | "
            "connection=%s | user=%s",
            message.business_connection_id,
            user.id,
        )
        return

    # ================== PROCESS DELETED MESSAGES ==================

    for deleted_message_id in message.message_ids:

        deleted_data = None

        # ================== SEARCH IN RAM ==================

        batch_key = (
            message.business_connection_id,
            message.chat.id,
        )

        batch = d1_message_batches.get(batch_key)

        if batch:
            for item in batch["messages"]:
                if item.get("message_id") == deleted_message_id:
                    deleted_data = item
                    break

        if deleted_data:
            logger.info(
                "DELETED MESSAGE FOUND IN RAM | "
                "connection=%s | chat=%s | message=%s | data=%s",
                message.business_connection_id,
                message.chat.id,
                deleted_message_id,
                deleted_data,
            )

                # ================== SEARCH IN D1 ==================

        if deleted_data is None:

            for d1_name in D1_ORDER:

                try:

                    d1_config = D1_DATABASES.get(
                        d1_name
                    )

                    if not d1_config:
                        logger.warning(
                            "DELETE D1 CONFIG NOT FOUND | "
                            "d1=%s | connection=%s | chat=%s | message=%s",
                            d1_name,
                            message.business_connection_id,
                            message.chat.id,
                            deleted_message_id,
                        )
                        continue

                    account_id = d1_config.get(
                        "account_id"
                    )

                    database_id = d1_config.get(
                        "database_id"
                    )

                    token_env = d1_config.get(
                        "token_env"
                    )

                    if not account_id:
                        logger.warning(
                            "DELETE D1 ACCOUNT ID MISSING | "
                            "d1=%s",
                            d1_name,
                        )
                        continue

                    if not database_id:
                        logger.warning(
                            "DELETE D1 DATABASE ID MISSING | "
                            "d1=%s",
                            d1_name,
                        )
                        continue

                    if not token_env:
                        logger.warning(
                            "DELETE D1 TOKEN ENV MISSING | "
                            "d1=%s",
                            d1_name,
                        )
                        continue

                    api_token = os.getenv(
                        token_env
                    )

                    if not api_token:
                        logger.warning(
                            "DELETE D1 API TOKEN MISSING | "
                            "d1=%s | token=%s",
                            d1_name,
                            token_env,
                        )
                        continue

                    url = (
                        f"https://api.cloudflare.com/client/v4/accounts/"
                        f"{account_id}/d1/database/"
                        f"{database_id}/query"
                    )

                    headers = {
                        "Authorization": f"Bearer {api_token}",
                        "Content-Type": "application/json",
                    }

                    payload = {
                        "sql": """
                            SELECT
                                business_connection_id,
                                chat_id,
                                batch_id,
                                messages_json
                            FROM message_batches
                            WHERE
                                business_connection_id = ?
                                AND chat_id = ?
                                AND EXISTS (
                                    SELECT 1
                                    FROM json_each(messages_json)
                                    WHERE CAST(
                                        json_extract(
                                            value,
                                            '$.message_id'
                                        ) AS INTEGER
                                    ) = ?
                                )
                            ORDER BY rowid DESC
                            LIMIT 1
                        """,
                        "params": [
                            message.business_connection_id,
                            message.chat.id,
                            deleted_message_id,
                        ],
                    }

                    logger.info(
                        "DELETE D1 SEARCH | "
                        "d1=%s | connection=%s | chat=%s | message=%s",
                        d1_name,
                        message.business_connection_id,
                        message.chat.id,
                        deleted_message_id,
                    )

                    async with httpx.AsyncClient() as client:

                        response = await client.post(
                            url,
                            headers=headers,
                            json=payload,
                            timeout=30,
                        )

                    if response.status_code != 200:
                        logger.warning(
                            "DELETE D1 SEARCH HTTP ERROR | "
                            "d1=%s | status=%s | connection=%s | chat=%s | message=%s",
                            d1_name,
                            response.status_code,
                            message.business_connection_id,
                            message.chat.id,
                            deleted_message_id,
                        )
                        continue

                    result = response.json()

                    if not result.get("success"):
                        logger.warning(
                            "DELETE D1 SEARCH FAILED | "
                            "d1=%s | result=%s",
                            d1_name,
                            result,
                        )
                        continue

                    result_data = result.get(
                        "result",
                        []
                    )

                    results = (
                        result_data[0].get(
                            "results",
                            []
                        )
                        if result_data
                        else []
                    )

                    if not results:
                        continue

                    row = results[0]

                    messages = json.loads(
                        row["messages_json"]
                    )

                    for item in messages:

                        if (
                            int(
                                item.get(
                                    "message_id"
                                )
                            )
                            == deleted_message_id
                        ):

                            deleted_data = item

                            logger.info(
                                "DELETED MESSAGE FOUND IN D1 | "
                                "d1=%s | connection=%s | chat=%s | message=%s | data=%s",
                                d1_name,
                                message.business_connection_id,
                                message.chat.id,
                                deleted_message_id,
                                deleted_data,
                            )

                            break

                    if deleted_data is not None:
                        break

                except Exception as e:

                    logger.exception(
                        "DELETE D1 SEARCH ERROR | "
                        "d1=%s | connection=%s | chat=%s | message=%s | error=%s",
                        d1_name,
                        message.business_connection_id,
                        message.chat.id,
                        deleted_message_id,
                        e,
                    )

                    continue

        # ================== MESSAGE NOT FOUND ==================

        if deleted_data is None:
            logger.warning(
                "DELETED MESSAGE NOT FOUND | "
                "RAM + D1 | connection=%s | chat=%s | message=%s",
                message.business_connection_id,
                message.chat.id,
                deleted_message_id,
            )

            await bot.send_message(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                text=(
                    "🗑 СООБЩЕНИЕ УДАЛЕНО\n\n"
                    f"👤 {user.first_name} {user.last_name or ''}\n"
                    f"🆔 User ID: {user.id}\n"
                    f"💬 Chat ID: {message.chat.id}\n"
                    f"🆔 Message ID: {deleted_message_id}\n\n"
                    "⚠️ Данные сообщения не найдены."
                ),
            )

            continue

        # ================== MESSAGE TYPE ==================

        message_type = deleted_data.get(
            "message_type"
        )

        text_content = deleted_data.get(
            "text_content"
        )

        file_id = deleted_data.get(
            "file_id"
        )

        # ================== LOG DELETION INFO ==================

        try:
            await bot.send_message(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                text=(
                    "🗑 СООБЩЕНИЕ УДАЛЕНО\n\n"
                    f"👤 {user.first_name} {user.last_name or ''}\n"
                    f"🆔 User ID: {user.id}\n"
                    f"💬 Chat ID: {message.chat.id}\n"
                    f"🆔 Message ID: {deleted_message_id}\n"
                    f"📦 Тип: {message_type}"
                ),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="👤 Открыть отправителя",
                                url=f"tg://user?id={user.id}",
                            )
                        ]
                    ]
                ),
            )

        except Exception as e:
            logger.exception(
                "DELETED MESSAGE LOG INFO ERROR | "
                "connection=%s | chat=%s | message=%s | error=%s",
                message.business_connection_id,
                message.chat.id,
                deleted_message_id,
                e,
            )
        # ================== TEXT ==================

        if message_type == "text":
            try:
                await bot.send_message(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    text=(
                        "♻️ УДАЛЁННЫЙ ТЕКСТ\n\n"
                        f"{text_content or '[пусто]'}"
                    ),
                )

                logger.info(
                    "DELETED TEXT RESTORED TO LOG | "
                    "connection=%s | chat=%s | message=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                )

            except Exception as e:
                logger.exception(
                    "DELETED TEXT RESTORE ERROR | "
                    "connection=%s | chat=%s | message=%s | error=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                    e,
                )

        # ================== PHOTO ==================

        elif message_type == "photo":
            try:
                await bot.send_photo(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    photo=file_id,
                    caption=(
                        "♻️ УДАЛЁННОЕ ФОТО"
                        + (
                            f"\n\n📝 Подпись:\n{text_content}"
                            if text_content
                            else ""
                        )
                    ),
                )

                logger.info(
                    "DELETED PHOTO RESTORED TO LOG | "
                    "connection=%s | chat=%s | message=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                )

            except Exception as e:
                logger.exception(
                    "DELETED PHOTO RESTORE ERROR | "
                    "connection=%s | chat=%s | message=%s | error=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                    e,
                )

        # ================== VIDEO ==================

        elif message_type == "video":
            try:
                await bot.send_video(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    video=file_id,
                    caption=(
                        "♻️ УДАЛЁННОЕ ВИДЕО"
                        + (
                            f"\n\n📝 Подпись:\n{text_content}"
                            if text_content
                            else ""
                        )
                    ),
                )

                logger.info(
                    "DELETED VIDEO RESTORED TO LOG | "
                    "connection=%s | chat=%s | message=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                )

            except Exception as e:
                logger.exception(
                    "DELETED VIDEO RESTORE ERROR | "
                    "connection=%s | chat=%s | message=%s | error=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                    e,
                )

        # ================== AUDIO ==================

        elif message_type == "audio":
            try:
                await bot.send_audio(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    audio=file_id,
                    caption=(
                        "♻️ УДАЛЁННОЕ АУДИО"
                        + (
                            f"\n\n📝 Подпись:\n{text_content}"
                            if text_content
                            else ""
                        )
                    ),
                )

                logger.info(
                    "DELETED AUDIO RESTORED TO LOG | "
                    "connection=%s | chat=%s | message=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                )

            except Exception as e:
                logger.exception(
                    "DELETED AUDIO RESTORE ERROR | "
                    "connection=%s | chat=%s | message=%s | error=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                    e,
                )

        # ================== VOICE ==================

        elif message_type == "voice":
            try:
                await bot.send_voice(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    voice=file_id,
                )

                logger.info(
                    "DELETED VOICE RESTORED TO LOG | "
                    "connection=%s | chat=%s | message=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                )

            except Exception as e:
                logger.exception(
                    "DELETED VOICE RESTORE ERROR | "
                    "connection=%s | chat=%s | message=%s | error=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                    e,
                )

        # ================== DOCUMENT ==================

        elif message_type == "document":
            try:
                await bot.send_document(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    document=file_id,
                    caption=(
                        "♻️ УДАЛЁННЫЙ ДОКУМЕНТ"
                        + (
                            f"\n\n📝 Подпись:\n{text_content}"
                            if text_content
                            else ""
                        )
                    ),
                )

                logger.info(
                    "DELETED DOCUMENT RESTORED TO LOG | "
                    "connection=%s | chat=%s | message=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                )

            except Exception as e:
                logger.exception(
                    "DELETED DOCUMENT RESTORE ERROR | "
                    "connection=%s | chat=%s | message=%s | error=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                    e,
                )

        # ================== STICKER ==================

        elif message_type == "sticker":
            try:
                await bot.send_sticker(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    sticker=file_id,
                )

                logger.info(
                    "DELETED STICKER RESTORED TO LOG | "
                    "connection=%s | chat=%s | message=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                )

            except Exception as e:
                logger.exception(
                    "DELETED STICKER RESTORE ERROR | "
                    "connection=%s | chat=%s | message=%s | error=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                    e,
                )

        # ================== ANIMATION / GIF ==================

        elif message_type == "animation":
            try:
                await bot.send_animation(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    animation=file_id,
                    caption=(
                        "♻️ УДАЛЁННАЯ АНИМАЦИЯ"
                        + (
                            f"\n\n📝 Подпись:\n{text_content}"
                            if text_content
                            else ""
                        )
                    ),
                )

                logger.info(
                    "DELETED ANIMATION RESTORED TO LOG | "
                    "connection=%s | chat=%s | message=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                )

            except Exception as e:
                logger.exception(
                    "DELETED ANIMATION RESTORE ERROR | "
                    "connection=%s | chat=%s | message=%s | error=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                    e,
                )

        # ================== VIDEO NOTE / CIRCLE ==================

        elif message_type == "video_note":
            try:
                await bot.send_video_note(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    video_note=file_id,
                )

                logger.info(
                    "DELETED VIDEO NOTE RESTORED TO LOG | "
                    "connection=%s | chat=%s | message=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                )

            except Exception as e:
                logger.exception(
                    "DELETED VIDEO NOTE RESTORE ERROR | "
                    "connection=%s | chat=%s | message=%s | error=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                    e,
                )

        # ================== LOCATION ==================

        elif message_type == "location":
            latitude = deleted_data.get(
                "latitude"
            )

            longitude = deleted_data.get(
                "longitude"
            )

            if latitude is not None and longitude is not None:
                try:
                    await bot.send_location(
                        chat_id=int(LOG_CHAT_ID),
                        message_thread_id=topic_id,
                        latitude=latitude,
                        longitude=longitude,
                    )

                    logger.info(
                        "DELETED LOCATION RESTORED TO LOG | "
                        "connection=%s | chat=%s | message=%s",
                        message.business_connection_id,
                        message.chat.id,
                        deleted_message_id,
                    )

                except Exception as e:
                    logger.exception(
                        "DELETED LOCATION RESTORE ERROR | "
                        "connection=%s | chat=%s | message=%s | error=%s",
                        message.business_connection_id,
                        message.chat.id,
                        deleted_message_id,
                        e,
                    )

        # ================== CONTACT ==================

        elif message_type == "contact":
            try:
                await bot.send_contact(
                    chat_id=int(LOG_CHAT_ID),
                    message_thread_id=topic_id,
                    phone_number=deleted_data.get(
                        "phone_number"
                    ),
                    first_name=deleted_data.get(
                        "first_name"
                    ),
                    last_name=deleted_data.get(
                        "last_name"
                    ),
                    vcard=deleted_data.get(
                        "vcard"
                    ),
                )

                logger.info(
                    "DELETED CONTACT RESTORED TO LOG | "
                    "connection=%s | chat=%s | message=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                )

            except Exception as e:
                logger.exception(
                    "DELETED CONTACT RESTORE ERROR | "
                    "connection=%s | chat=%s | message=%s | error=%s",
                    message.business_connection_id,
                    message.chat.id,
                    deleted_message_id,
                    e,
                )

        # ================== UNKNOWN ==================

        else:
            logger.warning(
                "DELETED MESSAGE TYPE NOT RESTORED | "
                "connection=%s | chat=%s | message=%s | type=%s",
                message.business_connection_id,
                message.chat.id,
                deleted_message_id,
                message_type,
            )

            await bot.send_message(
                chat_id=int(LOG_CHAT_ID),
                message_thread_id=topic_id,
                text=(
                    "⚠️ УДАЛЁННОЕ СООБЩЕНИЕ\n\n"
                    f"Тип: {message_type}\n"
                    f"Message ID: {deleted_message_id}\n\n"
                    "Восстановление этого типа пока не поддерживается."
                ),
            )

                    # ================== SEND DELETED MESSAGE TO USER ==================

        try:

            notification_text = (
                "🗑 ТВОЁ СООБЩЕНИЕ БЫЛО УДАЛЕНО\n\n"
                f"📦 Тип: {message_type}\n\n"
            )

            # ================== TEXT ==================

            if message_type == "text":

                await bot.send_message(
                    chat_id=user.id,
                    text=(
                        notification_text
                        + (
                            text_content
                            if text_content
                            else "Текст сообщения отсутствует."
                        )
                    ),
                )

            # ================== PHOTO ==================

            elif message_type == "photo" and file_id:

                await bot.send_photo(
                    chat_id=user.id,
                    photo=file_id,
                    caption=(
                        notification_text
                        + (
                            text_content
                            if text_content
                            else ""
                        )
                    ),
                )

            # ================== VIDEO ==================

            elif message_type == "video" and file_id:

                await bot.send_video(
                    chat_id=user.id,
                    video=file_id,
                    caption=(
                        notification_text
                        + (
                            text_content
                            if text_content
                            else ""
                        )
                    ),
                )

            # ================== AUDIO ==================

            elif message_type == "audio" and file_id:

                await bot.send_audio(
                    chat_id=user.id,
                    audio=file_id,
                    caption=(
                        notification_text
                        + (
                            text_content
                            if text_content
                            else ""
                        )
                    ),
                )

            # ================== VOICE ==================

            elif message_type == "voice" and file_id:

                await bot.send_voice(
                    chat_id=user.id,
                    voice=file_id,
                )

                await bot.send_message(
                    chat_id=user.id,
                    text=notification_text,
                )

            # ================== DOCUMENT ==================

            elif message_type == "document" and file_id:

                await bot.send_document(
                    chat_id=user.id,
                    document=file_id,
                    caption=(
                        notification_text
                        + (
                            text_content
                            if text_content
                            else ""
                        )
                    ),
                )

            # ================== STICKER ==================

            elif message_type == "sticker" and file_id:

                await bot.send_sticker(
                    chat_id=user.id,
                    sticker=file_id,
                )

                await bot.send_message(
                    chat_id=user.id,
                    text=notification_text,
                )

            # ================== ANIMATION / GIF ==================

            elif message_type == "animation" and file_id:

                await bot.send_animation(
                    chat_id=user.id,
                    animation=file_id,
                    caption=(
                        notification_text
                        + (
                            text_content
                            if text_content
                            else ""
                        )
                    ),
                )

            # ================== VIDEO NOTE / CIRCLE ==================

            elif message_type == "video_note" and file_id:

                await bot.send_video_note(
                    chat_id=user.id,
                    video_note=file_id,
                )

                await bot.send_message(
                    chat_id=user.id,
                    text=notification_text,
                )

            # ================== LOCATION ==================

            elif message_type == "location":

                latitude = deleted_data.get(
                    "latitude"
                )

                longitude = deleted_data.get(
                    "longitude"
                )

                if latitude is not None and longitude is not None:

                    await bot.send_location(
                        chat_id=user.id,
                        latitude=latitude,
                        longitude=longitude,
                    )

                    await bot.send_message(
                        chat_id=user.id,
                        text=notification_text,
                    )

            # ================== CONTACT ==================

            elif message_type == "contact":

                await bot.send_contact(
                    chat_id=user.id,
                    phone_number=deleted_data.get(
                        "phone_number"
                    ),
                    first_name=deleted_data.get(
                        "first_name"
                    ),
                    last_name=deleted_data.get(
                        "last_name"
                    ),
                    vcard=deleted_data.get(
                        "vcard"
                    ),
                )

                await bot.send_message(
                    chat_id=user.id,
                    text=notification_text,
                )

            # ================== UNKNOWN TYPE ==================

            else:

                await bot.send_message(
                    chat_id=user.id,
                    text=(
                        notification_text
                        + "Не удалось определить содержимое сообщения."
                    ),
                )

            logger.info(
                "DELETED MESSAGE SENT TO USER | "
                "user=%s | chat=%s | message=%s | type=%s",
                user.id,
                message.chat.id,
                deleted_message_id,
                message_type,
            )

        except Exception as e:

            logger.exception(
                "DELETED MESSAGE USER SEND ERROR | "
                "user=%s | chat=%s | message=%s | type=%s | error=%s",
                user.id,
                message.chat.id,
                deleted_message_id,
                message_type,
                e,
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


# ================== MINI APP AUTH ==================

@app.post("/miniapp/auth")
async def miniapp_auth(request: Request):

    data = await request.json()

    init_data = data.get("initData")

    if not init_data:
        return {
            "ok": False,
            "error": "initData is missing",
        }


    # ================== PARSE INIT DATA ==================

    parsed_data = dict(
        parse_qsl(
            init_data,
            keep_blank_values=True,
        )
    )

    received_hash = parsed_data.pop(
        "hash",
        None,
    )

    if not received_hash:
        return {
            "ok": False,
            "error": "hash is missing",
        }


    # ================== CREATE DATA CHECK STRING ==================

    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(
            parsed_data.items()
        )
    )


    # ================== CREATE SECRET KEY ==================

    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()


    # ================== CALCULATE HASH ==================

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()


    # ================== VERIFY TELEGRAM ==================

    if not hmac.compare_digest(
        calculated_hash,
        received_hash,
    ):
        return {
            "ok": False,
            "error": "Invalid initData",
        }


    # ================== GET USER ==================

    user_data = parsed_data.get(
        "user"
    )

    if not user_data:
        return {
            "ok": False,
            "error": "User data is missing",
        }


    import json

    user = json.loads(
        user_data
    )


    # ================== SUCCESS ==================

    return {
        "ok": True,
        "user": {
            "id": user.get("id"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "username": user.get("username"),
        },
    }


# ================== TRIAL EXPIRATION BACKGROUND TASK ==================

async def trial_expiration_loop():

    while True:

        try:

            await check_expired_trials()

        except Exception:

            logger.exception(
                "TRIAL EXPIRATION LOOP ERROR"
            )

        await asyncio.sleep(300)
        
        
# ================== STARTUP ==================

@app.on_event("startup")
async def startup():
    logger.info("STARTUP: BEFORE DATABASE")

    await init_db()
    await test_d1_1_2()
    await test_d1_storage()
    await test_d1_router_storage()
    await test_d1_daily_write_usage()
    await test_d1_daily_write_router()
    await test_d1_combined_router()

    asyncio.create_task(
        trial_expiration_loop()
    )
    
    logger.info("STARTUP: AFTER DATABASE")

    webhook_url = "https://kusuo-saiki.onrender.com/webhook"

    await bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
    )

    # ================== MINI APP MENU BUTTON ==================

    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="🧠 Kusuo Saiki",
            web_app=WebAppInfo(
                url="https://kusuo-miniapp.onrender.com"
            ),
        )
    )

    logger.info(
        "MINI APP MENU BUTTON SET"
    )

    logger.info("LastMod Business Bot started")
    logger.info("Webhook set: %s", webhook_url)

# ================== SHUTDOWN ==================

@app.on_event("shutdown")
async def shutdown():
    await bot.session.close()
    logger.info("LastMod Business Bot stopped")
