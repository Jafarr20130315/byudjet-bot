import os
import pandas as pd
from telegram import Update, Bot, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackContext
)

# === Bosqichlar ===
TIL, TOVAR, NARX = range(3)

# === Foydalanuvchini CSV faylda saqlash ===
def save_user_id(user_id):
    if os.path.exists("users.csv"):
        users_df = pd.read_csv("users.csv")
    else:
        users_df = pd.DataFrame(columns=["user_id"])

    if user_id not in users_df["user_id"].values:
        users_df.loc[len(users_df)] = [user_id]
        users_df.to_csv("users.csv", index=False)

# === /start komandasi ===
async def start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    save_user_id(user_id)

    keyboard = [
        [KeyboardButton("🇷🇺 Русский"), KeyboardButton("🇺🇿 O'zbek")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text("🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык:", reply_markup=reply_markup)
    return TIL

# === Tilni tanlash ===
async def tilni_tanlash(update: Update, context: CallbackContext) -> int:
    til = update.message.text
    if "Рус" in til:
        context.user_data["til"] = "rus"
        msg = (
            "Этот бот будет работать только тогда, когда его владелец его запустит!\n\n"
            "👋 Привет! Введите название товара."
        )
    else:
        context.user_data["til"] = "uzb"
        msg = (
            "Ushbu bot egasi qachon botni ishga tushirsa, o'shanda bot ishlaydi!\n\n"
            "👋 Salom! Tovar va narx kiritishni boshlaymiz. Tovar nomini yozing."
        )

    # Tilni almashtirish tugmasini berish
    til = context.user_data["til"]
    if til == "rus":
        buttons = [["🌀 ИЗМЕНИТЬ ЯЗЫК"]]
    else:
        buttons = [["🌀 TILNI ALMASHTIRISH"]]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)

    await update.message.reply_text(msg, reply_markup=reply_markup)
    return TOVAR

# === Tovar nomini olish ===
async def tovar(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if "ЯЗЫК" in text or "TILNI" in text:
        return await change_language(update, context)

    context.user_data["tovar"] = text
    til = context.user_data.get("til", "uzb")

    if til == "rus":
        await update.message.reply_text("Теперь введите цену товара:")
    else:
        await update.message.reply_text("Endi tovarning narxini kiriting:")
    return NARX

# === Narx olish va hisoblash ===
async def narx(update: Update, context: CallbackContext) -> int:
    til = context.user_data.get("til", "uzb")
    text = update.message.text

    if "ЯЗЫК" in text or "TILNI" in text:
        return await change_language(update, context)

    try:
        narx = float(text)
    except ValueError:
        if til == "rus":
            await update.message.reply_text("Неверный формат. Введите число.")
        else:
            await update.message.reply_text("Narxni noto'g'ri kiritdingiz. Iltimos, raqam kiriting.")
        return NARX

    tovar = context.user_data.get("tovar")
    if "hisob" not in context.user_data:
        context.user_data["hisob"] = 0
    context.user_data["hisob"] += narx

    if til == "rus":
        await update.message.reply_text(f"Товар: {tovar}\nЦена: {narx} сум\nОбщий счет: {context.user_data['hisob']} сум")
        await update.message.reply_text("Введите название следующего товара:")
    else:
        await update.message.reply_text(f"Tovar: {tovar}\nNarx: {narx} so'm\nUmumiy hisob: {context.user_data['hisob']} so'm")
        await update.message.reply_text("Yangi tovar nomini kiriting:")

    return TOVAR

# === Hisobni ko'rsatish ===
async def hisob(update: Update, context: CallbackContext) -> None:
    total = context.user_data.get("hisob", 0)
    til = context.user_data.get("til", "uzb")

    if til == "rus":
        await update.message.reply_text(f"Общий счет: {total} сум")
    else:
        await update.message.reply_text(f"Umumiy hisob: {total} so'm")

# === Tilni almashtirish ===
async def change_language(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [KeyboardButton("🇷🇺 Русский"), KeyboardButton("🇺🇿 O'zbek")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    til = context.user_data.get("til", "uzb")
    if til == "rus":
        await update.message.reply_text("Выберите язык:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Tilni tanlang:", reply_markup=reply_markup)

    return TIL

# === Main funksiyasi ===
async def main():
    global bot
    token = "8060933538:AAEs8l0PxrwoeIJSVjtGlEva0UE81d_T_DU"
    bot = Bot(token)
    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, tilni_tanlash)],
            TOVAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, tovar)],
            NARX: [MessageHandler(filters.TEXT & ~filters.COMMAND, narx)],
        },
        fallbacks=[CommandHandler("hisob", hisob)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("hisob", hisob))

    application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
