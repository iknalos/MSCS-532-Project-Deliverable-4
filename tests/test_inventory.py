"""Test suite for the inventory system (baseline and optimized).

Run from the project root:  python -m pytest tests -q
                       or:  python -m unittest discover tests -v
"""

import random
import unittest

from src.hash_table import HashTable
from src.min_heap import MinHeap
from src.skip_list import SkipList
from src.inventory import InventorySystem, DuplicateSKUError, UnknownSKUError
from src.optimized.hash_table_opt import OptimizedHashTable
from src.optimized.min_heap_opt import IndexedMinHeap
from src.optimized.price_index_opt import SortedPriceIndex
from src.optimized.inventory_opt import OptimizedInventorySystem


# --------------------------------------------------------------- hash tables

class HashTableContract:
    """Shared tests run against both hash table implementations."""

    def make(self):
        raise NotImplementedError

    def test_put_get_roundtrip(self):
        t = self.make()
        t.put("A1", 1)
        t.put("B2", 2)
        self.assertEqual(t.get("A1"), 1)
        self.assertEqual(t.get("B2"), 2)
        self.assertEqual(len(t), 2)

    def test_update_existing_key(self):
        t = self.make()
        t.put("A1", 1)
        t.put("A1", 99)
        self.assertEqual(t.get("A1"), 99)
        self.assertEqual(len(t), 1)

    def test_missing_key_returns_default(self):
        t = self.make()
        self.assertIsNone(t.get("nope"))
        self.assertEqual(t.get("nope", -1), -1)
        self.assertNotIn("nope", t)

    def test_remove(self):
        t = self.make()
        t.put("A1", 1)
        self.assertTrue(t.remove("A1"))
        self.assertFalse(t.remove("A1"))
        self.assertEqual(len(t), 0)
        self.assertNotIn("A1", t)

    def test_grows_past_initial_capacity(self):
        t = self.make()
        for i in range(1000):
            t.put(f"SKU-{i}", i)
        self.assertEqual(len(t), 1000)
        for i in range(0, 1000, 97):
            self.assertEqual(t.get(f"SKU-{i}"), i)

    def test_reinsert_after_delete(self):
        t = self.make()
        for i in range(200):
            t.put(f"K{i}", i)
        for i in range(0, 200, 2):
            t.remove(f"K{i}")
        for i in range(0, 200, 2):
            t.put(f"K{i}", i * 10)
        self.assertEqual(len(t), 200)
        self.assertEqual(t.get("K10"), 100)
        self.assertEqual(t.get("K11"), 11)

    def test_items_yields_all_live_entries(self):
        t = self.make()
        expected = {}
        for i in range(50):
            t.put(f"K{i}", i)
            expected[f"K{i}"] = i
        t.remove("K7")
        del expected["K7"]
        self.assertEqual(dict(t.items()), expected)


class TestHashTable(HashTableContract, unittest.TestCase):
    def make(self):
        return HashTable()


class TestOptimizedHashTable(HashTableContract, unittest.TestCase):
    def make(self):
        return OptimizedHashTable()

    def test_tombstone_cleanup_keeps_table_usable(self):
        t = self.make()
        for round_ in range(5):
            for i in range(500):
                t.put(f"R{round_}-K{i}", i)
            for i in range(500):
                self.assertTrue(t.remove(f"R{round_}-K{i}"))
        self.assertEqual(len(t), 0)


# --------------------------------------------------------------------- heaps

class HeapContract:
    def make(self):
        raise NotImplementedError

    def test_push_pop_orders_by_key(self):
        h = self.make()
        for qty, sku in [(5, "e"), (1, "a"), (3, "c"), (2, "b"), (4, "d")]:
            h.push(qty, sku)
        popped = [h.pop() for _ in range(len(h))]
        self.assertEqual(popped, [(1, "a"), (2, "b"), (3, "c"), (4, "d"), (5, "e")])

    def test_peek_does_not_remove(self):
        h = self.make()
        h.push(2, "x")
        h.push(1, "y")
        self.assertEqual(h.peek(), (1, "y"))
        self.assertEqual(len(h), 2)

    def test_empty_heap_raises(self):
        h = self.make()
        with self.assertRaises(IndexError):
            h.pop()
        with self.assertRaises(IndexError):
            h.peek()

    def test_update_key_up_and_down(self):
        h = self.make()
        for qty, sku in [(10, "a"), (20, "b"), (30, "c")]:
            h.push(qty, sku)
        self.assertTrue(h.update_key("c", 1))    # decrease -> new min
        self.assertEqual(h.peek(), (1, "c"))
        self.assertTrue(h.update_key("c", 99))   # increase -> sinks
        self.assertEqual(h.peek(), (10, "a"))
        self.assertFalse(h.update_key("zzz", 5))

    def test_remove_by_id(self):
        h = self.make()
        for qty, sku in [(1, "a"), (2, "b"), (3, "c")]:
            h.push(qty, sku)
        self.assertTrue(h.remove("a"))
        self.assertFalse(h.remove("a"))
        self.assertEqual(h.peek(), (2, "b"))

    def test_k_smallest_matches_sorted(self):
        h = self.make()
        rng = random.Random(42)
        pairs = [(rng.randint(0, 10_000), f"sku{i}") for i in range(500)]
        for qty, sku in pairs:
            h.push(qty, sku)
        expected = sorted(pairs)[:10]
        got = h.k_smallest(10)
        self.assertEqual(sorted(k for k, _ in got), [k for k, _ in expected])

    def test_k_smallest_k_larger_than_heap(self):
        h = self.make()
        h.push(2, "b")
        h.push(1, "a")
        self.assertEqual(len(h.k_smallest(10)), 2)


