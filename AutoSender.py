import telethon
from telethon import TelegramClient, events
import asyncio 

app_id = 25875948

api_hash = 'bbc8cd4753b320c932bd56254d2917a0'


ArsThon = TelegramClient("sessions", app_id, api_hash)
ArsThon.start()

print("The Tool is Running... ")

@ArsThon.on(events.NewMessage(outgoing=True, pattern="s (.*) "))
async def swing(event):
	
	if event.is_reply:
		
		geteventText = "".join(event.text.split(maxsplit=0))[0:].split(" ")
		sleps = int(geteventText[1])
		
		renge = int(geteventText[2])
		
		chatId = event.chat_id
		
		message = await event.get_reply_message()
		
		for i in range(renge):
			
			await asyncio.sleep(sleps)
			
			await ArsThon.send_message(chatId, message)
		
		await ArsThon.send_message("me",f"Automatic deployment completed in : {chatId}")
		
	else:
		
		await event.edit("You must reply to the message to be repeated ")


ArsThon.run_until_disconnected()