import json, os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler, ContextTypes, filters
)

BOT_TOKEN = "7838301513:AAFQ__L4cTZaV7-znwb3COSYWO4KWRH331A"
ADMIN_ID = 7199778669
DATA_FILE = "data.json"
BACK = "BACK"

# ----------------- DATA -----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "admin_messages": []}

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            d = json.load(f)
        except:
            return {"users": {}, "admin_messages": []}

    if "users" not in d: d["users"] = {}
    if "admin_messages" not in d: d["admin_messages"] = []

    for uid in d["users"]:
        u = d["users"][uid]
        if "groups" not in u: u["groups"] = []
        if "sending" not in u: u["sending"] = False
        if "step" not in u: u["step"] = None
        if "selected_messages" not in u: u["selected_messages"] = []
        if "delay" not in u: u["delay"] = 60
        if "repeat" not in u: u["repeat"] = 1

    return d

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

def get_user(uid):
    uid = str(uid)
    if uid not in data["users"]:
        data["users"][uid] = {
            "groups": [],
            "sending": False,
            "step": None,
            "selected_messages": [],
            "delay": 60,
            "repeat": 1
        }
        save_data()
    return data["users"][uid]

# ----------------- START -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return

    uid = update.effective_user.id
    text = "اهلاً بك\n\n⬇️ تحكم كامل من القائمة الرئيسية"

    keyboard = [
        [InlineKeyboardButton("📬 عرض الرسائل", callback_data="show")],
        [InlineKeyboardButton("⏱ اختيار الثواني", callback_data="delay"),
         InlineKeyboardButton("🔁 معدل التكرار", callback_data="repeat")],
        [InlineKeyboardButton("➕ إضافة كروب", callback_data="add_group"),
         InlineKeyboardButton("➖ حذف كروب", callback_data="remove_group")],
        [InlineKeyboardButton("📊 لوحة التحكم", callback_data="panel")],
        [InlineKeyboardButton("▶️ تشغيل الإرسال", callback_data="start_send"),
         InlineKeyboardButton("⏹ إيقاف الإرسال", callback_data="stop_send")]
    ]

    if uid == ADMIN_ID:
        keyboard.insert(0, [InlineKeyboardButton("➕ إضافة رسالة (أدمن)", callback_data="admin_add")])
        keyboard.insert(1, [InlineKeyboardButton("👥 عرض المستخدمين", callback_data="show_users")])

    markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=markup)

