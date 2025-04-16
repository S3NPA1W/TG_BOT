from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from app.handlers import router
from app.database.models import init_db
import asyncio
import logging
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    # Инициализация базы данных
    await init_db()
    
    # Создание бота и диспетчера
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    dp = Dispatcher()
    dp.include_router(router)
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())