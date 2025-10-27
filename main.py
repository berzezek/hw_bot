import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config
from database import Database
from utils.task_scheduler import initialize_weekly_tasks, weekly_task_scheduler, user_cleanup_scheduler

# Импорт handlers
from handlers.common import router as common_router
from handlers.child import router as child_router
from handlers.parent import router as parent_router

async def main():
    # Инициализация базы данных
    db = Database()
    if db:
        print("Database connected successfully.")
    
    # Инициализация бота
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация роутеров
    dp.include_router(common_router)
    dp.include_router(child_router)
    dp.include_router(parent_router)
    
    # Инициализация еженедельных заданий
    await initialize_weekly_tasks()
    
    # Запуск планировщиков
    asyncio.create_task(weekly_task_scheduler())
    asyncio.create_task(user_cleanup_scheduler())
    
    # Запуск бота
    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())