import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN
from database import get_session
from models import get_random_video, get_favorite_videos, add_favorite, is_favorite, LEVEL_MAP
from wishes import WISHES
import random

user_data = {}

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Избранное", callback_data="favorites")],
        [InlineKeyboardButton("Святой рандом", callback_data="holy_random")],
        [InlineKeyboardButton("Подобрать тренировку", callback_data="choose_duration")]
    ]
    await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "choose_duration":
        keyboard = [[InlineKeyboardButton(d, callback_data=f"duration:{d}")] for d in ["до 15 минут", "до 30 минут", "до 60 минут"]]
        await query.edit_message_text("Выберите длительность:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("duration:"):
        user_data[user_id] = {"duration": query.data.split(":")[1]}
        keyboard = [[InlineKeyboardButton(l, callback_data=f"level:{l}")] for l in ["начинающий", "продолжающий", "продвинутый"]]
        await query.edit_message_text("Выберите уровень:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("level:"):
        user_data[user_id]["level"] = query.data.split(":")[1]
        session = get_session()
        video = get_random_video(session, user_data[user_id])
        if video:
            buttons = [[
                InlineKeyboardButton("❤️ В избранное", callback_data=f"fav:{video.id}"),
                InlineKeyboardButton("Избранное", callback_data="favorites")
            ]]
            await query.edit_message_text(text=video.title + "\n" + video.url, reply_markup=InlineKeyboardMarkup(buttons))
            await asyncio.sleep(video.duration_minutes * 60)
            await context.bot.send_message(chat_id=user_id, text=random.choice(WISHES))
        else:
            keyboard = [[InlineKeyboardButton("Святой рандом", callback_data="holy_random")]]
            await query.edit_message_text("Не найдено подходящих видео. Хотите святой рандом?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("fav:"):
        video_id = int(query.data.split(":")[1])
        session = get_session()
        if not is_favorite(session, user_id, video_id):
            add_favorite(session, user_id, video_id)
        await query.edit_message_text("Добавлено в избранное!")

    elif query.data == "favorites":
        session = get_session()
        favorites = get_favorite_videos(session, user_id)
        if favorites:
            text = "\n\n".join([f.title + "\n" + f.url for f in favorites])
        else:
            text = "У вас пока нет избранного."
        await query.edit_message_text(text)

    elif query.data == "holy_random":
        session = get_session()
        video = get_random_video(session, {})
        if video:
            await query.edit_message_text(text=video.title + "\n" + video.url)
        else:
            await query.edit_message_text("Не удалось найти видео.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
