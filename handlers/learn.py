import json
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from services.claude_api import find_term_by_meaning, generate_mnemonic

with open("data/terms.json", "r", encoding="utf-8") as f:
    TERMS = json.load(f)


async def show_term(update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
    await update.message.reply_text("🔍 Ищу термин...")

    term_key = await find_term_by_meaning(user_input, list(TERMS.keys()))

    if not term_key or term_key not in TERMS:
        await update.message.reply_text(
            "🤔 Не нашла такой термин...\n"
            "Попробуй написать по-другому!"
        )
        return

    context.user_data["current_term"] = term_key
    context.user_data["mnemonic_count"] = 0

    await send_card(update.message, context, term_key)


async def send_card(message, context, term_key):
    """Отправляет карточку термина — принимает message напрямую"""
    term = TERMS[term_key]
    count = context.user_data.get("mnemonic_count", 0)

    if "mnemonic_image" not in term or count > 0:
        await message.reply_text("✨ Придумываю образ...")
        mnemonic_text = await generate_mnemonic(term_key, term["definition"])
        context.user_data["current_mnemonic"] = mnemonic_text
    else:
        context.user_data["current_mnemonic"] = (
            f"📝 *Расшифровка:*\n{term['mnemonic_letters']}\n\n"
            f"🎨 *Образ:*\n{term['mnemonic_image']}"
        )

    mnemonic = context.user_data["current_mnemonic"]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Образ подходит!", callback_data="image_ok"),
            InlineKeyboardButton("🔄 Другой образ", callback_data="image_new")
        ]
    ])

    await message.reply_text(
        f"🔤 *{term_key.upper()}*\n\n"
        f"📖 *Определение:*\n{term['definition']}\n\n"
        f"{mnemonic}\n\n"
        f"💭 *Представь это ярко в голове!\n"
        f"Прочитай определение ещё раз и запомни образ* 👆",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    term_key = context.user_data.get("current_term")
    count = context.user_data.get("mnemonic_count", 0)

    if data == "image_new":
        if count >= 2:
            await query.message.reply_text(
                "😅 Я уже показала 3 варианта!\n"
                "Попробуй использовать последний образ — иногда нужно просто дать мозгу время 🧠"
            )
            return
        context.user_data["mnemonic_count"] = count + 1
        await send_card(query.message, context, term_key)
        return

    if data == "image_ok":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Представил!", callback_data="imagined_yes"),
                InlineKeyboardButton("❌ Не получается", callback_data="imagined_no")
            ]
        ])
        await query.message.reply_text(
            "🧠 *Отлично!*\n\n"
            "Теперь закрой глаза на 5 секунд...\n"
            "Представь образ ярко и в цвете 🎨\n"
            "Совмести его с определением термина\n\n"
            "Получилось представить?",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    elif data == "imagined_yes":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Вспомнил!", callback_data="recalled_yes"),
                InlineKeyboardButton("❌ Не вспомнил", callback_data="recalled_no")
            ]
        ])
        await query.message.reply_text(
            "💪 *Почти готово!*\n\n"
            "Не подглядывая — как называется этот термин?\n"
            "Попробуй вспомнить через образ 🤔",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    elif data == "imagined_no":
        context.user_data["mnemonic_count"] = 0
        await query.message.reply_text(
            "🔄 Ничего страшного! Давай ещё раз, не торопись 😊"
        )
        await send_card(query.message, context, term_key)

    elif data == "recalled_yes":
        await query.message.reply_text(
            f"🎉 *ОТЛИЧНО! Ты запомнил термин!*\n\n"
            f"*{term_key.upper()}* теперь твой! 🧬\n\n"
            f"Хочешь выучить ещё один термин или проверить себя?",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(
                [["📚 Учить термин", "🎮 Проверить себя"]],
                resize_keyboard=True
            )
        )

    elif data == "recalled_no":
        await query.message.reply_text(
            "💪 Не страшно! Повторение — мать учения!\n"
            "Смотрим ещё раз 👇"
        )
        context.user_data["mnemonic_count"] = 0
        await send_card(query.message, context, term_key)