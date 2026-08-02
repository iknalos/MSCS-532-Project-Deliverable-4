"""Baseline skip list ordered by product price.

Answers price-range queries ("all products between $10 and $25").
A skip list (Pugh, 1990) gives expected O(log n) insert/delete/search
without the rebalancing logic of a self-balancing BST.

Keys are (price, sku) tuples so that products with equal prices remain
distinct and totally ordered.
"""

import random


class _Node:
    def __init__(self, key, value, level):
        self.key = key          # (price, sku) or None for head
        self.value = value
        self.forward = [None] * level


class SkipList:
    MAX_LEVEL = 16
    P = 0.5

    def __init__(self, seed=None):
        self._head = _Node(None, None, self.MAX_LEVEL)
        self._level = 1
        self._size = 0
        self._rng = random.Random(seed)

    def __len__(self):
        return self._size

    def _random_level(self):
        level = 1
        while self._rng.random() < self.P and level < self.MAX_LEVEL:
            level += 1
        return level

    def insert(self, key, value):
        """Insert or update. Expected O(log n)."""
        update = [None] * self.MAX_LEVEL
        node = self._head
        for i in range(self._level - 1, -1, -1):
            while node.forward[i] is not None and node.forward[i].key < key:
                node = node.forward[i]
            update[i] = node
        candidate = node.forward[0]
        if candidate is not None and candidate.key == key:
            candidate.value = value
            return
        level = self._random_level()
        if level > self._level:
            for i in range(self._level, level):
                update[i] = self._head
            self._level = level
        new_node = _Node(key, value, level)
        for i in range(level):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
        self._size += 1

    def remove(self, key):
        """Delete by key. Expected O(log n). Returns True if found."""
        update = [None] * self.MAX_LEVEL
        node = self._head
        for i in range(self._level - 1, -1, -1):
            while node.forward[i] is not None and node.forward[i].key < key:
                node = node.forward[i]
            update[i] = node
        target = node.forward[0]
        if target is None or target.key != key:
            return False
        for i in range(len(target.forward)):
            if update[i].forward[i] is target:
                update[i].forward[i] = target.forward[i]
        while self._level > 1 and self._head.forward[self._level - 1] is None:
            self._level -= 1
        self._size -= 1
        return True

    def search(self, key):
        """Exact-key lookup. Expected O(log n)."""
        node = self._head
        for i in range(self._level - 1, -1, -1):
            while node.forward[i] is not None and node.forward[i].key < key:
                node = node.forward[i]
        node = node.forward[0]
        if node is not None and node.key == key:
            return node.value
        return None

    def range_query(self, lo, hi):
        """All values with lo <= key <= hi. Expected O(log n + m)."""
        results = []
        node = self._head
        for i in range(self._level - 1, -1, -1):
            while node.forward[i] is not None and node.forward[i].key < lo:
                node = node.forward[i]
        node = node.forward[0]
        while node is not None and node.key <= hi:
            results.append(node.value)
            node = node.forward[0]
        return results
