import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, ChatMemberUpdatedFilter, MEMBER, LEFT, KICKED
from aiogram.types import BotCommand, ChatPermissions

logging.basicConfig(level=logging.INFO)

TOKEN = "8850468671:AAEJ31dG-_4JOmg3IOC9e_T3IdtVarLftnY"

bot = Bot(token=TOKEN)
dp = Dispatcher()

warnings = {}

GROUP_RULES = (
    "Правила группы:\n"
    "• Спам запрещен\n"
    "• Порнография 18+ запрещена, но сливать порно наших врагов можно\n"
    "• Ссылки на чат запрещено\n"
    "• Слив владельца (Topyak) запрещено"
)


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="ban", description="Забанить пользователя (в ответ)"),
        BotCommand(command="unban", description="Разбанить пользователя (в ответ)"),
        BotCommand(command="mute", description="Замутить пользователя (в ответ)"),
        BotCommand(command="warn", description="Выдать предупреждение (в ответ)"),
        BotCommand(command="rules", description="Показать правила группы"),
    ]
    await bot.set_my_commands(main_menu_commands)


# Приветствие новых участников (исправлено под aiogram 3)
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def welcome_user(event: types.ChatMemberUpdated):
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
        await message.reply("Эту команду нужно использовать в ответ на сообщение нарушителя!")
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
        await bot,unban_chat_member if False else bot.unban_chat_member(
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
        await message.reply("Используйте в ответ на сообщение пользователя!")
        return
    try:
        # Мутим на 5 минут по умолчанию
        until_date = datetime.now() + timedelta(minutes=5)
        await message.chat.restrict(
            user_id=message.reply_to_message.from_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.answer(f"Пользователь {message.reply_to_message.from_user.full_name} замучен на 5 минут.")
    except Exception as e:
        await message.answer(f"Ошибка мута: {e}")


async def main():
    await set_main_menu(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    
