"""Optimized price index: sorted array with binary search.

Phase 3 replaces the pure-Python skip list with a sorted array driven
by the C-implemented bisect module. The trade-off is deliberate and
documented: insertion/deletion become O(n) element shifts, but those
shifts are a single memmove in C, while every skip-list pointer hop is
interpreted Python. For read-heavy inventory workloads (range queries
dominate price changes) the sorted array wins by a wide margin, and
even the O(n) writes stay competitive until n grows very large.
"""

from bisect import bisect_left, bisect_right, insort


class SortedPriceIndex:
    __slots__ = ("_keys", "_values")

    def __init__(self):
        self._keys = []    # sorted list of (price, sku)
        self._values = {}  # (price, sku) -> sku

    def __len__(self):
        return len(self._keys)

    def build(self, pairs):
        """Bulk-load from (key, value) pairs in O(n log n)."""
        items = sorted(pairs)
        self._keys = [k for k, _ in items]
        self._values = dict(items)

    def insert(self, key, value):
        if key in self._values:
            self._values[key] = value
            return
        insort(self._keys, key)
        self._values[key] = value

    def remove(self, key):
        if key not in self._values:
            return False
        i = bisect_left(self._keys, key)
        del self._keys[i]
        del self._values[key]
        return True

    def search(self, key):
        return self._values.get(key)

    def range_query(self, lo, hi):
        """All values with lo <= key <= hi. O(log n + m)."""
        i = bisect_left(self._keys, lo)
        j = bisect_right(self._keys, hi)
        values = self._values
        return [values[k] for k in self._keys[i:j]]
