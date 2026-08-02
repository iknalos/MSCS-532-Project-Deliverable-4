"""Performance benchmark: baseline (Phase 2 PoC) vs optimized (Phase 3).

Measures, at increasing inventory sizes:
  * bulk load        - building all three indexes from n catalog rows
  * lookup           - 20,000 SKU lookups with an 80/20 hot-key skew
  * update_quantity  - 200 random stock adjustments
  * price range      - 200 range queries covering ~1% of the price space
  * low_stock(10)    - 50 low-stock alert queries
plus peak memory for a fully built 100k-product system (tracemalloc).

Writes results/benchmark_results.csv and one PNG chart per operation.
Run from the project root:  python benchmarks/benchmark.py
"""

import csv
import os
import random
import sys
import time
import tracemalloc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.inventory import InventorySystem
from src.optimized.inventory_opt import OptimizedInventorySystem

SIZES = [1_000, 5_000, 10_000, 50_000, 100_000]
LOOKUPS = 20_000
UPDATES = 200
RANGE_QUERIES = 200
LOW_STOCK_QUERIES = 50
MEMORY_SIZE = 100_000
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

CATEGORIES = ["Electronics", "Stationery", "Home", "Garden", "Toys",
              "Grocery", "Sports", "Auto", "Beauty", "Office"]


def make_rows(n, seed=42):
    rng = random.Random(seed)
    return [(f"SKU-{i:07d}",
             f"Product {i}",
             CATEGORIES[i % len(CATEGORIES)],
             round(rng.uniform(0.5, 500.0), 2),
             rng.randint(0, 1000))
            for i in range(n)]


def timed(fn):
    t0 = time.perf_counter()
    fn()
    return time.perf_counter() - t0


def build_baseline(rows):
    inv = InventorySystem()
    for row in rows:
        inv.add_product(*row)
    return inv


def build_optimized(rows):
    inv = OptimizedInventorySystem()
    inv.bulk_load(rows)
    return inv


def skewed_skus(rows, count, seed=7):
    """80% of lookups hit the hottest 2% of SKUs (Zipf-like retail skew)."""
    rng = random.Random(seed)
    hot = [r[0] for r in rows[:max(1, len(rows) // 50)]]
    all_skus = [r[0] for r in rows]
    return [rng.choice(hot) if rng.random() < 0.8 else rng.choice(all_skus)
            for _ in range(count)]


def bench_size(n):
    rows = make_rows(n)
    rng = random.Random(123)
    row = {"n": n}

    for label, builder in (("baseline", build_baseline),
                           ("optimized", build_optimized)):
        t0 = time.perf_counter()
        inv = builder(rows)
        row[f"bulk_load_{label}"] = time.perf_counter() - t0

        skus = skewed_skus(rows, LOOKUPS)
        row[f"lookup_{label}"] = timed(
            lambda: [inv.get_product(s) for s in skus])

        update_targets = [(rng.choice(rows)[0], rng.randint(0, 1000))
                          for _ in range(UPDATES)]
        row[f"update_qty_{label}"] = timed(
            lambda: [inv.update_quantity(s, q) for s, q in update_targets])

        bands = [(lo := rng.uniform(0.5, 495.0), lo + 5.0)
                 for _ in range(RANGE_QUERIES)]
        row[f"price_range_{label}"] = timed(
            lambda: [inv.products_in_price_range(lo, hi) for lo, hi in bands])

        row[f"low_stock_{label}"] = timed(
            lambda: [inv.low_stock(10) for _ in range(LOW_STOCK_QUERIES)])

        del inv
    print(f"  n={n:>7,}: "
          + ", ".join(f"{k.rsplit('_', 1)[0]} x{row[k[:-10] + '_baseline'] / max(row[k], 1e-9):.1f}"
                      for k in row if k.endswith("_optimized")))
    return row


def bench_memory():
    rows = make_rows(MEMORY_SIZE)
    out = {}
    for label, builder in (("baseline", build_baseline),
                           ("optimized", build_optimized)):
        tracemalloc.start()
        inv = builder(rows)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        out[label] = peak / (1024 * 1024)
        del inv
    return out


def write_csv(results, memory):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, "benchmark_results.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
        f.write(f"\n# peak memory at n={MEMORY_SIZE}: "
                f"baseline={memory['baseline']:.1f} MiB, "
                f"optimized={memory['optimized']:.1f} MiB\n")
    return path


OPS = [
    ("bulk_load", "Bulk load (build all indexes)"),
    ("lookup", f"{LOOKUPS:,} skewed SKU lookups"),
    ("update_qty", f"{UPDATES} quantity updates"),
    ("price_range", f"{RANGE_QUERIES} price-range queries"),
    ("low_stock", f"{LOW_STOCK_QUERIES} low-stock(10) queries"),
]


def plot(results, memory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ns = [r["n"] for r in results]
    for op, title in OPS:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.plot(ns, [r[f"{op}_baseline"] for r in results],
                "o-", label="Baseline (PoC)", color="#c0392b")
        ax.plot(ns, [r[f"{op}_optimized"] for r in results],
                "s-", label="Optimized", color="#27ae60")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Inventory size (products)")
        ax.set_ylabel("Time (seconds)")
        ax.set_title(title)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(RESULTS_DIR, f"{op}.png"), dpi=150)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    labels = ["Baseline (PoC)", "Optimized"]
    vals = [memory["baseline"], memory["optimized"]]
    bars = ax.bar(labels, vals, color=["#c0392b", "#27ae60"], width=0.5)
    ax.bar_label(bars, fmt="%.1f MiB")
    ax.set_ylabel("Peak memory (MiB)")
    ax.set_title(f"Peak memory building {MEMORY_SIZE:,} products")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, "memory.png"), dpi=150)
    plt.close(fig)


def main():
    print("Running benchmarks (baseline vs optimized)...")
    results = [bench_size(n) for n in SIZES]
    print(f"Measuring peak memory at n={MEMORY_SIZE:,}...")
    memory = bench_memory()
    path = write_csv(results, memory)
    plot(results, memory)
    print(f"\nResults written to {path}")
    print(f"Charts written to {RESULTS_DIR}")

    print("\nSpeedups (baseline / optimized):")
    header = "n".rjust(9) + "".join(op.rjust(14) for op, _ in OPS)
    print(header)
    for r in results:
        line = f"{r['n']:>9,}"
        for op, _ in OPS:
            ratio = r[f"{op}_baseline"] / max(r[f"{op}_optimized"], 1e-9)
            line += f"{ratio:>13.1f}x"
        print(line)
    print(f"\nPeak memory at n={MEMORY_SIZE:,}: "
          f"baseline {memory['baseline']:.1f} MiB -> "
          f"optimized {memory['optimized']:.1f} MiB")


if __name__ == "__main__":
    main()
