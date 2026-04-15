import time
import json
import requests
from aiogram import types, F, Dispatcher, Bot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.filters import Command
from config import GOOGLE_URL, WEB_APP_URL, BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def get_main_menu():
    buttons = [
        [KeyboardButton(text="🏥 Обрати аналізи", web_app=WebAppInfo(url=WEB_APP_URL))],  # ✅ WEB_APP_URL
        [KeyboardButton(text="📱 Поділитися контактом", request_contact=True)],
        [KeyboardButton(text="📋 Мої замовлення"), KeyboardButton(text="🕒 Графік роботи")],
        [KeyboardButton(text="👩‍💻 Зв'язатися з адміністратором")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@dp.message(F.text == "📋 Мої замовлення")
async def show_my_orders(message: types.Message):
    username = message.from_user.username
    if not username:
        await message.answer("⚠️ Для перегляду замовлень у вас має бути встановлено @username в налаштуваннях Telegram.")
        return

    await message.answer("🔍 Шукаю ваші замовлення, зачекайте...")

    try:
        # ✅ ДОДАН TIMEOUT
        response = requests.get(f"{GOOGLE_URL}?username={username}", timeout=10)
        
        if response.status_code != 200:
            await message.answer("❌ Не вдалося отримати дані з бази.")
            return

        # ✅ ОБРОБКА JSON ПОМИЛОК
        try:
            orders_data = response.json()
        except json.JSONDecodeError:
            await message.answer("❌ Помилка парсингу даних з бази.")
            return
        
        if not orders_data or len(orders_data) == 0:
            await message.answer("📭 У вас поки немає замовлень.")
            return

        text = "📂 **Ваші останні замовлення:**\n\n"
        for order in orders_data:
            # ✅ БЕЗПЕЧНИЙ ДОСТУП З .get()
            text += (
                f"🔸 **№{order.get('number', 'N/A')}** ({order.get('date', 'N/A')})\n"
                f"🧪 {order.get('tests', 'N/A')}\n"
                f"💰 Сума: {order.get('total', 'N/A')} грн\n"
                f"⚙️ Статус: {order.get('status', 'N/A')}\n"
                f"--------------------------\n"
            )
        await message.answer(text, parse_mode="Markdown")
        
    except requests.RequestException as e:
        # ✅ ОБРОБКА МЕРЕЖЕВИХ ПОМИЛОК
        print(f"Network error: {e}")
        await message.answer("❌ Помилка мережи. Спробуйте пізніше.")
    except Exception as e:
        print(f"Error fetching orders: {e}")
        await message.answer("⚠️ Помилка з��'язку з базою даних.")


@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    try:
        # Розпаковуємо дані
        raw_data = message.web_app_data.data
        order = json.loads(raw_data)
        
        # ГЕНЕРУЄМО НОМЕР ЗАМОВЛЕННЯ
        order_number = f"ORD-{int(time.time())}"
        
        # Дістаємо дані БЕЗПЕЧНО (через .get)
        patient = order.get('patient', {})
        p_name = patient.get('name', 'Не вказано')
        p_dob = patient.get('dob', 'Не вказано')
        p_gender = patient.get('gender', 'Не вказано')
        p_phone = patient.get('phone', 'Не вказано')
        
        # Отримуємо назви та ID
        analysis_ids = order.get('analysis_ids', '—')
        analysis_names = order.get('analysis_names', '—')
        total_price = order.get('total_price', 0)
        
        # Дані для Google
        data_for_google = {
            "order_number": order_number,
            "p_name": p_name,
            "p_dob": p_dob,
            "p_gender": p_gender,
            "p_phone": p_phone,
            "analysis_ids": analysis_ids,
            "analysis_names": analysis_names,
            "total_price": total_price,
            "username": message.from_user.username or "NoName"
        }

        # ✅ ОБРОБКА МЕРЕЖЕВИХ ПОМИЛОК
        try:
            response = requests.post(GOOGLE_URL, json=data_for_google, timeout=10)
        except requests.RequestException as e:
            print(f"Network error: {e}")
            await message.answer("❌ Помилка надсилання даних. Спробуйте пізніше.")
            return
        
        # ✅ ПЕРЕВІРКА ОБОХ СТАТУСІВ
        if response.status_code in (200, 201):
            text = (
                f"✅ **Замовлення №{order_number} прийнято!**\n\n"
                f"📋 **Аналізи:**\n{analysis_names}\n\n"
                f"💰 **Сума:** {total_price} грн\n"
                f"📍 Ми чекаємо на вас!"
            )
            await message.answer(text, parse_mode="Markdown")
        else:
            print(f"Google Script error: {response.status_code} - {response.text}")
            await message.answer("❌ Помилка збереження в БД. Зверніться до адміністратора.")

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        await message.answer("⚠️ Помилка обробки даних. Перевірте заповнення форми.")
    except Exception as e:
        print(f"Error: {e}") 
        await message.answer("⚠️ Помилка обробки даних. Перевірте заповнення форми.")