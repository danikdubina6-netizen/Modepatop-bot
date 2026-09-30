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
        BotCommand(command="ban", description="Забанить пользователя"),
        BotCommand(command="unban", description="Разбанить пользователя"),
        BotCommand(command="mute", description="Замутить пользователя"),
        BotCommand(command="unmute", description="Размутить пользователя"),
        BotCommand(command="rules", description="Показать правила группы"),
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


# Функция поиска пользователя (из реплая или по тексту/упоминанию)
async def get_target_user(message: types.Message):
    # 1. Если есть реплай на сообщение
    if message.reply_to_message:
        return message.reply_to_message.from_user
    
    # 2. Если есть упоминание через @username или сущности в тексте
    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention":
                return entity.user
            elif entity.type == "mention":
                # Достаем текст упоминания, например "@username"
                username = message.text[entity.offset:entity.offset + entity.length]
                # Попробуем найти через поиск (если бот видел пользователя) или через текст
                # В aiogram проще всего распарсить через аргументы, если указан юзернейм
                pass
                
    # 3. Попробуем найти по первому слову с собачкой `@` в тексте
    args = message.text.split()
    for arg in args:
        if arg.startswith("@"):
            username_clean = arg.lstrip("@")
            # Перебираем недавние сообщения или оставляем как текстовый поиск, 
            # но в Telegram API без базы данных по юзернейму напрямую забанить нельзя — нужен user_id.
            # Поэтому надежнее всего реплай или упоминание.
    return None


# Приветствие новых участников
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def welcome_user(event: types.ChatMemberUpdated):
    user = event.new_chat_member.user
    await event.chat.send_message(
        f"Привет, {user.full_name}!\n\n{get_rules_text()}"
    )


# Обработка команд и текста: ПРАВИЛА (/rules или просто "правила")
@dp.message(F.text.lower().in_(["/rules", "правила", "каталог правил"]))
async def text_rules(message: types.Message):
    await message.answer(get_rules_text())


