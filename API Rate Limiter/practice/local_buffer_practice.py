from collections import defaultdict


class FakeStore:
    """RedisStore role - the data is flushed on server"""

    def __init__(self):
        self._data = {"client_A": 10}
        self.down_for = set()  # clients whose write fails (simulated outage)
        self.while_waiting = None  # a function to run during the network call, once

    def get_count(self, client_id: str) -> int:
        return self._data.get(client_id, 0)

    def increment_count(self, client_id: str, count: int, window_sec: int) -> int:
        if self.while_waiting is not None:
            arriving = self.while_waiting
            self.while_waiting = None
            arriving()
        if client_id in self.down_for:
            print(f"  store <- INCRBY {client_id} {count} FAILED")
            raise ConnectionError("store unreachable")
        print(f"  store <- INCRBY {client_id} {count} (TTL {window_sec}s)")
        self._data[client_id] = self._data.get(client_id, 0) + count
        return self._data[client_id]


class LocalBuffer:
    def __init__(self, store):
        self.store = store
        self.pending = defaultdict(int)

    def increment(self, client_id: str, count: int = 1) -> None:
        self.pending[client_id] += count

    def get_count(self, client_id: str) -> int:
        return self.store.get_count(client_id) + self.pending.get(client_id, 0)

    def flush(self, window_sec: int = 60) -> None:
        snapshot = dict(self.pending)
        self.pending.clear()
        for client_id, count in snapshot.items():
            try:
                self.store.increment_count(client_id, count, window_sec)
            except ConnectionError as e:
                self.increment(client_id, count)
                print(e)


def show(title: str, buf: LocalBuffer, store: FakeStore) -> None:
    print(f"--- {title} ---")
    print("client_A:", buf.get_count("client_A"))
    print("client_B:", buf.get_count("client_B"))
    print("pending:", dict(buf.pending))
    print("store:", store._data)


if __name__ == "__main__":
    store = FakeStore()
    buf = LocalBuffer(store)

    buf.increment("client_B", 4)
    buf.increment("client_A", 3)
    show("before flush", buf, store)

    def new_request_arrives():
        print("  >> client_B +5 arrives during the network call")
        buf.increment("client_B", 5)

    store.down_for.add("client_B")
    store.while_waiting = new_request_arrives
    buf.flush()
    show("after failed flush", buf, store)

    store.down_for.clear()
    buf.flush()
    show("after retry", buf, store)
