from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards import get_main_parent_keyboard, get_children_keyboard, get_reset_stars_keyboard
from default_tasks import WEEKLY_TASKS

# Создаем роутер
router = Router()

db = Database()

class ParentState(StatesGroup):
    waiting_for_child_selection = State()
    waiting_for_task = State()
    waiting_for_stars = State()

# ДОБАВЛЕНИЕ ЗАДАНИЙ
@router.message(lambda message: message.text == "📝 Добавить задание")
async def cmd_add_task(message: types.Message, state: FSMContext):
    children = db.get_all_children()
    await message.answer("👶 Для кого задание?", reply_markup=get_children_keyboard(children))
    await state.set_state(ParentState.waiting_for_child_selection)

@router.message(ParentState.waiting_for_child_selection)
async def process_child_selection(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await send_parent_menu(message)
        await state.clear()
        return
    
    child_name = message.text.lower()
    if child_name not in db.get_all_children():
        await message.answer("❌ Выберите ребенка из списка")
        return
    
    await state.update_data(child_name=child_name)
    await message.answer("📝 Введите задание:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ParentState.waiting_for_task)

@router.message(ParentState.waiting_for_task)
async def process_task_text(message: types.Message, state: FSMContext):
    await state.update_data(task_text=message.text)
    await message.answer("⭐ Сколько звезд?")
    await state.set_state(ParentState.waiting_for_stars)

@router.message(ParentState.waiting_for_stars)
async def process_task_stars(message: types.Message, state: FSMContext):
    try:
        stars = int(message.text)
        data = await state.get_data()
        db.add_task(data['child_name'], data['task_text'], stars)
        
        await message.answer(
            f"✅ Задание для {data['child_name'].capitalize()} добавлено!",
            reply_markup=get_main_parent_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число:")

# НЕДЕЛЬНЫЕ ЗАДАНИЯ
@router.message(lambda message: message.text == "🔄 Добавить недельные задания")
async def cmd_add_weekly_tasks(message: types.Message):
    # Добавляем недельные задания для всех детей
    db.add_tasks_for_all_children(WEEKLY_TASKS)
    
    task_count = sum(len(tasks) for tasks in WEEKLY_TASKS.values())
    await message.answer(
        f"✅ Недельные задания добавлены!\n"
        f"📝 Всего заданий: {task_count}\n"
        f"👥 Для всех детей",
        reply_markup=get_main_parent_keyboard()
    )

@router.message(lambda message: message.text  == "📊 Статистика")
async def cmd_tasks_and_stats(message: types.Message):
    from datetime import datetime

    stats = db.get_statistics()
    tasks = db.get_tasks()

    text = "📋 <b>Задания и статистика</b>\n\n"

    # Общая статистика
    text += f"✅ Выполнено: <b>{stats['total_completed']}</b>\n"
    text += f"📝 Ожидает выполнения: <b>{stats['total_pending']}</b>\n\n"

    # По детям
    for child_name, child_stats in stats["children"].items():
        text += (
            f"👤 <b>{child_name.capitalize()}</b>\n"
            f"   ✅ {child_stats['completed']} | 📝 {child_stats['pending']} | ⭐ {child_stats['stars']}\n\n"
        )

    # Последние выполненные задания
    recent_tasks_all = []
    for child_name, child_stats in stats["children"].items():
        recent_tasks_all.extend(child_stats["recent_tasks"])

    recent_tasks_all.sort(key=lambda x: x[6] or "", reverse=True)
    recent_tasks = recent_tasks_all[:5]

    if recent_tasks:
        text += "🕒 <b>Последние выполненные:</b>\n"
        for task in recent_tasks:
            task_id, child_name, task_text, stars_reward, is_completed, is_weekly, completed_at, created_at = task
            if completed_at:
                try:
                    dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    time_str = dt.strftime("%d.%m %H:%M")
                except:
                    time_str = "недавно"
                text += f"   {child_name.capitalize()}: {task_text} ({stars_reward}⭐, {time_str})\n"
        text += "\n"

    # Список текущих активных заданий
    if tasks:
        tasks_dict = {}
        for task in tasks:
            if task[1] not in tasks_dict:
                tasks_dict[task[1]] = []
            tasks_dict[task[1]].append(task)

        text += "📝 <b>Активные задания:</b>\n\n"
        for child_name, child_tasks in tasks_dict.items():
            text += f"👶 {child_name.capitalize()}:\n"
            for task in child_tasks:
                text += f"   - {task[2]} ({task[3]}⭐)\n"
            text += "\n"
    else:
        text += "❌ Активных заданий нет.\n"

    await message.answer(text, parse_mode="HTML", reply_markup=get_main_parent_keyboard())

# Награждение
@router.message(lambda message: message.text == "💵 Наградить")
async def cmd_reward(message: types.Message):
    # Находим детей с ненулевым балансом
    children = db.get_all_children()
    children_with_stars = []
    
    for child in children:
        stars = db.get_child_stars(child)
        if stars > 0:
            children_with_stars.append((child, stars))
    
    if not children_with_stars:
        await message.answer("💰 У всех детей 0 звезд!")
        return
    
    text = "💵 <b>Награждение</b>\n\nВыберите ребенка:\n"
    for child, stars in children_with_stars:
        text += f"👤 {child.capitalize()}: <b>{stars}⭐</b>\n"
    
    await message.answer(
        text,
        reply_markup=get_reset_stars_keyboard(children_with_stars),
        parse_mode="HTML"
    )

@router.message(lambda message: message.text.startswith("💵 "))
async def process_reset_stars(message: types.Message):
    # Извлекаем имя ребенка из текста кнопки
    child_name = message.text.replace("💵 ", "").split(" (")[0].lower()
    
    db.reset_child_stars(child_name)
    await message.answer(
        f"✅ Награжден {child_name.capitalize()}!\n"
        f"💫 Звезды ждут",
        reply_markup=get_main_parent_keyboard()
    )

# ВЫХОД
@router.message(lambda message: message.text == "🚪 Выход")
async def cmd_logout(message: types.Message):
    db.set_current_user(message.from_user.id, None)
    await message.answer("👋 Вы вышли!", reply_markup=types.ReplyKeyboardRemove())

async def send_parent_menu(message: types.Message):
    await message.answer("👨‍👩‍👧‍👦 Панель родителя:", reply_markup=get_main_parent_keyboard())