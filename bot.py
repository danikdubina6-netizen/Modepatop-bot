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

# Словарь для хранения модераторов в формате {user_id: "Имя пользователя"}
group_moderators = {}


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="ban", description="Забанить пользователя (в ответ)"),
        BotCommand(command="unban", description="Разбанить пользователя (в ответ)"),
        BotCommand(command="mute", description="Замутить пользователя (в ответ)"),
        BotCommand(command="unmute", description="Размутить пользователя (в ответ)"),
        BotCommand(command="rules", description="Показать правила из описания"),
        BotCommand(command="addmod", description="Добавить модератора (в ответ)"),
        BotCommand(command="delmod", description="Убрать модератора (в ответ)"),
        BotCommand(command="mods", description="Список модераторов бота"),
    ]
    await bot.set_my_commands(main_menu_commands)


# Проверка, является ли пользователь владельцем чата
async def is_owner(message: types.Message) -> bool:
    if message.chat.type == "private":
        return True
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status == "creator"
    except Exception:
        return False


# Проверка: владелец или назначенный модератор
async def can_manage(message: types.Message) -> bool:
    if await is_owner(message):
        return True
    if message.from_user.id in group_moderators:
        return True
    return False


# ДОБАВИТЬ МОДЕРАТОРА
@dp.message(F.text.lower().regexp(r"^(/addmod(@\w+)?|добавить модератора)"))
async def add_moderator(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Только владелец группы может назначать модераторов!")
        return

    if not message.reply_to_message:
        await message.reply("❌ Сделай реплай на сообщение пользователя, которого хочешь сделать модератором!", parse_mode="Markdown")
        return

    target_user = message.reply_to_message.from_user
    group_moderators[target_user.id] = target_user.full_name
    await message.answer(f"✅ Пользователь {target_user.full_name} назначен модератором!")


# УБРАТЬ МОДЕРАТОРА
@dp.message(F.text.lower().regexp(r"^(/delmod(@\w+)?|убрать модератора)"))
async def remove_moderator(message: types.Message):
    if not await is_owner(message):
        await message.reply("⛔ Только владелец группы может снимать модераторов!")
        return

    if not message.reply_to_message:
        await message.reply("❌ Сделай реплай на сообщение модератора, которого хочешь разжаловать!", parse_mode="Markdown")
        return

    target_user = message.reply_to_message.from_user
    if target_user.id in group_moderators:
        del group_moderators[target_user.id]
        await message.answer(f"🗑 Пользователь {target_user.full_name} больше не модератор.")
    else:
        await message.answer(f"⚠️ Пользователь {target_user.full_name} не числился в модераторах.")


# СПИСОК АДМИНИСТРАТОРОВ / МОДЕРАТОРОВ БОТА
@dp.message(F.text.lower().regexp(r"^(/mods(@\w+)?|список администраторов|модераторы|админы)"))
async def list_moderators(message: types.Message):
    if not group_moderators:
        await message.answer("ℹ️ У этого бота пока нет назначенных модераторов.")
        return
    
    text = "🛡 **Список модераторов бота:**\n\n"
    for idx, (uid, name) in enumerate(group_moderators.items(), 1):
        text += f"{idx}. {name} (ID: `{uid}`)\n"
        
    await message.answer(text, parse_mode="Markdown")


# Приветствие новых участников с правилами из описания группы
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def welcome_user(event: types.ChatMemberUpdated):
    user = event.new_chat_member.user
    try:
        chat_info = await bot.get_chat(event.chat.id)
        rules_text = chat_info.description if chat_info.description else "Описание группы пока не заполнено."
        await event.chat.send_message(
            f"Привет, {user.full_name}!\n\n📋 **Правила группы:**\n{rules_text}",
            parse_mode="Markdown"
        )
    except Exception:
        await event.chat.send_message(f"Привет, {user.full_name}!")


# ПРАВИЛА (из описания группы)
@dp.message(F.text.lower().regexp(r"^(/rules(@\w+)?|правила|каталог правил)"))
async def text_rules(message: types.Message):
    if message.chat.type == "private":
        await message.answer("ℹ️ Эту команду лучше использовать в самой группе, чтобы увидеть её описание!")
        return
        
    try:
        chat_info = await bot.get_chat(message.chat.id)
        if chat_info.description:
            await message.answer(f"📋 **Правила группы:**\n\n{chat_info.description}", parse_mode="Markdown")
        else:
            await message.answer("⚠️ У этой группы еще не установлено описание с правилами!")
    except Exception as e:
        await message.answer(f"❌ Не удалось получить описание группы: {e}")


# БАН
@dp.message(F.text.lower().regexp(r"^(/ban(@\w+)?|бан)"))
async def text_ban(message: types.Message):
    if not await can_manage(message):
        await message.reply("⛔ У тебя нет прав на использование этой команды!")
        return

    if not message.reply_to_message:
        await message.reply("❌ Используй эту команду **в ответ на сообщение** нарушителя!", parse_mode="Markdown")
        return

    target_user = message.reply_to_message.from_user
    args = message.text.split()
    until_date = None
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
        if until_date:
            await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user.id, until_date=until_date)
        else:
            await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user.id)
            
        await message.answer(f"Пользователь {target_user.full_name} забанен {time_text}.")
    except Exception as e:
        await message.answer(f"Ошибка бана: {e}")


# РАЗБАН
@dp.message(F.text.lower().regexp(r"^(/unban(@\w+)?|разбан)"))
async def text_unban(message: types.Message):
    if not await can_manage(message):
        await message.reply("⛔ У тебя нет прав на использование этой команды!")
        return
    
    if not message.reply_to_message:
        await message.reply("❌ Используй команду в ответ на сообщение пользователя (`разбан`)!")
        return
    
    target_user = message.reply_to_message.from_user
    try:
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_user.id)
        await message.answer(f"Пользователь {target_user.full_name} разбанен.")
    except Exception as e:
        await message.answer(f"Ошибка разбана: {e}")


# МУТ
@dp.message(F.text.lower().regexp(r"^(/mute(@\w+)?|мут)"))
async def text_mute(message: types.Message):
    if not await can_manage(message):
        await message.reply("⛔ У тебя нет прав на использование этой команды!")
        return

    if not message.reply_to_message:
        await message.reply("❌ Используй эту команду **в ответ на сообщение** нарушителя!", parse_mode="Markdown")
        return
    
    target_user = message.reply_to_message.from_user
    args = message.text.split()
    until_date = None
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


# РАЗМУТ
@dp.message(F.text.lower().regexp(r"^(/unmute(@\w+)?|размут)"))
async def text_unmute(message: types.Message):
    if not await can_manage(message):
        await message.reply("⛔ У тебя нет прав на использование этой команды!")
        return

    if not message.reply_to_message:
        await message.reply("❌ Используй команду в ответ на сообщение пользователя (`размут`)!")
        return

    target_user = message.reply_to_message.from_user
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
        
