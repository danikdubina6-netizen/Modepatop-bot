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

# Список правил группы
group_rules_list = [
    "Спам запрещен",
    "Порнография 18+ запрещена, но сливать порно наших врагов можно",
    "Ссылки на чат запрещено",
    "Слив владельца (Topyak) запрещено"
]

def get_rules_text():
    text = "Правила группы:\n"
    for i, rule in enumerate(group_rules_list, 1):
        text += f"{i}. {rule}\n"
    return text.strip()


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="ban", description="Забанить пользователя (в ответ)"),
        BotCommand(command="unban", description="Разбанить пользователя (в ответ)"),
        BotCommand(command="mute", description="Замутить (например: /mute 1 час)"),
        BotCommand(command="unmute", description="Размутить пользователя (в ответ)"),
        BotCommand(command="rules", description="Показать правила группы"),
        BotCommand(command="addrule", description="Добавить правило (только владелец)"),
        BotCommand(command="delrule", description="Удалить правило по номеру (только владелец)"),
    ]
    await bot.set_my_commands(main_menu_commands)


# Функция проверки, является ли пользователь создателем (владельцем) чата
async def is_owner(message: types.Message) -> bool:
    if message.chat.type == "private":
        return True
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status == "creator"
    except Exception:
        return False


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


# Добавление правила (только для владельца)
@dp.message(Command("addrule"))
async def cmd_add_rule(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Эта команда доступна только владельцу группы!")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Напиши правило после команды, например:\n`/addrule Не флудить капсом`", parse_mode="Markdown")
        return
    
    new_rule = args[1]
    group_rules_list.append(new_rule)
    await message.answer(f"✅ Правило добавлено владельцем!\n\n{get_rules_text()}")


# Удаление правила по номеру (только для владельца)
@dp.message(Command("delrule"))
async def cmd_del_rule(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Эта команда доступна только владельцу группы!")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].isdigit():
        await message.reply("Укажи номер правила для удаления, например:\n`/delrule 2`\n\nПосмотреть номера можно через /rules", parse_mode="Markdown")
        return

    index = int(args[1]) - 1
    if 0 <= index < len(group_rules_list):
        removed = group_rules_list.pop(index)
        await message.answer(f"🗑 Правило «{removed}» удалено!\n\n{get_rules_text()}")
    else:
        await message.reply("❌ Нет правила с таким номером! Проверь список через `/rules`.")


@dp.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Эта команда доступна только владельцу группы!")
        return
    if not message.reply_to_message:
        await message.reply("Эту команду нужно использовать в ответ на сообщение нарушителя!")
        return
    try:
        await bot.ban_chat_member(
            chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id
        )
        await message.answer(
            f"Пользователь {message.reply_to_message.from_user.full_name} забанен владельцем."
        )
    except Exception as e:
        await message.answer(f"Ошибка бана: {e}")


@dp.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Эта команда доступна только владельцу группы!")
        return
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


# Измененная команда мута с поддержкой времени
@dp.message(Command("mute"))
async def cmd_mute(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Эта команда доступна только владельцу группы!")
        return
    if not message.reply_to_message:
        await message.reply("Используйте в ответ на сообщение пользователя!")
        return
    
    args = message.text.split()
    duration_minutes = 5  # По умолчанию 5 минут, если время не указано
    time_text = "5 минут"

    if len(args) >= 2:
        try:
            amount = int(args[1])
            unit = args[2].lower() if len(args) > 2 else "мин"
            
            if "час" in unit or "ч" in unit:
                duration_minutes = amount * 60
                time_text = f"{amount} час(а)" if amount < 5 else f"{amount} часов"
            elif "д" in unit:
                duration_minutes = amount * 24 * 60
                time_text = f"{amount} день/дней"
            else:
                duration_minutes = amount
                time_text = f"{amount} минут(ы)"
        except ValueError:
            await message.reply("❌ Неверный формат времени! Пример:\n`/mute 1 час` или `/mute 30 минут`", parse_mode="Markdown")
            return

    try:
        until_date = datetime.now() + timedelta(minutes=duration_minutes)
        await message.chat.restrict(
            user_id=message.reply_to_message.from_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.answer(f"Пользователь {message.reply_to_message.from_user.full_name} замучен на {time_text}.")
    except Exception as e:
        await message.answer(f"Ошибка мута: {e}")


@dp.message(Command("unmute"))
async def cmd_unmute(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Эта команда доступна только владельцу группы!")
        return
    if not message.reply_to_message:
        await message.reply("Используйте в ответ на сообщение пользователя!")
        return
    try:
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
        await message.answer(f"Пользователь {message.reply_to_message.from_user.full_name} размучен.")
    except Exception as e:
        await message.answer(f"Ошибка размута: {e}")


async def main():
    await set_main_menu(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    
