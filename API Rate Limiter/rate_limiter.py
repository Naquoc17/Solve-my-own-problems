import redis
import time

class RedisStore:
    
    _LUA = """
    local current = redis.call('INCRBY', KEYS[1], ARGV[1])
    if current == tonumber(ARGV[1]) then
        redis.call('EXPIRE', KEYS[1], ARGV[2])
    end
    return current
    """
    
    def __init__(self, host: str, port: int):
        self.redis = redis.Redis(host=host, port=port)
        
    def get_count(self, client_id: str) -> int:
        count = self.redis.get(client_id)
        return int(count) if count else 0
    
    def increment_count(self, client_id: str, count: int, window_sec: int) -> int:
        return self.redis.eval(self._LUA, 1, client_id, count, window_sec)
        
class RulesStore:
    _CONFIG_SOURCE = {
        "client_A": {"limit": 100, "window_sec": 60},
        "client_B": {"limit": 500, "window_sec": 60},
    }
    
    def __init__(self):
        self.cache = dict()
        self.last_refresh = 0
        
    def get_config(self, client_id: str) -> dict:
        if time.time() - self.last_refresh > 60:
            self.cache = dict(self._CONFIG_SOURCE)
            self.last_refresh = time.time()
        return self.cache.get(client_id, {"limit": 100, "window_sec": 60})