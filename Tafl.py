from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji
import os
import json
import asyncio
import random

# --- الإعدادات الخاصة بك ---
API_ID = 26928420
API_HASH = '0facea2bb49930df0718fb74cda1790d'
BOT_TOKEN = '8468499654:AAHl8DaG0IOFH68CGCJvll0DMzrF8xfik8M' 
ADMIN_ID = 7199778669 

SESSION_FOLDER = 'accounts_sessions'
CHANNELS_FILE = 'channels.json'

if not os.path.exists(SESSION_FOLDER):
    os.makedirs(SESSION_FOLDER)

bot = TelegramClient('control_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# متغيرات الحالة
running_clients = []
is_running = False

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

# --- قائمة التفاعلات (حسب اختيارك وترتيبك) ---
reaction_options = [
    '❤️', '🥰', '😍', '❤️‍🔥', '🤩', '😘', '💘', '💯', '✨', '🌟',
    '🔥', '⚡', '🏆', '👏', '🙌', '💪', '🎉', '😂', '🤣', '😁', 
    '😄', '😆', '🥳', '😎', '👍', '👌', '🙏', '😇', '🫡', '🤝', 
    '🕊️', '🐳', '💔', '🥲', '😢', '🥺', '😟', '😭', '🌚', '🦄', '🍓'
]

# --- لوحة التحكم ---
def main_buttons():
    return [
        [Button.inline("📢 القنوات المضافة", b"view_ch"), Button.inline("➕ إضافة قناة", b"add_ch")],
        [Button.inline("🔐 تسجيل حساب جديد", b"add_acc"), Button.inline("📊 عدد الحسابات", b"count_acc")],
        [Button.inline("🚀 بدء التفاعل", b"start_react"), Button.inline("🛑 إيقاف التفاعل", b"stop_react")],
        [Button.inline("🗑️ تفريغ القنوات", b"clear_ch")]
    ]

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id != ADMIN_ID: return
    await event.respond("🤖 **لوحة تحكم بوت التفاعل التلقائي**\n\nتم تحديث قائمة التفاعلات حسب اختيارك. جاهز للعمل!", buttons=main_buttons())

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    global channels, is_running, running_clients
    if event.sender_id != ADMIN_ID: return
    data = event.data

    if data == b"view_ch":
        text = "📢 **القنوات المراقبة:**\n\n" + ("\n".join([f"- {c}" for c in channels]) if channels else "⚠️ القائمة فارغة.")
        await event.edit(text, buttons=main_buttons())

    elif data == b"add_ch":
        async with bot.conversation(event.sender_id) as conv:
            await conv.send_message("📥 أرسل معرف القناة (مثال: @username):")
            res = await conv.get_response()
            ch = res.text.strip()
            if ch not in channels:
                channels.append(ch)
                save_channels()
                await conv.send_message(f"✅ تمت إضافة {ch}", buttons=main_buttons())

    elif data == b"count_acc":
        count = len([f for f in os.listdir(SESSION_FOLDER) if f.endswith('.session') and 'control_bot' not in f])
        await event.answer(f"📊 لديك {count} حسابات.", alert=True)

    elif data == b"clear_ch":
        channels = []
        save_channels()
        await event.edit("🗑️ تم مسح القنوات.", buttons=main_buttons())

    elif data == b"add_acc":
        await add_account_logic(event)

    elif data == b"start_react":
        if is_running: return await event.answer("⚠️ يعمل بالفعل!", alert=True)
        if not channels: return await event.answer("⚠️ أضف قناة أولاً!", alert=True)
        await event.respond("🚀 جاري تشغيل المحرك...")
        asyncio.create_task(run_reaction_engine(event))

    elif data == b"stop_react":
        if not is_running: return await event.answer("⚠️ متوقف بالفعل.", alert=True)
        is_running = False
        for c in running_clients: await c.disconnect()
        running_clients = []
        await event.respond("🛑 تم إيقاف التفاعل وفصل الحسابات.", buttons=main_buttons())

# --- تسجيل حساب جديد ---
async def add_account_logic(event):
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("📱 أرسل الرقم (مثال: +964...):")
        phone = (await conv.get_response()).text.strip()
        session_name = os.path.join(SESSION_FOLDER, phone.replace('+', ''))
        client = TelegramClient(session_name, API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            await conv.send_message(f"📩 أرسل الكود لـ {phone}:")
            code = (await conv.get_response()).text.strip()
            try: await client.sign_in(phone, code)
            except Exception:
                await conv.send_message("🔐 أرسل رمز التحقق بخطوتين:")
                pw = (await conv.get_response()).text.strip()
                await client.sign_in(password=pw)
        await conv.send_message("✅ تم التسجيل بنجاح!", buttons=main_buttons())
        await client.disconnect()

# --- محرك التفاعل ---
async def run_reaction_engine(event):
    global is_running, running_clients
    sessions = [f for f in os.listdir(SESSION_FOLDER) if f.endswith('.session') and 'control_bot' not in f]
    
    if not sessions:
        await event.respond("❌ لا توجد حسابات مسجلة!")
        is_running = False
        return

    is_running = True
    for s in sessions:
        path = os.path.join(SESSION_FOLDER, s.replace('.session', ''))
        c = TelegramClient(path, API_ID, API_HASH)
        try:
            await c.start()
            running_clients.append(c)
        except: continue

    @events.register(events.NewMessage(chats=channels))
    async def handler(msg_event):
        for client in running_clients:
            try:
                await client(SendReactionRequest(
                    peer=msg_event.chat_id,
                    msg_id=msg_event.id,
                    reaction=[ReactionEmoji(random.choice(reaction_options))]
                ))
                await asyncio.sleep(0.3)
            except: continue

    for client in running_clients:
        client.add_event_handler(handler)
        for ch in channels:
            try: await client(JoinChannelRequest(ch))
            except: pass

    await event.respond(f"✅ المحرك يعمل الآن بـ {len(running_clients)} حساب!\n📢 القنوات المراقبة: {len(channels)}")
    
    while is_running: await asyncio.sleep(1)

print("--- البوت جاهز ---")
bot.run_until_disconnected()
