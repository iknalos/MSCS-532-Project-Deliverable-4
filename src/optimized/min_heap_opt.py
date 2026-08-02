"""Optimized indexed min-heap.

Phase 3 changes relative to the baseline heap:
  * A position map (item_id -> array index) makes update_key and remove
    O(log n) instead of O(n) linear search.
  * build() constructs the heap bottom-up in O(n) (Floyd's heapify)
    instead of n pushes at O(n log n).
  * k_smallest uses a bounded partial extraction of the heap prefix,
    O(k log k) with a candidate frontier, instead of sorting all n.
"""

import heapq


class IndexedMinHeap:
    __slots__ = ("_data", "_pos")

    def __init__(self):
        self._data = []          # list of [key, item_id]
        self._pos = {}           # item_id -> index in _data

    def __len__(self):
        return len(self._data)

    def build(self, pairs):
        """Bulk-load from (key, item_id) pairs in O(n)."""
        self._data = [[k, i] for k, i in pairs]
        n = len(self._data)
        for i in range(n // 2 - 1, -1, -1):
            self._sift_down(i)
        self._pos = {entry[1]: idx for idx, entry in enumerate(self._data)}

    def push(self, key, item_id):
        if item_id in self._pos:
            raise KeyError(f"duplicate item_id: {item_id}")
        self._data.append([key, item_id])
        self._pos[item_id] = len(self._data) - 1
        self._sift_up(len(self._data) - 1)

    def peek(self):
        if not self._data:
            raise IndexError("peek from empty heap")
        return tuple(self._data[0])

    def pop(self):
        if not self._data:
            raise IndexError("pop from empty heap")
        root = tuple(self._data[0])
        del self._pos[root[1]]
        last = self._data.pop()
        if self._data:
            self._data[0] = last
            self._pos[last[1]] = 0
            self._sift_down(0)
        return root

    def update_key(self, item_id, new_key):
        """O(log n): direct index lookup, then one sift."""
        i = self._pos.get(item_id)
        if i is None:
            return False
        old_key = self._data[i][0]
        self._data[i][0] = new_key
        if new_key < old_key:
            self._sift_up(i)
        else:
            self._sift_down(i)
        return True

    def remove(self, item_id):
        """O(log n) removal by id."""
        i = self._pos.get(item_id)
        if i is None:
            return False
        del self._pos[item_id]
        last = self._data.pop()
        if i < len(self._data):
            self._data[i] = last
            self._pos[last[1]] = i
            self._sift_down(i)
            self._sift_up(i)
        return True

    def k_smallest(self, k):
        """k smallest pairs in O(k log k) using a frontier walk.

        Explores the heap as an implicit tree: start at the root and
        repeatedly take the smallest frontier node, adding its children.
        Never touches more than 2k+1 entries.
        """
        data = self._data
        n = len(data)
        if n == 0 or k <= 0:
            return []
        k = min(k, n)
        out = []
        frontier = [(data[0][0], 0)]
        while frontier and len(out) < k:
            key, i = heapq.heappop(frontier)
            out.append((key, data[i][1]))
            left, right = 2 * i + 1, 2 * i + 2
            if left < n:
                heapq.heappush(frontier, (data[left][0], left))
            if right < n:
                heapq.heappush(frontier, (data[right][0], right))
        return out

    def _sift_up(self, i):
        data, pos = self._data, self._pos
        entry = data[i]
        while i > 0:
            parent = (i - 1) // 2
            if entry[0] < data[parent][0]:
                data[i] = data[parent]
                pos[data[i][1]] = i
                i = parent
            else:
                break
        data[i] = entry
        pos[entry[1]] = i

    def _sift_down(self, i):
        data, pos = self._data, self._pos
        n = len(data)
        entry = data[i]
        while True:
            smallest = i
            left, right = 2 * i + 1, 2 * i + 2
            if left < n and data[left][0] < (data[smallest][0] if smallest != i else entry[0]):
                smallest = left
            if right < n and data[right][0] < (data[smallest][0] if smallest != i else entry[0]):
                smallest = right
            if smallest == i:
                break
            data[i] = data[smallest]
            pos[data[i][1]] = i
            i = smallest
        data[i] = entry
        pos[entry[1]] = i
