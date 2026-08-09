# Dynamic Inventory Management System — Deliverable 4: Final Report and Presentation

**MSCS 532 – Algorithms and Data Structures — Term Project, Final Phase**
*Developing and Optimizing Data Structures for Real-World Applications Using Python*

This repository contains the final deliverable of the term project:

- **`Deliverable4_Final_Report.docx`** — comprehensive final report (APA format)
  integrating all prior phases: literature review, requirements, design
  rationale, proof-of-concept implementation, testing methodology,
  optimization, performance evaluation with measured metrics and charts,
  discussion of trade-offs and threats to validity, and impact / future
  directions. Six peer-reviewed references.
- **`Deliverable4_Presentation.pptx`** — 13-slide, 15-minute presentation
  with full speaker notes on every slide.
- **`Deliverable4_Presentation_Script.docx`** — the speaker script with
  per-slide timings (totals 15:00).
- **`Deliverable4_Oral_Presentation.mp4`** — the recorded 15-minute oral
  presentation delivered from these slides.
- The complete, runnable system the report describes: baseline and optimized
  implementations, the 65-case contract test suite, the demo, and the
  benchmark harness with the measured results used in the report.

## Project summary

An inventory system for e-commerce/retail composed of three purpose-chosen
indexes kept consistent by a facade: a hash table (SKU lookup), a binary
min-heap keyed on quantity (low-stock alerts), and an ordered price index
(range queries), plus a category index. Phase 2 implemented everything from
first principles as a correct baseline; Phase 3 optimized it:

| Requirement | Baseline (Phase 2) | Optimized (Phase 3) |
|---|---|---|
| SKU lookup / insert / delete | Chaining hash table | Open addressing, perturbed probing, tombstones |
| Low-stock alerts (k scarcest) | Min-heap, O(n) update-by-SKU | Indexed heap: O(log n) update, O(n) build, O(k log k) top-k |
| Price-range queries | Skip list (Pugh, 1990) | Sorted array + C-level `bisect` |
| System level | — | One-pass `bulk_load`, LRU lookup cache, `__slots__` records |

**Headline results (n = 100,000):** quantity updates ~2,750x faster,
low-stock queries ~3,400x faster (asymptotic fixes; gaps grow with n);
bulk load ~2.4x, skewed lookups ~1.4x, range queries ~1.6x (constant-factor
fixes); peak memory 69.3 → 57.6 MiB. All 65 contract tests pass on both
implementations, so every speedup comes with unchanged observable behavior.

## Layout

```
Deliverable4_Final_Report.docx           the comprehensive final report
Deliverable4_Presentation.pptx           15-minute slides (speaker notes included)
Deliverable4_Presentation_Script.docx    speaker script with per-slide timings
Deliverable4_Oral_Presentation.mp4       recorded 15-minute oral presentation
src/                                     Phase 2 baseline implementations
src/optimized/                           Phase 3 optimized implementations
tests/test_inventory.py                  65 contract tests, run against BOTH versions
demo.py                                  end-to-end demonstration
benchmarks/benchmark.py                  baseline-vs-optimized benchmark suite
benchmarks/results/                      measured CSV + charts used in the report
```

## Running

```bash
python demo.py                          # guided demonstration
python -m unittest discover tests -v    # 65-case test suite (run from repo root)
python benchmarks/benchmark.py          # benchmarks (rewrites benchmarks/results/)
```

Requires Python 3.10+. `matplotlib` is needed only for benchmark charts; the
core system has no dependencies.

## Prior phase repositories

- Deliverable 1 (design): https://github.com/iknalos/MSCS-532-Project-Deliverable-1
- Deliverable 2 (proof of concept): https://github.com/iknalos/MSCS-532-Project-Deliverable-2
- Deliverable 3 (optimization and evaluation): https://github.com/iknalos/MSCS-532-Project-Deliverable-3
