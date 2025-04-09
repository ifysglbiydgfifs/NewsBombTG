from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, Update, InlineKeyboardButton, \
    InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from sqlalchemy.orm import Session
from models import engine, User, UserChannel, Entity, news_entity_link, Digest, News
from parser_init import parse
from datetime import datetime
import asyncio

import parser_init
from clusterization import clusterization_start
from entities_extractor import extract_and_save_entities

START_DATE, END_DATE, ADD_CHANNEL, REMOVE_CHANNEL = range(4)  # Добавили REMOVE_CHANNEL
session = Session(engine)

ADMIN_ID = 123456789
is_parsing = False

keyboard = [
        [KeyboardButton("▶️ Начать парсинг")],
        [KeyboardButton("⭐ Избранные каналы")],
        [KeyboardButton("➕ Добавить в избранное")],
        [KeyboardButton("➖ Удалить из избранного")],
        [KeyboardButton("🌐 Открыть веб-приложение")],
        [KeyboardButton("🛠 Админ-панель")]
    ]
markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

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
        context.user_data['action'] = 'parse'
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

    elif text == "➖ Удалить из избранного":
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
        context.user_data['action'] = 'web'
        await update.message.reply_text("Введите дату начала (ГГГГ-ММ-ДД):")
        return START_DATE

    elif text == "🛠 Админ-панель":
        await update.message.reply_text("🛠 В разработке.")

async def get_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['start_date'] = update.message.text
    await update.message.reply_text("Введите дату конца (ГГГГ-ММ-ДД):")
    return END_DATE

async def get_end_date_parse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['is_busy'] = True

    try:
        start_date = datetime.strptime(context.user_data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(update.message.text, '%Y-%m-%d')
        favorites = context.user_data['favorites']

        await update.message.reply_text("🔄 Парсинг начался...", reply_markup=ReplyKeyboardRemove())

        anim_msg = await update.message.reply_text("🔄 Парсинг")
        previous_text = "🔄 Парсинг"

        for i in range(10):
            dots = "." * (i % 4)
            current_text = f"🔄 Парсинг{dots}"
            if current_text != previous_text:
                await anim_msg.edit_text(current_text)
                previous_text = current_text
            await asyncio.sleep(1.5)

        for fav in favorites:
            link = fav.channel_url
            channel_name = link.split("/")[-1]
            parse(link, start_date, end_date, channel_name)

        await anim_msg.delete()
        await update.message.reply_text("✅ Парсинг завершен.", reply_markup=markup)

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}", reply_markup=markup)
    finally:
        context.user_data['is_busy'] = False

    return ConversationHandler.END

async def get_end_date_web(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_date = context.user_data['start_date']
    end_date = update.message.text
    url = f"https://news-bomb-production.up.railway.app/?start_date={start_date}&end_date={end_date}"

    context.user_data['is_busy'] = True
    await update.message.reply_text("🔄 Выделение сущностей...", reply_markup=ReplyKeyboardRemove())

    anim_msg = await update.message.reply_text("🔄 Выделение сущностей")
    previous_text = "🔄 Выделение сущностей"

    try:
        for i in range(10):
            dots = "." * (i % 4)
            current_text = f"🔄 Выделение сущностей{dots}"
            if current_text != previous_text:
                await anim_msg.edit_text(current_text)
                previous_text = current_text
            await asyncio.sleep(1.5)

        session = Session(engine)
        session.query(news_entity_link).delete()
        session.query(Entity).delete()
        session.query(Digest).delete()
        session.commit()

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_ts = int(start_dt.timestamp() * 1000)
        end_ts = int(end_dt.timestamp() * 1000)

        messages = session.query(News).filter(News.time >= start_ts, News.time <= end_ts).all()

        if not messages:
            await anim_msg.delete()
            await update.message.reply_text("❌ Не найдено сообщений за указанный период.", reply_markup=markup)
            return ConversationHandler.END

        extract_and_save_entities(messages)
        clusterization_start()

        await anim_msg.delete()
        await update.message.reply_text(
            f"Открываю веб-приложение с датами: {start_dt.strftime('%Y-%m-%d')} по {end_dt.strftime('%Y-%m-%d')}.",
            reply_markup=markup
        )

        keyboard = [
            [InlineKeyboardButton("Открыть приложение", web_app=WebAppInfo(url))],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Перейдите по ссылке, чтобы увидеть новости:", reply_markup=reply_markup)

    except Exception as e:
        await anim_msg.delete()
        await update.message.reply_text(f"❌ Ошибка при обработке дат: {e}", reply_markup=markup)
    finally:
        context.user_data['is_busy'] = False

    return ConversationHandler.END

async def get_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    end_date = update.message.text
    context.user_data['end_date'] = end_date

    if context.user_data.get('action') == 'parse':
        return await get_end_date_parse(update, context)
    elif context.user_data.get('action') == 'web':
        return await get_end_date_web(update, context)

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
    app = Application.builder().token("7735571468:AAFlFNzK9K68hpkafy3e_GzHpYqqzzk722U").build()

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
