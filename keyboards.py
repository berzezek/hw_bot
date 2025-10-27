from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_child_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Мои задания")],
            [KeyboardButton(text="⭐ Мои звезды")],
            # [KeyboardButton(text="🎁 Обменять звезды")],
            # [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🚪 Выход")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_main_parent_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👶 Добавить задание")],
            [KeyboardButton(text="🎁 Добавить приз")],
            [KeyboardButton(text="💵 Рассчитаться с ребенком")],  # Новая кнопка
            [KeyboardButton(text="📊 Общая статистика")],
            [KeyboardButton(text="🔄 Обновить недельные задания")],
            [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🚪 Выход")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_children_selection_keyboard(available_children, current_child=None):
    """Клавиатура для выбора ребенка"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    
    for child in available_children:
        if child != current_child:  # Не показываем текущего ребенка
            emoji = "👤" if child != "parent" else "👨‍👩‍👧‍👦"
            keyboard.add(KeyboardButton(text=f"{emoji} {child.capitalize()}"))
    
    keyboard.add(KeyboardButton(text="➕ Новый ребенок"))
    return keyboard

def get_logout_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚪 Выход")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_child_selection_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="djama"), KeyboardButton(text="ramz")],
            [KeyboardButton(text="riza"), KeyboardButton(text="all")],
        ],
        resize_keyboard=True,
    )
    return keyboard


def get_tasks_keyboard(tasks, show_complete=True):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for task in tasks:
        task_id, child_name, task_text, stars_reward, is_completed, is_weekly, *_ = task

        emoji = "🔄 " if is_weekly else ""
        if is_completed:
            button_text = f"✅ {emoji}{task_text} (+{stars_reward}⭐)"
            callback_data = f"view_task:{task_id}"
        else:
            button_text = f"{emoji}{task_text} (+{stars_reward}⭐)"
            callback_data = f"complete_task:{task_id}"

        if show_complete and not is_completed:
            keyboard.inline_keyboard.append(
                [InlineKeyboardButton(text=button_text, callback_data=callback_data)]
            )
        elif not show_complete:
            keyboard.inline_keyboard.append(
                [InlineKeyboardButton(text=button_text, callback_data=callback_data)]
            )

    return keyboard


def get_prizes_keyboard(prizes):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for prize in prizes:
        prize_id, prize_text, stars_cost, *_ = prize
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{prize_text} ({stars_cost}⭐)",
                    callback_data=f"exchange:{prize_id}",
                )
            ]
        )
    return keyboard


def get_admin_users_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Обновить список", callback_data="refresh_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧹 Очистить неактивных", callback_data="cleanup_users"
                )
            ],
        ]
    )
    return keyboard


def get_parent_cash_out_keyboard():
    """Клавиатура для расчета с детьми"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💵 Рассчитаться с ребенком")],
            [KeyboardButton(text="📋 История расчетов")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_children_cash_out_keyboard(children):
    """Клавиатура для выбора ребенка для расчета"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    
    for child in children:
        keyboard.add(KeyboardButton(text=f"💵 {child.capitalize()}"))
    
    keyboard.add(KeyboardButton(text="🔙 Назад"))
    return keyboard

def get_cash_out_confirmation_keyboard(child_name, stars):
    """Клавиатура подтверждения расчета"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ Да, рассчитаться ({stars}⭐)", 
                    callback_data=f"confirm_cashout:{child_name}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена", 
                    callback_data="cancel_cashout"
                )
            ]
        ]
    )
    return keyboard