import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config
from database import Database

# Импорт обработчиков
from handlers.common import router as common_router
from handlers.parent import router as parent_router
from handlers.child import router as child_router

async def main():
    # Инициализация базы
    db = Database()
    
    # Инициализация бота
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация роутеров
    dp.include_router(common_router)
    dp.include_router(parent_router)
    dp.include_router(child_router)
    
    print("🤖 Бот запущен!")
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())