from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ОСНОВНЫЕ КЛАВИАТУРЫ
def get_main_parent_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Добавить задание")],
            [KeyboardButton(text="🔄 Добавить недельные задания")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="💵 Наградить")],
            [KeyboardButton(text="🚪 Выход")]
        ],
        resize_keyboard=True
    )

def get_main_child_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Мои задания")],
            [KeyboardButton(text="⭐ Мои звезды")],
            [KeyboardButton(text="🚪 Выход")]
        ],
        resize_keyboard=True
    )

def get_children_keyboard(children):
    """Клавиатура для выбора ребенка"""
    keyboard_buttons = []
    for child in children:
        keyboard_buttons.append([KeyboardButton(text=child.capitalize())])
    keyboard_buttons.append([KeyboardButton(text="🔙 Назад")])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard_buttons,
        resize_keyboard=True
    )

def get_tasks_keyboard(tasks):
    """Клавиатура с заданиями"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for task in tasks:
        task_id, child_name, task_text, stars_reward, is_completed, is_weekly, completed_at, created_at = task
        if not is_completed:
            emoji = "🔄 " if is_weekly else ""
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{emoji}{task_text} (+{stars_reward}⭐)", 
                    callback_data=f"complete:{task_id}"
                )
            ])
    
    return keyboard

def get_reset_stars_keyboard(children_with_stars):
    """Клавиатура для обнуления звезд"""
    keyboard_buttons = []
    for child_name, stars in children_with_stars:
        keyboard_buttons.append([KeyboardButton(text=f"💵 {child_name.capitalize()} ({stars}⭐)")])
    keyboard_buttons.append([KeyboardButton(text="🔙 Назад")])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard_buttons,
        resize_keyboard=True
    )