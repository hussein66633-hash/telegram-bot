import telethon
from telethon import TelegramClient, events
import asyncio

# ---------------------------------
# ⚡ بيانات البوت
# ---------------------------------
app_id = 25875948
api_hash = 'bbc8cd4753b320c932bd56254d2917a0'

# إنشاء البوت
ArsThon = TelegramClient("sessions", app_id, api_hash)
ArsThon.start()
print("The Tool is Running... ")

# ---------------------------------
# 📝 الحدث الرئيسي للرد على الرسائل
# ---------------------------------
@ArsThon.on(events.NewMessage(outgoing=True, pattern=r"s (\d+) (\d+)"))
async def swing(event):
    if event.is_reply:
        geteventText = event.text.split()
        sleps = int(geteventText[1])
        renge = int(geteventText[2])
        chatId = event.chat_id
        message = await event.get_reply_message()

        for i in range(renge):
            await asyncio.sleep(sleps)
            await ArsThon.send_message(chatId, message)

        await ArsThon.send_message("me", f"Automatic deployment completed in : {chatId}")
    else:
        await event.edit("You must reply to the message to be repeated ")

# ---------------------------------
# 🌟 Keep-Alive داخلي للحفاظ على التشغيل
# ---------------------------------
async def keep_alive():
    while True:
        try:
            # مجرد sleep يحافظ على process حية
            await asyncio.sleep(60)
        except Exception:
            pass

# تشغيل Keep-Alive
ArsThon.loop.create_task(keep_alive())

# تشغيل البوت
ArsThon.run_until_disconnected()