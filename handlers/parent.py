from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards import get_main_parent_keyboard, get_child_selection_keyboard, get_admin_users_keyboard, get_parent_cash_out_keyboard, get_children_cash_out_keyboard, get_cash_out_confirmation_keyboard
from utils.task_scheduler import update_weekly_tasks
from .common import send_parent_menu

router = Router()
db = Database()

class ParentState(StatesGroup):
    waiting_for_child_name = State()
    waiting_for_task = State()
    waiting_for_stars = State()
    waiting_for_prize = State()
    waiting_for_prize_cost = State()
    waiting_for_cash_out_selection = State()

@router.message(lambda message: message.text == "👶 Добавить задание")
async def cmd_add_task(message: types.Message, state: FSMContext):
    await message.answer("👶 Для кого добавляем задание?", reply_markup=get_child_selection_keyboard())
    await state.set_state(ParentState.waiting_for_child_name)

@router.message(ParentState.waiting_for_child_name)
async def process_child_name(message: types.Message, state: FSMContext):
    child_name = message.text.lower().strip()
    if child_name == "all":
        await message.answer("❌ В разработке.")
        return
    await state.update_data(child_name=child_name)
    await message.answer("📝 Введите текст задания:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ParentState.waiting_for_task)

@router.message(ParentState.waiting_for_task)
async def process_task_text(message: types.Message, state: FSMContext):
    await state.update_data(task_text=message.text)
    await message.answer("⭐ Сколько звезд дать за выполнение?")
    await state.set_state(ParentState.waiting_for_stars)

@router.message(ParentState.waiting_for_stars)
async def process_task_stars(message: types.Message, state: FSMContext):
    try:
        stars = int(message.text)
        data = await state.get_data()
        
        db.add_task(data['child_name'], data['task_text'], stars)
        
        await message.answer(f"✅ Задание для {data['child_name'].capitalize()} добавлено!", 
                           reply_markup=get_main_parent_keyboard())
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число:")

@router.message(lambda message: message.text == "🎁 Добавить приз")
async def cmd_add_prize(message: types.Message, state: FSMContext):
    await message.answer("🎁 Введите описание приза:")
    await state.set_state(ParentState.waiting_for_prize)

@router.message(ParentState.waiting_for_prize)
async def process_prize_text(message: types.Message, state: FSMContext):
    await state.update_data(prize_text=message.text)
    await message.answer("⭐ Сколько звезд должен стоить приз?")
    await state.set_state(ParentState.waiting_for_prize_cost)

@router.message(ParentState.waiting_for_prize_cost)
async def process_prize_cost(message: types.Message, state: FSMContext):
    try:
        cost = int(message.text)
        data = await state.get_data()
        
        db.add_prize(data['prize_text'], cost)
        
        await message.answer("✅ Приз добавлен!", reply_markup=get_main_parent_keyboard())
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число:")

@router.message(lambda message: message.text == "📊 Общая статистика")
async def cmd_statistics(message: types.Message):
    import sqlite3
    from datetime import datetime, timedelta
    
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    # Получаем ВЫПОЛНЕННЫЕ задания всех детей
    cursor.execute("""
        SELECT 
            t.child_name,
            t.task_text,
            t.stars_reward,
            t.completed_at,
            u.stars as current_stars
        FROM tasks t
        LEFT JOIN users u ON u.child_name = t.child_name AND u.role = 'child'
        WHERE t.is_completed = TRUE
        ORDER BY t.completed_at DESC
    """)
    
    completed_tasks = cursor.fetchall()
    
    stats_text = "📊 <b>Статистика выполненных заданий</b>\n\n"
    
    if not completed_tasks:
        stats_text += "❌ Пока нет выполненных заданий\n"
        conn.close()
        await message.answer(stats_text, parse_mode="HTML")
        return
    
    # Группируем задания по детям
    tasks_by_child = {}
    for task in completed_tasks:
        child_name, task_text, stars_reward, completed_at, current_stars = task
        
        if child_name not in tasks_by_child:
            tasks_by_child[child_name] = {
                'tasks': [],
                'total_earned': 0,
                'current_stars': current_stars or 0
            }
        
        tasks_by_child[child_name]['tasks'].append({
            'text': task_text,
            'stars': stars_reward,
            'completed_at': completed_at
        })
        tasks_by_child[child_name]['total_earned'] += stars_reward
    
    # Выводим статистику по каждому ребенку
    for child_name, data in tasks_by_child.items():
        total_completed = len(data['tasks'])
        total_earned = data['total_earned']
        current_stars = data['current_stars']
        
        stats_text += f"👤 <b>{child_name.capitalize()}</b>\n"
        stats_text += f"   ✅ Выполнено заданий: <b>{total_completed}</b>\n"
        stats_text += f"   💰 Заработано звезд: <b>{total_earned}</b>\n"
        stats_text += f"   ⭐ Звезд сейчас: <b>{current_stars}</b>\n\n"
        
        # Последние 5 выполненных заданий (или все, если меньше 5)
        recent_tasks = data['tasks'][:5]
        stats_text += "   <b>Последние задания:</b>\n"
        
        for i, task in enumerate(recent_tasks, 1):
            # Форматируем дату выполнения
            completed_date = ""
            if task['completed_at']:
                try:
                    dt = datetime.fromisoformat(task['completed_at'].replace('Z', '+00:00'))
                    completed_date = dt.strftime(" (%d.%m)")
                except:
                    completed_date = ""
            
            stats_text += f"   {i}. {task['text']} <b>+{task['stars']}⭐</b>{completed_date}\n"
        
        # Если заданий больше 5, показываем сколько еще
        if len(data['tasks']) > 5:
            stats_text += f"   ... и еще <b>{len(data['tasks']) - 5}</b> заданий\n"
        
        stats_text += "\n"
    
    # Общая сводка по выполненным заданиям
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE is_completed = TRUE")
    total_completed_all = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(stars_reward) FROM tasks WHERE is_completed = TRUE")
    total_earned_all = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(stars) FROM users WHERE role = 'child'")
    total_stars_now = cursor.fetchone()[0] or 0
    
    stats_text += "🏆 <b>Общая сводка:</b>\n"
    stats_text += f"   📈 Всего выполнено: <b>{total_completed_all}</b> заданий\n"
    stats_text += f"   💰 Всего заработано: <b>{total_earned_all}</b> звезд\n"
    stats_text += f"   ⭐ На руках у детей: <b>{total_stars_now}</b> звезд\n"
    
    # Статистика за последнюю неделю
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(stars_reward), 0) 
        FROM tasks 
        WHERE is_completed = TRUE AND completed_at > ?
    """, (week_ago,))
    
    weekly_stats = cursor.fetchone()
    weekly_completed = weekly_stats[0] or 0
    weekly_earned = weekly_stats[1] or 0
    
    stats_text += f"   📅 За неделю: <b>{weekly_completed}</b> заданий, <b>{weekly_earned}</b> звезд\n"
    
    conn.close()
    
    await message.answer(stats_text, parse_mode="HTML")

@router.message(lambda message: message.text == "🔄 Обновить недельные задания")
async def cmd_refresh_weekly_tasks(message: types.Message):
    await update_weekly_tasks()
    await message.answer("✅ Еженедельные задания обновлены!", reply_markup=get_main_parent_keyboard())

@router.callback_query(lambda c: c.data == "refresh_users")
async def refresh_users_list(callback: types.CallbackQuery):
    """Обновить список пользователей"""
    users = db.get_all_users()
    
    if not users:
        await callback.message.edit_text("❌ Нет активных пользователей.")
        return
    
    users_text = "👥 Активные пользователи:\n\n"
    for user in users:
        user_id, username, role, child_name, stars, created_at, last_active = user
        role_emoji = "👨‍👩‍👧‍👦" if role == 'parent' else '👤'
        name = child_name.capitalize() if child_name else "Родитель"
        users_text += f"{role_emoji} {name}: {stars}⭐\n"
    
    await callback.message.edit_text(users_text, reply_markup=get_admin_users_keyboard())
    await callback.answer("Список обновлен!")

@router.callback_query(lambda c: c.data == "cleanup_users")
async def cleanup_inactive_users(callback: types.CallbackQuery):
    """Очистить неактивных пользователей"""
    deleted_count = db.cleanup_inactive_users()
    await callback.message.edit_text(f"✅ Удалено {deleted_count} неактивных пользователей.")
    await callback.answer()

@router.message(lambda message: message.text == "💵 Рассчитаться с ребенком")
async def cmd_cash_out_menu(message: types.Message):
    """Меню расчета с детьми"""
    await message.answer(
        "💵 <b>Расчет с детьми</b>\n\n"
        "Выберите действие:",
        reply_markup=get_parent_cash_out_keyboard(),
        parse_mode="HTML"
    )

@router.message(lambda message: message.text == "💵 Рассчитаться с ребенком")
async def cmd_cash_out_start(message: types.Message, state: FSMContext):
    """Начать процесс расчета с ребенком"""
    # Получаем детей у которых есть звезды
    import sqlite3
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT child_name, stars 
        FROM users 
        WHERE role = 'child' AND stars > 0 
        ORDER BY stars DESC
    ''')
    
    children_with_stars = cursor.fetchall()
    conn.close()
    
    if not children_with_stars:
        await message.answer(
            "💰 <b>Нет детей с звездами для расчета</b>\n\n"
            "Все дети уже получили свои награды! 🎉",
            parse_mode="HTML"
        )
        return
    
    # Формируем список детей
    children_text = "👥 <b>Дети с звездами:</b>\n\n"
    for child_name, stars in children_with_stars:
        children_text += f"👤 {child_name.capitalize()}: <b>{stars}⭐</b>\n"
    
    children_text += "\nВыберите ребенка для расчета:"
    
    children_names = [child[0] for child in children_with_stars]
    
    await message.answer(
        children_text,
        reply_markup=get_children_cash_out_keyboard(children_names),
        parse_mode="HTML"
    )
    await state.set_state(ParentState.waiting_for_cash_out_selection)

@router.message(ParentState.waiting_for_cash_out_selection)
async def process_cash_out_selection(message: types.Message, state: FSMContext):
    """Обработка выбора ребенка для расчета"""
    if message.text == "🔙 Назад":
        await send_parent_menu(message)
        await state.clear()
        return
    
    # Извлекаем имя ребенка из текста кнопки
    child_name = message.text.replace("💵 ", "").strip().lower()
    
    # Получаем текущие звезды ребенка
    current_stars = db.get_child_stars(child_name)
    
    if current_stars == 0:
        await message.answer(
            f"❌ У {child_name.capitalize()} уже 0 звезд!",
            reply_markup=get_parent_cash_out_keyboard()
        )
        await state.clear()
        return
    
    await message.answer(
        f"💵 <b>Подтверждение расчета</b>\n\n"
        f"👤 Ребенок: <b>{child_name.capitalize()}</b>\n"
        f"⭐ Текущие звезды: <b>{current_stars}</b>\n\n"
        f"После расчета звезды будут обнулены, и вы сможете выдать ребенку вознаграждение 💰",
        reply_markup=get_cash_out_confirmation_keyboard(child_name, current_stars),
        parse_mode="HTML"
    )
    await state.clear()

@router.callback_query(lambda c: c.data.startswith('confirm_cashout:'))
async def process_cash_out_confirmation(callback: types.CallbackQuery):
    """Подтверждение расчета с ребенком"""
    child_name = callback.data.split(":")[1]
    
    # Выполняем расчет
    cashed_out_stars = db.cash_out_stars(child_name)
    
    if cashed_out_stars > 0:
        await callback.message.edit_text(
            f"🎉 <b>Расчет завершен!</b>\n\n"
            f"👤 Ребенок: <b>{child_name.capitalize()}</b>\n"
            f"💫 Обнулено звезд: <b>{cashed_out_stars}⭐</b>\n\n"
            f"Теперь вы можете выдать ребенку вознаграждение! 💰",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"❌ <b>Не удалось выполнить расчет</b>\n\n"
            f"Возможно, у {child_name.capitalize()} уже 0 звезд.",
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(lambda c: c.data == "cancel_cashout")
async def process_cash_out_cancel(callback: types.CallbackQuery):
    """Отмена расчета"""
    await callback.message.edit_text(
        "❌ <b>Расчет отменен</b>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(lambda message: message.text == "📋 История расчетов")
async def cmd_cash_out_history(message: types.Message):
    """Показать историю расчетов"""
    history = db.get_cash_out_history()
    
    if not history:
        await message.answer(
            "📋 <b>История расчетов</b>\n\n"
            "Расчетов с детьми еще не было.",
            parse_mode="HTML"
        )
        return
    
    history_text = "📋 <b>История расчетов с детьми</b>\n\n"
    
    total_cashed_out = 0
    for record in history:
        exchanged_at, stars_spent, child_name = record
        
        # Форматируем дату
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(exchanged_at.replace('Z', '+00:00'))
            date_str = dt.strftime("%d.%m.%Y %H:%M")
        except:
            date_str = exchanged_at
        
        history_text += f"👤 {child_name.capitalize()}: <b>{stars_spent}⭐</b>\n"
        history_text += f"📅 {date_str}\n\n"
        
        total_cashed_out += stars_spent
    
    history_text += f"💫 <b>Всего выплачено: {total_cashed_out}⭐</b>"
    
    await message.answer(history_text, parse_mode="HTML")