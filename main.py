import time
import json
import requests
import asyncio
import logging
from datetime import datetime
from aiogram import types, F, Dispatcher, Bot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.filters import Command
from config import GOOGLE_URL, WEB_APP_URL, BOT_TOKEN

# ✅ НАЛАШТУВАННЯ ЛОГУВАННЯ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 📱 Словник для зберігання номерів телефонів користувачів
user_phones = {}
# 📋 Словник для зберігання статусу отримання контакту
user_contact_status = {}


def get_main_menu():
    """Головне меню бота"""
    buttons = [
        [KeyboardButton(text="🏥 Обрати дослідження", web_app=WebAppInfo(url=WEB_APP_URL))],
        [KeyboardButton(text="📋 Мої замовлення"), KeyboardButton(text="🕒 Графік роботи")],
        [KeyboardButton(text="👩‍💻 Адміністратор"), KeyboardButton(text="📝 Оформити звернення")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_contact_menu():
    """Меню для запиту контакту"""
    buttons = [
        [KeyboardButton(text="✅ Поділитися контактом", request_contact=True)],
        [KeyboardButton(text="❌ Продовжити без контакту")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start - привіт користувача"""
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name or message.from_user.username or "Друже"
        
        logger.info(f"User {user_id} ({user_name}) started bot")
        
        # ✅ ПЕРЕВІРЯЄМО ЧИ МАЄМО УЖЕ НОМЕР
        if user_id in user_phones:
            logger.info(f"User {user_id} has phone: {user_phones[user_id]}")
            await message.answer(
                f"👋 З поверненням, {user_name}!\n\n"
                f"🏥 **CentroLab** - якісні лабораторні дослідження\n\n"
                "Оберіть дію:",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
        else:
            # ✅ ЗАПИТУЄМО КОНТАКТ
            await message.answer(
                f"👋 Вітаємо, {user_name}!\n\n"
                f"🏥 **CentroLab** - якісні лабораторні дослідження\n\n"
                "🔐 Щоб прискорити оформлення замовлення, поділіться контактом (опціонально):",
                reply_markup=get_contact_menu(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Error in cmd_start: {str(e)}", exc_info=True)
        await message.answer("⚠️ Помилка при запуску. Спробуйте ще раз.")


@dp.message(F.contact)
async def handle_contact(message: types.Message):
    """Обробка поділеного контакту"""
    try:
        user_id = message.from_user.id
        phone = message.contact.phone_number
        
        # ✅ ОЧИЩУЄМО НОМЕР
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # ✅ ЗБЕРІГАЄМО НОМЕР
        user_phones[user_id] = phone
        user_contact_status[user_id] = 'provided'
        
        logger.info(f"User {user_id} shared phone: {phone}")
        
        await message.answer(
            f"✅ Спасибі! Номер **{phone}** збережено.\n\n"
            "Тепер можете оформляти замовлення 👇",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_contact: {str(e)}", exc_info=True)
        await message.answer("⚠️ Помилка при обробці контакту.")


@dp.message(F.text == "❌ Продовжити без контакту")
async def skip_contact(message: types.Message):
    """Користувач вибрав не ділитися контактом"""
    try:
        user_id = message.from_user.id
        user_contact_status[user_id] = 'declined'
        
        logger.info(f"User {user_id} declined sharing contact")
        
        await message.answer(
            "Без проблем! Номер телефону можна буде ввести при оформленні замовлення.\n\n"
            "Оберіть дію:",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in skip_contact: {str(e)}", exc_info=True)
        await message.answer("⚠️ Помилка.")


@dp.message(F.text == "🕒 Графік роботи")
async def show_schedule(message: types.Message):
    """Показати графік роботи"""
    try:
        logger.info(f"User {message.from_user.id} requested schedule")
        
        await message.answer(
            "🕒 **Графік роботи CentroLab:**\n\n"
            "📅 Понеділок - П'ятниця: 08:00 - 18:00\n"
            "📅 Субота: 09:00 - 15:00\n"
            "📅 Неділя: Вихідний\n\n"
            "📍 **Адреса:** вул. Прикладна, 42, Київ\n"
            "☎️ **Телефон:** +380 (68) 123-45-67",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_schedule: {str(e)}", exc_info=True)
        await message.answer("⚠️ Помилка при отриманні графіку.")


@dp.message(F.text == "👩‍💻 Адміністратор")
async def contact_admin(message: types.Message):
    """Контактна інформація адміна"""
    try:
        logger.info(f"User {message.from_user.id} requested admin contact")
        
        await message.answer(
            "👩‍💻 **Контактна інформація:**\n\n"
            "☎️ Телефон: **+380 (68) 123-45-67**\n"
            "📧 Email: **admin@centrolab.ua**\n"
            "💬 Telegram: **@centrolab_support**\n"
            "🕐 Час роботи: 08:00 - 18:00 (Пн-Пт)\n\n"
            "⏰ Ми відповідаємо протягом 30 хвилин",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in contact_admin: {str(e)}", exc_info=True)
        await message.answer("⚠️ Помилка при отриманні контактів адміна.")


@dp.message(F.text == "📝 Оформити звернення")
async def submit_appeal(message: types.Message):
    """Оформлення звернення"""
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name or message.from_user.username or "Користувач"
        
        logger.info(f"User {user_id} ({user_name}) wants to submit appeal")
        
        await message.answer(
            "📝 **Оформлення звернення**\n\n"
            "🔜 Функція знаходиться у розробці.\n\n"
            "Поки що напишіть свої запитання в чат адміністратору: @centrolab_support\n\n"
            "Дякуємо за розуміння! 🙏",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in submit_appeal: {str(e)}", exc_info=True)
        await message.answer("⚠️ Помилка при оформленні звернення.")


@dp.message(F.text == "📋 Мої замовлення")
async def show_my_orders(message: types.Message):
    """Показати замовлення користувача"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        
        if not username:
            logger.warning(f"User {user_id} has no username set")
            await message.answer(
                "⚠️ Для перегляду замовлень встановіть @username в Telegram!\n\n"
                "**Як це зробити:**\n"
                "1. Відкрийте Налаштування\n"
                "2. Перейдіть у 'Конфіденційність'\n"
                "3. Виберіть 'Ім'я користувача'\n"
                "4. Встановіть своє ім'я\n\n"
                "Потім спробуйте ще раз.",
                reply_markup=get_main_menu()
            )
            return

        logger.info(f"User {user_id} ({username}) requested orders list")
        await message.answer("🔍 Шукаю ваші замовлення...")

        try:
            response = requests.get(f"{GOOGLE_URL}?username={username}", timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Google Sheets error: {response.status_code}")
                await message.answer("❌ Помилка отримання даних з бази.")
                return

            try:
                orders_data = response.json()
            except json.JSONDecodeError as je:
                logger.error(f"JSON decode error: {str(je)}")
                await message.answer("❌ Помилка парсингу даних.")
                return
            
            if not orders_data or len(orders_data) == 0:
                logger.info(f"No orders found for user {username}")
                await message.answer(
                    "📭 У вас поки немає замовлень.\n\n"
                    "Натисніть '🏥 Обрати дослідження' щоб оформити перше замовлення! 👇",
                    reply_markup=get_main_menu()
                )
                return

            text = "📂 **Ваші замовлення:**\n\n"
            for i, order in enumerate(orders_data, 1):
                payment_label = "🏢 У відділенні" if order.get('payment_method') == 'office' else "💳 Онлайн"
                
                text += (
                    f"{i}. **№{order.get('number', 'N/A')}**\n"
                    f"   📅 {order.get('date', 'N/A')}\n"
                    f"   👤 {order.get('name', 'N/A')}\n"
                    f"   🧪 {order.get('tests', 'N/A')}\n"
                    f"   💰 {order.get('total', 'N/A')} грн\n"
                    f"   💳 Оплата: {payment_label}\n"
                    f"   ⚙️ Статус: {order.get('status', 'N/A')}\n\n"
                )
            
            logger.info(f"Found {len(orders_data)} orders for user {username}")
            await message.answer(text, parse_mode="Markdown", reply_markup=get_main_menu())
            
        except requests.RequestException as re:
            logger.error(f"Network error: {str(re)}")
            await message.answer("❌ Помилка мережи. Спробуйте пізніше.")
        except Exception as e:
            logger.error(f"Error fetching orders: {str(e)}", exc_info=True)
            await message.answer("⚠️ Помилка зв'язку з БД.")
            
    except Exception as e:
        logger.error(f"Error in show_my_orders: {str(e)}", exc_info=True)
        await message.answer("⚠️ Помилка при отриманні замовлень.")


@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    """Обробка замовлення з WebApp"""
    try:
        user_id = message.from_user.id
        logger.info(f"User {user_id} submitted order from WebApp")
        
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
        
        logger.info(f"Order {order_number}: {p_name}, {len(analysis_ids.split(','))} tests, {total_price}₴")
        
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
        except requests.RequestException as re:
            logger.error(f"Network error sending to Google Sheets: {str(re)}")
            await message.answer("❌ Помилка надсилання даних. Спробуйте пізніше.")
            return
        
        # ПЕРЕВІРЯЄМО ВІДПОВІДЬ
        if response.status_code in (200, 201):
            logger.info(f"Order {order_number} successfully saved to Google Sheets")
            
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
            logger.error(f"Google Sheets error: {response.status_code} - {response.text}")
            await message.answer(
                "❌ Помилка збереження в БД. Зверніться до адміністратора.",
                reply_markup=get_main_menu()
            )

    except json.JSONDecodeError as je:
        logger.error(f"JSON decode error: {str(je)}", exc_info=True)
        await message.answer(
            "⚠️ Помилка обробки даних. Перевірте заповнення форми.",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logger.error(f"Error in handle_web_app_data: {str(e)}", exc_info=True)
        await message.answer(
            "⚠️ Помилка обробки даних.",
            reply_markup=get_main_menu()
        )


@dp.message()
async def echo(message: types.Message):
    """Обробка усіх інших повідомлень"""
    try:
        logger.info(f"User {message.from_user.id} sent unknown command: {message.text}")
        await message.answer(
            "Вибачте, я не розумію цю команду.\n\n"
            "Використовуйте меню нижче 👇",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logger.error(f"Error in echo: {str(e)}", exc_info=True)


# ✅ ЗАПУСК БОТА З ОБРОБКОЮ ПОМИЛОК
async def main():
    """Головна функція запуску бота"""
    logger.info("🤖 Bot starting...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Critical error: {str(e)}", exc_info=True)
        # ✅ АВТОМАТИЧНИЙ ПЕРЕЗАПУСК
        logger.info("Attempting restart in 10 seconds...")
        await asyncio.sleep(10)
        await main()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print("⚠️ Fatal error - check bot.log for details")