import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo
import requests
from dotenv import load_dotenv

# Завантажуємо секрети з .env
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_URL = os.getenv("GOOGLE_SCRIPT_URL")
WEB_APP_URL = os.getenv("WEB_APP_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🏥 Обрати аналізи", web_app=WebAppInfo(url=WEB_APP_URL))]
        ],
        resize_keyboard=True
    )
    await message.answer(f"Вітаємо у медичній лабораторії, {message.from_user.first_name}!\nНатисніть кнопку нижче, щоб оформити замовлення.", reply_markup=markup)

@dp.message(F.web_app_data)
async def handle_data(message: types.Message):
    # Отримуємо дані з вашої форми
    user_order = message.web_app_data.data
    
    # Готуємо дані для відправки в Google Таблицю
    data_for_google = {
        "user_id": message.from_user.id,
        "user_name": message.from_user.full_name,
        "order": user_order
    }

    try:
        response = requests.post(GOOGLE_URL, json=data_for_google)
        if response.status_code == 200:
            await message.answer("✅ Дякуємо! Ваше замовлення прийнято. Ми зв'яжемося з вами найближчим часом.")
        else:
            await message.answer("❌ Сталася помилка при збереженні. Спробуйте пізніше.")
    except Exception as e:
        await message.answer(f"⚠️ Помилка зв'язку: {e}")

async def main():
    print("🚀 Бот запущений і готовий до роботи...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())