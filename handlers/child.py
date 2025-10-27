from aiogram import Router, types
from database import Database
from keyboards import get_main_child_keyboard, get_tasks_keyboard, get_children_keyboard

# Создаем роутер
router = Router()

db = Database()

# ЗАДАНИЯ
@router.message(lambda message: message.text == "📋 Мои задания")
async def cmd_my_tasks(message: types.Message):
    current_child = db.get_current_user(message.from_user.id)
    if not current_child:
        await message.answer("❌ Сначала войдите как сыночка через /start")
        return
    
    tasks = db.get_tasks(current_child, completed=False)
    
    if not tasks:
        await message.answer("📝 Нет 🎯!")
        return
    
    text = f"📋 <b>Задания для {current_child.capitalize()}</b>\n\n"
    # for task in tasks:
    #     task_id, child_name, task_text, stars_reward, is_completed, is_weekly, completed_at, created_at = task
    #     emoji = "🔄 " if is_weekly else ""
    #     text += f"{emoji}{task_text} <b>(+{stars_reward}⭐)</b>\n"
    
    await message.answer(text, reply_markup=get_tasks_keyboard(tasks), parse_mode="HTML")

# ЗВЕЗДЫ
@router.message(lambda message: message.text == "⭐ Мои звезды")
async def cmd_my_stars(message: types.Message):
    current_child = db.get_current_user(message.from_user.id)
    if not current_child or current_child == "parent":
        await message.answer("❌ Сначала войдите как сыночка через /start")
        return
    
    stars = db.get_child_stars(current_child)
    
    # Получаем разные типы заданий
    pending_reward_tasks = db.get_pending_reward_tasks(current_child)
    
    # Получаем общую статистику
    import sqlite3
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    # Всего выполненных заданий за все время
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE child_name = ? AND is_completed = TRUE", (current_child,))
    total_completed = cursor.fetchone()[0]
    
    # Ожидающие выполнения задания
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE child_name = ? AND is_completed = FALSE", (current_child,))
    pending_tasks = cursor.fetchone()[0]
    
    conn.close()
    
    text = f"⭐ <b>Статистика {current_child.capitalize()}</b>\n\n"
    
    # Текущий баланс
    text += f"💰 <b>Текущие звезды:</b> {stars}⭐\n\n"
    
    # Задания ожидающие награды
    if pending_reward_tasks:
        text += f"✅ <b>Ожидают награды:</b> {len(pending_reward_tasks)} 🎯\n"
        
        total_pending_stars = sum(task[3] for task in pending_reward_tasks)
        text += f"💫 <b>Будут начислены:</b> {total_pending_stars}⭐\n\n"
        
        text += "<b>Последние задания:</b>\n"
        for i, task in enumerate(pending_reward_tasks[:5], 1):
            task_id, child_name, task_text, stars_reward, is_completed, is_weekly, completed_at, created_at = task
            emoji = "🔄 " if is_weekly else ""
            text += f"   {i}. {emoji}{task_text} <b>(+{stars_reward}⭐)</b>\n"
        
        if len(pending_reward_tasks) > 5:
            text += f"   ... и еще {len(pending_reward_tasks) - 5}\n"
        
        text += "\n"
    
    # Общая статистика
    text += "📊 <b>Общая статистика:</b>\n"
    text += f"   ✅ Выполнено за все время: {total_completed} 🎯\n"
    text += f"   📝 Ожидает выполнения: {pending_tasks} 🎯\n"
    
    if pending_reward_tasks:
        text += f"   🎁 Ожидают 🏆: {len(pending_reward_tasks)} 🎯\n"
    
    # Мотивационные сообщения
    text += "\n"
    if stars == 0 and not pending_reward_tasks:
        text += "Выполняй 🎯 Зарабатывай ⭐ Получай 🏆"
    elif stars > 0:
        text += f"💫 У тебя {stars} ⭐ - Жди 🏆!"
    elif pending_reward_tasks:
        text += f"📋 Выполнено {len(pending_reward_tasks)} 🎯 - жди 🏆 в конце недели"
    
    await message.answer(text, parse_mode="HTML")

# ВЫПОЛНЕНИЕ ЗАДАНИЙ
@router.callback_query(lambda c: c.data.startswith('complete:'))
async def process_task_completion(callback: types.CallbackQuery):
    current_child = db.get_current_user(callback.from_user.id)
    if not current_child:
        await callback.answer("❌ Сначала войдите как сыночка")
        return
    
    task_id = int(callback.data.split(":")[1])
    earned_stars = db.complete_task(task_id, current_child)
    
    if earned_stars > 0:
        current_stars = db.get_child_stars(current_child)
        await callback.message.edit_text(
            f"🎉 Задание выполнено!\n"
            f"💫 Получено: {earned_stars}⭐\n"
            f"💰 Теперь у тебя: {current_stars}⭐"
        )
    else:
        await callback.message.edit_text("❌ Не удалось выполнить задание")
    
    await callback.answer()

# СМЕНА РЕБЕНКА
@router.message(lambda message: message.text == "🔄 Сменить ребенка")
async def cmd_switch_child(message: types.Message):
    children = db.get_all_children()
    if len(children) <= 1:
        await message.answer("❌ Нет других детей для переключения")
        return
    
    await message.answer("👥 Выберите ребенка:", reply_markup=get_children_keyboard(children))

@router.message(lambda message: message.text in [child.capitalize() for child in db.get_all_children()])
async def process_switch_child(message: types.Message):
    child_name = message.text.lower()
    db.set_current_child(message.from_user.id, child_name)
    stars = db.get_child_stars(child_name)
    
    await message.answer(
        f"✅ Теперь вы {child_name.capitalize()}!\n⭐ Звезды: {stars}",
        reply_markup=get_main_child_keyboard()
    )

# ВЫХОД
@router.message(lambda message: message.text == "🚪 Выход")
async def cmd_logout(message: types.Message):
    db.set_current_child(message.from_user.id, None)
    await message.answer("👋 Вы вышли!", reply_markup=types.ReplyKeyboardRemove())