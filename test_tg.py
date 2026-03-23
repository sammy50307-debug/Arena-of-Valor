import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

async def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    print('Token:', token[:10], '...')
    bot = Bot(token)
    try:
        await bot.send_message(chat_id='8457850038', text='Debug Message')
        print('Success!')
    except Exception as e:
        print('Error:', repr(e))

asyncio.run(main())
