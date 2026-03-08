import os
import time
import tempfile
import asyncio
import yt_dlp
import nest_asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

nest_asyncio.apply()

# ========= ضع التوكن الجديد هنا =========
TOKEN = "8519890988:AAFsVFOihnAdFFjNXxQMwyf0yFCRnd5LDmk"
MAX_SEND_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# ========= أزرار =========
MAIN_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📥 تحميل فيديو", callback_data="download")]
])

BACK_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
])

# ========= تحميل الفيديو =========
def download_video(url):
    path = os.path.join(
        tempfile.gettempdir(),
        f"video_{int(time.time())}.mp4"
    )

    ydl_opts = {
        "format": "best",
        "outtmpl": path,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "retries": 5,
        "quiet": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return path if os.path.exists(path) else None

# ========= /start =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 أرسل رابط فيديو من:\n"
        "YouTube - TikTok - Instagram - Facebook",
        reply_markup=MAIN_KEYBOARD
    )

# ========= استقبال الرابط =========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting"):
        return

    context.user_data["waiting"] = False
    wait_msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        path = await asyncio.to_thread(download_video, update.message.text.strip())
    except Exception as e:
        print("ERROR:", e)
        await wait_msg.edit_text(f"❌ خطأ:\n{e}")
        return

    if not path:
        await wait_msg.edit_text("❌ فشل التحميل")
        return

    if os.path.getsize(path) > MAX_SEND_SIZE:
        await wait_msg.edit_text("❌ الفيديو أكبر من 2GB")
        os.remove(path)
        return

    with open(path, "rb") as video:
        await update.message.reply_video(video=video)

    os.remove(path)
    await wait_msg.delete()

# ========= الأزرار =========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "download":
        context.user_data["waiting"] = True
        await query.edit_message_text(
            "📥 أرسل رابط الفيديو:",
            reply_markup=BACK_KEYBOARD
        )

    elif query.data == "back":
        context.user_data.clear()
        await query.edit_message_text(
            "🎬 أرسل رابط فيديو",
            reply_markup=MAIN_KEYBOARD
        )

# ========= تشغيل البوت =========
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("✅ البوت يعمل...")
app.run_polling(drop_pending_updates=True)