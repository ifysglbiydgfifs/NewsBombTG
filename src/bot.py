from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters, ContextTypes
)
from sqlalchemy.orm import Session
from models import engine, User, UserChannel
from parser_init import parse
from datetime import datetime

START_DATE, END_DATE, ADD_CHANNEL = range(3)
session = Session(engine)

# Старт и добавление пользователя
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    username = user.username or ""

    existing_user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not existing_user:
        new_user = User(telegram_id=telegram_id, username=username, credits=0)
        session.add(new_user)
        session.commit()

    keyboard = [
        [KeyboardButton("▶️ Начать парсинг")],
        [KeyboardButton("⭐ Избранные каналы")],
        [KeyboardButton("➕ Добавить в избранное")],
        [KeyboardButton("🌐 Открыть веб-приложение")],
        [KeyboardButton("🛠 Админ-панель")]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=markup)


# Обработка нажатий
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "▶️ Начать парсинг":
        user_id = update.effective_user.id
        db_user = session.query(User).filter_by(telegram_id=user_id).first()
        favorites = session.query(UserChannel).filter_by(user_id=db_user.id).all()
        if not favorites:
            await update.message.reply_text("❗ Добавьте хотя бы один канал в избранное.")
            return ConversationHandler.END
        context.user_data['favorites'] = favorites
        await update.message.reply_text("Введите дату начала (ГГГГ-ММ-ДД):")
        return START_DATE

    elif text == "⭐ Избранные каналы":
        user_id = update.effective_user.id
        db_user = session.query(User).filter_by(telegram_id=user_id).first()
        favorites = session.query(UserChannel).filter_by(user_id=db_user.id).all()
        if not favorites:
            await update.message.reply_text("У вас нет избранных каналов.")
        else:
            msg = "\n".join([f"🔹 {ch.channel_url}" for ch in favorites])
            await update.message.reply_text(f"Ваши избранные каналы:\n{msg}")

    elif text == "➕ Добавить в избранное":
        await update.message.reply_text("Отправьте ссылку на канал:")
        return ADD_CHANNEL

    elif text == "🌐 Открыть веб-приложение":
        await update.message.reply_text(
            "Откройте веб-приложение:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Открыть", url="https://news-bomb-production.up.railway.app/")]
            ])
        )

    elif text == "🛠 Админ-панель":
        await update.message.reply_text("🛠 В разработке.")


# Получение даты начала
async def get_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['start_date'] = update.message.text
    await update.message.reply_text("Введите дату конца (ГГГГ-ММ-ДД):")
    return END_DATE


# Получение даты конца и парсинг
async def get_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        start_date = datetime.strptime(context.user_data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(update.message.text, '%Y-%m-%d')
        favorites = context.user_data['favorites']

        for fav in favorites:
            link = fav.channel_url
            channel_name = link.split("/")[-1]
            parse(link, start_date, end_date, channel_name)

        await update.message.reply_text(f"✅ Парсинг завершен.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    return ConversationHandler.END


# Добавление в избранное
async def add_to_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.effective_user.id
    db_user = session.query(User).filter_by(telegram_id=user_id).first()

    existing = session.query(UserChannel).filter_by(user_id=db_user.id, channel_url=url).first()
    if existing:
        await update.message.reply_text("🔁 Этот канал уже в избранном.")
    else:
        try:
            new_channel = UserChannel(user_id=db_user.id, channel_url=url)
            session.add(new_channel)
            session.commit()
            await update.message.reply_text("✅ Канал добавлен в избранное!")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при добавлении: {e}")
    return ConversationHandler.END


# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено.")
    return ConversationHandler.END


def main():
    app = Application.builder().token("7735571468:AAFlFNzK9K68hpkafy3e_GzHpYqqzzk722U").build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)],
        states={
            START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_start_date)],
            END_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_end_date)],
            ADD_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_to_favorites)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    app.run_polling()


if __name__ == '__main__':
    main()
