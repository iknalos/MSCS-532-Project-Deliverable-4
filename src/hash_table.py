"""Baseline hash table with separate chaining.

Maps SKU strings to Product records. This is the proof-of-concept
implementation for Phase 2: correct and simple, with a deliberately
relaxed load-factor policy that Phase 3 tightens up.
"""


class HashTable:
    """Separate-chaining hash table.

    Each bucket is a Python list of (key, value) pairs. The table
    resizes (doubles) when the load factor exceeds MAX_LOAD.
    """

    MAX_LOAD = 1.0  # entries per bucket before resizing (relaxed in PoC)

    def __init__(self, capacity=8):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._capacity = capacity
        self._size = 0
        self._buckets = [[] for _ in range(capacity)]

    def _index(self, key):
        return hash(key) % self._capacity

    def put(self, key, value):
        """Insert or update a key. Average O(1), worst O(n)."""
        bucket = self._buckets[self._index(key)]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return
        bucket.append((key, value))
        self._size += 1
        if self._size / self._capacity > self.MAX_LOAD:
            self._resize(self._capacity * 2)

    def get(self, key, default=None):
        """Look up a key. Average O(1), worst O(n)."""
        bucket = self._buckets[self._index(key)]
        for k, v in bucket:
            if k == key:
                return v
        return default

    def remove(self, key):
        """Delete a key. Returns True if the key existed."""
        bucket = self._buckets[self._index(key)]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket.pop(i)
                self._size -= 1
                return True
        return False

    def _resize(self, new_capacity):
        old_items = list(self.items())
        self._capacity = new_capacity
        self._size = 0
        self._buckets = [[] for _ in range(new_capacity)]
        for k, v in old_items:
            self.put(k, v)

    def items(self):
        for bucket in self._buckets:
            yield from bucket

    def keys(self):
        for k, _ in self.items():
            yield k

    def __contains__(self, key):
        sentinel = object()
        return self.get(key, sentinel) is not sentinel

    def __len__(self):
        return self._size
