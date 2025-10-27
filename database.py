import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="bot.db"):
        self.db_path = db_path
        self.init_db()
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Таблица детей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS children (
                name TEXT PRIMARY KEY,
                stars INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица заданий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_name TEXT,
                task_text TEXT,
                stars_reward INTEGER,
                is_completed BOOLEAN DEFAULT FALSE,
                is_weekly BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица сессий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                telegram_id INTEGER PRIMARY KEY,
                current_user TEXT,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица для отслеживания обнулений звезд
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS star_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_name TEXT,
                reset_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Инициализируем детей
        children = ["djama", "ramz", "riza"]
        for child_name in children:
            cursor.execute(
                'INSERT OR IGNORE INTO children (name, stars) VALUES (?, ?)',
                (child_name, 0)
            )
        
        conn.commit()
        conn.close()
    
    # СЕССИИ
    def set_current_user(self, telegram_id, user_name):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO sessions (telegram_id, current_user) VALUES (?, ?)',
            (telegram_id, user_name)
        )
        conn.commit()
        conn.close()
    
    def get_current_user(self, telegram_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT current_user FROM sessions WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_all_children(self):
        """Получить всех детей"""
        return ["djama", "ramz", "riza"]
    
    # ДЕТИ И ЗВЕЗДЫ
    def get_child_stars(self, child_name):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT stars FROM children WHERE name = ?', (child_name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    
    def reset_child_stars(self, child_name):
        """Обнулить звезды ребенка и запомнить время обнуления"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Записываем время обнуления
        cursor.execute(
            'INSERT INTO star_resets (child_name) VALUES (?)',
            (child_name,)
        )
        
        # Обнуляем звезды
        cursor.execute('UPDATE children SET stars = 0 WHERE name = ?', (child_name,))
        
        conn.commit()
        conn.close()
        return True
    
    def get_last_reset_time(self, child_name):
        """Получить время последнего обнуления звезд"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT reset_at FROM star_resets WHERE child_name = ? ORDER BY reset_at DESC LIMIT 1',
            (child_name,)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    # ЗАДАНИЯ
    def add_task(self, child_name, task_text, stars_reward, is_weekly=False):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO tasks (child_name, task_text, stars_reward, is_weekly) VALUES (?, ?, ?, ?)',
            (child_name, task_text, stars_reward, is_weekly)
        )
        conn.commit()
        conn.close()
    
    def add_tasks_for_all_children(self, tasks_dict):
        """Добавить задания для всех детей"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for child_name, tasks in tasks_dict.items():
            for task in tasks:
                cursor.execute(
                    'INSERT INTO tasks (child_name, task_text, stars_reward, is_weekly) VALUES (?, ?, ?, ?)',
                    (child_name, task["text"], task["stars"], True)
                )
        
        conn.commit()
        conn.close()
    
    def get_tasks(self, child_name=None, completed=False):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if child_name:
            cursor.execute(
                'SELECT * FROM tasks WHERE child_name = ? AND is_completed = ? ORDER BY created_at DESC',
                (child_name, completed)
            )
        else:
            cursor.execute(
                'SELECT * FROM tasks WHERE is_completed = ? ORDER BY created_at DESC',
                (completed,)
            )
        
        tasks = cursor.fetchall()
        conn.close()
        return tasks
    
    def get_active_completed_tasks(self, child_name=None):
        """Получить выполненные задания, за которые еще не рассчитались"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if child_name:
            # Для конкретного ребенка
            last_reset = self.get_last_reset_time(child_name)
            if last_reset:
                # Берем задания выполненные ПОСЛЕ последнего обнуления
                cursor.execute(
                    '''SELECT * FROM tasks 
                    WHERE child_name = ? AND is_completed = TRUE AND completed_at > ?
                    ORDER BY completed_at DESC''',
                    (child_name, last_reset)
                )
            else:
                # Если обнулений не было, берем все выполненные задания
                cursor.execute(
                    'SELECT * FROM tasks WHERE child_name = ? AND is_completed = TRUE ORDER BY completed_at DESC',
                    (child_name,)
                )
        else:
            # Для всех детей - сложная логика
            tasks = []
            children = self.get_all_children()
            for child in children:
                child_tasks = self.get_active_completed_tasks(child)
                tasks.extend(child_tasks)
            conn.close()
            return tasks
        
        tasks = cursor.fetchall()
        conn.close()
        return tasks
    
    def get_statistics(self):
        """Получить статистику по активным заданиям (исключая обнуленные)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {
            "total_completed": 0,
            "total_pending": 0,
            "children": {}
        }
        
        children = self.get_all_children()
        
        for child in children:
            # Активные выполненные задания (после последнего обнуления)
            active_completed = self.get_active_completed_tasks(child)
            
            # Все ожидающие задания
            cursor.execute(
                'SELECT COUNT(*) FROM tasks WHERE child_name = ? AND is_completed = FALSE',
                (child,)
            )
            pending = cursor.fetchone()[0]
            
            stars = self.get_child_stars(child)
            
            stats["children"][child] = {
                "completed": len(active_completed),
                "pending": pending,
                "stars": stars,
                "recent_tasks": active_completed[:5]  # Последние 5 заданий
            }
            
            stats["total_completed"] += len(active_completed)
            stats["total_pending"] += pending
        
        conn.close()
        return stats
    
    def complete_task(self, task_id, child_name):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Получаем информацию о задании
            cursor.execute('SELECT stars_reward FROM tasks WHERE id = ?', (task_id,))
            result = cursor.fetchone()
            if not result:
                return 0
            
            stars_reward = result[0]
            
            # Помечаем задание выполненным
            cursor.execute(
                'UPDATE tasks SET is_completed = TRUE, completed_at = CURRENT_TIMESTAMP WHERE id = ?',
                (task_id,)
            )
            
            # Начисляем звезды
            current_stars = self.get_child_stars(child_name)
            new_stars = current_stars + stars_reward
            
            # Обновляем звезды ребенка
            cursor.execute('UPDATE children SET stars = ? WHERE name = ?', (new_stars, child_name))
            
            conn.commit()
            return stars_reward
            
        except Exception as e:
            print(f"Ошибка: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def delete_weekly_tasks(self):
        """Удалить все еженедельные задания"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE is_weekly = TRUE')
        conn.commit()
        conn.close()
    
    def has_weekly_tasks(self):
        """Проверить есть ли недельные задания"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE is_weekly = TRUE')
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def get_active_completed_tasks_for_child(self, child_name):
        """Получить выполненные задания ребенка, за которые еще не рассчитались"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Получаем время последнего обнуления
        last_reset = self.get_last_reset_time(child_name)
        
        if last_reset:
            # Берем задания выполненные ПОСЛЕ последнего обнуления
            cursor.execute(
                '''SELECT * FROM tasks 
                WHERE child_name = ? AND is_completed = TRUE AND completed_at > ?
                ORDER BY completed_at DESC''',
                (child_name, last_reset)
            )
        else:
            # Если обнулений не было, берем все выполненные задания
            cursor.execute(
                'SELECT * FROM tasks WHERE child_name = ? AND is_completed = TRUE ORDER BY completed_at DESC',
                (child_name,)
            )
        
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_pending_reward_tasks(self, child_name):
        """Получить задания, за которые ожидается награда (выполнены но не обнулены)"""
        return self.get_active_completed_tasks_for_child(child_name)