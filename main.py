import time
import json
import requests
import asyncio
from aiogram import types, F, Dispatcher, Bot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.filters import Command
from config import GOOGLE_URL, WEB_APP_URL, BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_phones = {}


def get_main_menu():
    """Головне меню"""
    buttons = [
        [KeyboardButton(text="🏥 Обрати аналізи", web_app=WebAppInfo(url=WEB_APP_URL))],
        [KeyboardButton(text="📱 Поділитися контактом", request_contact=True)],
        [KeyboardButton(text="📋 Мої замовлення"), KeyboardButton(text="🕒 Графік роботи")],
        [KeyboardButton(text="👩‍💻 Зв'язатися з адміністратором")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start - привіт користувача"""
    user_name = message.from_user.first_name or message.from_user.username or "Користувач"
    await message.answer(
        f"👋 Вітаємо, {user_name} у CentroLab!\n\n"
        "Оберіть дію:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )


@dp.message(F.contact)
async def handle_contact(message: types.Message):
    """Обробка поділеного контакту"""
    user_id = message.from_user.id
    phone = message.contact.phone_number
    user_phones[user_id] = phone
    
    await message.answer(
       # f"✅ Дякуємо! Номер **{phone}** збережено.",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )


@dp.message(F.text == "🕒 Графік роботи")
async def show_schedule(message: types.Message):
    """Показати графік роботи"""
    await message.answer(
        "🕒 **Графік роботи CentroLab:**\n\n"
        "📅 Понеділок - П'ятниця: 08:00 - 18:00\n"
        "📅 Субота: 09:00 - 15:00\n"
        "📅 Неділя: Вихідний\n\n"
        "☎️ Телефон: +380 (68) 123-45-67",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )


@dp.message(F.text == "👩‍💻 Зв'язатися з адміністратором")
async def contact_admin(message: types.Message):
    """Контактна інформація адміна"""
    await message.answer(
        "👩‍💻 **Контактна інформація:**\n\n"
        "☎️ Телефон: **+380 (68) 123-45-67**\n"
        "📧 Email: **admin@centrolab.ua**\n"
        "💬 Telegram: **@centrolab_support**\n\n"
        "⏰ Доступні в робочі часи",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )


@dp.message(F.text == "📋 Мої замовлення")
async def show_my_orders(message: types.Message):
    """Показати замовлення користувача"""
    username = message.from_user.username
    if not username:
        await message.answer(
            "⚠️ Для перегляду замовлень встановіть @username в Telegram!\n\n"
            "Налаштування → Ім'я користувача",
            reply_markup=get_main_menu()
        )
        return

    await message.answer("🔍 Шукаю ваші замовлення...")

    try:
        response = requests.get(f"{GOOGLE_URL}?username={username}", timeout=10)
        
        if response.status_code != 200:
            await message.answer("❌ Помилка отримання даних з бази.")
            return

        try:
            orders_data = response.json()
        except json.JSONDecodeError:
            await message.answer("❌ Помилка парсингу даних.")
            return
        
        if not orders_data or len(orders_data) == 0:
            await message.answer(
                "📭 У вас поки немає замовлень.\n\n"
                "Натисніть '🏥 Обрати аналізи' щоб оформити замовлення! 👇",
                reply_markup=get_main_menu()
            )
            return

        text = "📂 **Ваші замовлення:**\n\n"
        for i, order in enumerate(orders_data, 1):
            payment_label = "🏢 У відділенні" if order.get('payment_method') == 'office' else "💳 Онлайн"
            
            text += (
                f"{i}. **№{order.get('number', 'N/A')}**\n"
                f"   📅 {order.get('date', 'N/A')}\n"
                f"   🧪 {order.get('tests', 'N/A')}\n"
                f"   💰 {order.get('total', 'N/A')} грн\n"
                f"   💳 {payment_label}\n"
                f"   ⚙️ {order.get('status', 'N/A')}\n\n"
            )
        
        await message.answer(text, parse_mode="Markdown", reply_markup=get_main_menu())
        
    except requests.RequestException as e:
        print(f"Network error: {e}")
        await message.answer("❌ Помилка мережи. Спробуйте пізніше.")
    except Exception as e:
        print(f"Error fetching orders: {e}")
        await message.answer("⚠️ Помилка зв'язку з БД.")


@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    """Обробка замовлення з WebApp"""
    try:
        raw_data = message.web_app_data.data
        order = json.loads(raw_data)
        
        # ГЕНЕРУЄМО НОМЕР ЗАМОВЛЕННЯ
        order_number = f"ORD-{int(time.time())}"
        
        # ВИТЯГАЄМО ДАНІ ПАЦІЄНТА
        patient = order.get('patient', {})
        p_name = patient.get('name', 'Не вказано')
        p_dob = patient.get('dob', 'Не вказано')
        p_gender = patient.get('gender', 'Не вказано')
        p_phone = patient.get('phone', '')
        
        # ВИТЯГАЄМО ДОСЛІДЖЕННЯ
        analysis_ids = order.get('analysis_ids', '—')
        analysis_names = order.get('analysis_names', '—')
        total_price = order.get('total_price', 0)
        payment_method = order.get('payment_method', 'office')
        
        # ФОРМУЄМО ДАНІ ДЛЯ GOOGLE SHEETS
        data_for_google = {
            "order_number": order_number,
            "p_name": p_name,
            "p_dob": p_dob,
            "p_gender": p_gender,
            "p_phone": p_phone,
            "analysis_ids": analysis_ids,
            "analysis_names": analysis_names,
            "total_price": total_price,
            "payment_method": payment_method,
            "username": message.from_user.username or "NoName"
        }

        # НАДСИЛАЄМО В GOOGLE SHEETS
        try:
            response = requests.post(GOOGLE_URL, json=data_for_google, timeout=10)
        except requests.RequestException as e:
            print(f"Network error: {e}")
            await message.answer("❌ Помилка надсилання даних. Спробуйте пізніше.")
            return
        
        # ПЕРЕВІРЯЄМО ВІДПОВІДЬ
        if response.status_code in (200, 201):
            # ФОРМУЄМО ПОВІДОМЛЕННЯ ДЛЯ КОРИСТУВАЧА
            text = (
                f"✅ **Замовлення №{order_number} успішно оформлено!**\n\n"
                f"👤 **Дані пацієнта:**\n"
                f"• ПІБ: {p_name}\n"
                f"• Дата народження: {p_dob}\n"
                f"• Стать: {p_gender}\n"
                f"• Телефон: {p_phone if p_phone else '—'}\n\n"
                f"🧪 **Обрані дослідження:**\n{analysis_names}\n\n"
                f"💰 **Сума:** {total_price} грн\n"
                f"💳 **Спосіб оплати:** {'🏢 У відділенні' if payment_method == 'office' else '💳 Онлайн'}\n\n"
                f"📍 Ми чекаємо на вас у лабораторії!"
            )
            await message.answer(text, parse_mode="Markdown", reply_markup=get_main_menu())
        else:
            print(f"Google Script error: {response.status_code} - {response.text}")
            await message.answer(
                "❌ Помилка збереження в БД. Зверніться до адміністратора.",
                reply_markup=get_main_menu()
            )

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        await message.answer(
            "⚠️ Помилка обробки даних. Перевірте заповнення форми.",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        print(f"Error: {e}") 
        await message.answer(
            "⚠️ Помилка обробки даних.",
            reply_markup=get_main_menu()
        )


@dp.message()
async def echo(message: types.Message):
    """Обробка усіх інших повідомлень"""
    await message.answer(
        "Вибачте, я не розумію цю команду.\n\n"
        "Використовуйте меню нижче 👇",
        reply_markup=get_main_menu()
    )


# ЗАПУСК БОТА
async def main():
    print("🤖 Бот запускається...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Бот зупинений користувачем")