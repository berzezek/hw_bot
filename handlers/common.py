from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
import config
from keyboards import get_main_child_keyboard, get_main_parent_keyboard

# Создаем роутер
router = Router()

db = Database()

class LoginState(StatesGroup):
    waiting_for_password = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # Проверяем текущую сессию
    current_user = db.get_current_user(message.from_user.id)
    
    if current_user:
        if current_user == "parent":
            await send_parent_menu(message)
        else:
            await show_child_interface(message, current_user)
        return
    
    await message.answer("👋 Добро пожаловать! Введите пароль:")
    await state.set_state(LoginState.waiting_for_password)

@router.message(LoginState.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    
    # Определяем кто входит по паролю
    user_type = None
    for user, pwd in config.PASSWORDS.items():
        if password == pwd:
            user_type = user
            break
    
    if user_type == "parent":
        db.set_current_user(message.from_user.id, "parent")
        await message.answer("✅ Вы вошли как родитель!", reply_markup=get_main_parent_keyboard())
        await state.clear()
    
    elif user_type in ["djama", "ramz", "riza"]:
        db.set_current_user(message.from_user.id, user_type)
        stars = db.get_child_stars(user_type)
        await message.answer(
            f"✅ Привет, {user_type.capitalize()}!\n⭐ Твои звезды: {stars}",
            reply_markup=get_main_child_keyboard()
        )
        await state.clear()
    
    else:
        await message.answer("❌ Неверный пароль. Попробуйте еще раз:")

async def send_parent_menu(message: types.Message):
    await message.answer("👨‍👩‍👧‍👦 Панель родителя:", reply_markup=get_main_parent_keyboard())

async def show_child_interface(message: types.Message, child_name: str):
    stars = db.get_child_stars(child_name)
    await message.answer(
        f"👤 {child_name.capitalize()}\n⭐ Звезды: {stars}",
        reply_markup=get_main_child_keyboard()
    )