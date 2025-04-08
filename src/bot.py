from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from sqlalchemy.orm import Session
from models import engine, User, UserChannel, Entity, news_entity_link, Digest
from parser_init import parse
from datetime import datetime
import asyncio

START_DATE, END_DATE, ADD_CHANNEL, REMOVE_CHANNEL = range(4)  # Добавили REMOVE_CHANNEL
session = Session(engine)

ADMIN_ID = 123456789
is_parsing = False

def is_admin(user_id):
    return user_id == ADMIN_ID

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
        [KeyboardButton("➖ Удалить из избранного")],  # Кнопка для удаления
        [KeyboardButton("🌐 Открыть веб-приложение")],
        [KeyboardButton("🛠 Админ-панель")]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=markup)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_parsing
    if is_parsing:
        await update.message.reply_text("❗ Парсинг в процессе. Пожалуйста, подождите.")
        return

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

    elif text == "➖ Удалить из избранного":  # Новый блок для удаления
        user_id = update.effective_user.id
        db_user = session.query(User).filter_by(telegram_id=user_id).first()
        favorites = session.query(UserChannel).filter_by(user_id=db_user.id).all()
        if not favorites:
            await update.message.reply_text("У вас нет избранных каналов для удаления.")
        else:
            msg = "\n".join([f"{i+1}. {ch.channel_url}" for i, ch in enumerate(favorites)])
            await update.message.reply_text(f"Выберите канал для удаления:\n{msg}")
            context.user_data['favorites'] = favorites
            return REMOVE_CHANNEL

    elif text == "🌐 Открыть веб-приложение":
        await update.message.reply_text("Введите дату начала (ГГГГ-ММ-ДД):")
        return START_DATE

    elif text == "🛠 Админ-панель":
        await update.message.reply_text("🛠 В разработке.")

async def get_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['start_date'] = update.message.text
    await update.message.reply_text("Введите дату конца (ГГГГ-ММ-ДД):")
    return END_DATE

async def get_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_date = context.user_data['start_date']
    end_date = update.message.text

    try:
        # Проверим формат дат
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')

        # После получения дат открываем веб-приложение с параметрами
        url = f"https://news-bomb-production.up.railway.app/?start_date={start_date}&end_date={end_date}"
        await update.message.reply_text(f"Открою веб-приложение с датами:\nНачало: {start_date}\nКонец: {end_date}",
                                       reply_markup=ReplyKeyboardMarkup([[
                                           KeyboardButton("Открыть приложение", web_app=WebAppInfo(url))
                                       ]]))
    except ValueError:
        await update.message.reply_text("❌ Неверный формат даты. Пожалуйста, введите даты в формате ГГГГ-ММ-ДД.")
        return END_DATE

    return ConversationHandler.END

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

async def remove_from_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    try:
        channel_index = int(choice) - 1
        favorites = context.user_data['favorites']
        if 0 <= channel_index < len(favorites):
            channel_to_remove = favorites[channel_index]
            session.delete(channel_to_remove)
            session.commit()
            await update.message.reply_text(f"✅ Канал {channel_to_remove.channel_url} удален из избранного.")
        else:
            await update.message.reply_text("❌ Неверный выбор.")
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите номер канала.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено.")
    return ConversationHandler.END

# Функции для админ-панели
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа к админ-панели.")
        return

    keyboard = [
        [KeyboardButton("Просмотреть всех пользователей")],
        [KeyboardButton("Удалить пользователя")],
        [KeyboardButton("Просмотр статистики парсинга")]
    ]
    markup = ReplyKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 Админ-панель:", reply_markup=markup)

async def view_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = session.query(User).all()
    user_list = "\n".join([f"ID: {user.id}, Telegram: {user.telegram_id}, Username: {user.username}" for user in users])
    await update.message.reply_text(f"Все пользователи:\n{user_list}")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите ID пользователя для удаления:")

async def view_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = "Статистика парсинга пока не доступна."
    await update.message.reply_text(stats)

def main():
    app = Application.builder().token("YOUR_BOT_TOKEN").build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)],
        states={
            START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_start_date)],
            END_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_end_date)],
            ADD_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_to_favorites)],
            REMOVE_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_from_favorites)],  # Новый state
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
