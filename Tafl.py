from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji
import os
import json
import asyncio
import random

# --- الإعدادات التي زودتها بها ---
API_ID = 26928420
API_HASH = '0facea2bb49930df0718fb74cda1790d'
BOT_TOKEN = '8468499654:AAHl8DaG0IOFH68CGCJvll0DMzrF8xfik8M' 
ADMIN_ID = 7199778669 

SESSION_FOLDER = 'accounts_sessions'
CHANNELS_FILE = 'channels.json'

if not os.path.exists(SESSION_FOLDER):
    os.makedirs(SESSION_FOLDER)

# إنشاء عميل بوت التحكم
bot = TelegramClient('control_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# دالة لتحميل البيانات
def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, 'r') as f: return json.load(f)
        except: return default
    return default

channels = load_data(CHANNELS_FILE, [])

def save_channels():
    with open(CHANNELS_FILE, 'w') as f:
        json.dump(channels, f)

# قائمة الإيموجيات
reaction_options = ['❤️', '🔥', '👍', '🥰', '👏', '🤩', '⚡', '💯', '🤣', '💎', '🌚', '🐳']

# --- واجهة الأزرار ---
def main_buttons():
    return [
        [Button.inline("📢 القنوات المضافة", b"view_ch"), Button.inline("➕ إضافة قناة", b"add_ch")],
        [Button.inline("🔐 تسجيل حساب جديد", b"add_acc"), Button.inline("📊 عدد الحسابات", b"count_acc")],
        [Button.inline("🚀 بدء التفاعل الآن", b"start_react"), Button.inline("🗑️ تفريغ القنوات", b"clear_ch")],
        [Button.url("المطور", "https://t.me/YourUsername")]
    ]

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id != ADMIN_ID: 
        return await event.respond("❌ عذراً، هذا البوت مخصص للمالك فقط.")
    await event.respond("🤖 **أهلاً بك في لوحة تحكم التفاعل التلقائي**\n\n1. أضف القنوات التي تريد مراقبتها.\n2. سجل حسابات التفاعل (أرقام الهاتف).\n3. اضغط على زر البدء لتشغيل المحرك.", buttons=main_buttons())

# --- معالجة الأزرار ---
@bot.on(events.CallbackQuery)
async def callback_handler(event):
    global channels
    if event.sender_id != ADMIN_ID: return
    data = event.data

    if data == b"view_ch":
        text = "📢 **القنوات المراقبة حالياً:**\n\n" + ("\n".join([f"- {c}" for c in channels]) if channels else "⚠️ لا توجد قنوات مضافة.")
        await event.edit(text, buttons=main_buttons())

    elif data == b"add_ch":
        async with bot.conversation(event.sender_id) as conv:
            await conv.send_message("📥 أرسل معرف القناة الآن مع الـ @ (مثال: @my_channel):")
            response = await conv.get_response()
            ch = response.text.strip()
            if ch not in channels:
                channels.append(ch)
                save_channels()
                await conv.send_message(f"✅ تمت إضافة القناة {ch} بنجاح.", buttons=main_buttons())

    elif data == b"count_acc":
        count = len([f for f in os.listdir(SESSION_FOLDER) if f.endswith('.session') and 'control_bot' not in f])
        await event.answer(f"📊 لديك {count} حساب تفاعل جاهز.", alert=True)

    elif data == b"clear_ch":
        channels = []
        save_channels()
        await event.edit("🗑️ تم مسح جميع القنوات.", buttons=main_buttons())

    elif data == b"add_acc":
        await add_account_logic(event)

    elif data == b"start_react":
        if not channels:
            await event.answer("⚠️ أضف قناة واحدة على الأقل أولاً!", alert=True)
            return
        await event.respond("🚀 جاري تشغيل المحرك وفحص الحسابات وانضمامها للقنوات...")
        asyncio.create_task(run_reaction_engine(event))

# --- إضافة حساب جديد ---
async def add_account_logic(event):
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("📱 أرسل رقم الهاتف (مثال: +9647XXXXXXXX):")
        phone_msg = await conv.get_response()
        phone = phone_msg.text.strip()
        
        session_name = os.path.join(SESSION_FOLDER, phone.replace('+', ''))
        client = TelegramClient(session_name, API_ID, API_HASH)
        
        await client.connect()
        if not await client.is_user_authorized():
            try:
                await client.send_code_request(phone)
                await conv.send_message(f"📩 أرسل كود التحقق المرسل لـ {phone}:")
                code_msg = await conv.get_response()
                code = code_msg.text.strip()
                await client.sign_in(phone, code)
            except Exception as e:
                from telethon.errors import SessionPasswordNeededError
                if isinstance(e, SessionPasswordNeededError):
                    await conv.send_message("🔐 الحساب محمي بكلمة سر (التحقق بخطوتين)، أرسلها الآن:")
                    pw_msg = await conv.get_response()
                    pw = pw_msg.text.strip()
                    await client.sign_in(password=pw)
                else:
                    await conv.send_message(f"❌ خطأ غير متوقع: {e}")
                    return
        
        me = await client.get_me()
        await conv.send_message(f"✅ تم بنجاح تسجيل: {me.first_name}\n(@{me.username if me.username else 'بدون يوزر'})", buttons=main_buttons())
        await client.disconnect()

# --- محرك التفاعل ---
async def run_reaction_engine(event):
    sessions = [f for f in os.listdir(SESSION_FOLDER) if f.endswith('.session') and 'control_bot' not in f]
    
    if not sessions:
        await event.respond("❌ لا توجد حسابات مسجلة! يرجى إضافة حساب أولاً.")
        return

    clients = []
    for s in sessions:
        path = os.path.join(SESSION_FOLDER, s.replace('.session', ''))
        c = TelegramClient(path, API_ID, API_HASH)
        try:
            await c.start()
            clients.append(c)
        except: continue

    @events.register(events.NewMessage(chats=channels))
    async def handler(new_msg_event):
        # اختيار إيموجي واحد لكل منشور لضمان تفاعل كل الحسابات بنفس الإيموجي أو عشوائي
        chosen_emoji = random.choice(reaction_options)
        for client in clients:
            try:
                await client(SendReactionRequest(
                    peer=new_msg_event.chat_id,
                    msg_id=new_msg_event.id,
                    reaction=[ReactionEmoji(chosen_emoji)]
                ))
            except: continue

    for client in clients:
        client.add_event_handler(handler)
        for ch in channels:
            try: await client(JoinChannelRequest(ch))
            except: pass

    await event.respond(f"✅ المحرك يعمل الآن!\n📡 عدد الحسابات النشطة: {len(clients)}\n📢 تراقب {len(channels)} قناة.")
    
    await asyncio.gather(*[client.run_until_disconnected() for client in clients])

print("--- البوت قيد التشغيل الآن ---")
bot.run_until_disconnected()
