"""
╔══════════════════════════════════════════════╗
║          🌸 BloomGo — Telegram Bot           ║
║                                              ║
║  Установка:  pip install aiogram aiohttp     ║
║  Запуск:     python bloomgo_bot.py           ║
╚══════════════════════════════════════════════╝

ПЕРЕД ЗАПУСКОМ замените 3 строки:
  BOT_TOKEN  — токен от @BotFather
  WEBAPP_URL — ссылка с Netlify
  ADMIN_IDS  — ваш Telegram ID (узнать у @userinfobot)
"""

import asyncio
import json
import logging

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

# ═══════════════════════════════════════════
#  ⚙️  НАСТРОЙКИ — ЗАМЕНИТЕ НА СВОИ
# ═══════════════════════════════════════════

BOT_TOKEN  = "8260722962:AAFxlXEhn0A9Y22LulZX19RY1Napt9IJZ8s"
WEBAPP_URL = "https://v1ksssqqpon-oss.github.io/cveticlaud/"
ADMIN_IDS  = [1655167987]   # Ваш Telegram ID

# ═══════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp  = Dispatcher()


# ───────────────────────────────────────────
#  /start
# ───────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    name = message.from_user.first_name or "Гость"

    kb = ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(
                text="🌸 Открыть магазин",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]],
        resize_keyboard=True
    )

    await message.answer(
        f"Привет, <b>{name}</b>! 🌸\n\n"
        "Добро пожаловать в <b>BloomGo</b> — свежие цветы "
        "с доставкой за 60 минут.\n\n"
        "👇 Нажмите кнопку, чтобы выбрать букет:",
        reply_markup=kb
    )


# ───────────────────────────────────────────
#  /help
# ───────────────────────────────────────────
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🌸 <b>BloomGo — команды</b>\n\n"
        "/start — открыть магазин\n"
        "/orders — мои заказы\n"
        "/help — эта справка\n\n"
        "По любым вопросам — пишите нам прямо здесь!"
    )


# ───────────────────────────────────────────
#  /orders — история заказов пользователя
# ───────────────────────────────────────────
@dp.message(Command("orders"))
async def cmd_orders(message: types.Message):
    # В реальном проекте здесь запрос к базе данных
    await message.answer(
        "📦 <b>Ваши заказы</b>\n\n"
        "🚚 <b>#BG-4821</b> — Роскошь роз × 1\n"
        "    <i>В пути · прибудет в 14:30</i>\n\n"
        "✅ <b>#BG-4815</b> — Пионы мечты × 1\n"
        "    <i>Доставлен 15 февраля</i>"
    )


# ───────────────────────────────────────────
#  /admin — панель администратора
# ───────────────────────────────────────────
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к этой команде.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="👨‍💼 Открыть админ-панель",
            web_app=WebAppInfo(url=WEBAPP_URL + "?screen=admin")
        )
    ]])

    await message.answer(
        "👨‍💼 <b>Панель администратора</b>\n\n"
        "📊 Сегодня: 23 заказа · 48 900 ₽\n"
        "📦 В обработке: 8\n"
        "🚚 В доставке: 6\n"
        "✅ Завершено: 9",
        reply_markup=kb
    )


