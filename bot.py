import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import BotCommand, ChatPermissions

# Включаем логирование для бота
logging.basicConfig(level=logging.INFO)

# ТОКЕН БОТА (Вставлен прямо в код)
TOKEN = "8726690670:AAGeO4bC1Ncpclb_X8R_XCNaG8nTgkC2-SU"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных для варнов в памяти: {chat_id: {user_id: count}}
warnings = {}

# Текст правил группы
GROUP_RULES = (
    "Привет! Добро пожаловать в группу.\n"
    "Вот основные правила:\n"
    "1. Не оскорбляйте участников.\n"
    "2. Не спамьте.\n"
    "3. Соблюдайте уважение."
)


# --- НАСТРОЙКА ГЛАВНЫХ ПУНКТОВ МЕНЮ (КНОПКА "/") ---
async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="ban", description="Забанить пользователя (в ответ)"),
        BotCommand(
            command="unban", description="Разбанить пользователя (в ответ)"
        ),
        BotCommand(
            command="mute", description="Замутить на 3, 5 или 10 минут (в ответ)"
        ),
        BotCommand(command="warn", description="Выдать предупреждение (в ответ)"),
        BotCommand(command="rules", description="Показать правила группы"),
    ]
    await bot.set_my_commands(main_menu_commands)


# --- ПРИВЕТСТВИЕ И ОТПРАВКА ПРАВИЛ ПРИ ВХОДЕ ---
@dp.chat_member()
async def welcome_user(event: types.ChatMemberUpdated):
    if (
        event.old_chat_member.status in ["left", "kicked"]
        and event.new_chat_member.status == "member"
    ):
        user = event.new_chat_member.user
        await event.chat.send_message(
            f"Привет, {user.full_name}!\n\n{GROUP_RULES}"
        )


# --- КОМАНДА: ПРАВИЛА (/rules) ---
@dp.message(Command("rules"))
async def cmd_rules(message: types.Message):
    await message.answer(GROUP_RULES)


# --- КОМАНДА: БАН (/ban) ---
@dp.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if not message.reply_to_message:
        await message.reply(
            "Эту команду нужно использовать в ответ на сообщение нарушителя!"
        )
        return

    chat_id = message.chat.id
    user_to_ban = message.reply_to_message.from_user

    try:
        await bot.ban_chat_member(chat_id=chat_id, user_id=user_to_ban.id)
        await message.answer(
            f"Пользователь {user_to_ban.full_name} был забанен."
        )
    except Exception as e:
        await message.answer(
            f"Не удалось забанить пользователя. Убедитесь, что бот — администратор.\nОшибка: {e}"
        )


# --- КОМАНДА: РАЗБАН (/unban) ---
@dp.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if not message.reply_to_message:
        await message.reply(
            "Эту команду нужно использовать в ответ на сообщение пользователя!"
        )
        return

    chat_id = message.chat.id
    user_to_unban = message.reply_to_message.from_user

    try:
        await bot.unban_chat_member(chat_id=chat_id, user_id=user_to_unban.id)
        await message.answer(
            f"Пользователь {user_to_unban
