import json
from datetime import datetime

# Задания по умолчанию для каждого ребенка
DEFAULT_TASKS = {
    "djama": [
        {"text": "Убраться в комнате", "stars": 3},
        {"text": "Сделать домашнее задание", "stars": 5},
        {"text": "Помыть посуду", "stars": 2},
        {"text": "Почитать книгу 30 минут", "stars": 4},
        {"text": "Погулять с собакой", "stars": 3},
    ],
    "ramz": [
        {"text": "Собрать портфель на завтра", "stars": 2},
        {"text": "Вынести мусор", "stars": 2},
        {"text": "Поиграть в развивающую игру", "stars": 4},
        {"text": "Помочь на кухне", "stars": 3},
        {"text": "Почитать вслух 15 минут", "stars": 3},
    ],
    "riza": [
        {"text": "Полить цветы", "stars": 2},
        {"text": "Приготовить простой ужин", "stars": 5},
        {"text": "Сделать зарядку", "stars": 3},
        {"text": "Написать в дневнике", "stars": 4},
        {"text": "Убрать в шкафу", "stars": 3},
    ],
}

# Еженедельные задания (обновляются каждую неделю)
WEEKLY_TASKS = {
    "djama": [
        {"text": "Прочитать новую книгу", "stars": 10},
        {"text": "Сходить в библиотеку", "stars": 8},
        {"text": "Подготовить доклад для школы", "stars": 12},
    ],
    "ramz": [
        {"text": "Собрать конструктор", "stars": 8},
        {"text": "Нарисовать картину", "stars": 10},
        {"text": "Выучить стихотворение", "stars": 12},
    ],
    "riza": [
        {"text": "Испечь печенье", "stars": 10},
        {"text": "Сшить что-нибудь", "stars": 12},
        {"text": "Организовать уборку", "stars": 8},
    ],
}


def get_default_tasks(child_name):
    """Получить задания по умолчанию для ребенка"""
    return DEFAULT_TASKS.get(child_name.lower(), [])


def get_weekly_tasks(child_name):
    """Получить еженедельные задания для ребенка"""
    return WEEKLY_TASKS.get(child_name.lower(), [])


def get_all_tasks_for_child(child_name):
    """Получить все задания для ребенка (обычные + еженедельные)"""
    default_tasks = get_default_tasks(child_name)
    weekly_tasks = get_weekly_tasks(child_name)
    return default_tasks + weekly_tasks


def save_last_update_date():
    """Сохранить дату последнего обновления заданий"""
    with open("last_update.json", "w") as f:
        json.dump({"last_update": datetime.now().isoformat()}, f)


def get_last_update_date():
    """Получить дату последнего обновления заданий"""
    try:
        with open("last_update.json", "r") as f:
            data = json.load(f)
            return datetime.fromisoformat(data["last_update"])
    except (FileNotFoundError, KeyError):
        return datetime.now()
