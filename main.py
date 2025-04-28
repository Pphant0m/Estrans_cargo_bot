import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

# === Налаштування ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "123456789"))
APPLICATIONS_FILE = "applications.txt"  # Файл для збереження заявок

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN is missing!")

# === Стани ===
(
    CHOOSING, CHOOSING_ORDER_TYPE, NAME, PHONE, ADDRESS, MESSAGE,
    PASSENGER_NAME, PASSENGER_BIRTHDATE, PASSENGER_PHONE, PASSENGER_ADDRESS,
    SEARCH, PRODUCT_ORDER
) = range(12)

# === Константи ===
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
        [InlineKeyboardButton("🛒 Замовити продукти", callback_data="order_products")],
        [InlineKeyboardButton("🔍 Пошук заявки", callback_data="search")]
    ])

def order_type_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇳🇴 З Норвегії", callback_data="order_norway")],
        [InlineKeyboardButton("🇺🇦 З України", callback_data="order_ukraine")]
    ])

# === Допоміжні функції ===
async def safe_send(query, text: str, reply_markup=None):
    try:
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception:
        await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def save_application(summary: str):
    with open(APPLICATIONS_FILE, "a", encoding="utf-8") as f:
        f.write(summary + "\n\n")

async def send_summary(context: ContextTypes.DEFAULT_TYPE, user_id: int, summary: str):
    await context.bot.send_message(chat_id=user_id, text="✅ Прийнято!\n\n" + summary)
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary)

# === Обробники ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message or update.callback_query
    await safe_send(message, "Привіт! Обери дію:", main_menu())
    return CHOOSING

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    actions = {
        "make_order": (safe_send, "Оберіть тип заявки:", order_type_menu, CHOOSING_ORDER_TYPE),
        "passenger": (safe_send, "Введіть ім'я та прізвище латиницею:", None, PASSENGER_NAME),
        "contact_driver": (safe_send, CONTACT_LINKS, main_menu, CHOOSING),
        "pricing": (safe_send, f"Ознайомтеся з умовами:\n{PRICING_URL}", main_menu, CHOOSING),
        "search": (safe_send, "Введіть текст для пошуку:", None, SEARCH),
        "order_products": (safe_send, "🛒 Введіть список товарів:", None, PRODUCT_ORDER)
    }
    if data := actions.get(query.data):
        await data[0](query, data[1], data[2]() if data[2] else None)
        return data[3]
    return CHOOSING

async def choose_order_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['order_type'] = query.data
    await safe_send(query, "Введіть своє ім’я:" if query.data == "order_norway" else "Введіть ім'я отримувача:")
    return NAME

async def simple_input(update: Update, context: ContextTypes.DEFAULT_TYPE, next_state: int, key: str, prompt: str):
    context.user_data[key] = update.message.text
    await update.message.reply_text(prompt)
    return next_state

# === Збір даних ===
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await simple_input(update, context, PHONE, 'name', "Введіть номер телефону:")

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await simple_input(update, context, ADDRESS, 'phone', "Введіть адресу:")

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await simple_input(update, context, MESSAGE, 'address', "Опишіть посилку:")

async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['message'] = update.message.text
    user = update.effective_user
    summary = (
        f"📬 Нова {context.user_data['order_type']} від @{user.username or user.full_name}:\n"
        f"👤 Ім’я: {context.user_data['name']}\n📞 Телефон: {context.user_data['phone']}\n"
        f"📍 Адреса: {context.user_data['address']}\n📝 Повідомлення: {context.user_data['message']}"
    )
    await send_summary(context, user.id, summary)
    await update.message.reply_text(SOCIAL_LINKS, parse_mode="HTML")
    await update.message.reply_text("Головне меню:", reply_markup=main_menu())
    await save_application(summary)
    return CHOOSING

# === Пасажир ===
async def get_passenger_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await simple_input(update, context, PASSENGER_BIRTHDATE, 'passenger_name', "Введіть дату народження:")

async def get_passenger_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await simple_input(update, context, PASSENGER_PHONE, 'passenger_birthdate', "Введіть номер телефону:")

async def get_passenger_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await simple_input(update, context, PASSENGER_ADDRESS, 'passenger_phone', "Введіть адресу забору:")

async def get_passenger_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['passenger_address'] = update.message.text
    user = update.effective_user
    summary = (
        f"🚌 Нова заявка пасажира від @{user.username or user.full_name}:\n"
        f"👤 Ім’я: {context.user_data['passenger_name']}\n🎂 Дата народження: {context.user_data['passenger_birthdate']}\n"
        f"📞 Телефон: {context.user_data['passenger_phone']}\n📍 Адреса: {context.user_data['passenger_address']}"
    )
    await send_summary(context, user.id, summary)
    await update.message.reply_text(SOCIAL_LINKS, parse_mode="HTML")
    await update.message.reply_text("Головне меню:", reply_markup=main_menu())
    await save_application(summary)
    return CHOOSING

# === Пошук заявок ===
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.lower()
    if not os.path.exists(APPLICATIONS_FILE):
        await update.message.reply_text("📂 База пуста.", reply_markup=main_menu())
        return CHOOSING
    with open(APPLICATIONS_FILE, "r", encoding="utf-8") as f:
        results = [app.strip() for app in f.read().lower().split("\n\n") if query in app]
    for res in results:
        await update.message.reply_text(f"🔎 Знайдено:\n\n{res}")
    if not results:
        await update.message.reply_text("❌ Нічого не знайдено.")
    await update.message.reply_text("Головне меню:", reply_markup=main_menu())
    return CHOOSING

# === Замовлення продуктів ===
async def get_product_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    summary = (
        f"🛒 Замовлення від @{user.username or user.full_name}:\n"
        f"📝 Список:\n{update.message.text}"
    )
    await send_summary(context, user.id, summary)
    await update.message.reply_text(SOCIAL_LINKS, parse_mode="HTML")
    await update.message.reply_text("Головне меню:", reply_markup=main_menu())
    await save_application(summary)
    return CHOOSING

# === Скасування ===
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано.", reply_markup=main_menu())
    return CHOOSING

# === Ініціалізація застосунку ===
app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER, start),
        MessageHandler(filters.TEXT & ~filters.COMMAND, start),
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
        SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, search)],
        PRODUCT_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product_order)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)

if __name__ == "__main__":
    print("🟢 Estrans Cargo Bot запущено (polling)...")
    app.run_polling()
