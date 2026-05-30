#import logging
import os
import json
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("8805232719:AAEEjPQzLnAUSh8EhLtrjUFVq-QN6n83peo", "")
ADMIN_GROUP_ID = os.getenv("-1003955990003", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
APPLICATIONS_FILE = "applications.json"

LANGUAGE, TRUCK_NUMBER, DRIVER_NAME, COUNTRY, CITY, RELEASE_DATE, CONFIRM = range(7)

TEXTS = {
    "ru": {
        "welcome": "👋 Добро пожаловать!\nВыберите язык:",
        "ask_truck": "🚛 Введите номер фуры:",
        "ask_driver": "👤 Введите ваше имя (ФИО):",
        "ask_country": "🌍 В какой стране вы находитесь?",
        "ask_city": "🏙 В каком городе?",
        "ask_date": "📅 Когда освобождается машина?\nФормат: ДД.ММ.ГГГГ (пример: 25.06.2025)",
        "confirm_title": "📋 Проверьте данные:",
        "confirm_btn": "✅ Подтвердить",
        "cancel_btn": "❌ Отменить",
        "success": "✅ Заявка принята! Диспетчеры готовят груз. Спасибо!",
        "cancelled": "❌ Отменено. Начните заново — /start",
        "invalid_date": "❌ Неверный формат. Введите ДД.ММ.ГГГГ",
        "truck_label": "Номер фуры",
        "driver_label": "Водитель",
        "country_label": "Страна",
        "city_label": "Город",
        "date_label": "Дата освобождения",
    },
    "uz": {
        "welcome": "👋 Xush kelibsiz!\nTilni tanlang:",
        "ask_truck": "🚛 Yuk mashinasi raqamini kiriting:",
        "ask_driver": "👤 Ismingizni kiriting (FIO):",
        "ask_country": "🌍 Qaysi mamlakatdasiz?",
        "ask_city": "🏙 Qaysi shaharda?",
        "ask_date": "📅 Mashina qachon bo'shaydi?\nFormat: KK.OO.YYYY (masalan: 25.06.2025)",
        "confirm_title": "📋 Ma'lumotlarni tekshiring:",
        "confirm_btn": "✅ Tasdiqlash",
        "cancel_btn": "❌ Bekor qilish",
        "success": "✅ Ariza qabul qilindi! Dispetcherlar yuk tayyorlayapti. Rahmat!",
        "cancelled": "❌ Bekor qilindi. Qaytadan — /start",
        "invalid_date": "❌ Format noto'g'ri. KK.OO.YYYY kiriting",
        "truck_label": "Yuk mashinasi",
        "driver_label": "Haydovchi",
        "country_label": "Mamlakat",
        "city_label": "Shahar",
        "date_label": "Bo'shash sanasi",
    }
}

def load_applications():
    if os.path.exists(APPLICATIONS_FILE):
        with open(APPLICATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_application(data):
    apps = load_applications()
    apps.append(data)
    with open(APPLICATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(apps, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [["🇷🇺 Русский", "🇺🇿 O'zbekcha"]]
    await update.message.reply_text("👋 Добро пожаловать! / Xush kelibsiz!\nВыберите язык / Tilni tanlang:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
    return LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lang"] = "uz" if "O'zbekcha" in update.message.text else "ru"
    await update.message.reply_text(TEXTS[context.user_data["lang"]]["ask_truck"], reply_markup=ReplyKeyboardRemove())
    return TRUCK_NUMBER

async def get_truck_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["truck_number"] = update.message.text.strip()
    await update.message.reply_text(TEXTS[context.user_data["lang"]]["ask_driver"])
    return DRIVER_NAME

async def get_driver_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["driver_name"] = update.message.text.strip()
    await update.message.reply_text(TEXTS[context.user_data["lang"]]["ask_country"])
    return COUNTRY

async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["country"] = update.message.text.strip()
    await update.message.reply_text(TEXTS[context.user_data["lang"]]["ask_city"])
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text.strip()
    await update.message.reply_text(TEXTS[context.user_data["lang"]]["ask_date"])
    return RELEASE_DATE

async def get_release_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    date_text = update.message.text.strip()
    try:
        datetime.strptime(date_text, "%d.%m.%Y")
    except ValueError:
        await update.message.reply_text(TEXTS[lang]["invalid_date"])
        return RELEASE_DATE
    context.user_data["release_date"] = date_text
    t = TEXTS[lang]
    d = context.user_data
    summary = f"{t['confirm_title']}\n\n🚛 {t['truck_label']}: {d['truck_number']}\n👤 {t['driver_label']}: {d['driver_name']}\n🌍 {t['country_label']}: {d['country']}\n🏙 {t['city_label']}: {d['city']}\n📅 {t['date_label']}: {d['release_date']}"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(t["confirm_btn"], callback_data="confirm"), InlineKeyboardButton(t["cancel_btn"], callback_data="cancel")]])
    await update.message.reply_text(summary, reply_markup=keyboard)
    return CONFIRM

async def confirm_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "ru")
    t = TEXTS[lang]
    if query.data == "cancel":
        await query.edit_message_text(t["cancelled"])
        return ConversationHandler.END
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    app_data = {"id": len(load_applications()) + 1, "truck_number": context.user_data["truck_number"], "driver_name": context.user_data["driver_name"], "country": context.user_data["country"], "city": context.user_data["city"], "release_date": context.user_data["release_date"], "submitted_at": now, "telegram_username": query.from_user.username or ""}
    save_application(app_data)
    msg = f"🆕 НОВАЯ ЗАЯВКА #{app_data['id']}\n{'─'*28}\n🚛 Фура: {app_data['truck_number']}\n👤 Водитель: {app_data['driver_name']}\n🌍 Страна: {app_data['country']}\n🏙 Город: {app_data['city']}\n📅 Освобождение: {app_data['release_date']}\n⏰ Время: {app_data['submitted_at']}\n📱 TG: @{app_data['telegram_username']}"
    try:
        await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=msg)
    except Exception as e:
        logger.error(f"Ошибка отправки в группу: {e}")
    await query.edit_message_text(t["success"])
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(TEXTS[lang]["cancelled"], reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def admin_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_IDS and update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Нет доступа.")
        return
    apps = load_applications()
    if not apps:
        await update.message.reply_text("📭 Заявок пока нет.")
        return
    text = f"📋 Последние заявки ({len(apps)} всего):\n\n"
    for a in reversed(apps[-10:]):
        text += f"#{a['id']} | {a['truck_number']} | {a['driver_name']}\n   📍 {a['country']}, {a['city']} | 📅 {a['release_date']}\n   ⏰ {a['submitted_at']}\n\n"
    await update.message.reply_text(text)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            TRUCK_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_truck_number)],
            DRIVER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_driver_name)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            RELEASE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_release_date)],
            CONFIRM: [CallbackQueryHandler(confirm_application)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("applications", admin_applications))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
