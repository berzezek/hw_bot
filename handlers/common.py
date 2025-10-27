from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
import config
from keyboards import get_main_child_keyboard, get_main_parent_keyboard, get_logout_keyboard, get_children_selection_keyboard

router = Router()
db = Database()

class LoginState(StatesGroup):
    waiting_for_password = State()
    waiting_for_child_selection = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # Проверяем, есть ли уже выбранный ребенок для этого Telegram пользователя
    current_child = db.get_current_child(message.from_user.id)
    
    if current_child:
        # Если уже выбран ребенок, показываем его меню
        await show_child_interface(message, current_child)
        return
    
    # Проверяем, есть ли доступные дети для переключения
    available_children = db.get_available_children(message.from_user.id)
    
    if available_children:
        # Если есть доступные дети, предлагаем выбрать
        await message.answer(
            "👋 Выберите ребенка или войдите как новый:",
            reply_markup=get_children_selection_keyboard(available_children)
        )
        await state.set_state(LoginState.waiting_for_child_selection)
        return
    
    # Если нет доступных детей, просим ввести пароль
    await message.answer("👋 Добро пожаловать! Введите пароль для входа:")
    await state.set_state(LoginState.waiting_for_password)

@router.message(LoginState.waiting_for_child_selection)
async def process_child_selection(message: types.Message, state: FSMContext):
    selected_child = message.text.strip()
    
    if selected_child == "➕ Новый ребенок":
        await message.answer("Введите пароль для нового ребенка:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(LoginState.waiting_for_password)
        return
    
    # Устанавливаем выбранного ребенка как текущего
    db.set_current_child(message.from_user.id, selected_child)
    await show_child_interface(message, selected_child)
    await state.clear()

@router.message(LoginState.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    
    if password == config.ADMIN_PASSWORD:
        # Родитель
        db.add_user(message.from_user.id, message.from_user.username, 'parent')
        db.set_current_child(message.from_user.id, "parent")
        await message.answer("✅ Вы вошли как родитель!", reply_markup=get_logout_keyboard())
        await send_parent_menu(message)
        await state.clear()
    
    elif password in config.CHILD_PASSWORDS.values():
        # Ребенок
        child_name = None
        for name, pwd in config.CHILD_PASSWORDS.items():
            if pwd == password:
                child_name = name
                break
        
        if child_name:
            # Создаем уникальный ID для ребенка на основе Telegram ID + имени
            child_user_id = hash(f"{message.from_user.id}_{child_name}") % 1000000000
            
            db.add_user(child_user_id, f"{message.from_user.username}_{child_name}", 'child', child_name)
            db.set_current_child(message.from_user.id, child_name)
            
            await message.answer(f"✅ Привет, {child_name.capitalize()}!", reply_markup=get_logout_keyboard())
            await show_child_interface(message, child_name)
            await state.clear()
        else:
            await message.answer("❌ Ошибка. Попробуйте еще раз:")
    else:
        await message.answer("❌ Неверный пароль. Попробуйте еще раз:")

async def show_child_interface(message: types.Message, child_name: str):
    """Показать интерфейс для выбранного ребенка"""
    user_data = db.get_user_by_child_name(child_name)
    if user_data:
        stars = user_data[4]
        await message.answer(
            f"👤 <b>{child_name.capitalize()}</b>\n⭐ Звезд: <b>{stars}</b>\n\nВыберите действие:",
            reply_markup=get_main_child_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Ошибка: данные ребенка не найдены")

async def send_parent_menu(message: types.Message):
    await message.answer("👨‍👩‍👧‍👦 Панель родителя:", reply_markup=get_main_parent_keyboard())

@router.message(Command("switch"))
async def cmd_switch(message: types.Message, state: FSMContext):
    """Команда для переключения между пользователями"""
    available_children = db.get_available_children(message.from_user.id)
    current_child = db.get_current_child(message.from_user.id)
    
    if not available_children:
        await message.answer("❌ Нет доступных пользователей для переключения.")
        return
    
    text = "🔄 <b>Переключение пользователей</b>\n\n"
    if current_child:
        text += f"Текущий: <b>{current_child.capitalize()}</b>\n\n"
    
    text += "Выберите пользователя:"
    
    await message.answer(
        text,
        reply_markup=get_children_selection_keyboard(available_children, current_child),
        parse_mode="HTML"
    )

@router.message(Command("logout"))
async def cmd_logout(message: types.Message, state: FSMContext):
    """Выход из текущего аккаунта"""
    db.set_current_child(message.from_user.id, None)
    await message.answer(
        "👋 Вы вышли из аккаунта. Используйте /start для входа в другой аккаунт.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()