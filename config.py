import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Основные настройки
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]

# Настройки базы данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot.db')

# Настройки Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Настройки логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = 'bot.log' 