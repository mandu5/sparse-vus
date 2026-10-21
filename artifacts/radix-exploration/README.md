# Fixed-word radix preparation exploration — 2026-10-21

Status: promising development-only prototype; no production mutation, no holdout access, no external SOTA claim. Run performed after root's explicit CPU-quiet signal, after its full test suite completed. All source hashes unchanged before/after. The predeclared six largest series in the existing 42-series development set were used, three models each, width30, three randomized paired repetitions. Warm-up/JIT compilation excluded; each timed call includes input validation, preparation and exhaustive width evaluation.

## Key source finding

NumPy's general sort manual says integer stable sorts use radix, but **uint64 stable argsort does not dispatch to radix in the actual NumPy1.26.4 implementation**.

- NumPy1.26.4 is commit `9815c16f449e12915ef35a8255329ba26dacd5c0` (2024-02-05).
- [`arraytypes.c.src` lines4348–4439](https://github.com/numpy/numpy/blob/9815c16f449e12915ef35a8255329ba26dacd5c0/numpy/core/src/multiarray/arraytypes.c.src#L4348): dtype list begins Bool, Byte, UByte, Short, UShort, Int, UInt, Long, ULong, LongLong, ULongLong; `rsort=1*5,0*16` enables radix only for the first five (at most16-bit integers).
- [`item_selection.c` lines1663–1698](https://github.com/numpy/numpy/blob/9815c16f449e12915ef35a8255329ba26dacd5c0/numpy/core/src/multiarray/item_selection.c#L1663): `PyArray_ArgSort` dispatches through the dtype's `argsort[which]` function pointer.
- [`radixsort.cpp`](https://github.com/numpy/numpy/blob/9815c16f449e12915ef35a8255329ba26dacd5c0/numpy/core/src/npysort/radixsort.cpp#L134) contains the indirect counting-radix implementation, but the existence of a function is not proof it is selected for every integer dtype.
- NumPy2.3.0's analogous `arraytypes.c.src` retains the same `1*5,0*16` selection. Upgrading to that version alone does not repair the complexity argument.
- [NumPy1.26 general sort notes](https://numpy.org/doc/1.26/reference/generated/numpy.sort.html) should therefore not be used alone to prove the uint64 indirect-sort path is linear.

## Prototype methods

`prototype.py` implements three preparation variants for comparison, sharing a linear temporal scan of nearest-two interval distances:

1. `counting`: self-contained Numba eight-pass stable LSD counting radix with256buckets/pass on transformed uint64 keys. No comparison sorting.
2. `u16`: four successive stable NumPy uint16 digit argsorts. Each digit path actually uses radix in NumPy1.26.4; composition remains fixed-word linear but allocates more intermediate arrays.
3. `u64_timsort`: transformed uint64 `np.argsort(kind='stable')`, the original hypothesis with its actual timsort complexity. Included as a negative control for the dispatch claim.

All finite input scores are first converted to float64 under the existing API. For bit representation `u`, ascending order key is `~u` for negative values and `u XOR sign_bit` otherwise; descending order uses its bitwise complement. Signed zeros are normalized to one key before sorting because the numerical metric treats -0 and +0 as a tie. NaN/infinity remain rejected by the existing validator. This is the standard floating-point sortable-key transformation, not novel research.

After sorting all keys, a single rank scan reads complete equal-score groups. If a group contains any maximum-buffer-support position, its support group number is recorded, `before` is the start rank, and `after` is the end rank. Unsupported groups create no support event but still contribute to subsequent ranks. Consequently both off-support tie counts and strict-higher counts agree with the old searchsorted/histogram preparation.

For each temporally sorted support position, advance a monotone interval pointer to the first start strictly to its right. The two closest distinct intervals must occur among the two immediately preceding and two immediately following intervals. Tracking the two smallest distances in that constant-size set reproduces the original four-candidate geometry with `O(Q+K)` time.

## Conditional complexity

Under fixed64-bit word-RAM operations and the declared binary-label/finite-float64 contract:

- Validation, label runs, maximum support construction: `O(n+Q+K)`.
- Key transformation, eight fixed radix passes, complete tie scan: `O(n+Q)`.
- Nearest-two geometry: `O(Q+K)`.
- Exhaustive sparse PR width sweep: `O((L+1)(Q+G+K))`.

Since `G <= Q` and `K <= Q`, total is `O(n+(L+1)Q)` time. This is not a comparison-model result for arbitrary real numbers. It does not make generic radix sorting novel. Auxiliary memory remains linear in input/support/width sizes; radix stores input-sized keys, permutation and scratch arrays in addition to support mapping. It must not be described as support-only memory.

## Verification and exploratory outcomes

83 small fixtures covered random and heavily tied scores, positive/negative finite extremes, subnormal values, both signed-zero arrangements, non-native endian and strided inputs. Every one of all12 preparation outputs was compared for all3 variants. Six selected development series×3models added54 full-array comparisons, giving303 parity fixtures.144 metric checks had maximum observed absolute difference exactly0. Input immutability also checked.

| Variant | Median whole-call speedup | Range | Wins | Sum of18case medians |
|---|---:|---:|---:|---:|
| Current preparation | 1 | — | — | 1.168063455s |
| Eight-pass counting radix | 2.653712411 | 2.303752239–3.112847779 | 18/18 | 0.420764040s |
| Four uint16 radix sorts | 2.280452338 | 1.916340412–2.750875735 | 18/18 | 0.485092082s |
| uint64 timsort + linear geometry | 1.186912404 | 1.028774286–1.583907172 | 18/18 | 0.937346044s |

Environment: macOS26.6.1 ARM64, NumPy1.26.4, Numba0.59.1, one thread. See `protocol.json` for frozen selection, `result.json` for every per-case value/timing, and `before.sha256`/`after.sha256` for unchanged source hashes.

Decision: advance the actual counting-radix variant to production-quality testing and formal development evaluation **before** holdout. These selected-large-input results do not establish benefits for small, sparse or tied workloads, other widths, Linux, or the complete selection pipeline. Do not retroactively relabel these18cases as an independent final test.


## Archival copy

`prototype.py` is a portable copy: only the machine-specific ROOT assignment was replaced with a repository-relative path. `portable_copy_changes.json` records both source hashes. The original probe script and all JSON outcomes are byte-preserved. `before.sha256` and `after.sha256` refer to the originally executed temporary files; their original prototype hash deliberately differs from the portable copy. This directory is exploratory evidence, not the production evaluator or an independently preregistered test.
