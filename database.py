import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path="bot.db"):
        self.db_path = db_path
        self.init_db()
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей (дети и родители)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                role TEXT,
                child_name TEXT,
                stars INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица сессий (для переключения между пользователями)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                telegram_user_id INTEGER PRIMARY KEY,
                current_child_name TEXT,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                completed_by INTEGER,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица призов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prizes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prize_text TEXT,
                stars_cost INTEGER,
                is_available BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица обменов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchanges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                prize_id INTEGER,
                stars_spent INTEGER,
                exchanged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Добавляем недостающие колонки если их нет
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        conn.commit()
        conn.close()
    
    def cleanup_inactive_users(self, hours=24):
        """Очистить неактивных пользователей из таблицы sessions"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Очищаем только сессии, не самих пользователей
        cursor.execute(
            'DELETE FROM sessions WHERE last_active < datetime("now", ?)',
            (f"-{hours} hours",)
        )
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        return deleted_count
    
    def update_user_activity(self, user_id):
        """Обновить время последней активности пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()
    
    def update_session_activity(self, telegram_user_id):
        """Обновить время последней активности сессии"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE telegram_user_id = ?',
            (telegram_user_id,)
        )
        conn.commit()
        conn.close()
    
    # СЕССИИ И ПЕРЕКЛЮЧЕНИЕ ПОЛЬЗОВАТЕЛЕЙ
    def set_current_child(self, telegram_user_id, child_name):
        """Установить текущего ребенка для Telegram пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO sessions (telegram_user_id, current_child_name, last_active) VALUES (?, ?, CURRENT_TIMESTAMP)',
            (telegram_user_id, child_name)
        )
        conn.commit()
        conn.close()
    
    def get_current_child(self, telegram_user_id):
        """Получить текущего ребенка для Telegram пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT current_child_name FROM sessions WHERE telegram_user_id = ?', (telegram_user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_available_children(self, telegram_user_id):
        """Получить всех детей, доступных для этого Telegram пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Получаем всех детей из сессий этого пользователя
        cursor.execute('''
            SELECT DISTINCT current_child_name 
            FROM sessions 
            WHERE telegram_user_id = ? AND current_child_name != 'parent'
        ''', (telegram_user_id,))
        
        children = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        return children
    
    def add_user(self, user_id, username, role, child_name=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO users (user_id, username, role, child_name, stars, last_active) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)',
            (user_id, username, role, child_name, 0)
        )
        conn.commit()
        conn.close()
    
    def get_user_by_child_name(self, child_name):
        """Получить пользователя по имени ребенка"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE child_name = ? AND role = "child"', (child_name,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def get_user(self, user_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    # Остальные методы без изменений...
    def add_task(self, child_name, task_text, stars_reward, is_weekly=False):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO tasks (child_name, task_text, stars_reward, is_weekly) VALUES (?, ?, ?, ?)',
            (child_name, task_text, stars_reward, is_weekly)
        )
        conn.commit()
        conn.close()
    
    def get_tasks(self, child_name=None, completed=False, weekly_only=False):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM tasks WHERE is_completed = ?'
        params = [completed]
        
        if child_name:
            query += ' AND child_name = ?'
            params.append(child_name)
        
        if weekly_only:
            query += ' AND is_weekly = TRUE'
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        tasks = cursor.fetchall()
        conn.close()
        return tasks
    
    def get_child_stars(self, child_name):
        """Получить количество звезд ребенка по имени"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT stars FROM users WHERE child_name = ? AND role = "child"', (child_name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def get_child_user_id(self, child_name):
        """Получить user_id ребенка по имени"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE child_name = ? AND role = "child"', (child_name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def complete_task(self, task_id, child_name_or_id):
        """Пометить задание выполненным и начислить звезды ребенку"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Определяем настоящее имя ребенка
            if isinstance(child_name_or_id, int) or child_name_or_id.isdigit():
                # Если передано число (Telegram ID), получаем имя из сессии
                telegram_id = int(child_name_or_id)
                child_name = self.get_current_child(telegram_id)
                if not child_name:
                    print(f"❌ Не найден ребенок для Telegram ID {telegram_id}")
                    return 0
            else:
                # Если передано имя, используем его
                child_name = child_name_or_id
            
            print(f"🎯 Выполняется задание {task_id} для ребенка '{child_name}'")
            
            # Получаем информацию о задании
            cursor.execute('SELECT stars_reward, is_completed FROM tasks WHERE id = ?', (task_id,))
            result = cursor.fetchone()
            
            if not result:
                print(f"❌ Задание {task_id} не найдено")
                return 0
            
            stars_reward, is_completed = result
            
            if is_completed:
                print(f"❌ Задание {task_id} уже выполнено")
                return 0
            
            print(f"💰 Награда за задание: {stars_reward} звезд")
            
            # Получаем текущие звезды ребенка
            current_stars = self.get_child_stars(child_name)
            print(f"💰 Текущие звезды {child_name}: {current_stars}")
            
            # Помечаем задание выполненным
            cursor.execute(
                'UPDATE tasks SET is_completed = TRUE, completed_at = CURRENT_TIMESTAMP WHERE id = ?',
                (task_id,)
            )
            
            # Вычисляем новые звезды
            new_stars = current_stars + stars_reward
            print(f"💰 Новые звезды {child_name}: {new_stars}")
            
            # Обновляем звезды ребенка
            user_id = self.get_child_user_id(child_name)
            if user_id:
                cursor.execute('UPDATE users SET stars = ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?', 
                            (new_stars, user_id))
                print(f"✅ Звезды обновлены для {child_name} (user_id: {user_id})")
                
                # Проверяем что обновилось
                cursor.execute('SELECT stars FROM users WHERE user_id = ?', (user_id,))
                updated_stars = cursor.fetchone()[0]
                print(f"✅ Проверка: в базе теперь {updated_stars} звезд")
            else:
                # Если пользователя нет, создаем его
                new_user_id = hash(f"auto_{child_name}") % 1000000000
                cursor.execute(
                    'INSERT INTO users (user_id, username, role, child_name, stars) VALUES (?, ?, ?, ?, ?)',
                    (new_user_id, f"auto_{child_name}", "child", child_name, new_stars)
                )
                print(f"✅ Создан новый пользователь для {child_name}")
            
            conn.commit()
            print(f"🎉 Задание {task_id} выполнено! Начислено {stars_reward} звезд для {child_name}")
            return stars_reward
            
        except Exception as e:
            print(f"❌ Ошибка при выполнении задания: {e}")
            import traceback
            traceback.print_exc()
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
    
    def add_prize(self, prize_text, stars_cost):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO prizes (prize_text, stars_cost) VALUES (?, ?)',
            (prize_text, stars_cost)
        )
        conn.commit()
        conn.close()
    
    def get_prizes(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM prizes WHERE is_available = TRUE ORDER BY stars_cost')
        prizes = cursor.fetchall()
        conn.close()
        return prizes
    
    def exchange_stars(self, user_id, prize_id):
        """Обменять звезды на приз"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Получаем информацию о призе
            cursor.execute('SELECT prize_text, stars_cost, is_available FROM prizes WHERE id = ?', (prize_id,))
            prize_result = cursor.fetchone()
            
            if not prize_result:
                print(f"❌ Приз {prize_id} не найден")
                return False
            
            prize_text, prize_cost, is_available = prize_result
            
            if not is_available:
                print(f"❌ Приз {prize_id} недоступен")
                return False
            
            # Получаем информацию о пользователе
            cursor.execute('SELECT stars, child_name FROM users WHERE user_id = ?', (user_id,))
            user_result = cursor.fetchone()
            
            if not user_result:
                print(f"❌ Пользователь {user_id} не найден")
                return False
            
            user_stars, child_name = user_result
            
            print(f"🔄 Попытка обмена: {child_name} ({user_stars}⭐) -> {prize_text} ({prize_cost}⭐)")
            
            if user_stars < prize_cost:
                print(f"❌ Недостаточно звезд: {user_stars} < {prize_cost}")
                return False
            
            if user_stars - prize_cost < 0:
                print(f"❌ Отрицательный баланс после обмена: {user_stars} - {prize_cost}")
                return False
            
            # Выполняем обмен
            new_balance = user_stars - prize_cost
            
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
            conn.rollback()
            return False
        finally:
            conn.close()

    def cash_out_stars(self, child_name):
        """Обнулить звезды ребенка (родитель рассчитался)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Получаем текущее количество звезд
            current_stars = self.get_child_stars(child_name)
            
            if current_stars == 0:
                print(f"ℹ️ У {child_name} и так 0 звезд")
                return 0
            
            # Получаем user_id ребенка
            user_id = self.get_child_user_id(child_name)
            if not user_id:
                print(f"❌ Ребенок {child_name} не найден")
                return 0
            
            # Обнуляем звезды
            cursor.execute(
                'UPDATE users SET stars = 0 WHERE user_id = ?',
                (user_id,)
            )
            
            # Записываем операцию в таблицу exchanges с prize_id = 0 (особая метка)
            cursor.execute(
                'INSERT INTO exchanges (user_id, prize_id, stars_spent) VALUES (?, ?, ?)',
                (user_id, 0, current_stars)  # prize_id = 0 означает "обналичка"
            )
            
            conn.commit()
            print(f"✅ Родитель рассчитался с {child_name}! Обнулено {current_stars} звезд")
            return current_stars
            
        except Exception as e:
            print(f"❌ Ошибка при обнулении звезд: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()

    def get_cash_out_history(self, child_name=None):
        """Получить историю расчетов родителя с детьми"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if child_name:
            # История для конкретного ребенка
            cursor.execute('''
                SELECT e.exchanged_at, e.stars_spent, u.child_name 
                FROM exchanges e
                JOIN users u ON e.user_id = u.user_id
                WHERE e.prize_id = 0 AND u.child_name = ?
                ORDER BY e.exchanged_at DESC
            ''', (child_name,))
        else:
            # Вся история
            cursor.execute('''
                SELECT e.exchanged_at, e.stars_spent, u.child_name 
                FROM exchanges e
                JOIN users u ON e.user_id = u.user_id
                WHERE e.prize_id = 0
                ORDER BY e.exchanged_at DESC
            ''')
        
        history = cursor.fetchall()
        conn.close()
        return history