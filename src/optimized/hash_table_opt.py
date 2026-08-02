"""Optimized hash table: open addressing with linear probing.

Phase 3 changes relative to the chaining baseline:
  * Open addressing in flat parallel arrays (no per-bucket list objects)
    -- fewer allocations and better locality, lower memory per entry.
  * Power-of-two capacity with bitmask indexing instead of modulo.
  * Perturbed probing (CPython-style) to break up clustering.
  * Tighter maximum load factor (2/3) so probe chains stay short.
  * Tombstones for deletion, cleaned out on resize.
"""

_EMPTY = object()
_TOMBSTONE = object()


class OptimizedHashTable:
    __slots__ = ("_capacity", "_mask", "_size", "_used", "_keys", "_values")

    MAX_LOAD = 2 / 3

    def __init__(self, capacity=8):
        cap = 8
        while cap < capacity:
            cap <<= 1
        self._capacity = cap
        self._mask = cap - 1
        self._size = 0        # live entries
        self._used = 0        # live entries + tombstones
        self._keys = [_EMPTY] * cap
        self._values = [None] * cap

    # Probing is inlined in put/get/remove: a shared generator would add
    # a Python frame per probe step and dominate the cost of the lookup.

    def put(self, key, value):
        keys = self._keys
        mask = self._mask
        h = hash(key)
        i = h & mask
        perturb = h & 0xFFFFFFFFFFFFFFFF
        first_tombstone = -1
        while True:
            slot = keys[i]
            if slot is _EMPTY:
                target = first_tombstone if first_tombstone >= 0 else i
                keys[target] = key
                self._values[target] = value
                self._size += 1
                if first_tombstone < 0:
                    self._used += 1
                    if self._used / self._capacity > self.MAX_LOAD:
                        self._resize()
                return
            if slot is _TOMBSTONE:
                if first_tombstone < 0:
                    first_tombstone = i
            elif slot == key:
                self._values[i] = value
                return
            perturb >>= 5
            i = (5 * i + perturb + 1) & mask

    def get(self, key, default=None):
        keys = self._keys
        mask = self._mask
        h = hash(key)
        i = h & mask
        perturb = h & 0xFFFFFFFFFFFFFFFF
        while True:
            slot = keys[i]
            if slot is _EMPTY:
                return default
            if slot is not _TOMBSTONE and slot == key:
                return self._values[i]
            perturb >>= 5
            i = (5 * i + perturb + 1) & mask

    def remove(self, key):
        keys = self._keys
        mask = self._mask
        h = hash(key)
        i = h & mask
        perturb = h & 0xFFFFFFFFFFFFFFFF
        while True:
            slot = keys[i]
            if slot is _EMPTY:
                return False
            if slot is not _TOMBSTONE and slot == key:
                keys[i] = _TOMBSTONE
                self._values[i] = None
                self._size -= 1
                return True
            perturb >>= 5
            i = (5 * i + perturb + 1) & mask

    def _resize(self):
        old_keys, old_values = self._keys, self._values
        new_cap = self._capacity * 2
        # Shrink back if mostly tombstones.
        while new_cap > 8 and self._size * 3 < new_cap:
            new_cap >>= 1
        self._capacity = max(new_cap, 8)
        self._mask = self._capacity - 1
        self._keys = [_EMPTY] * self._capacity
        self._values = [None] * self._capacity
        self._size = 0
        self._used = 0
        for k, v in zip(old_keys, old_values):
            if k is not _EMPTY and k is not _TOMBSTONE:
                self.put(k, v)

    def items(self):
        for k, v in zip(self._keys, self._values):
            if k is not _EMPTY and k is not _TOMBSTONE:
                yield k, v

    def keys(self):
        for k, _ in self.items():
            yield k

    def __contains__(self, key):
        sentinel = object()
        return self.get(key, sentinel) is not sentinel

    def __len__(self):
        return self._size
