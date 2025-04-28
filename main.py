import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

# === Налаштування ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "123456789"))

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN is missing!")

APPLICATIONS_FILE = "applications.txt"  # Файл для збереження заявок

# === Стани ===
CHOOSING, CHOOSING_ORDER_TYPE, NAME, PHONE, ADDRESS, MESSAGE = range(6)
PASSENGER_NAME, PASSENGER_BIRTHDATE, PASSENGER_PHONE, PASSENGER_ADDRESS, PASSENGER_TRIP_DATE = range(6, 11)
SEARCH = 11
PRODUCT_ORDER = 12  # ➡️ Новий стан для замовлення продуктів

# === Кнопки та посилання ===
SOCIAL_LINKS = (
    "Дякуємо за заявку!\n\nНаші соцмережі:\n"
    "<a href='https://www.facebook.com/groups/1814614405457006?locale=uk_UA'>Facebook</a>\n"
    "<a href='https://t.me/estransuanor'>Telegram</a>"
)

CONTACT_LINKS = (
    "\n📞 Контакти водія:\n"
    "WhatsApp: https://wa.me/380963508202\n"
    "Telegram: https://t.me/Phant0mWAdeR\n"
    "Телефон: +4796801527\n"
    "Телефон: +380963508202"
)

PRICING_URL = "https://t.me/estransuanor/13"

# === Меню кнопок ===
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇳🇴 🇺🇦 📦 Оформити посилку", callback_data="make_order")],
        [InlineKeyboardButton("🧍 Пасажир", callback_data="passenger")],
        [
            InlineKeyboardButton("📞 Зв’язок з водієм", callback_data="contact_driver"),
            InlineKeyboardButton("📋 Умови та розцінки", callback_data="pricing")
        ],
        [InlineKeyboardButton("🛒 Замовити продукти та інше", callback_data="order_products")],
        [InlineKeyboardButton("🔍 Пошук заявки", callback_data="search")]
    ])

def order_type_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇳🇴 Заявка посилки з Норвегії⬅📦", callback_data="order_norway")],
        [InlineKeyboardButton("🇺🇦 Заявка посилки з України➡️📦", callback_data="order_ukraine")]
    ])

# === Допоміжна функція ===
async def safe_edit_or_send(query, text: str, reply_markup=None):
    try:
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        if "message to edit not found" in str(e).lower():
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            raise

# === Обробники ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Привіт! Обери дію:", reply_markup=main_menu())
    elif update.callback_query:
        await safe_edit_or_send(update.callback_query, "Привіт! Обери дію:", reply_markup=main_menu())
    return CHOOSING

async def auto_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start(update, context)

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return CHOOSING

    await query.answer()
    data = query.data

    if data == "make_order":
        await safe_edit_or_send(query, "Оберіть тип заявки:", reply_markup=order_type_menu())
        return CHOOSING_ORDER_TYPE
    elif data == "passenger":
        await safe_edit_or_send(query, "Введіть ім'я та прізвище латиницею:")
        return PASSENGER_NAME
    elif data == "contact_driver":
        await safe_edit_or_send(query, CONTACT_LINKS, reply_markup=main_menu())
    elif data == "pricing":
        await safe_edit_or_send(query, f"Ознайомтеся з умовами:\n{PRICING_URL}", reply_markup=main_menu())
    elif data == "search":
        await safe_edit_or_send(query, "Введіть текст для пошуку заявки:")
        return SEARCH
    elif data == "order_products":
        await safe_edit_or_send(
            query,
            "🛒 Тут ви можете зробити замовлення на покупку нами продуктів та інших речей з України та Польщі і ми привеземо все це вам )\n\n"
            "Введіть, будь ласка, список товарів:"
        )
        return PRODUCT_ORDER

    return CHOOSING

async def choose_order_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return CHOOSING

    await query.answer()
    context.user_data['order_type'] = query.data

    if query.data == "order_norway":
        await safe_edit_or_send(query, "Введіть своє ім’я:")
    else:
        await safe_edit_or_send(query, "Введіть ім'я та прізвище отримувача в Норвегії:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введіть номер телефону:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Введіть адресу (місто, вулиця, номер будинку):")
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    await update.message.reply_text("Надайте короткий опис посилки:")
    return MESSAGE