# Добавление правила: /addrule или "добавить правило ТЕКСТ"
@dp.message(F.text.lower().startswith(("/addrule", "добавить правило")))
async def text_add_rule(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Эта функция доступна только владельцу группы!")
        return

    text_lower = message.text.lower()
    if text_lower.startswith("/addrule"):
        args = message.text.split(maxsplit=1)
    else:
        args = message.text.split(maxsplit=2) # на случай "добавить правило ТЕКСТ"
        args = [args[0], args[2]] if len(args) > 2 else [args[0]]

    if len(args) < 2:
        await message.reply("Напиши само правило после команды, например:\n`добавить правило Не флудить капсом`", parse_mode="Markdown")
        return
    
    new_rule = args[1]
    group_rules_list.append(new_rule)
    await message.answer(f"✅ Правило добавлено владельцем!\n\n{get_rules_text()}")


# Удаление правила: /delrule или "удалить правило НОМЕР"
@dp.message(F.text.lower().startswith(("/delrule", "удалить правило")))
async def text_del_rule(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Эта функция доступна только владельцу группы!")
        return

    # Достаем цифру из текста
    words = message.text.split()
    number_str = None
    for word in words:
        if word.isdigit():
            number_str = word
            break

    if not number_str:
        await message.reply("Укажи номер правила для удаления, например:\n`удалить правило 2`\n\nПосмотреть номера можно через `правила`", parse_mode="Markdown")
        return

    index = int(number_str) - 1
    if 0 <= index < len(group_rules_list):
        removed = group_rules_list.pop(index)
        await message.answer(f"🗑 Правило «{removed}» удалено!\n\n{get_rules_text()}")
    else:
        await message.reply("❌ Нет правила с таким номером! Проверь список через `правила`.")


# БАН (через /ban или слово "бан" с поддержкой времени и упоминания/реплая)
@dp.message(F.text.lower().startswith(("/ban", "бан")))
async def text_ban(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Эта команда доступна только владельцу группы!")
        return

    target_user = await get_target_user(message)
    if not target_user:
        await message.reply("Используй команду **в ответ на сообщение** нарушителя или **упомяни его** (например: `бан @user 1 час`)!", parse_mode="Markdown")
        return

    args = message.text.split()
    until_date = None
    time_text = "навсегда"

    # Ищем число и единицу измерения времени в тексте
    if len(args) >= 2:
        try:
            # Пробуем найти число среди аргументов
            for i, arg in enumerate(args):
                if arg.isdigit():
                    amount = int(arg)
                    unit = args[i+1].lower() if i+1 < len(args) else "мин"
                    
                    if "час" in unit or "ч" in unit:
                        duration_minutes = amount * 60
                        time_text = f"на {amount} час(а)" if amount < 5 else f"на {amount} часов"
                    elif "д" in unit:
                        duration_minutes = amount * 24 * 60
                        time_text = f"на {amount} день/дней"
                    else:
                        duration_minutes = amount
                        time_text = f"на {amount} минут(ы)"
                    
                    until_date = datetime.now() + timedelta(minutes=duration_minutes)
                    break
        except Exception:
            pass

    try:
        if until_date:
            await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user.id, until_date=until_date)
        else:
            await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user.id)
            
        await message.answer(f"Пользователь {target_user.full_name} забанен владельцем {time_text}.")
    except Exception as e:
        await message.answer(f"Ошибка бана: {e}")


# РАЗБАН (/unban или "разбан")
@dp.message(F.text.lower().startswith(("/unban", "разбан")))
async def text_unban(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Эта команда доступна только владельцу группы!")
        return
    
    target_user = await get_target_user(message)
    if not target_user:
        await message.reply("Используй в ответ на сообщение пользователя или упомяни его (`разбан @user`)!")
        return
    
    try:
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_user.id)
        await message.answer(f"Пользователь {target_user.full_name} разбанен.")
    except Exception as e:
        await message.answer(f"Ошибка разбана: {e}")


# МУТ (/mute или "мут" с поддержкой времени и упоминания/реплая)
@dp.message(F.text.lower().startswith(("/mute", "мут")))
async def text_mute(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Эта команда доступна только владельцу группы!")
        return

    target_user = await get_target_user(message)
    if not target_user:
        await message.reply("Используй команду **в ответ на сообщение** или **упомяни пользователя** (например: `мут @user 1 час`)!", parse_mode="Markdown")
        return
    
    args = message.text.split()
    until_date = None  # None = навсегда
    time_text = "навсегда"

    if len(args) >= 2:
        try:
            for i, arg in enumerate(args):
                if arg.isdigit():
                    amount = int(arg)
                    unit = args[i+1].lower() if i+1 < len(args) else "мин"
                    
                    if "час" in unit or "ч" in unit:
                        duration_minutes = amount * 60
                        time_text = f"на {amount} час(а)" if amount < 5 else f"на {amount} часов"
                    elif "д" in unit:
                        duration_minutes = amount * 24 * 60
                        time_text = f"на {amount} день/дней"
                    else:
                        duration_minutes = amount
                        time_text = f"на {amount} минут(ы)"
                        
                    until_date = datetime.now() + timedelta(minutes=duration_minutes)
                    break
        except Exception:
            pass

    try:
        await message.chat.restrict(
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.answer(f"Пользователь {target_user.full_name} замучен {time_text}.")
    except Exception as e:
        await message.answer(f"Ошибка мута: {e}")


# РАЗМУТ (/unmute или "размут")
@dp.message(F.text.lower().startswith(("/unmute", "размут")))
async def text_unmute(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Эта команда доступна только владельцу группы!")
        return

    target_user = await get_target_user(message)
    if not target_user:
        await message.reply("Используй в ответ на сообщение пользователя или упомяни его (`размут @user`)!")
        return

    try:
        await message.chat.restrict(
            user_id=target_user.id,
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
        await message.answer(f"Пользователь {target_user.full_name} размучен.")
    except Exception as e:
        await message.answer(f"Ошибка размута: {e}")


async def main():
    await set_main_menu(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    
