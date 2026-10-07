from collections import defaultdict


class FakeStore:
    """RedisStore role - The data is flushed on server"""

    def __init__(self):
        self._data = {"client_A": 10}

    def get_count(self, client_id: str) -> int:
        return self._data.get(client_id, 0)


class LocalBuffer:
    def __init__(self, store):
        self.store = store
        self.pending = defaultdict(int)

    def increment(self, client_id: str, count: int = 1) -> None:
        self.pending[client_id] += count

    def get_count(self, client_id: str) -> int:
        return self.pending.get(client_id, 0) + self.store.get_count(client_id)


if __name__ == "__main__":
    buf = LocalBuffer(FakeStore())

    buf.increment("client_A", 3)

    print("client_A:", buf.get_count("client_A"))
    print("client_B:", buf.get_count("client_B"))
    print("so key trong pending:", len(buf.pending))