# ───────────────────────────────────────────
#  Данные из Mini App (оформление заказа)
# ───────────────────────────────────────────
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    """
    Срабатывает когда пользователь нажимает «Оплатить» в Mini App.
    Mini App должен вызвать:
      window.Telegram.WebApp.sendData(JSON.stringify(orderData))
    """
    try:
        data = json.loads(message.web_app_data.data)
    except json.JSONDecodeError:
        await message.answer("❌ Ошибка при получении данных. Попробуйте ещё раз.")
        return

    event = data.get("type")

    # ── Новый заказ ──────────────────────────
    if event == "order":
        order_id  = data.get("order_id", "BG-0000")
        items     = data.get("items", [])
        total     = data.get("total", 0)
        address   = data.get("address", "не указан")
        time_slot = data.get("time_slot", "как можно скорее")
        card_text = data.get("card_text", "")

        lines = "\n".join(
            f"  • {i['name']} × {i['qty']} = {i['price'] * i['qty']:,} ₽"
            for i in items
        ) or "  — пусто —"

        # Ответ клиенту
        await message.answer(
            f"✅ <b>Заказ #{order_id} принят!</b>\n\n"
            f"📦 <b>Состав:</b>\n{lines}\n\n"
            f"💰 <b>Итого:</b> {total:,} ₽\n"
            f"📍 <b>Адрес:</b> {address}\n"
            f"🕐 <b>Время доставки:</b> {time_slot}\n"
            + (f"💌 <b>Открытка:</b> {card_text}\n" if card_text else "") +
            "\nПришлём фото букета перед отправкой! 📸\n"
            "Следите за статусом: /orders"
        )

        # Уведомление администраторам
        user = message.from_user
        admin_text = (
            f"🔔 <b>Новый заказ #{order_id}</b>\n\n"
            f"👤 {user.full_name}"
            + (f" (@{user.username})" if user.username else "") +
            f"\n📱 ID: <code>{user.id}</code>\n\n"
            f"📦 <b>Состав:</b>\n{lines}\n\n"
            f"💰 <b>Сумма:</b> {total:,} ₽\n"
            f"📍 <b>Адрес:</b> {address}\n"
            f"🕐 <b>Время:</b> {time_slot}"
            + (f"\n💌 <b>Открытка:</b> {card_text}" if card_text else "")
        )

        admin_kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="✅ Принять",
                callback_data=f"accept_{order_id}_{user.id}"
            ),
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=f"cancel_{order_id}_{user.id}"
            ),
        ], [
            InlineKeyboardButton(
                text="🚚 Передать в доставку",
                callback_data=f"deliver_{order_id}_{user.id}"
            ),
        ]])

        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, admin_text, reply_markup=admin_kb)
            except Exception as e:
                logging.warning(f"Не удалось отправить уведомление админу {admin_id}: {e}")

    # ── AI-запрос ────────────────────────────
    elif event == "ai_request":
        mood   = data.get("mood", "")
        budget = data.get("budget", "любой")
        await message.answer(
            f"🤖 <b>AI-подбор букета</b>\n\n"
            f"Настроение: {mood}\n"
            f"Бюджет: {budget}\n\n"
            f"Рекомендую: <b>Роскошь роз</b> 🌹\n"
            f"<i>Идеально подходит для вашего случая!</i>"
        )

    else:
        logging.info(f"Неизвестный тип события: {event}")


# ───────────────────────────────────────────
#  Кнопки управления заказом (для админа)
# ───────────────────────────────────────────
@dp.callback_query(F.data.startswith("accept_"))
async def cb_accept(callback: CallbackQuery):
    parts    = callback.data.split("_")
    order_id = parts[1]
    user_id  = int(parts[2]) if len(parts) > 2 else None

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"✅ Заказ #{order_id} принят в работу!")
    await callback.answer("Принято!")

    if user_id:
        try:
            await bot.send_message(
                user_id,
                f"🌸 <b>Заказ #{order_id} принят!</b>\n"
                f"Флорист уже собирает ваш букет ✂️"
            )
        except Exception:
            pass


@dp.callback_query(F.data.startswith("cancel_"))
async def cb_cancel(callback: CallbackQuery):
    parts    = callback.data.split("_")
    order_id = parts[1]
    user_id  = int(parts[2]) if len(parts) > 2 else None

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"❌ Заказ #{order_id} отменён.")
    await callback.answer("Отменено")

    if user_id:
        try:
            await bot.send_message(
                user_id,
                f"😔 К сожалению, заказ #{order_id} был отменён.\n"
                f"Напишите нам, если это ошибка."
            )
        except Exception:
            pass


@dp.callback_query(F.data.startswith("deliver_"))
async def cb_deliver(callback: CallbackQuery):
    parts    = callback.data.split("_")
    order_id = parts[1]
    user_id  = int(parts[2]) if len(parts) > 2 else None

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"🚚 Заказ #{order_id} передан курьеру!")
    await callback.answer("Передано в доставку!")

    if user_id:
        try:
            await bot.send_message(
                user_id,
                f"🚚 <b>Заказ #{order_id} в пути!</b>\n"
                f"Курьер уже едет к вам. Ожидайте! 🌸"
            )
        except Exception:
            pass


# ───────────────────────────────────────────
#  Все остальные сообщения
# ───────────────────────────────────────────
@dp.message()
async def fallback(message: types.Message):
    await message.answer(
        "Нажмите кнопку <b>«🌸 Открыть магазин»</b> "
        "или отправьте /start"
    )


# ───────────────────────────────────────────
#  Запуск
# ───────────────────────────────────────────
async def main():
    print("=" * 45)
    print("  🌸  BloomGo Bot запущен!")
    print("=" * 45)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
