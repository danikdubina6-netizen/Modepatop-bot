import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import BotCommand, ChatPermissions

logging.basicConfig(level=logging.INFO)

TOKEN = "8850468671:AAEJ31dG-_4JOmg3IOC9e_T3IdtVarLftnY"

bot = Bot(token=TOKEN)
dp = Dispatcher()

warnings = {}

GROUP_RULES = (
    "Правила группы:
• Спам запрещен
• Порнография 18+ запрещена, но сливать порно наших врагов можно
• Ссылки на чат запрещено
• Слив владельца (Topyak) запрещено"
)


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


@dp.message(Command("rules"))
async def cmd_rules(message: types.Message):
    await message.answer(GROUP_RULES)


@dp.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if not message.reply_to_message:
        await message.reply(
            "Эту команду нужно использовать в ответ на сообщение нарушителя!"
        )
        return
    try:
        await bot.ban_chat_member(
            chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id
        )
        await message.answer(
            f"Пользователь {message.reply_to_message.from_user.full_name} забанен."
        )
    except Exception as e:
        await message.answer(f"Ошибка бана: {e}")


@dp.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Используйте в ответ на сообщение пользователя!")
        return
    try:
        await bot.unban_chat_member(
            chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id
        )
        await message.answer(
            f"Пользователь {message.reply_to_message.from_user.full_name} разбанен."
        )
    except Exception as e:
        await message.answer(f"Ошибка разбана: {e}")


@dp.message(Command("mute"))
async def cmd_mute(message: types.Message):
    if not message.reply_to_message:
