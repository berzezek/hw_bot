from aiogram import Router, types

from database import Database
from keyboards import get_tasks_keyboard, get_prizes_keyboard

router = Router()
db = Database()

@router.message(lambda message: message.text == "📝 Мои задания")
async def cmd_my_tasks(message: types.Message):
    current_child = db.get_current_child(message.from_user.id)
    if not current_child:
        await message.answer("❌ Сначала выберите ребенка через /start")
        return
    
    user_data = db.get_user_by_child_name(current_child)
    if not user_data:
        await message.answer("❌ Ошибка: данные ребенка не найдены")
        return
    
    child_name = current_child
    tasks = db.get_tasks(child_name, completed=False)
    completed_tasks = db.get_tasks(child_name, completed=True)
    
    if not tasks:
        await message.answer("📝 У тебя пока нет заданий! Задания обновляются каждую неделю ✨")
        return
    
    await message.answer("📝 Твои текущие задания:", reply_markup=get_tasks_keyboard(tasks, show_complete=True))
    
    if completed_tasks:
        await message.answer("✅ Выполненные задания:", reply_markup=get_tasks_keyboard(completed_tasks, show_complete=False))

@router.message(lambda message: message.text == "⭐ Мои звезды")
async def cmd_my_stars(message: types.Message):
    current_child = db.get_current_child(message.from_user.id)
    if not current_child:
        await message.answer("❌ Сначала выберите ребенка через /start")
        return
    
    user_data = db.get_user_by_child_name(current_child)
    if user_data:
        await message.answer(f"⭐ У {current_child.capitalize()} {user_data[4]} звезд!")

# @router.message(lambda message: message.text == "🎁 Обменять звезды")
# async def cmd_exchange(message: types.Message):
#     current_child = db.get_current_child(message.from_user.id)
#     if not current_child:
#         await message.answer("❌ Сначала выберите ребенка через /start")
#         return
    
#     prizes = db.get_prizes()
#     user_data = db.get_user_by_child_name(current_child)
    
#     if not prizes:
#         await message.answer("🎁 Пока нет призов для обмена!")
#         return
    
#     await message.answer(
#         f"⭐ У {current_child.capitalize()} {user_data[4]} звезд\n🎁 Выбери приз:",
#         reply_markup=get_prizes_keyboard(prizes)
#     )


@router.message(lambda message: message.text == "🚪 Выход")
async def cmd_logout_button(message: types.Message):
    db.set_current_child(message.from_user.id, None)
    await message.answer(
        "👋 Вы вышли из аккаунта. Используйте /start для входа.",
        reply_markup=types.ReplyKeyboardRemove()
    )

@router.callback_query(lambda c: c.data.startswith('complete_task:'))
async def process_task_completion(callback: types.CallbackQuery):
    current_child = db.get_current_child(callback.from_user.id)
    if not current_child:
        await callback.answer("❌ Сначала выберите ребенка")
        return
    
    task_id = int(callback.data.split(":")[1])
    child_name = current_child
    
    print(f"🔄 Начинаем выполнение задания {task_id} для ребенка '{child_name}' (Telegram ID: {callback.from_user.id})")
    
    # Передаем и имя ребенка и Telegram ID для надежности
    stars_earned = db.complete_task(task_id, child_name)
    
    if stars_earned > 0:
        # Получаем обновленное количество звезд
        current_stars = db.get_child_stars(child_name)
        
        print(f"✅ Задание выполнено! Звезд заработано: {stars_earned}, всего: {current_stars}")
        
        await callback.message.edit_text(
            f"🎉 Задание выполнено! Ты получил {stars_earned} звезд!\n\n"
            f"⭐ Теперь у тебя: {current_stars} звезд"
        )
    else:
        print(f"❌ Не удалось выполнить задание {task_id}")
        await callback.message.edit_text("❌ Не удалось выполнить задание. Возможно, оно уже выполнено.")
    
    await callback.answer()

def exchange_stars(self, user_id, prize_id):
    """Обменять звезды на приз"""
    conn = self._get_connection()
    cursor = conn.cursor()
    
    try:
        print(f"🔍 Начинаем обмен: user_id={user_id}, prize_id={prize_id}")
        
        # Получаем информацию о пользователе
        cursor.execute('SELECT user_id, stars, child_name, role FROM users WHERE user_id = ?', (user_id,))
        user_result = cursor.fetchone()
        
        if not user_result:
            print(f"❌ Пользователь с user_id {user_id} не найден")
            return False
        
        user_id_db, user_stars, child_name, role = user_result
        print(f"👤 Найден пользователь: {child_name} (роль: {role}), звезд: {user_stars}")
        
        # Получаем информацию о призе
        cursor.execute('SELECT prize_text, stars_cost, is_available FROM prizes WHERE id = ?', (prize_id,))
        prize_result = cursor.fetchone()
        
        if not prize_result:
            print(f"❌ Приз с id {prize_id} не найден")
            return False
        
        prize_text, prize_cost, is_available = prize_result
        print(f"🎁 Найден приз: {prize_text}, стоимость: {prize_cost}⭐, доступен: {is_available}")
        
        if not is_available:
            print(f"❌ Приз {prize_text} недоступен")
            return False
        
        print(f"💰 Проверка баланса: {user_stars}⭐ >= {prize_cost}⭐ = {user_stars >= prize_cost}")
        
        if user_stars < prize_cost:
            print(f"❌ Недостаточно звезд: {user_stars} < {prize_cost}")
            return False
        
        # Выполняем обмен
        new_balance = user_stars - prize_cost
        
        print(f"💸 Списание звезд: {user_stars} - {prize_cost} = {new_balance}")
        
        # Списание звезд
        cursor.execute(
            'UPDATE users SET stars = ? WHERE user_id = ?',
            (new_balance, user_id)
        )
        
        # Запись обмена
        cursor.execute(
            'INSERT INTO exchanges (user_id, prize_id, stars_spent) VALUES (?, ?, ?)',
            (user_id, prize_id, prize_cost)
        )
        
        conn.commit()
        print(f"✅ Обмен выполнен! {child_name} получил {prize_text}. Новый баланс: {new_balance}⭐")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обмене звезд: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()