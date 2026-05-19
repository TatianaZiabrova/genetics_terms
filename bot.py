import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

MAIN_MENU = ReplyKeyboardMarkup(
    [["📚 Учить термин", "🎮 Проверить себя"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = None
    context.user_data["quiz_mode"] = None
    context.user_data["onboarding"] = True
    
    await update.message.reply_text(
        "👋 Привет! Я помогу тебе запомнить термины по генетике для ЕГЭ!\n\n"
        "🧠 *Как это работает — метод мнемоники:*\n\n"
        "1️⃣ Читаешь *определение* термина — понимаешь смысл\n\n"
        "2️⃣ Смотришь *расшифровку по буквам* — каждая часть термина превращается в простое слово\n\n"
        "3️⃣ Представляешь *безумный образ* — чем смешнее и ярче картинка в голове, тем лучше запомнишь!\n\n"
        "4️⃣ Совмещаешь образ с определением — теперь термин *прилип* к смыслу 🎯\n\n"
        "5️⃣ Проверяешь себя — и убеждаешься что помнишь!\n\n"
        "💡 *Секрет:* мозг запоминает странные и смешные образы в 10 раз лучше чем скучный текст. Поэтому чем абсурднее картинка — тем лучше!\n\n"
        "Готов попробовать? 👇",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [["🚀 Понятно, начнём!"]],
            resize_keyboard=True
        )
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Просто напиши термин — например *кроссинговер*\n"
        "Или нажми кнопку внизу 👇",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    quiz_mode = context.user_data.get("quiz_mode")

    # Если идёт проверка — проверяем ответ
    if quiz_mode and text != "🏠 Главное меню":
        from handlers.quiz import check_answer
        await check_answer(update, context)
        return
    
    if text == "🚀 Понятно, начнём!":
        context.user_data["onboarding"] = False
        await update.message.reply_text(
            "Отлично! Выбирай что делаем 👇",
            reply_markup=MAIN_MENU
        )
        return

    if text == "📚 Учить термин":
        context.user_data["mode"] = "learn"
        context.user_data["quiz_mode"] = None
        await update.message.reply_text(
            "Введи термин который хочешь запомнить 👇"
        )

    elif text == "🎮 Проверить себя":
        context.user_data["mode"] = "quiz"
        context.user_data["quiz_mode"] = None
        quiz_menu = ReplyKeyboardMarkup(
            [
                ["🅑 Определение → Термин"],
                ["🅒 Термин → Определение"],
                ["🅓 Викторина (4 варианта)"],
                ["🏠 Главное меню"]
            ],
            resize_keyboard=True
        )
        await update.message.reply_text(
            "Как будем проверять? Выбери режим 👇",
            reply_markup=quiz_menu
        )

    elif text == "🅑 Определение → Термин":
        from handlers.quiz import quiz_b
        await quiz_b(update, context)

    elif text == "🅒 Термин → Определение":
        from handlers.quiz import quiz_v
        await quiz_v(update, context)

    elif text == "🅓 Викторина (4 варианта)":
        from handlers.quiz import quiz_g
        await quiz_g(update, context)

    elif text == "🏠 Главное меню":
        context.user_data["mode"] = None
        context.user_data["quiz_mode"] = None
        await update.message.reply_text(
            "Главное меню 👇",
            reply_markup=MAIN_MENU
        )

    else:
        from handlers.learn import show_term
        await show_term(update, context, text)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    from telegram.ext import CallbackQueryHandler
    from handlers.learn import handle_callback
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("🤖 Бот запущен! Нажми Ctrl+C чтобы остановить.")
    app.run_polling()

if __name__ == "__main__":
    main()