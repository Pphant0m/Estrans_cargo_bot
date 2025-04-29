import os
# from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ChatMemberHandler, ContextTypes, filters
)

# === Load environment variables ===
# load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "123456789"))

APPLICATIONS_FILE = "applications.txt"

# === Conversation States ===
CHOOSING, CHOOSING_ORDER_TYPE, NAME, PHONE, ADDRESS, MESSAGE = range(6)

# === Menus ===
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Оформити посилку", callback_data="make_order")],
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
        [InlineKeyboardButton("🇳🇴 З Норвегії⬅📦", callback_data="order_norway")],
        [InlineKeyboardButton("🇺🇦 З України➡️📦", callback_data="order_ukraine")]
    ])

# === Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.chat_data.clear()

    if update.message:
        await update.message.reply_text("Привіт! Оберіть дію:", reply_markup=main_menu())
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("Привіт! Оберіть дію:", reply_markup=main_menu())

    return CHOOSING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.chat_data.clear()
    await update.message.reply_text("Скасовано.", reply_markup=main_menu())
    return CHOOSING

async def force_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_member:
        status = update.chat_member.new_chat_member.status
        if status == "member":
            chat_id = update.effective_chat.id
            await context.bot.send_message(chat_id=chat_id, text="Привіт! Оберіть дію:", reply_markup=main_menu())

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "make_order":
        await query.message.edit_text("Оберіть тип заявки:", reply_markup=order_type_menu())
        return CHOOSING_ORDER_TYPE
    elif data == "passenger":
        await query.message.edit_text("Введіть ім'я та прізвище латиницею:")
        return NAME
    elif data == "contact_driver":
        await query.message.edit_text("Контакт водія: 📞 +380963508202", reply_markup=main_menu())
    elif data == "pricing":
        await query.message.edit_text("Умови та розцінки: https://t.me/estransuanor/13", reply_markup=main_menu())
    elif data == "search":
        await query.message.edit_text("Введіть текст для пошуку заявки:")
        return MESSAGE
    elif data == "order_products":
        await query.message.edit_text("🛒 Введіть список товарів для замовлення:")
        return MESSAGE

    return CHOOSING

async def choose_order_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['order_type'] = query.data
    await query.message.edit_text("Введіть ім'я:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введіть номер телефону:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Введіть адресу:")
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    await update.message.reply_text("Надайте короткий опис посилки:")
    return MESSAGE

async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['message'] = update.message.text
    await save_application(update, context)
    await update.message.reply_text("✅ Дані отримано. Дякуємо!", reply_markup=main_menu())
    return CHOOSING

async def save_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.full_name

    summary = (
        f"📬 Нова заявка від @{username} (ID: {user_id}):\n"
        f"👤 Ім’я: {context.user_data.get('name')}\n"
        f"📞 Телефон: {context.user_data.get('phone')}\n"
        f"📍 Адреса: {context.user_data.get('address')}\n"
        f"📝 Повідомлення: {context.user_data.get('message')}"
    )

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary)

    with open(APPLICATIONS_FILE, "a", encoding="utf-8") as file:
        file.write(summary + "\n\n")

# === App Runner ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [CallbackQueryHandler(choose_action)],
            CHOOSING_ORDER_TYPE: [CallbackQueryHandler(choose_order_type)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(ChatMemberHandler(force_start, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))

    app.run_polling()

if __name__ == "__main__":
    main()