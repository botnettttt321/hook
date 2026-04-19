import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.session.aiohttp import AiohttpSession
from datetime import datetime, timedelta

# --- НАСТРОЙКИ ---
TOKEN = '8208731009:AAFH8W2OQ0Cdi3CaNtinwMC48DfBW6Xpu2M'
ADMIN_ID = 8661495543
CHANNEL_ID = -1003946828032

# Настройка сессии через прокси (если нужен)
proxy_url = "http://fScyAU:zsNAfn@23.229.49.181:9126"
session = AiohttpSession(proxy=proxy_url)

# --- СОЗДАЕМ ОБЪЕКТЫ BOT И DISPATCHER ---
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

submissions = {}
last_submission = {}

# --- КЛАВИАТУРА АДМИНА ---
def admin_keyboard(submission_id: int):
    btn_accept = InlineKeyboardButton(text="Принять ✅", callback_data=f"accept_{submission_id}")
    btn_reject = InlineKeyboardButton(text="Отклонить ❌", callback_data=f"reject_{submission_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[btn_accept, btn_reject]])

# --- КОМАНДА /START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "🏫 Школа №2 г. Минска\n"
        "Официальный бот-предложка\n\n"
        "Привет! Здесь ты можешь предложить пост для нашего канала. 📩\n\n"
        "Что можно присылать?\n"
        "• Текст, фото или видео.\n"
        "• Твоя заявка уйдет на модерацию.\n\n"
        "⚠️ Ограничение: 1 пост в час."
    )
    await message.answer(welcome_text)

# --- ОБРАБОТКА ПРЕДЛОЖЕНИЙ (ТЕКСТ, ФОТО, ВИДЕО) ---
@dp.message(F.chat.type == "private")
async def handle_submission(message: types.Message):
    if message.text and message.text.startswith("/"):
        return

    user_id = message.from_user.id
    now = datetime.now()

    if user_id in last_submission and now - last_submission[user_id] < timedelta(hours=1):
        await message.reply("⏳ Ошибка: предлагать посты можно не чаще раза в час.")
        return

    submission_id = len(submissions) + 1
    submissions[submission_id] = message
    last_submission[user_id] = now

    name = message.from_user.full_name
    username = f"(@{message.from_user.username})" if message.from_user.username else ""
    admin_text = f"📩 Новый пост от: {name} {username}".strip()
    kb = admin_keyboard(submission_id)

    if message.photo:
        await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id,
                             caption=admin_text, reply_markup=kb)
    elif message.video:
        await bot.send_video(chat_id=ADMIN_ID, video=message.video.file_id,
                             caption=admin_text, reply_markup=kb)
    elif message.text:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text + "\n\n" + message.text,
                               reply_markup=kb)
    else:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=kb)

    await message.reply("✅ Ваш пост отправлен на модерацию!")

# --- ОБРАБОТКА КНОПОК АДМИНА ---
@dp.callback_query()
async def handle_admin_callback(callback: types.CallbackQuery):
    data = callback.data
    submission_id = int(data.split("_")[1])
    submission_msg = submissions.get(submission_id)

    if not submission_msg:
        await callback.answer("❌ Ошибка: сообщение не найдено")
        return

    if data.startswith("accept_"):
        await bot.send_message(submission_msg.chat.id, "✅ Ваш пост принят!")
        await bot.send_message(ADMIN_ID, f"Пост {submission_id} принят")

        # --- Отправка в канал ---
        caption_prefix = "📢 Пост из предложки:\n\n"
        if submission_msg.text:
            text_to_send = caption_prefix + submission_msg.text
            await bot.send_message(CHANNEL_ID, text_to_send)
        elif submission_msg.photo:
            caption = submission_msg.caption or ""
            await bot.send_photo(CHANNEL_ID, submission_msg.photo[-1].file_id,
                                 caption=caption_prefix + caption)
        elif submission_msg.video:
            caption = submission_msg.caption or ""
            await bot.send_video(CHANNEL_ID, submission_msg.video.file_id,
                                 caption=caption_prefix + caption)

    elif data.startswith("reject_"):
        await bot.send_message(submission_msg.chat.id, "❌ Ваш пост отклонён.")
        await bot.send_message(ADMIN_ID, f"Пост {submission_id} отклонён")

    await callback.answer()

# --- ЗАПУСК БОТА ---
async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())