# ----------------- BUTTONS -----------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = get_user(q.from_user.id)
    d = q.data

    if d == BACK:
        await start(update, context)
        return

    # عرض الرسائل
    if d == "show":
        if not data["admin_messages"]:
            await q.message.edit_text(
                "📭 لا توجد رسائل",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع", callback_data=BACK)]])
            )
            return

        text = "📬 الرسائل الحالية:\n\n"
        btns = []

        for idx, m in enumerate(data["admin_messages"]):
            text += f"📄 الرسالة {idx+1}:\n{m}\n\n"
            btns.append([InlineKeyboardButton("🗑 حذف الرسالة", callback_data=f"delete_msg_{idx}")])

        btns.append([InlineKeyboardButton("↩️ رجوع", callback_data=BACK)])
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btns))

    elif d.startswith("delete_msg_"):
        idx = int(d.split("_")[2])
        if 0 <= idx < len(data["admin_messages"]):
            data["admin_messages"].pop(idx)
            # إزالة الفهرس من selected_messages لكل المستخدمين
            for u in data["users"].values():
                if idx in u["selected_messages"]:
                    u["selected_messages"].remove(idx)
            save_data()
            await q.message.reply_text("✅ تم حذف الرسالة")
        await start(update, context)

    # اختيار الثواني
    elif d == "delay":
        delay_buttons = [60, 120, 200, 300, 400, 500, 600, 800]
        btns, row = [], []
        for i, s in enumerate(delay_buttons, 1):
            row.append(InlineKeyboardButton(f"{s} ثانية", callback_data=f"set_delay_{s}"))
            if i % 2 == 0:
                btns.append(row); row = []
        if row: btns.append(row)
        btns.append([InlineKeyboardButton("↩️ رجوع", callback_data=BACK)])
        await q.message.edit_text("⏱ اختر الثواني", reply_markup=InlineKeyboardMarkup(btns))

    elif d.startswith("set_delay_"):
        user["delay"] = int(d.split("_")[2])
        save_data()
        await q.message.reply_text("✅ تم ضبط الثواني")

    # تكرار
    elif d == "repeat":
        user["step"] = "repeat"
        await q.message.reply_text("🔁 اكتب رقم التكرار أو inf")

    # لوحة التحكم
    elif d == "panel":
        msgs = len(data["admin_messages"])
        groups = len(user["groups"])
        daily = msgs * groups if user["repeat"] else "∞"
        await q.message.reply_text(
            f"📊 لوحة التحكم\n\n"
            f"👥 المستخدمين: {len(data['users'])}\n"
            f"👥 الكروبات: {groups}\n"
            f"📨 رسائل يومية: {daily}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع", callback_data=BACK)]])
        )

    # إضافة رسالة الأدمن
    elif d == "admin_add" and q.from_user.id == ADMIN_ID:
        user["step"] = "admin_msg"
        await q.message.reply_text("✍️ أرسل الرسالة لإضافتها")

    # إضافة كروب
    elif d == "add_group":
        user["step"] = "add_group"
        await q.message.reply_text("➕ أرسل يوزر الكروب")

    # حذف كروب
    elif d == "remove_group":
        user["step"] = "remove_group"
        await q.message.reply_text("➖ أرسل يوزر الكروب")

    # تشغيل الإرسال
    elif d == "start_send":
        if not user["groups"] or not user["selected_messages"]:
            await q.message.reply_text("❌ أضف كروبات ورسائل أولاً")
            return
        user["sending"] = True
        save_data()
        asyncio.create_task(sender(q.from_user.id, context))
        await q.message.reply_text("🚀 بدأ الإرسال")

    # إيقاف الإرسال
    elif d == "stop_send":
        user["sending"] = False
        save_data()
        await q.message.reply_text("⛔ تم الإيقاف")

    # عرض المستخدمين
    elif d == "show_users" and q.from_user.id == ADMIN_ID:
        text = "👥 المستخدمين:\n\n"
        for uid, u in data["users"].items():
            text += (
                f"🆔 {uid}\n"
                f"👥 كروبات: {len(u['groups'])}\n"
                f"⏱ تأخير: {u['delay']}\n"
                f"🔁 تكرار: {u['repeat']}\n\n"
            )
        await q.message.edit_text(
            text if text else "لا يوجد مستخدمين",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع", callback_data=BACK)]])
        )

# ----------------- INPUT -----------------
async def input_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    user = get_user(update.effective_user.id)
    if not user["step"]:
        return

    t = update.message.text.strip()

    # تكرار
    if user["step"] == "repeat":
        user["repeat"] = None if t.lower() == "inf" else int(t)

    # رسالة الأدمن + إضافة تلقائية لكل المستخدمين
    elif user["step"] == "admin_msg" and update.effective_user.id == ADMIN_ID:
        if t not in data["admin_messages"]:
            data["admin_messages"].append(t)
            msg_index = len(data["admin_messages"]) - 1
            for uid, u in data["users"].items():
                if msg_index not in u["selected_messages"]:
                    u["selected_messages"].append(msg_index)

    # إضافة كروب
    elif user["step"] == "add_group":
        if t not in user["groups"]:
            try:
                chat = await context.bot.get_chat(t)
                me = await context.bot.get_chat_member(chat.id, context.bot.id)
                if me.status in ["administrator", "creator"]:
                    user["groups"].append(t)
                    await update.message.reply_text("✅ تم إضافة الكروب")
            except:
                await update.message.reply_text("❌ يوزر غير صحيح")

    # حذف كروب
    elif user["step"] == "remove_group":
        if t in user["groups"]:
            user["groups"].remove(t)
            await update.message.reply_text("✅ تم حذف الكروب")

    user["step"] = None
    save_data()

# ----------------- SENDER -----------------
async def sender(uid, context):
    user = get_user(uid)
    count = 0
    while user["sending"]:
        for g in user["groups"]:
            for i in user["selected_messages"]:
                try:
                    await context.bot.send_message(g, data["admin_messages"][i])
                    await asyncio.sleep(user["delay"])
                except:
                    pass
        count += 1
        if user["repeat"] and count >= user["repeat"]:
            user["sending"] = False
            save_data()

# ----------------- RUN -----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, input_text))
app.run_polling()