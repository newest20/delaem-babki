import sqlite3
from contextlib import contextmanager
from config import DATABASE_URL

@contextmanager
def get_db_connection():
    """Контекстный менеджер для работы с базой данных"""
    conn = sqlite3.connect('bot.db')
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Инициализация базы данных"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Создание таблицы пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_vip BOOLEAN DEFAULT FALSE,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Создание таблицы логов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()

def add_user(user_id, username, first_name, last_name):
    """Добавление нового пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        conn.commit()

def log_action(user_id, action):
    """Логирование действий пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (user_id, action)
            VALUES (?, ?)
        ''', (user_id, action))
        conn.commit()

def get_user_stats(user_id):
    """Получение статистики пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM logs WHERE user_id = ?
        ''', (user_id,))
        return cursor.fetchone()[0]

def set_vip_status(user_id, is_vip):
    """Установка VIP статуса"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET is_vip = ? WHERE user_id = ?
        ''', (is_vip, user_id))
        conn.commit()

def get_vip_status(user_id):
    """Проверка VIP статуса"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT is_vip FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else False 