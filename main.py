# ========================
# ИМПОРТЫ
# ========================
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from app.handlers import router
from app.database.models import init_db
import asyncio
import logging
from dotenv import load_dotenv
import os

load_dotenv()

# ========================
# ОСНОВНАЯ ФУНКЦИЯ
# ========================
async def main():
    """
    Главная функция бота:
    - Инициализирует базу данных
    - Создает бота и диспетчер
    - Запускает обработку сообщений
    """
    await init_db()
    
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    dp = Dispatcher()
    dp.include_router(router)
    
    await dp.start_polling(bot)

# ========================
# ТОЧКА ВХОДА
# ========================
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())