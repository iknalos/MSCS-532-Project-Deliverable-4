"""Baseline (proof-of-concept) inventory management system.

Composes the three core data structures:
  * HashTable  -- SKU -> Product primary index (O(1) expected lookup)
  * MinHeap    -- quantity-ordered index for low-stock alerts
  * SkipList   -- price-ordered index for price-range queries

A secondary HashTable maps category -> set of SKUs for category listing.
"""

from src.hash_table import HashTable
from src.min_heap import MinHeap
from src.skip_list import SkipList


class Product:
    """A single inventory record."""

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


class DuplicateSKUError(ValueError):
    pass


class UnknownSKUError(KeyError):
    pass


class InventorySystem:
    """Facade tying the indexes together and keeping them consistent."""

    def __init__(self):
        self._products = HashTable()
        self._stock_heap = MinHeap()
        self._price_index = SkipList()
        self._categories = HashTable()

    def __len__(self):
        return len(self._products)

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
        product = self._products.get(sku)
        if product is None:
            raise UnknownSKUError(sku)
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

    def low_stock(self, k):
        """The k products with the smallest quantities."""
        return [self.get_product(sku)
                for _, sku in self._stock_heap.k_smallest(k)]

    def products_in_price_range(self, lo, hi):
        """All products with lo <= price <= hi, in price order."""
        skus = self._price_index.range_query((lo, ""), (hi, "￿"))
        return [self.get_product(sku) for sku in skus]

    def products_in_category(self, category):
        members = self._categories.get(category) or set()
        return [self.get_product(sku) for sku in sorted(members)]
