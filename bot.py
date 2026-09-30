import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, ChatMemberUpdatedFilter, MEMBER
from aiogram.types import BotCommand, ChatPermissions

logging.basicConfig(level=logging.INFO)

TOKEN = "8850468671:AAEJ31dG-_4JOmg3IOC9e_T3IdtVarLftnY"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Используем список для правил, чтобы их можно было динамически дополнять
group_rules_list = [
    "Спам запрещен",
    "Порнография 18+ запрещена, но сливать порно наших врагов можно",
    "Ссылки на чат запрещено",
    "Слив владельца (Topyak) запрещено"
]

def get_rules_text():
    text = "Правила группы:\n"
    for i, rule in enumerate(group_rules_list, 1):
        text += f"• {rule}\n"
    return text.strip()


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="ban", description="Забанить пользователя (в ответ)"),
        BotCommand(command="unban", description="Разбанить пользователя (в ответ)"),
        BotCommand(command="mute", description="Замутить на 5 минут (в ответ)"),
        BotCommand(command="unmute", description="Размутить пользователя (в ответ)"),
        BotCommand(command="warn", description="Выдать предупреждение (в ответ)"),
        BotCommand(command="rules", description="Показать правила группы"),
        BotCommand(command="addrule", description="Добавить правило (написать текст после команды)"),
    ]
    await bot.set_my_commands(main_menu_commands)


# Приветствие новых участников
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def welcome_user(event: types.ChatMemberUpdated):
    user = event.new_chat_member.user
    await event.chat.send_message(
        f"Привет, {user.full_name}!\n\n{get_rules_text()}"
    )


@dp.message(Command("rules"))
async def cmd_rules(message: types.Message):
    await message.answer(get_rules_text())


# Команда добавления нового правила
@dp.message(Command("addrule"))
async def cmd_add_rule(message: types.Message):
    # Убираем саму команду "/addrule", чтобы остался только текст правила
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Напиши правило после команды, например:\n`/addrule Не флудить капсом`", parse_mode="Markdown")
        return
    
    new_rule = args[1]
    group_rules_list.append(new_rule)
    await message.answer(f"✅ Новое правило успешно добавлено!\n\n{get_rules_text()}")


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
        await message.reply("Используйте в ответ на сообщение пользователя!")
        return
    try:
        until_date = datetime.now() + timedelta(minutes=5)
        await message.chat.restrict(
            user_id=message.reply_to_message.from_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.answer(f"Пользователь {message.reply_to_message.from_user.full_name} замучен на 5 минут.")
    except Exception as e:
        await message.answer(f"Ошибка мута: {e}")


# Новая команда: Размут
@dp.message(Command("unmute"))
async def cmd_unmute(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Используйте в ответ на сообщение пользователя!")
        return
    try:
        # Возвращаем стандартные права на отправку сообщений
        await message.chat.restrict(
            user_id=message.reply_to_message.from_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_add_web_page_previews=True
            )
        )
        await message.answer(f"Пользователь {message.reply_to_message.from_user.full_name ам} размучен.")
    except Exception as e:
        await message.answer(f"Ошибка размута: {e}")


async def main():
    await set_main_menu(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    
