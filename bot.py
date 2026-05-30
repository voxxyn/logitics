import logging
import os
import json
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
APPLICATIONS_FILE = "applications.json"

LANGUAGE, TRUCK_NUMBER, TRUCK_TYPE, TRUCK_BRAND, DRIVER_NAME, COUNTRY, CITY, RELEASE_DATE, CONFIRM = range(9)

TEXTS = {
    "ru": {
        "ask_truck": "🚛 Введите номер фуры:",
        "ask_truck_type": "📦 Выберите тип фуры:",
        "ask_truck_brand": "🏭 Выберите марку авто:",
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
        "truck_type_label": "Тип фуры",
        "truck_brand_label": "Марка",
        "driver_label": "Водитель",
        "country_label": "Страна",
        "city_label": "Город",
        "date_label": "Дата освобождения",
    },
    "uz": {
        "ask_truck": "🚛 Юк машинаси рақамини киринг:",
        "ask_truck_type": "📦 Юк машинаси турини танланг:",
        "ask_truck_brand": "🏭 Автомобиль русумини танланг:",
        "ask_driver": "👤 Исмингизни киринг (ФИО):",
        "ask_country": "🌍 Қайси мамлакатдасиз?",
        "ask_city": "🏙 Қайси шаҳарда?",
        "ask_date": "📅 Машина қачон бўшайди?\nФормат: КК.ОО.ЙЙЙЙ (масалан: 25.06.2025)",
        "confirm_title": "📋 Маълумотларни текширинг:",
        "confirm_btn": "✅ Тасдиқлаш",
        "cancel_btn": "❌ Бекор қилиш",
        "success": "✅ Ариза қабул қилинди! Диспетчерлар юк тайёрлаяпти. Раҳмат!",
        "cancelled": "❌ Бекор қилинди. Қайтадан — /start",
        "invalid_date": "❌ Формат нотўғри. КК.ОО.ЙЙЙЙ киринг",
        "truck_label": "Юк машинаси рақами",
        "truck_type_label": "Тури",
        "truck_brand_label": "Русуми",
        "driver_label": "Ҳайдовчи",
        "country_label": "Мамлакат",
        "city_label": "Шаҳар",
        "date_label": "Бўшаш санаси",
    }
}

TRUCK_TYPES = ["🚛 Мега", "🚂 Паровоз", "❄️ Реф"]
TRUCK_BRANDS = ["FAW", "MAN", "VOLVO", "DAF", "RENO"]

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

def truck_type_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚛 Мега", callback_data="type_Мега"),
         InlineKeyboardButton("🚂 Паровоз", callback_data="type_Паровоз"),
         InlineKeyboardButton("❄️ Реф", callback_data="type_Реф")]
    ])

def truck_brand_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("FAW", callback_data="brand_FAW"),
         InlineKeyboardButton("MAN", callback_data="brand_MAN"),
         InlineKeyboardButton("VOLVO", callback_data="brand_VOLVO")],
        [InlineKeyboardButton("DAF", callback_data="brand_DAF"),
         InlineKeyboardButton("RENO", callback_data="brand_RENO")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [["🇷🇺 Русский", "🇺🇿 Ўзбекча"]]
    await update.message.reply_text(
        "👋 Добро пожаловать! / Хуш келибсиз!\nВыберите язык / Тилни танланг:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lang"] = "uz" if "Ўзбекча" in update.message.text else "ru"
    lang = context.user_data["lang"]
    await update.message.reply_text(TEXTS[lang]["ask_truck"], reply_markup=ReplyKeyboardRemove())
    return TRUCK_NUMBER

async def get_truck_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["truck_number"] = update.message.text.strip()
    lang = context.user_data["lang"]
    await update.message.reply_text(TEXTS[lang]["ask_truck_type"], reply_markup=truck_type_keyboard())
    return TRUCK_TYPE

async def get_truck_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["truck_type"] = query.data.replace("type_", "")
    lang = context.user_data["lang"]
    await query.edit_message_text(
        f"{TEXTS[lang]['ask_truck_type']}\n✅ {context.user_data['truck_type']}"
    )
    await query.message.reply_text(TEXTS[lang]["ask_truck_brand"], reply_markup=truck_brand_keyboard())
    return TRUCK_BRAND

async def get_truck_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["truck_brand"] = query.data.replace("brand_", "")
    lang = context.user_data["lang"]
    await query.edit_message_text(
        f"{TEXTS[lang]['ask_truck_brand']}\n✅ {context.user_data['truck_brand']}"
    )
    await query.message.reply_text(TEXTS[lang]["ask_driver"])
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
    summary = (
        f"{t['confirm_title']}\n\n"
        f"🚛 {t['truck_label']}: {d['truck_number']}\n"
        f"📦 {t['truck_type_label']}: {d['truck_type']}\n"
        f"🏭 {t['truck_brand_label']}: {d['truck_brand']}\n"
        f"👤 {t['driver_label']}: {d['driver_name']}\n"
        f"🌍 {t['country_label']}: {d['country']}\n"
        f"🏙 {t['city_label']}: {d['city']}\n"
        f"📅 {t['date_label']}: {d['release_date']}"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(t["confirm_btn"], callback_data="confirm"),
        InlineKeyboardButton(t["cancel_btn"], callback_data="cancel")
    ]])
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
    app_data = {
        "id": len(load_applications()) + 1,
        "truck_number": context.user_data["truck_number"],
        "truck_type": context.user_data["truck_type"],
        "truck_brand": context.user_data["truck_brand"],
        "driver_name": context.user_data["driver_name"],
        "country": context.user_data["country"],
        "city": context.user_data["city"],
        "release_date": context.user_data["release_date"],
        "submitted_at": now,
        "telegram_username": query.from_user.username or ""
    }
    save_application(app_data)
    msg = (
        f"🆕 НОВАЯ ЗАЯВКА #{app_data['id']}\n"
        f"{'─'*28}\n"
        f"🚛 Фура: {app_data['truck_number']}\n"
        f"📦 Тип: {app_data['truck_type']}\n"
        f"🏭 Марка: {app_data['truck_brand']}\n"
        f"👤 Водитель: {app_data['driver_name']}\n"
        f"🌍 Страна: {app_data['country']}\n"
        f"🏙 Город: {app_data['city']}\n"
        f"📅 Освобождение: {app_data['release_date']}\n"
        f"⏰ Время: {app_data['submitted_at']}\n"
        f"📱 TG: @{app_data['telegram_username']}"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=msg)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
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
        text += (
            f"#{a['id']} | {a.get('truck_brand','')} {a.get('truck_type','')} | {a['truck_number']}\n"
            f"   👤 {a['driver_name']}\n"
            f"   📍 {a['country']}, {a['city']} | 📅 {a['release_date']}\n"
            f"   ⏰ {a['submitted_at']}\n\n"
        )
    await update.message.reply_text(text)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            TRUCK_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_truck_number)],
            TRUCK_TYPE: [CallbackQueryHandler(get_truck_type, pattern="^type_")],
            TRUCK_BRAND: [CallbackQueryHandler(get_truck_brand, pattern="^brand_")],
            DRIVER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_driver_name)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            RELEASE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_release_date)],
            CONFIRM: [CallbackQueryHandler(confirm_application, pattern="^(confirm|cancel)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("applications", admin_applications))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
