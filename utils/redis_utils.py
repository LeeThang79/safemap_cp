import redis
from config import Config
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            try:
                cls._instance.client = redis.Redis(
                    host=Config.REDIS_HOST,
                    port=Config.REDIS_PORT,
                    db=Config.REDIS_DB,
                    decode_responses=True # Decodes responses to UTF-8 strings
                )
                # Test connection
                cls._instance.client.ping()
                logger.info("Connected to Redis successfully.")
            except redis.exceptions.ConnectionError as e:
                logger.error(f"Could not connect to Redis: {e}. All Redis operations will be mocked.")
                cls._instance.client = cls._instance._create_mock_redis_client()
            except Exception as e:
                logger.error(f"Unexpected error connecting to Redis: {e}. All Redis operations will be mocked.")
                cls._instance.client = cls._instance._create_mock_redis_client()
        return cls._instance

    def _create_mock_redis_client(self):
        # A simple mock for Redis client
        class MockRedisClient:
            def __init__(self):
                self._data = {}
                self._expires = {}
                logger.warning("Using Mock Redis client. Data will not be persisted.")

            def hset(self, key, mapping):
                self._data[key] = {**self._data.get(key, {}), **mapping}
                logger.debug(f"MockRedis: hset {key} -> {mapping}")
            
            def hgetall(self, key):
                return self._data.get(key, {})

            def incr(self, key):
                self._data[key] = int(self._data.get(key, 0)) + 1
                logger.debug(f"MockRedis: incr {key} -> {self._data[key]}")
                return self._data[key]

            def expire(self, key, seconds):
                self._expires[key] = datetime.now() + timedelta(seconds=seconds)
                logger.debug(f"MockRedis: expire {key} in {seconds}s")
            
            def get(self, key):
                if key in self._expires and self._expires[key] < datetime.now():
                    self._data.pop(key, None)
                    self._expires.pop(key, None)
                    return None
                return self._data.get(key)
            
            def set(self, key, value):
                self._data[key] = value

            # Add other methods as needed for your specific use cases
            def sadd(self, key, member):
                if key not in self._data: self._data[key] = set()
                if member in self._data[key]: return 0
                self._data[key].add(member)
                return 1

        from datetime import datetime, timedelta # Import here to avoid circular dependency
        return MockRedisClient()


    def get_client(self):
        return self.client

# Example usage:
# redis_conn = RedisClient().get_client()
# redis_conn.hset("myhash", {"field": "value"})