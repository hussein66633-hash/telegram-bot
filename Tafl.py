import os, json, asyncio, random
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import SendReactionRequest, DeleteMessagesRequest
from telethon.tl.types import ReactionEmoji

# ========= الإعدادات =========
API_ID = 26928420
API_HASH = '0facea2bb49930df0718fb74cda1790d'
BOT_TOKEN = '8468499654:AAHl8DaG0IOFH68CGCJvll0DMzrF8xfik8M'
ADMIN_ID = 7199778669

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FOLDER = os.path.join(BASE_DIR, 'accounts_sessions')
DATA_FILE = os.path.join(BASE_DIR, 'bot_data.json')

os.makedirs(SESSION_FOLDER, exist_ok=True)

def load_db():
    if os.path.exists(DATA_FILE):
        try: return json.load(open(DATA_FILE))
        except: pass
    return {"channels": {}, "codes": {}}

def save_db(d):
    with open(DATA_FILE, 'w') as f:
        json.dump(d, f, indent=2)

db = load_db()
bot = TelegramClient("control_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_states = {}
login_clients = {}
is_running = False
reactions = ['❤️','🔥','😍','😂','👍','👏','🥰']

def main_btns():
    status = "🟢 النظام يعمل حالياً" if is_running else "🛑 النظام متوقف الآن"
    return [
        [Button.inline("🔐 تسجيل حساب", b"add_acc")],
        [Button.inline("🚀 بدء التفاعل", b"start_react"), Button.inline("🛑 إيقاف التفاعل", b"stop_react")],
        [Button.inline("🛠️ صناعة كود", b"gen_code"), Button.inline("🔑 استخدام كود", b"redeem_code")],
        [Button.inline("➕ إضافة قناة", b"add_ch"), Button.inline("⌛ انتهاء الاشتراك", b"exp_btn")],
        [Button.inline("📡 القنوات المشتركة", b"sub_channels"), Button.inline("📊 الحسابات", b"count_acc")],
        [Button.inline(status, b"status")]
    ]

def welcome_text():
    return "🤖 مرحبا بك في بوت التفاعل التلقائي\n\nيمكنك التحكم من البوت من الأزرار في الأسفل 👇"

# ========= الأزرار (CallbackQuery) =========
@bot.on(events.CallbackQuery)
async def cb(event):
    global is_running
    if event.sender_id != ADMIN_ID: return
    data = event.data

    if data == b"back":
        user_states.pop(event.sender_id, None)
        await event.edit(welcome_text(), buttons=main_btns())
    
    elif data == b"add_ch":
        user_states[event.sender_id] = {"step": "WAIT_CH", "msg_id": event.message_id}
        await event.edit("📥 أرسل معرف القناة الآن (@username):", buttons=[[Button.inline("🔙 رجوع", b"back")]])

    elif data == b"gen_code":
        user_states[event.sender_id] = {"step": "CODE_NAME", "msg_id": event.message_id}
        await event.edit("✍️ اكتب اسم الكود الجديد:", buttons=[[Button.inline("🔙 رجوع", b"back")]])

    elif data == b"redeem_code":
        user_states[event.sender_id] = {"step": "USE_CODE", "msg_id": event.message_id}
        await event.edit("🔑 أدخل كود التفعيل:", buttons=[[Button.inline("🔙 رجوع", b"back")]])

    elif data == b"add_acc":
        user_states[event.sender_id] = {"step": "WAIT_PHONE", "msg_id": event.message_id}
        await event.edit("📱 أرسل الرقم مع رمز الدولة (+964xxx):", buttons=[[Button.inline("🔙 رجوع", b"back")]])

    elif data == b"sub_channels":
        if not db["channels"]:
            return await event.answer("❌ لا توجد قنوات حالياً", alert=True)
        btns = [[Button.inline(f"🗑 حذف {c}", f"del_{c}".encode())] for c in db["channels"]]
        btns.append([Button.inline("🔙 رجوع", b"back")])
        await event.edit("📡 القنوات المشتركة (اضغط للحذف):", buttons=btns)

    elif data.startswith(b"del_"):
        ch = data.decode()[4:]
        db["channels"].pop(ch, None)
        save_db(db)
        await event.answer(f"✅ تم حذف {ch}")
        if not db["channels"]: await event.edit(welcome_text(), buttons=main_btns())
        else:
            btns = [[Button.inline(f"🗑 حذف {c}", f"del_{c}".encode())] for c in db["channels"]]
            btns.append([Button.inline("🔙 رجوع", b"back")])
            await event.edit("📡 القنوات المشتركة:", buttons=btns)

    elif data == b"exp_btn":
        if not db["channels"]: return await event.answer("❌ لا توجد اشتراكات", alert=True)
        txt = "⌛ **مواعيد انتهاء الاشتراك:**\n\n"
        for ch, exp in db["channels"].items(): txt += f"• {ch} → {exp}\n"
        await event.edit(txt, buttons=[[Button.inline("🔙 رجوع", b"back")]])

    elif data == b"count_acc":
        cnt = len([f for f in os.listdir(SESSION_FOLDER) if f.endswith(".session")])
        await event.answer(f"📊 عدد الحسابات: {cnt}", alert=True)

    elif data == b"start_react":
        is_running = True
        await event.edit(welcome_text(), buttons=main_btns())

    elif data == b"stop_react":
        is_running = False
        await event.edit(welcome_text(), buttons=main_btns())

    elif data.startswith(b"ACT|"):
        _, code, ch = data.decode().split("|")
        if ch in db["codes"][code].get("used", []):
            return await event.answer("⚠️ هذه القناة استخدمت هذا الكود مسبقاً!", alert=True)
        
        days = db["codes"][code]["days"]
        current_date = db["channels"].get(ch, datetime.now().strftime("%Y-%m-%d"))
        new_date = datetime.strptime(current_date, "%Y-%m-%d") + timedelta(days=days)
        db["channels"][ch] = new_date.strftime("%Y-%m-%d")
        db["codes"][code]["used"].append(ch)
        save_db(db)
        await event.edit(f"✅ تم تفعيل اشتراك {ch} بنجاح!", buttons=[[Button.inline("🔙 رجوع", b"back")]])

# ========= الرسائل (NewMessage) =========
@bot.on(events.NewMessage)
async def msg_handler(event):
    if event.sender_id != ADMIN_ID or event.text.startswith('/'): return
    state = user_states.get(event.sender_id)
    if not state: return

    text, msg_id = event.text.strip(), state.get("msg_id")
    try: await bot.delete_messages(event.chat_id, [event.id])
    except: pass

    if state["step"] == "WAIT_CH":
        db["channels"][text] = (datetime.now()+timedelta(days=365)).strftime("%Y-%m-%d")
        save_db(db)
        user_states.pop(event.sender_id)
        await bot.edit_message(event.chat_id, msg_id, f"✅ تمت إضافة القناة {text} بنجاح!", buttons=[[Button.inline("🔙 رجوع", b"back")]])

    elif state["step"] == "CODE_NAME":
        state.update({"step": "CODE_DAYS", "code": text})
        await bot.edit_message(event.chat_id, msg_id, f"⏳ الكود: {text}\n✍️ اكتب مدة الاشتراك بالأيام:", buttons=[[Button.inline("🔙 رجوع", b"back")]])

    elif state["step"] == "CODE_DAYS" and text.isdigit():
        state.update({"step": "CODE_LIMIT", "days": int(text)})
        await bot.edit_message(event.chat_id, msg_id, f"👥 كود: {state['code']}\n✍️ أرسل عدد الأشخاص المسموح لهم:", buttons=[[Button.inline("🔙 رجوع", b"back")]])

    elif state["step"] == "CODE_LIMIT" and text.isdigit():
        db["codes"][state["code"]] = {"days": state["days"], "limit": int(text), "used": []}
        save_db(db)
        user_states.pop(event.sender_id)
        await bot.edit_message(event.chat_id, msg_id, f"✅ تم إنشاء كود `{state['code']}` بنجاح!", buttons=[[Button.inline("🔙 رجوع", b"back")]])

    elif state["step"] == "USE_CODE":
        if text not in db["codes"]: return await bot.edit_message(event.chat_id, msg_id, "❌ الكود غير صحيح!", buttons=[[Button.inline("🔙 رجوع", b"back")]])
        btns = [[Button.inline(ch, f"ACT|{text}|{ch}".encode())] for ch in db["channels"]]
        btns.append([Button.inline("🔙 رجوع", b"back")])
        await bot.edit_message(event.chat_id, msg_id, f"🔑 كود: {text}\n📡 اختر القناة لتفعيلها:", buttons=btns)

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.respond(welcome_text(), buttons=main_btns())

bot.run_until_disconnected()
