import logging
import asyncio
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from api import get_anime, get_manga, get_manhwa
from image_gen import download_image
from styles import (
    style_classic, style_full_bleed, style_modern, style_minimal,
    style_poster_focus, style_magazine, style_vertical,
    style_dark_gradient, style_anime_list, style_kenshin_special
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== HARDCODED CONFIGURATION ====================
BOT_TOKEN = "8689630171:AAGH6h7MKBTPNpWKs8CMiFu8oI9a3sQhImo"
BRANDING_IMAGE_URL = "https://files.catbox.moe/nl6m4u.jpg"
# ================================================================

# Load branding image
branding_img = None
if BRANDING_IMAGE_URL:
    try:
        branding_img = asyncio.run(download_image(BRANDING_IMAGE_URL))
        logger.info("Custom branding loaded")
    except Exception as e:
        logger.warning(f"Could not load branding image: {e}")

user_data = {}  # {chat_id: info_dict}

STYLES = [
    ("🎨 Classic Card", style_classic),
    ("🌀 Full Bleed", style_full_bleed),
    ("🔥 Modern Card", style_modern),
    ("✨ Minimalist", style_minimal),
    ("🎬 Poster Focus", style_poster_focus),
    ("📰 Magazine", style_magazine),
    ("📌 Vertical Banner", style_vertical),
    ("🌑 Dark Gradient", style_dark_gradient),
    ("📋 Anime List", style_anime_list),
    ("⚡ Kenshin Special", style_kenshin_special),
]

async def fetch_and_show_styles(update: Update, context: ContextTypes.DEFAULT_TYPE, title: str, media_type: str):
    chat_id = update.effective_chat.id
    msg = await update.message.reply_text(f"🔍 Searching for {title} ({media_type})...")
    try:
        if media_type == "anime":
            info = await get_anime(title)
        elif media_type == "manga":
            info = await get_manga(title)
        else:
            info = await get_manhwa(title)
        user_data[chat_id] = info

        page = 0
        total = len(STYLES)
        per_page = 5
        keyboard = []
        for i in range(per_page):
            idx = page * per_page + i
            if idx >= total: break
            keyboard.append([InlineKeyboardButton(STYLES[idx][0], callback_data=f"style_{idx}")])
        keyboard.append([InlineKeyboardButton("➡️ Next", callback_data=f"page_{page+1}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.edit_text(f"✅ Found: {info['title']}\nChoose a thumbnail style:", reply_markup=reply_markup)
        context.user_data['current_page'] = page
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ **KENSHIN ANIME Thumbnail Bot**\n\n"
        "Send:\n/anime <title>\n/manga <title>\n/manhwa <title>\n\n"
        "Example: /anime solo leveling\n/manga berserk\n/manhwa greatest estate developer\n\n"
        "Choose from 10 unique styles!",
        parse_mode="Markdown"
    )

async def anime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /anime <title>")
        return
    title = " ".join(context.args)
    await fetch_and_show_styles(update, context, title, "anime")

async def manga_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /manga <title>")
        return
    title = " ".join(context.args)
    await fetch_and_show_styles(update, context, title, "manga")

async def manhwa_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /manhwa <title>")
        return
    title = " ".join(context.args)
    await fetch_and_show_styles(update, context, title, "manhwa")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id
    info = user_data.get(chat_id)
    if not info:
        await query.edit_message_text("Session expired. Please search again.")
        return

    if data.startswith("style_"):
        idx = int(data.split("_")[1])
        style_name, style_func = STYLES[idx]
        await query.edit_message_text(f"🎨 Generating thumbnail with **{style_name}**...", parse_mode="Markdown")
        try:
            img_bytes = await style_func(info, branding_img)
            caption = f"✨ *{info['title']}* – {info['rating']:.1f}/10\n{info['synopsis'][:100]}...\n\n⚡ Powered by KENSHIN ANIME"
            await context.bot.send_photo(chat_id=chat_id, photo=img_bytes, caption=caption, parse_mode="Markdown")
            await query.delete_message()
        except Exception as e:
            await query.edit_message_text(f"❌ Generation failed: {str(e)}")
    elif data.startswith("page_"):
        page = int(data.split("_")[1])
        per_page = 5
        total = len(STYLES)
        keyboard = []
        for i in range(per_page):
            idx = page * per_page + i
            if idx >= total: break
            keyboard.append([InlineKeyboardButton(STYLES[idx][0], callback_data=f"style_{idx}")])
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page_{page-1}"))
        if (page+1)*per_page < total:
            nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}"))
        if nav:
            keyboard.append(nav)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("anime", anime_cmd))
    app.add_handler(CommandHandler("manga", manga_cmd))
    app.add_handler(CommandHandler("manhwa", manhwa_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler, pattern="^(style_|page_)"))
    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
