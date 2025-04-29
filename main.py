import os
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ChatMemberHandler, ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "123456789"))

APPLICATIONS_FILE = "applications.txt"

SOCIAL_LINKS = (
    "Наші соцмережі:\n"
    "<a href='https://www.facebook.com/groups/1814614405457006?locale=uk_UA'>Facebook</a>\n"
    "<a href='https://t.me/estransuanor'>Telegram</a>"
)

CONTACT_LINKS = (
    "📞 Контакти водія:\n"
    "WhatsApp: https://wa.me/380963508202\n"
    "Telegram: https://t.me/Phant0mWAdeR\n"
    "Телефон: +4796801527\n"
    "Телефон: +380963508202"
)

CHOOSING, CHOOSING_ORDER_TYPE, NAME, PHONE, ADDRESS, DATE, MESSAGE = range(7)

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
        context.user_data["order_type"] = "passenger"
        await query.message.edit_text("Введіть ім'я та прізвище латиницею:")
        return NAME
    elif data == "contact_driver":
        await query.message.edit_text(
            f"<b>📨 Контактна інформація:</b>\n\n{SOCIAL_LINKS}\n\n{CONTACT_LINKS}",
            reply_markup=main_menu(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    elif data == "pricing":
        await query.message.edit_text("📋 Умови та розцінки: https://t.me/estransuanor/13", reply_markup=main_menu())
    elif data == "search":
        context.user_data['searching'] = True
        await query.message.edit_text("🔍 Введіть ключові слова для пошуку заявки:")
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

    if context.user_data.get("order_type") == "passenger":
        await update.message.reply_text("Вкажіть дату поїздки:")
        return DATE
    else:
        await update.message.reply_text("Надайте короткий опис посилки:")
        return MESSAGE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    await update.message.reply_text("Надайте короткий опис:")
    return MESSAGE

async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if context.user_data.get('searching'):
        context.user_data['searching'] = False
        results = []

        if os.path.exists(APPLICATIONS_FILE):
            with open(APPLICATIONS_FILE, "r", encoding="utf-8") as file:
                applications = file.read().split("\n\n")
                for app in applications:
                    if text.lower() in app.lower():
                        results.append(app)

        if results:
            for result in results[:5]:
                await update.message.reply_text(f"🔎 Знайдено:\n{result}")
        else:
            await update.message.reply_text("❌ Нічого не знайдено за вашим запитом.")

        return CHOOSING

    context.user_data['message'] = text

    # Спочатку контакти
    await update.message.reply_text(
        f"<b>📨 Контактна інформація:</b>\n\n{SOCIAL_LINKS}\n\n{CONTACT_LINKS}",
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    # Потім підтвердження та меню
    await update.message.reply_text("✅ Дані отримано. Дякуємо!", reply_markup=main_menu())

    # В самому кінці — заявка
    await save_application(update, context)

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
    )

    if context.user_data.get("order_type") == "passenger":
        summary += f"📅 Дата поїздки: {context.user_data.get('date')}\n"

    summary += f"📝 Повідомлення: {context.user_data.get('message')}"

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary)
    await update.message.reply_text(f"Ось ваша заявка:\n\n{summary}")

    with open(APPLICATIONS_FILE, "a", encoding="utf-8") as file:
        file.write(summary + "\n\n")

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
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
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
