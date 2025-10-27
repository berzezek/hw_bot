import asyncio
from database import Database

db = Database()

async def reset_weekly_tasks():
    """Обнулить еженедельные задания"""
    db.delete_weekly_tasks()
    print("✅ Еженедельные задания обновлены")

async def weekly_scheduler():
    """Планировщик еженедельных заданий"""
    while True:
        await reset_weekly_tasks()
        # Ждем 7 дней
        await asyncio.sleep(7 * 24 * 60 * 60)