class TestMinHeap(HeapContract, unittest.TestCase):
    def make(self):
        return MinHeap()


class TestIndexedMinHeap(HeapContract, unittest.TestCase):
    def make(self):
        return IndexedMinHeap()

    def test_build_heapifies_in_bulk(self):
        h = self.make()
        rng = random.Random(7)
        pairs = [(rng.randint(0, 999), f"s{i}") for i in range(1000)]
        h.build(pairs)
        self.assertEqual(len(h), 1000)
        popped = [h.pop()[0] for _ in range(1000)]
        self.assertEqual(popped, sorted(popped))

    def test_duplicate_id_rejected(self):
        h = self.make()
        h.push(1, "a")
        with self.assertRaises(KeyError):
            h.push(2, "a")


# ------------------------------------------------------------- price indexes

class PriceIndexContract:
    def make(self):
        raise NotImplementedError

    def test_insert_search(self):
        s = self.make()
        s.insert((9.99, "A"), "A")
        s.insert((4.99, "B"), "B")
        self.assertEqual(s.search((9.99, "A")), "A")
        self.assertIsNone(s.search((1.00, "Z")))
        self.assertEqual(len(s), 2)

    def test_range_query_inclusive_and_sorted(self):
        s = self.make()
        prices = [(1.0, "a"), (2.5, "b"), (2.5, "c"), (7.0, "d"), (9.0, "e")]
        for key in prices:
            s.insert(key, key[1])
        self.assertEqual(s.range_query((2.5, ""), (7.0, "￿")), ["b", "c", "d"])
        self.assertEqual(s.range_query((0.0, ""), (0.5, "￿")), [])
        self.assertEqual(s.range_query((1.0, ""), (9.0, "￿")),
                         ["a", "b", "c", "d", "e"])

    def test_remove(self):
        s = self.make()
        s.insert((5.0, "x"), "x")
        self.assertTrue(s.remove((5.0, "x")))
        self.assertFalse(s.remove((5.0, "x")))
        self.assertEqual(len(s), 0)

    def test_update_existing_key_overwrites(self):
        s = self.make()
        s.insert((5.0, "x"), "old")
        s.insert((5.0, "x"), "new")
        self.assertEqual(len(s), 1)
        self.assertEqual(s.search((5.0, "x")), "new")

    def test_large_random_workload_matches_reference(self):
        s = self.make()
        rng = random.Random(99)
        ref = {}
        for i in range(2000):
            key = (round(rng.uniform(0, 100), 2), f"s{i}")
            s.insert(key, key[1])
            ref[key] = key[1]
        lo, hi = (25.0, ""), (75.0, "￿")
        expected = [v for k, v in sorted(ref.items()) if lo <= k <= hi]
        self.assertEqual(s.range_query(lo, hi), expected)


class TestSkipList(PriceIndexContract, unittest.TestCase):
    def make(self):
        return SkipList(seed=1234)


class TestSortedPriceIndex(PriceIndexContract, unittest.TestCase):
    def make(self):
        return SortedPriceIndex()


# ------------------------------------------------------- integration (both)

