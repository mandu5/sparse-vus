# Structural active-prefix VUS result

One completed local Apple Silicon run of 16 predeclared synthetic cases. All structural assertions and PR parity checks passed; maximum absolute PR difference was `1.3877787807814457e-17`. The reference was the production radix evaluator, not an independent dense oracle. The report was recomputed in a fresh process and all source, input, raw-log, environment, and randomization bindings passed.

CPU: `Apple M1 Pro`. Three warmed, randomized serial repetitions per method/case; medians below include the complete public scalar PR call. Profiling and I/O were outside timing. No runtime success criterion was used.

At the largest planned width, `L=2048`, every input has `n=8195`:

| Family | Saturation visits | Last-positive / full visits | Saturation median (ms) | Last-positive / saturation | Radix / saturation |
| --- | ---: | ---: | ---: | ---: | ---: |
| `singleton_original_last` | 6,143 | 2,099,201 | 0.609167 | 17.536x | 34.861x |
| `two_positive_separation` | 8,192 | 4,198,402 | 0.716500 | 17.063x | 53.882x |
| `interval8_original_last` | 46,413 | 2,113,544 | 0.829875 | 12.793x | 25.589x |
| `tied_singleton` | 2,099,201 | 2,099,201 | 5.773583 | 1.012x | 3.374x |

The two-positive construction intentionally has tied background scores. Its four terminating high-score events are distinct; it is not an all-distinct score witness. Its exact saturation visit totals are `4L` at all four widths. The singleton and interval-of-eight unique-score cases satisfy the per-width `3` and `23` visit bounds respectively.

The all-tied negative control visits the entire active tie in every stop mode. At `L=2048`, the last-positive and full-scan runtime ratios are approximately one; its gain relative to radix therefore must not be credited to early termination. Its total active work remains quadratic in the width.

Each of the three comparator methods won 3 of the 16 case-level median comparisons against saturation; saturation won the remaining 13. In particular, at `L=32`, radix was faster on the singleton-original-last, interval-of-eight, and tied-singleton inputs. All raw timings and small-case losses are retained in `measurements.jsonl` and `report.json`. These deliberately constructed families support the specified work bounds; they do not establish population performance, firstness, or global SOTA.

Receipts:

- Protocol SHA-256: `61f69703dd7e2a4a3e368307abfdbdebe49ca31f91ae5039424e44bba386995f`.
- Input manifest SHA-256: `de94a3046d41ff0a91d47350f230c99267c92654a2358d2bbb3ef4a3394f6418`.
- Measurements SHA-256: `812ab9c5fab5aa85ced8151b699f468efcfdbbdaefb5341409febc83b677aa5f`.
- Saturation kernel SHA-256: `319271b40a5f029e71088eedc2830d98665f55f5f7dbbbe3b1d03b5fdc7a1914`.
- Runner SHA-256: `55d97b5c0973ce3281bf560b6f94ad5d6d31f88676e9cd17657255aa95159873`.
