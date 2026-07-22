import os
import re
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import asyncio
from concurrent.futures import ThreadPoolExecutor

# === تعطيل جميع رسائل الـ logging ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

# === بيانات البوت ===
TOKEN = "8519890988:AAGVKgrFDCNcftBuctZ00YU8lPWs92zPJKk"
OWNER_ID = 7199778669
DATA_FILE = "users_data.json"

DOWNLOAD_PATH = os.path.join(os.getcwd(), "downloads")

def ensure_download_folder():
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    return DOWNLOAD_PATH

ensure_download_folder()

user_states = {}
user_data = {}
executor = ThreadPoolExecutor(max_workers=10)

def load_data():
    global user_data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
        except:
            user_data = {}
    else:
        user_data = {}

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

def add_user(user_id, username, first_name):
    user_id_str = str(user_id)
    if user_id_str not in user_data:
        user_data[user_id_str] = {
            "username": username or "",
            "first_name": first_name or "",
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "downloads": [],
            "download_count": 0,
            "is_active": True
        }
        save_data()
    else:
        user_data[user_id_str]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_data[user_id_str]["is_active"] = True
        save_data()

def update_downloads(user_id, platform, link):
    user_id_str = str(user_id)
    if user_id_str in user_data:
        user_data[user_id_str]["download_count"] += 1
        user_data[user_id_str]["downloads"].append({
            "platform": platform,
            "link": link,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_data()

def get_stats():
    total_users = len(user_data)
    active_users = 0
    inactive_users = 0
    total_downloads = 0
    all_links = []
    
    for uid, data in user_data.items():
        try:
            last_active = datetime.strptime(data["last_active"], "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - last_active).days <= 30:
                active_users += 1
            else:
                inactive_users += 1
        except:
            inactive_users += 1
        total_downloads += data.get("download_count", 0)
        for d in data.get("downloads", []):
            all_links.append(d.get("link", ""))
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "total_downloads": total_downloads,
        "all_links": all_links
    }

def get_platform(url):
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "YouTube"
    elif "tiktok.com" in url_lower:
        return "TikTok"
    elif "instagram.com" in url_lower:
        return "Instagram"
    elif "facebook.com" in url_lower or "fb.com" in url_lower:
        return "Facebook"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "Twitter/X"
    else:
        return "غير معروف"

def download_video(url):
    platform = get_platform(url)
    ensure_download_folder()
    
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s_%(id)s.%(ext)s'),
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'extract_audio': False,
        'ignoreerrors': True,
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['hls', 'dash']
            }
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if info is None:
                raise Exception("لم يتم العثور على الفيديو")
            
            filename = ydl.prepare_filename(info)
            
            if os.path.exists(filename):
                return filename, platform
            
            for file in os.listdir(DOWNLOAD_PATH):
                if info.get('id', '') in file:
                    return os.path.join(DOWNLOAD_PATH, file), platform
            
            raise Exception("الملف لم يتم تحميله")
                
    except Exception as e:
        raise Exception(f"فشل التحميل: {str(e)}")

def main_menu_text():
    return """🎬 مرحباً بك في بوت تحميل الفيديو !

يمكنك تحميل فيديوهات من :
• YouTube
• TikTok
• Instagram
• Facebook
• Twitter/X

📌 الاستخدام :
1️⃣ اضغط على زر 'تحميل فيديو'
2️⃣ أرسل الرابط
3️⃣ انتظر التحميل

🤖 صانع البوت : @z_2w1"""

def main_menu_keyboard(user_id=None):
    keyboard = [
        [InlineKeyboardButton("📥 تحميل فيديو", callback_data="download")],
    ]
    
    if user_id == OWNER_ID:
        keyboard.append([InlineKeyboardButton("📊 الاحصائيات", callback_data="stats")])
        keyboard.append([InlineKeyboardButton("📢 اذاعة للجميع", callback_data="broadcast")])
    
    return InlineKeyboardMarkup(keyboard)

def back_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    add_user(user_id, user.username, user.first_name)
    
    await update.message.reply_text(
        main_menu_text(),
        reply_markup=main_menu_keyboard(user_id)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "download":
        user_states[user_id] = "waiting_for_link"
        await query.edit_message_text(
            "📥 ارسل رابط الفيديو الآن\n\nيدعم: YouTube - TikTok - Instagram - Facebook - Twitter/X",
            reply_markup=back_menu_keyboard()
        )
    
    elif data == "stats":
        if user_id != OWNER_ID:
            await query.edit_message_text(
                "⛔ هذه الخاصية متاحة للمالك فقط",
                reply_markup=back_menu_keyboard()
            )
            return
        
        try:
            stats = get_stats()
            stats_text = f"""📊 الاحصائيات التفصيلية

👥 المستخدمين الكلي: {stats['total_users']}
✅ نشطين (آخر 30 يوم): {stats['active_users']}
❌ غير نشطين: {stats['inactive_users']}

📥 عدد التحميلات الكلي: {stats['total_downloads']}"""
            
            await query.edit_message_text(
                stats_text,
                reply_markup=back_menu_keyboard()
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ حدث خطأ في جلب الاحصائيات:\n{str(e)}",
                reply_markup=back_menu_keyboard()
            )
    
    elif data == "broadcast":
        if user_id != OWNER_ID:
            await query.edit_message_text(
                "⛔ هذه الخاصية متاحة للمالك فقط",
                reply_markup=back_menu_keyboard()
            )
            return
        
        msg = await query.edit_message_text(
            "📢 ارسل الرسالة التي تريد إذاعتها لجميع المستخدمين",
            reply_markup=back_menu_keyboard()
        )
        user_states[user_id] = {"state": "waiting_for_broadcast", "msg_id": msg.message_id}
    
    elif data == "back":
        user_states.pop(user_id, None)
        await query.edit_message_text(
            main_menu_text(),
            reply_markup=main_menu_keyboard(user_id)
        )

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, url, platform, user_id, user, waiting_msg):
    filepath = None
    try:
        loop = asyncio.get_event_loop()
        filepath, platform = await loop.run_in_executor(executor, download_video, url)
        
        if not os.path.exists(filepath):
            raise Exception("الملف غير موجود بعد التحميل")
        
        update_downloads(user_id, platform, url)
        
        # حذف رسالة "جاري التحميل"
        await waiting_msg.delete()
        
        # إرسال الفيديو للمستخدم
        with open(filepath, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=None
            )
        
        # رسالة تأكيد للمستخدم
        await update.message.reply_text(
            f"✅ تم تحميل الفيديو من {platform}"
        )
        
        # إرسال للمالك
        if user_id != OWNER_ID:
            # إرسال الفيديو للمالك
            with open(filepath, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=OWNER_ID,
                    video=video_file,
                    caption=None
                )
            
            # إرسال التفاصيل للمالك
            owner_info = f"""📥 طلب تحميل جديد

الاسم: {user.first_name}
اليوزر نيم: @{user.username or 'لا يوجد'}
المنصه: {platform}
الرابط: {url}
التاريخ: {datetime.now().strftime('%Y-%m-%d')}
الوقت: {datetime.now().strftime('%H:%M:%S')}
ايدي المستخدم: {user_id}"""
            
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=owner_info
            )
        
        user_states.pop(user_id, None)
        
        # القائمة الرئيسية
        await update.message.reply_text(
            main_menu_text(),
            reply_markup=main_menu_keyboard(user_id)
        )
        
    except Exception as e:
        await waiting_msg.delete()
        await update.message.reply_text(
            f"❌ حدث خطأ أثناء التحميل:\n{str(e)}\n\nتأكد من:\n- الرابط صحيح\n- الفيديو غير محذوف"
        )
        await update.message.reply_text(
            main_menu_text(),
            reply_markup=main_menu_keyboard(user_id)
        )
    
    finally:
        # حذف الفيديو من الجهاز في جميع الأحوال
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"✅ تم حذف الملف: {filepath}")
            except Exception as e:
                print(f"❌ فشل حذف الملف: {e}")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text
    user = update.effective_user
    
    add_user(user_id, user.username, user.first_name)
    
    state_data = user_states.get(user_id)
    
    if isinstance(state_data, dict):
        state = state_data.get("state")
    else:
        state = state_data
    
    if state == "waiting_for_link":
        url = message_text.strip()
        
        if not re.match(r'https?://[^\s]+', url):
            await update.message.reply_text(
                "❌ رابط غير صحيح!\nأرسل رابط صحيح يبدأ بـ http:// أو https://",
                reply_markup=back_menu_keyboard()
            )
            return
        
        platform = get_platform(url)
        
        # رسالة "جاري التحميل"
        waiting_msg = await update.message.reply_text(
            f"⏳ جاري تحميل الفيديو من {platform}...\nيرجى الانتظار"
        )
        
        asyncio.create_task(download_and_send(update, context, url, platform, user_id, user, waiting_msg))
    
    elif state == "waiting_for_broadcast":
        if user_id == OWNER_ID:
            broadcast_text = message_text
            
            try:
                msg_id = state_data.get("msg_id")
                await context.bot.delete_message(chat_id=user_id, message_id=msg_id)
            except:
                pass
            
            try:
                await update.message.delete()
            except:
                pass
            
            sending_msg = await update.message.reply_text(
                f"⏳ جاري إرسال الإذاعة لجميع المستخدمين..."
            )
            
            sent_count = 0
            for uid in user_data.keys():
                try:
                    await context.bot.send_message(
                        chat_id=int(uid),
                        text=f"📢 اذاعة للجميع من المالك:\n\n{broadcast_text}"
                    )
                    sent_count += 1
                except:
                    pass
            
            await sending_msg.delete()
            
            await update.message.reply_text(
                f"✅ تم إرسال الإذاعة لـ {sent_count} مستخدم"
            )
            
            await update.message.reply_text(
                main_menu_text(),
                reply_markup=main_menu_keyboard(user_id)
            )
            
            user_states.pop(user_id, None)
        else:
            await update.message.reply_text(
                "⛔ غير مصرح لك بهذه الخاصية",
                reply_markup=main_menu_keyboard(user_id)
            )
    
    else:
        await update.message.reply_text(
            main_menu_text(),
            reply_markup=main_menu_keyboard(user_id)
        )

def main():
    load_data()
    ensure_download_folder()
    
    print("✅ تم تشغيل البوت")
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()