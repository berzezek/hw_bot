import sqlite3

def check_database():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    print("=== ПРОВЕРКА БАЗЫ ДАННЫХ ===")
    
    # Проверяем таблицу users
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    print("Пользователи в базе:")
    for user in users:
        print(f"ID: {user[0]}, Имя: {user[1]}, Роль: {user[2]}, Ребенок: {user[3]}, Звезды: {user[4]}")
    
    # Проверяем таблицу tasks
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    print("\nЗадания в базе:")
    for task in tasks:
        print(f"ID: {task[0]}, Ребенок: {task[1]}, Задание: {task[2]}, Звезды: {task[3]}, Выполнено: {task[4]}")
    
    conn.close()

if __name__ == "__main__":
    check_database()