"""Demonstration script for the Dynamic Inventory Management System.

Walks through every core operation on a small, readable dataset, then
shows the same behavior on the optimized implementation.

Run from the project root:  python demo.py
"""

from src.inventory import InventorySystem, DuplicateSKUError, UnknownSKUError
from src.optimized.inventory_opt import OptimizedInventorySystem

CATALOG = [
    ("ELEC-001", "USB-C Cable 1m",   "Electronics", 7.99, 120),
    ("ELEC-002", "27in Monitor",     "Electronics", 189.00, 4),
    ("ELEC-003", "1080p Webcam",     "Electronics", 49.99, 2),
    ("ELEC-004", "Wireless Mouse",   "Electronics", 24.50, 35),
    ("STAT-001", "A5 Notebook",      "Stationery",  3.49, 15),
    ("STAT-002", "Pen Pack (10)",    "Stationery",  5.99, 300),
    ("STAT-003", "Desk Organizer",   "Stationery",  18.75, 8),
    ("HOME-001", "LED Desk Lamp",    "Home",        32.00, 22),
    ("HOME-002", "Coffee Mug",       "Home",        11.25, 64),
    ("HOME-003", "Wall Clock",       "Home",        27.90, 6),
]


def show(title, products):
    print(f"\n  {title}")
    for p in products:
        print(f"    {p.sku:<9} {p.name:<18} ${p.price:>7.2f}  qty={p.quantity}")


def run_demo(inv, label):
    print(f"\n{'=' * 62}\n {label}\n{'=' * 62}")

    print(f"\n[1] Adding {len(CATALOG)} products (hash table + heap + price index)")
    for row in CATALOG:
        inv.add_product(*row)
    print(f"    Inventory size: {len(inv)}")

    print("\n[2] O(1) SKU lookup via hash table")
    p = inv.get_product("ELEC-002")
    print(f"    get_product('ELEC-002') -> {p.name}, ${p.price}, qty={p.quantity}")

    print("\n[3] Low-stock alert via min-heap (3 scarcest products)")
    show("low_stock(3):", inv.low_stock(3))

    print("\n[4] Price-range query via ordered index ($5 - $30)")
    show("products_in_price_range(5, 30):", inv.products_in_price_range(5, 30))

    print("\n[5] Category listing")
    show("products_in_category('Home'):", inv.products_in_category("Home"))

    print("\n[6] Updates propagate to every index")
    inv.update_quantity("STAT-002", 1)
    print("    update_quantity('STAT-002', 1)  -> Pen Pack nearly sold out")
    show("low_stock(3) now:", inv.low_stock(3))
    inv.update_price("ELEC-001", 149.00)
    print("    update_price('ELEC-001', 149.00) -> cable leaves the $5-$30 band")
    show("products_in_price_range(5, 30) now:", inv.products_in_price_range(5, 30))

    print("\n[7] Deletion removes the product from all indexes")
    inv.remove_product("ELEC-003")
    print(f"    remove_product('ELEC-003') -> size {len(inv)}")
    show("low_stock(3) after removal:", inv.low_stock(3))

    print("\n[8] Error handling")
    try:
        inv.add_product("ELEC-001", "Duplicate", "X", 1.0, 1)
    except DuplicateSKUError as e:
        print(f"    DuplicateSKUError: {e}")
    try:
        inv.get_product("MISSING-SKU")
    except UnknownSKUError as e:
        print(f"    UnknownSKUError: {e}")


if __name__ == "__main__":
    run_demo(InventorySystem(), "BASELINE (proof of concept, Phase 2)")
    run_demo(OptimizedInventorySystem(), "OPTIMIZED (Phase 3)")
    print("\nDemo complete.")