class InventoryContract:
    def make(self):
        raise NotImplementedError

    def _stock(self, inv):
        inv.add_product("SKU-1", "USB Cable", "Electronics", 7.99, 120)
        inv.add_product("SKU-2", "Notebook", "Stationery", 3.49, 15)
        inv.add_product("SKU-3", "Monitor", "Electronics", 189.00, 4)
        inv.add_product("SKU-4", "Pen Pack", "Stationery", 5.99, 300)
        inv.add_product("SKU-5", "Webcam", "Electronics", 49.99, 2)

    def test_add_and_get(self):
        inv = self.make()
        self._stock(inv)
        self.assertEqual(inv.get_product("SKU-3").name, "Monitor")
        self.assertEqual(len(inv), 5)

    def test_duplicate_sku_rejected(self):
        inv = self.make()
        self._stock(inv)
        with self.assertRaises(DuplicateSKUError):
            inv.add_product("SKU-1", "Dup", "X", 1.0, 1)

    def test_unknown_sku_raises(self):
        inv = self.make()
        with self.assertRaises(UnknownSKUError):
            inv.get_product("NOPE")
        with self.assertRaises(UnknownSKUError):
            inv.remove_product("NOPE")

    def test_low_stock_ordering(self):
        inv = self.make()
        self._stock(inv)
        low = inv.low_stock(2)
        self.assertEqual({p.sku for p in low}, {"SKU-5", "SKU-3"})

    def test_low_stock_reflects_quantity_updates(self):
        inv = self.make()
        self._stock(inv)
        inv.update_quantity("SKU-4", 1)  # Pen Pack now the scarcest
        low = inv.low_stock(1)
        self.assertEqual(low[0].sku, "SKU-4")
        self.assertEqual(inv.get_product("SKU-4").quantity, 1)

    def test_price_range_query(self):
        inv = self.make()
        self._stock(inv)
        names = [p.name for p in inv.products_in_price_range(3.0, 8.0)]
        self.assertEqual(names, ["Notebook", "Pen Pack", "USB Cable"])

    def test_price_update_moves_product_between_ranges(self):
        inv = self.make()
        self._stock(inv)
        inv.update_price("SKU-1", 250.00)
        in_low = [p.sku for p in inv.products_in_price_range(3.0, 8.0)]
        in_high = [p.sku for p in inv.products_in_price_range(200.0, 300.0)]
        self.assertNotIn("SKU-1", in_low)
        self.assertIn("SKU-1", in_high)

    def test_remove_product_clears_all_indexes(self):
        inv = self.make()
        self._stock(inv)
        inv.remove_product("SKU-5")
        self.assertEqual(len(inv), 4)
        self.assertNotIn("SKU-5", [p.sku for p in inv.low_stock(5)])
        self.assertNotIn("SKU-5",
                         [p.sku for p in inv.products_in_price_range(0, 1000)])
        self.assertNotIn("SKU-5",
                         [p.sku for p in inv.products_in_category("Electronics")])

    def test_category_listing(self):
        inv = self.make()
        self._stock(inv)
        skus = [p.sku for p in inv.products_in_category("Stationery")]
        self.assertEqual(skus, ["SKU-2", "SKU-4"])

    def test_negative_values_rejected(self):
        inv = self.make()
        with self.assertRaises(ValueError):
            inv.add_product("BAD", "Bad", "X", -1.0, 5)
        with self.assertRaises(ValueError):
            inv.add_product("BAD", "Bad", "X", 1.0, -5)

    def test_zero_quantity_is_valid_and_lowest(self):
        inv = self.make()
        self._stock(inv)
        inv.add_product("SKU-6", "Sold Out Item", "Misc", 9.99, 0)
        self.assertEqual(inv.low_stock(1)[0].sku, "SKU-6")


class TestInventorySystem(InventoryContract, unittest.TestCase):
    def make(self):
        return InventorySystem()


class TestOptimizedInventorySystem(InventoryContract, unittest.TestCase):
    def make(self):
        return OptimizedInventorySystem()

    def test_bulk_load_matches_incremental(self):
        inv = self.make()
        rows = [(f"SKU-{i}", f"Item {i}", "Cat", float(i), i % 50)
                for i in range(500)]
        inv.bulk_load(rows)
        self.assertEqual(len(inv), 500)
        self.assertEqual(inv.get_product("SKU-123").name, "Item 123")
        low = inv.low_stock(3)
        self.assertTrue(all(p.quantity == 0 for p in low))
        in_range = inv.products_in_price_range(10.0, 20.0)
        self.assertEqual(len(in_range), 11)

    def test_cache_invalidated_on_remove(self):
        inv = self.make()
        inv.add_product("SKU-1", "Item", "Cat", 1.0, 1)
        inv.get_product("SKU-1")          # warm the cache
        inv.remove_product("SKU-1")
        with self.assertRaises(UnknownSKUError):
            inv.get_product("SKU-1")


if __name__ == "__main__":
    unittest.main()
