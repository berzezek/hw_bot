import asyncio
import sqlite3
from datetime import datetime, timedelta
from database import Database
from default_tasks import get_weekly_tasks, save_last_update_date, get_last_update_date

db = Database()

async def check_and_update_weekly_tasks():
    """Проверить и обновить еженедельные задания"""
    last_update = get_last_update_date()
    now = datetime.now()
    
    # Проверяем, прошла ли неделя с последнего обновления
    if (now - last_update) >= timedelta(days=7):
        await update_weekly_tasks()
        save_last_update_date()
        print("Еженедельные задания обновлены!")

async def update_weekly_tasks():
    """Обновить еженедельные задания"""
    # Удаляем старые еженедельные задания
    db.delete_weekly_tasks()
    
    # Добавляем новые еженедельные задания для всех детей
    children = ["djama", "ramz", "riza"]  # Используем ваши имена детей
    for child in children:
        weekly_tasks = get_weekly_tasks(child)
        for task in weekly_tasks:
            db.add_task(child, task["text"], task["stars"], is_weekly=True)

async def weekly_task_scheduler():
    """Планировщик для еженедельного обновления заданий"""
    while True:
        await check_and_update_weekly_tasks()
        # Проверяем каждые 24 часа
        await asyncio.sleep(24 * 60 * 60)  # 24 часа

async def user_cleanup_scheduler():
    """Планировщик для очистки неактивных сессий"""
    while True:
        try:
            deleted_count = db.cleanup_inactive_users()
            if deleted_count > 0:
                print(f"Очищено {deleted_count} неактивных сессий")
            # Проверяем каждые 6 часов
            await asyncio.sleep(6 * 60 * 60)  # 6 часов
        except Exception as e:
            print(f"Ошибка в очистке сессий: {e}")
            await asyncio.sleep(60 * 60)  # Ждем 1 час при ошибке

async def initialize_weekly_tasks():
    """Инициализировать еженедельные задания при запуске бота"""
    await check_and_update_weekly_tasks()