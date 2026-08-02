"""Baseline binary min-heap keyed on product quantity.

Supports the low-stock alert query ("which k products are closest to
running out?"). The PoC version updates an item's key by linear search,
which is O(n) and becomes the main Phase 3 optimization target.
"""


class MinHeap:
    """Array-backed binary min-heap of (key, item_id) pairs."""

    def __init__(self):
        self._data = []  # list of [key, item_id]

    def __len__(self):
        return len(self._data)

    def push(self, key, item_id):
        """Insert. O(log n)."""
        self._data.append([key, item_id])
        self._sift_up(len(self._data) - 1)

    def peek(self):
        """Smallest (key, item_id) without removing it. O(1)."""
        if not self._data:
            raise IndexError("peek from empty heap")
        return tuple(self._data[0])

    def pop(self):
        """Remove and return smallest (key, item_id). O(log n)."""
        if not self._data:
            raise IndexError("pop from empty heap")
        last = self._data.pop()
        if self._data:
            root = tuple(self._data[0])
            self._data[0] = last
            self._sift_down(0)
            return root
        return tuple(last)

    def update_key(self, item_id, new_key):
        """Change an item's key.

        PoC implementation: linear search for the item, then sift.
        O(n) search + O(log n) sift -- the documented bottleneck.
        """
        for i, entry in enumerate(self._data):
            if entry[1] == item_id:
                old_key = entry[0]
                entry[0] = new_key
                if new_key < old_key:
                    self._sift_up(i)
                else:
                    self._sift_down(i)
                return True
        return False

    def remove(self, item_id):
        """Remove an item by id. O(n) search + O(log n) fix-up."""
        for i, entry in enumerate(self._data):
            if entry[1] == item_id:
                last = self._data.pop()
                if i < len(self._data):
                    self._data[i] = last
                    self._sift_down(i)
                    self._sift_up(i)
                return True
        return False

    def k_smallest(self, k):
        """Return the k smallest (key, item_id) pairs.

        PoC implementation sorts a copy of the array: O(n log n).
        """
        return [tuple(e) for e in sorted(self._data, key=lambda e: e[0])[:k]]

    def _sift_up(self, i):
        data = self._data
        while i > 0:
            parent = (i - 1) // 2
            if data[i][0] < data[parent][0]:
                data[i], data[parent] = data[parent], data[i]
                i = parent
            else:
                break

    def _sift_down(self, i):
        data = self._data
        n = len(data)
        while True:
            smallest = i
            left, right = 2 * i + 1, 2 * i + 2
            if left < n and data[left][0] < data[smallest][0]:
                smallest = left
            if right < n and data[right][0] < data[smallest][0]:
                smallest = right
            if smallest == i:
                break
            data[i], data[smallest] = data[smallest], data[i]
            i = smallest
