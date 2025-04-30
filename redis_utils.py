import redis
from config import REDIS_HOST, REDIS_PORT, REDIS_DB

# Создание подключения к Redis
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)

def cache_user_data(user_id, data):
    """Кэширование данных пользователя"""
    key = f"user:{user_id}"
    redis_client.hmset(key, data)
    redis_client.expire(key, 3600)  # Время жизни кэша - 1 час

def get_cached_user_data(user_id):
    """Получение кэшированных данных пользователя"""
    key = f"user:{user_id}"
    return redis_client.hgetall(key)

def increment_user_counter(user_id):
    """Увеличение счетчика действий пользователя"""
    key = f"counter:{user_id}"
    return redis_client.incr(key)

def get_user_counter(user_id):
    """Получение счетчика действий пользователя"""
    key = f"counter:{user_id}"
    return int(redis_client.get(key) or 0)

def clear_user_cache(user_id):
    """Очистка кэша пользователя"""
    user_key = f"user:{user_id}"
    counter_key = f"counter:{user_id}"
    redis_client.delete(user_key, counter_key) 