"""Optimized inventory management system (Phase 3).

Same public interface as src.inventory.InventorySystem, rebuilt on the
optimized structures plus two system-level optimizations:

  * bulk_load() builds all indexes in one pass (O(n) heapify, one sort)
    instead of n independent inserts.
  * An LRU cache in front of the primary index exploits the skew of
    real inventory workloads, where a small set of hot SKUs receives
    most lookups. The cache is invalidated on writes to the cached SKU.
"""

from collections import OrderedDict

from src.optimized.hash_table_opt import OptimizedHashTable
from src.optimized.min_heap_opt import IndexedMinHeap
from src.optimized.price_index_opt import SortedPriceIndex
from src.inventory import DuplicateSKUError, UnknownSKUError


class Product:
    """Inventory record with __slots__ to cut per-instance memory."""

    __slots__ = ("sku", "name", "category", "price", "quantity")

    def __init__(self, sku, name, category, price, quantity):
        if price < 0:
            raise ValueError("price must be non-negative")
        if quantity < 0:
            raise ValueError("quantity must be non-negative")
        self.sku = sku
        self.name = name
        self.category = category
        self.price = price
        self.quantity = quantity

    def __repr__(self):
        return (f"Product(sku={self.sku!r}, name={self.name!r}, "
                f"category={self.category!r}, price={self.price}, "
                f"quantity={self.quantity})")


class OptimizedInventorySystem:
    CACHE_SIZE = 4096

    def __init__(self):
        self._products = OptimizedHashTable()
        self._stock_heap = IndexedMinHeap()
        self._price_index = SortedPriceIndex()
        self._categories = OptimizedHashTable()
        self._cache = OrderedDict()

    def __len__(self):
        return len(self._products)

    # ------------------------------------------------------------- bulk load

    def bulk_load(self, rows):
        """Load (sku, name, category, price, quantity) rows efficiently."""
        heap_pairs = []
        price_pairs = []
        for sku, name, category, price, quantity in rows:
            if sku in self._products:
                raise DuplicateSKUError(f"SKU already exists: {sku}")
            product = Product(sku, name, category, price, quantity)
            self._products.put(sku, product)
            heap_pairs.append((quantity, sku))
            price_pairs.append(((price, sku), sku))
            members = self._categories.get(category)
            if members is None:
                members = set()
                self._categories.put(category, members)
            members.add(sku)
        self._stock_heap.build(heap_pairs)
        self._price_index.build(price_pairs)

    # ------------------------------------------------------------------ CRUD

    def add_product(self, sku, name, category, price, quantity):
        if sku in self._products:
            raise DuplicateSKUError(f"SKU already exists: {sku}")
        product = Product(sku, name, category, price, quantity)
        self._products.put(sku, product)
        self._stock_heap.push(quantity, sku)
        self._price_index.insert((price, sku), sku)
        members = self._categories.get(category)
        if members is None:
            members = set()
            self._categories.put(category, members)
        members.add(sku)
        return product

    def get_product(self, sku):
        cache = self._cache
        product = cache.get(sku)
        if product is not None:
            cache.move_to_end(sku)
            return product
        product = self._products.get(sku)
        if product is None:
            raise UnknownSKUError(sku)
        cache[sku] = product
        if len(cache) > self.CACHE_SIZE:
            cache.popitem(last=False)
        return product

    def remove_product(self, sku):
        product = self._products.get(sku)
        if product is None:
            raise UnknownSKUError(sku)
        self._products.remove(sku)
        self._stock_heap.remove(sku)
        self._price_index.remove((product.price, sku))
        members = self._categories.get(product.category)
        if members:
            members.discard(sku)
        self._cache.pop(sku, None)
        return product

    # --------------------------------------------------------------- updates

    def update_quantity(self, sku, new_quantity):
        product = self.get_product(sku)
        product.quantity = new_quantity
        self._stock_heap.update_key(sku, new_quantity)

    def update_price(self, sku, new_price):
        product = self.get_product(sku)
        self._price_index.remove((product.price, sku))
        product.price = new_price
        self._price_index.insert((new_price, sku), sku)

    # --------------------------------------------------------------- queries
    #
    # Scan-type queries materialize their results straight from the
    # primary index, bypassing the LRU cache. Routing scans through the
    # cache would evict the hot working set with cold keys touched once
    # (cache pollution) -- the same reason database buffer pools use
    # scan-resistant replacement policies.

    def low_stock(self, k):
        get = self._products.get
        return [get(sku) for _, sku in self._stock_heap.k_smallest(k)]

    def products_in_price_range(self, lo, hi):
        skus = self._price_index.range_query((lo, ""), (hi, "￿"))
        get = self._products.get
        return [get(sku) for sku in skus]

    def products_in_category(self, category):
        members = self._categories.get(category) or set()
        get = self._products.get
        return [get(sku) for sku in sorted(members)]
