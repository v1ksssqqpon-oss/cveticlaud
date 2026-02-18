import asyncio
import json
import logging
import os
import time

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ═══════════════════════════════════════════
#  ⚙️  НАСТРОЙКИ — ПРОВЕРЬ ДАННЫЕ
# ═══════════════════════════════════════════
BOT_TOKEN  = "8260722962:AAFxlXEhn0A9Y22LulZX19RY1Napt9IJZ8s"
WEBAPP_URL = "https://v1ksssqqpon-oss.github.io/cveticlaud/"
ADMIN_IDS  = [1655167987]  # Твой ID
DB_PATH    = "products.json" 
# ═══════════════════════════════════════════

logging.basicConfig(level=logging.INFO)

# Инициализация бота (Фикс для aiogram 3.7+)
bot = Bot(
    token=BOT_TOKEN, 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

# Состояния для добавления товара
class AddProduct(StatesGroup):
    waiting_for_photo = State()
    waiting_for_name = State()
    waiting_for_price = State()

# ───────────────────────────────────────────
#  РАБОТА С БАЗОЙ ТОВАРОВ (JSON)
# ───────────────────────────────────────────
def load_products():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_product(product_data):
    products = load_products()
    products.append(product_data)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

def delete_product_by_id(p_id):
    products = load_products()
    new_products = [p for p in products if str(p['id']) != str(p_id)]
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(new_products, f, ensure_ascii=False, indent=4)

# ───────────────────────────────────────────
#  АДМИН-ПАНЕЛЬ (СТРОГО ДЛЯ ADMIN_IDS)
# ───────────────────────────────────────────

@dp.message(Command("admin"), F.from_user.id.in_(ADMIN_IDS))
async def admin_menu(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить букет", callback_query_data="add_item")],
        [InlineKeyboardButton(text="🗑 Удалить букет", callback_query_data="list_del")]
    ])
    await message.answer("🛠 <b>Панель управления BloomGo</b>\nВыберите действие:", reply_markup=kb)

# FSM процесс добавления
@dp.callback_query(F.data == "add_item", F.from_user.id.in_(ADMIN_IDS))
async def start_add(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("1️⃣ Пришлите <b>ФОТО</b> букета:")
    await state.set_state(AddProduct.waiting_for_photo)
    await callback.answer()

@dp.message(AddProduct.waiting_for_photo, F.photo, F.from_user.id.in_(ADMIN_IDS))
async def add_photo(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(photo=file_id)
    await message.answer("2️⃣ Введите <b>НАЗВАНИЕ</b>:")
    await state.set_state(AddProduct.waiting_for_name)

@dp.message(AddProduct.waiting_for_name, F.from_user.id.in_(ADMIN_IDS))
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("3️⃣ Введите <b>ЦЕНУ</b> (число):")
    await state.set_state(AddProduct.waiting_for_price)

@dp.message(AddProduct.waiting_for_price, F.from_user.id.in_(ADMIN_IDS))
async def add_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Ошибка! Введите цену только цифрами.")
    
    data = await state.get_data()
    new_item = {
        "id": int(time.time()),
        "name": data['name'],
        "price": int(message.text),
        "photo": data['photo']
    }
    save_product(new_item)
    await message.answer(f"✅ Товар <b>{data['name']}</b> успешно сохранен!")
    await state.clear()

# Удаление товара
@dp.callback_query(F.data == "list_del", F.from_user.id.in_(ADMIN_IDS))
async def list_del(callback: CallbackQuery):
    products = load_products()
    if not products:
        return await callback.message.answer("База товаров пуста.")
    
    for p in products:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Удалить", callback_query_data=f"del_{p['id']}")]
        ])
        await callback.message.answer_photo(p['photo'], caption=f"ID: {p['id']}\n{p['name']} — {p['price']}₽", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("del_"), F.from_user.id.in_(ADMIN_IDS))
async def confirm_del(callback: CallbackQuery):
    p_id = callback.data.split("_")[1]
    delete_product_by_id(p_id)
    await callback.message.delete()
    await callback.answer("Удалено!")

# ───────────────────────────────────────────
#  КЛИЕНТСКАЯ ЛОГИКА (ИЗ ОРИГИНАЛА)
# ───────────────────────────────────────────

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🌸 Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True
    )
    await message.answer(
        f"<b>Привет, {message.from_user.first_name}!</b> 🌸\n\n"
        "Добро пожаловать в BloomGo. Здесь вы найдете лучшие цветы в городе.",
        reply_markup=kb
    )

@dp.message(F.web_app_data)
async def handle_order(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        items = data.get("items", [])
        total = data.get("totalPrice", 0)
        user_info = data.get("user", {})
        order_id = int(message.message_id)
        
        items_text = "\n".join([f"• {i['name']} ({i['price']}₽)" for i in items])
        admin_text = (
            f"🔔 <b>НОВЫЙ ЗАКАЗ #{order_id}</b>\n\n"
            f"👤 Клиент: {user_info.get('name', 'Не указано')}\n"
            f"📞 Телефон: {user_info.get('phone', 'Не указано')}\n"
            f"📍 Адрес: {user_info.get('address', 'Не указано')}\n\n"
            f"🛒 Товары:\n{items_text}\n\n"
            f"💰 Итого: <b>{total}₽</b>"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_query_data=f"conf_{order_id}_{message.from_user.id}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_query_data=f"canc_{order_id}_{message.from_user.id}")]
        ])

        for admin_id in ADMIN_IDS:
            await bot.send_message(admin_id, admin_text, reply_markup=kb)

        await message.answer("🌸 <b>Ваш заказ отправлен!</b>\nМенеджер свяжется с вами в ближайшее время.")
    except Exception as e:
        logging.error(f"Error: {e}")

# Обработка статусов заказов (Confirm / Cancel / Deliver)
@dp.callback_query(F.data.startswith("conf_"))
async def cb_confirm(callback: CallbackQuery):
    parts = callback.data.split("_")
    order_id, u_id = parts[1], parts[2]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚚 Передать курьеру", callback_query_data=f"deliver_{order_id}_{u_id}")]
    ])
    
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.message.answer(f"✅ Заказ #{order_id} подтвержден!")
    await bot.send_message(u_id, f"✅ Ваш заказ #{order_id} подтвержден! Мы уже начали его собирать. 🌸")

@dp.callback_query(F.data.startswith("canc_"))
async def cb_cancel(callback: CallbackQuery):
    parts = callback.data.split("_")
    order_id, u_id = parts[1], parts[2]
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"❌ Заказ #{order_id} отменен.")
    await bot.send_message(u_id, f"😔 К сожалению, ваш заказ #{order_id} был отменен.")

@dp.callback_query(F.data.startswith("deliver_"))
async def cb_deliver(callback: CallbackQuery):
    parts = callback.data.split("_")
    order_id, u_id = parts[1], parts[2]
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"🚚 Заказ #{order_id} в доставке!")
    await bot.send_message(u_id, f"🚚 <b>Ваш заказ #{order_id} в пути!</b>\nОжидайте курьера в ближайшее время. 🌸")

@dp.message()
async def fallback(message: types.Message):
    await message.answer("Пожалуйста, используйте меню или команду /start")

# ───────────────────────────────────────────
async def main():
    print("🚀 BloomGo Bot запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
