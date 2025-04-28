import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Стейти розмови
ASK_NAME, ASK_AGE = range(2)

# Старт команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Привіт! Як тебе звати?",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()  # Очищаємо дані перед новою сесією
    return ASK_NAME

# Отримання імені
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        f"Дякую, {context.user_data['name']}! Скільки тобі років?"
    )
    return ASK_AGE

# Отримання віку
async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        age = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Будь ласка, введи число.")
        return ASK_AGE

    context.user_data['age'] = age
    await update.message.reply_text(
        f"Тебе звати {context.user_data['name']} і тобі {context.user_data['age']} років. Дякую за відповіді!"
    )
    return ConversationHandler.END

# Обробка скасування
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Розмову скасовано. Якщо захочеш почати знову, напиши /start.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

# Обробка невідомих повідомлень
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вибач, я не розумію цю команду. Використай /start, щоб почати спілкування."
    )

def main():
    # Створюємо бота
    application = Application.builder().token("ТВОКЕН_ТУТ").build()

    # Обробник розмови
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Додаємо хендлери
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.COMMAND, unknown))  # Невідомі команди

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
