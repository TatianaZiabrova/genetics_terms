import json
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from services.fuzzy_search import find_term

# Загружаем базу терминов
with open("data/terms.json", "r", encoding="utf-8") as f:
    TERMS = json.load(f)

# Режим Б — бот даёт определение, ребёнок пишет термин
async def quiz_b(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Выбираем случайный термин
    term_key = random.choice(list(TERMS.keys()))
    term = TERMS[term_key]
    
    # Сохраняем правильный ответ
    context.user_data["correct_answer"] = term_key
    context.user_data["quiz_mode"] = "b"
    
    await update.message.reply_text(
        f"📖 *Что это за термин?*\n\n"
        f"{term['definition']}\n\n"
        f"Напиши ответ 👇",
        parse_mode="Markdown"
    )

# Режим В — бот даёт термин, ребёнок пишет определение
async def quiz_v(update: Update, context: ContextTypes.DEFAULT_TYPE):
    term_key = random.choice(list(TERMS.keys()))
    term = TERMS[term_key]
    
    context.user_data["correct_answer"] = term["definition"]
    context.user_data["quiz_mode"] = "v"
    context.user_data["current_term"] = term_key
    
    await update.message.reply_text(
        f"🔤 *Что такое {term_key.upper()}?*\n\n"
        f"Напиши определение своими словами 👇",
        parse_mode="Markdown"
    )

# Режим Г — викторина с 4 вариантами
async def quiz_g(update: Update, context: ContextTypes.DEFAULT_TYPE):
    term_key = random.choice(list(TERMS.keys()))
    term = TERMS[term_key]
    
    # Берём 3 случайных неправильных ответа
    wrong_keys = [k for k in TERMS.keys() if k != term_key]
    wrong_choices = random.sample(wrong_keys, 3)
    
    # Перемешиваем все 4 варианта
    all_choices = [term_key] + wrong_choices
    random.shuffle(all_choices)
    
    # Сохраняем правильный ответ
    context.user_data["correct_answer"] = term_key
    context.user_data["quiz_mode"] = "g"
    
    # Делаем кнопки
    buttons = [[choice] for choice in all_choices]
    buttons.append(["🏠 Главное меню"])
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    await update.message.reply_text(
        f"📖 *Что это за термин?*\n\n"
        f"{term['definition']}\n\n"
        f"Выбери правильный ответ 👇",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# Проверяем ответ пользователя
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text.lower().strip()
    correct = context.user_data.get("correct_answer", "")
    mode = context.user_data.get("quiz_mode", "")
    
    if mode == "b" or mode == "g":
        # Ищем термин с учётом опечаток
        matched, score = find_term(user_answer, list(TERMS.keys()))
        if matched == correct or score > 80:
            await update.message.reply_text("✅ Правильно! Молодец! 🎉")
        else:
            await update.message.reply_text(
                f"❌ Неправильно\n\n"
                f"Правильный ответ: *{correct.upper()}*\n\n"
                f"💡 Подсказка: {TERMS[correct]['mnemonic_letters']}",
                parse_mode="Markdown"
            )
    
    elif mode == "v":
        # Для режима В просто показываем правильное определение
        await update.message.reply_text(
            f"📖 *Правильное определение:*\n\n"
            f"{correct}\n\n"
            f"Ты написал похоже? 🤔",
            parse_mode="Markdown"
        )
    
    # Сбрасываем режим
    context.user_data["quiz_mode"] = None