async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['message'] = update.message.text

    user = update.effective_user
    user_id = user.id
    username = user.username or user.full_name

    summary = (
        f"📬 Нова {context.user_data['order_type']} від @{username} (ID: {user_id}):\n\n"
        f"👤 Ім’я: {context.user_data['name']}\n"
        f"📞 Телефон: {context.user_data['phone']}\n"
        f"📍 Адреса: {context.user_data['address']}\n"
        f"📝 Повідомлення: {context.user_data['message']}"
    )

    await context.bot.send_message(chat_id=user_id, text="✅ Заявка прийнята!\n\n" + summary)
    await update.message.reply_text(SOCIAL_LINKS, parse_mode="HTML")
    await update.message.reply_text("Готово!", reply_markup=main_menu())
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary)

    with open(APPLICATIONS_FILE, "a", encoding="utf-8") as f:
        f.write(summary + "\n\n")

    return CHOOSING

async def get_passenger_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['passenger_name'] = update.message.text
    await update.message.reply_text("Введіть дату народження (ДД.ММ.РРРР):")
    return PASSENGER_BIRTHDATE

async def get_passenger_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['passenger_birthdate'] = update.message.text
    await update.message.reply_text("Введіть номер телефону для зв'язку:")
    return PASSENGER_PHONE

async def get_passenger_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['passenger_phone'] = update.message.text
    await update.message.reply_text("Введіть адресу забору (місто, вулиця, номер будинку):")
    return PASSENGER_ADDRESS

async def get_passenger_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['passenger_address'] = update.message.text
    await update.message.reply_text("Введіть дату поїздки (ДД.ММ.РРРР):")
    return PASSENGER_TRIP_DATE

async def get_passenger_trip_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['passenger_trip_date'] = update.message.text

    user = update.effective_user
    user_id = user.id
    username = user.username or user.full_name

    summary = (
        f"🚌 Нова заявка пасажира від @{username} (ID: {user_id}):\n\n"
        f"👤 Ім'я та прізвище: {context.user_data['passenger_name']}\n"
        f"🎂 Дата народження: {context.user_data['passenger_birthdate']}\n"
        f"📞 Телефон: {context.user_data['passenger_phone']}\n"
        f"📍 Адреса забору: {context.user_data['passenger_address']}\n"
        f"📅 Дата поїздки: {context.user_data['passenger_trip_date']}"
    )

    await context.bot.send_message(chat_id=user_id, text="✅ Дані прийняті!\n\n" + summary)
    await update.message.reply_text(SOCIAL_LINKS, parse_mode="HTML")
    await update.message.reply_text("Готово!", reply_markup=main_menu())
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary)

    with open(APPLICATIONS_FILE, "a", encoding="utf-8") as f:
        f.write(summary + "\n\n")

    return CHOOSING

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.lower()

    if not os.path.exists(APPLICATIONS_FILE):
        await update.message.reply_text("📂 База заявок поки пуста.", reply_markup=main_menu())
        return CHOOSING

    with open(APPLICATIONS_FILE, "r", encoding="utf-8") as f:
        data = f.read().lower()

    results = []
    applications = data.split("\n\n")
    for app in applications:
        if query in app:
            results.append(app.strip())

    if results:
        for res in results:
            await update.message.reply_text(f"🔎 Знайдено заявку:\n\n{res}")
    else:
        await update.message.reply_text("❌ Нічого не знайдено.")

    await update.message.reply_text("Головне меню:", reply_markup=main_menu())
    return CHOOSING

async def get_product_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.full_name

    order_list = update.message.text

    summary = (
        f"🛒 НОВЕ замовлення продуктів від @{username} (ID: {user_id}):\n\n"
        f"📝 Список товарів:\n{order_list}"
    )

    await context.bot.send_message(chat_id=user_id, text="✅ Ваше замовлення прийняте!\n\n" + summary)
    await update.message.reply_text(SOCIAL_LINKS, parse_mode="HTML")
    await update.message.reply_text("Головне меню:", reply_markup=main_menu())
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary)

    with open(APPLICATIONS_FILE, "a", encoding="utf-8") as f:
        f.write(summary + "\n\n")

    return CHOOSING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано.", reply_markup=main_menu())
    return CHOOSING

# === Ініціалізація застосунку ===
app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER, auto_start),
        MessageHandler(filters.TEXT & ~filters.COMMAND, auto_start),
        CallbackQueryHandler(choose_action)
    ],
    states={
        CHOOSING: [CallbackQueryHandler(choose_action)],
        CHOOSING_ORDER_TYPE: [CallbackQueryHandler(choose_order_type)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
        MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_message)],
        PASSENGER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_passenger_name)],
        PASSENGER_BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_passenger_birthdate)],
        PASSENGER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_passenger_phone)],
        PASSENGER_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_passenger_address)],
        PASSENGER_TRIP_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_passenger_trip_date)],
        SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, search)],
        PRODUCT_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product_order)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)

if __name__ == "__main__":
    print("🟢 Estrans Cargo Bot is running (polling)...")
    app.run_polling()
