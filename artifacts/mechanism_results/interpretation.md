# Frozen mechanism ablation

This experiment isolates the global rank-count preprocessing step. The full-sort adapter sorts every score and obtains exact counts using binary searches at support-score values. Both sparse variants retain the same support construction, support-score unique operation, interval distances, group assignments, and immutable compiled integration kernel. The adapter never calls the original preparation function first. It is a controlled ablation; an implementation designed around a global sort could reuse that ordering in other preprocessing steps.

The [protocol](../mechanism_protocol.json) was frozen at 2026-10-19 14:47:19 UTC. Timing ran from 14:54:18 to 14:55:41 UTC after the primary benchmark released the CPU. The grid contains 112 feasible cells over two lengths, four positive-label densities, four interval counts, and four maximum widths. Sixteen cells with more intervals than positive points were excluded in advance. Buffer expansion changes the actual maximum-support fraction, so the figures plot measured Q/n rather than label density.

All 101 preliminary validation cases had exactly matching preparation arrays and bitwise-identical outputs from the two sparse variants. The 112 timed cases repeated the array and bitwise checks; all five methods agreed within the frozen absolute tolerance of 1e-11. The largest observed error was 6.80566714095221e-14. There were 1,680 timed calls: five methods, three shuffled repetitions, and 112 cells. Timings include preparation and integration and exclude warmup, data generation, validation, and plotting. Hardware was an Apple M1 Pro, with NumPy 1.26.4, Numba 0.59.1, and one numerical thread.

| Runtime ratio | Geometric mean | Median | Range | Ratio at least 1.10 | Ratio at most 1/1.10 |
|---|---:|---:|---:|---:|---:|
| Full-sort sparse / current sparse | 1.1123 | 1.0976 | 0.9395–1.8044 | 56 | 0 |
| Fastest dense / current sparse | 1.3701 | 1.2524 | 0.2629–7.5266 | 69 | 34 |
| Fastest dense / full-sort sparse | 1.2319 | 1.1482 | 0.2260–6.2332 | 62 | 39 |

The fastest dense comparator is the minimum of the three dense-method median times within each cell. Every raw duration, output, method order, and selected comparator is retained in [raw_cases.jsonl](raw_cases.jsonl). The summaries are in [mechanism_results.json](../mechanism_results.json).

Avoiding the global sort supplies a modest additional gain in this grid. Much of the larger sparse-versus-dense advantage remains when the sparse integration kernel is fed by a global sort. At n=100,000 and L=100, the geometric-mean gain over the full-sort adapter is 1.0356×, while the gain over fastest dense is 2.4827×. This distinguishes the contribution of the changed rank-count preprocessing from support-restricted integration.

The break-even behavior is substantial. At L=0, current-sparse speedup over fastest dense has geometric means 0.7435× at n=10,000 and 0.8239× at n=100,000. For measured Q/n at least 0.6, the geometric mean is 0.7829× across 18 cells. These cases favor dense evaluation. In the measured Q/n bin [0.02, 0.1), the full-sort/current-sparse ratio is 0.9830× across eight cells, so avoiding the global sort is not uniformly helpful even when support is restricted.

These are descriptive results for a fixed synthetic grid, not population estimates or evidence for a universal speedup. The 10% thresholds were specified before timing and are descriptive timing margins, not significance tests. Three repetitions do not establish that small differences near 1× are reproducible across machines or workloads. No new state-of-the-art claim follows from this ablation alone.

Suggested figure caption: Each point is one frozen synthetic cell; colors indicate maximum buffer width L. The x-axis shows the realized maximum-support fraction Q/n after expansion. Runtime ratios use medians of three randomized repetitions and favor the current sparse implementation above 1×. The left panels compare a global-sort adapter with identical remaining preprocessing and the same compiled sparse kernel. The right panels use the fastest of three dense implementations per cell. Left panels use a shared linear ratio axis and right panels use a shared logarithmic ratio axis. Full raw results, including slowdowns and all predeclared exclusions, are retained.

The figure-only readability helper preserves the initial PNG/SVG at their receipt-bound paths and writes new `mechanism.readable.png` and `mechanism.readable.svg` figures with a separate `figure_receipt.json`. It changes no source or result bound to the timing receipt and generates no PDF. The original timed results SHA-256 is `5fe7660a4b6f3544127b6aea0ac33df0f9c2bbe2bce5166bea5ef7307cc0e0d6`.
