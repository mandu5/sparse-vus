# Independent tie-run code review — 23 October 2026

Disposition: **no blocking correctness or complexity defect found in the reviewed
snapshot**. This is an adversarial code review with untimed correctness probes;
it is not a performance result, proof of a final floating-point error bound,
novelty assessment, or publication review. No implementation, repository test,
frozen kernel, or frozen evidence file was edited by this reviewer.

## Reviewed snapshot and scope

Base commit: `78974a3387b1600c31d5efaf56341a769d9618cb`.

| File | SHA-256 |
| --- | --- |
| `src/sparse_vus/tie_runs.py` | `8058994f4f7a7745326218bfa9b7c39444acde2d38dfc07e65e9455a50ba7436` |
| `tests/test_tie_runs.py` | `82d7d46e6aa9c6e116c7681e2f619d31741bbdfc526498dcd3aa65a53c1b7b16` |
| `docs/superpowers/plans/2026-10-23-tie-runs.md` | `8ef439a423b7ead66382c08d3461da4c1ecf1331f8ad8896597c313c15e88e39` |

The public input contract, global radix grouping, activation schedule, and dense
reference were also inspected at the called helpers in `core.py`, `radix.py`,
`saturation.py`, and `compiled.py`. CodeGraph tools were not available. Review
reads were restricted to the nominated files and their direct dependencies.

## Findings

**Minor — retain synthetic high-limb subtraction cases in repository tests.**
`tests/test_tie_runs.py:80` checks real prefixes through 10,000. Those tests
exercise low-limb carries but cannot exercise a nonzero high limb. Such a real
prefix would require an impractical table. `_sqrt_range` has a distinct
middle-to-high borrow path at `tie_runs.py:63-66`; a future change there can
therefore escape the current suite. The independent synthetic probes below
passed the current implementation. Preserve at least the double-borrow and
high-limb subtraction cases as regression tests before freezing the candidate.
This is a coverage gap, not a demonstrated implementation defect.

**Minor — preserve the arithmetic boundary in claims.**
`tie_runs.py:36` computes `sqrt(float(j))`; its rounded binary64 result is stored
exactly after scaling by `2**52`. For indices above `2**53`, conversion of `j`
can round before square root. Moreover, limb conversion and positive addition
at lines 67-68 are not guaranteed to give the correctly rounded exact range
sum. The independent synthetic checks observed a one-ULP difference from a
single final rounding. The module's existing distinction between exact integer
prefix subtraction and approximate final metric values is appropriate. Any
paper or API description should retain it and avoid claiming correctly rounded
range sums or bitwise equality with direct `sqrt(1-d/w)` evaluation. This is a
wording boundary, not a failure of the stated numerical contract.

## Correctness and complexity audit

- **Complete global ties:** `_support_ranks` obtains `before` and `after` from
  all positions, including off-support members of the same binary64 score
  class. `_evaluate` finishes every temporal run of an active group before
  checking the stop. Conversion-induced ties and both signed zeros retain the
  shared validated binary64 semantics.
- **Run construction:** the one original interval has one contiguous maximum
  support. Scanning its class identifiers and grouping each maximal temporal
  run therefore preserves its position set exactly. All original positives
  are active at width zero. Group activation at the minimum distance admits
  exactly those classes with at least one active position.
- **Width boundaries:** at widths zero and one, neither ramp intersects a
  position. The zero denominator computed at width zero is never used. At
  larger widths a ramp distance satisfies `1 <= d <= floor(w/2)`, so every
  queried numerator index lies in `[ceil(w/2), w-1]`, within the prepared table.
  Left/right endpoints were checked independently against position masks.
  Activation buckets stop at `min(L//2,n-1)`; all later widths continue using
  the fully activated list, so `L >> n` does not drop groups.
- **Integer stop:** write `A=original_count`, `C=buffer_count`, and `P=P0`.
  Every admitted buffer weight is at least `1/sqrt(2) > 2/3` in the ideal
  target, so `A+C//3 >= P` suffices for `A+B/2 >= P`. The test uses integer
  counts only and runs after a complete group. No rounded mass triggers it.
  Before stopping, `3*A+C < 3*P`; each visited active class contributes at
  least one new position. Hence there are at most `3*P` visited classes,
  including the terminating class. All original positives must eventually be
  visited if the scan has not already stopped, so it cannot exhaust the list
  without a valid terminal event.
- **ROC and PR completion:** with one component, the first active class hits
  that component. After the integer certificate, ideal recall remains one:
  omitted PR increments are zero and omitted ROC area is `1-current_FPR`.
  Skipped inactive score classes are accounted for by the rank-gap rectangle
  before each visited class.
- **Unsigned arithmetic:** low-limb addition propagates carry into the middle
  limb; middle overflow and a subsequent carry overflow propagate into the
  high limb. Subtraction subtracts the low borrow from the middle result and
  propagates the resulting high borrow. Each helper uses nonnegative integer
  differences before any conversion to floating point. Synthetic cases tested
  the path in which both low and middle limbs borrow.
- **Capacity:** for nonnegative signed 64-bit table indices, rounded
  `sqrt(float(j)) < 2**32`, its scaled integer is below `2**84`, and fewer than
  `2**63` terms give a prefix below `2**147`. Three 64-bit limbs suffice. This
  is a representation bound for addressable arrays, not a promise that such
  arrays can be allocated. The shift exponent is between zero and 31, so no
  shift by 64 or more occurs in this domain.
- **Work accounting:** radix preparation, run grouping, and capped activation
  buckets are linear in `n`; the prefix table and width loop cost `O(L)`.
  Each visited class scans every one of its maximum-support runs, including
  runs wholly outside the current width. The unconditional `query_count`
  increment records these inspections. Thus the stated work term is the sum
  of whole-class run counts, not the count of only currently intersecting runs.
  All persistent/temporary arrays together use `O(n+L)` words under the stated
  fixed-word, unit-cost arithmetic model. Highly fragmented ties can still
  cause large run counts; no universal speedup follows.

## Executed checks

Environment: local CPython 3.12, NumPy 1.26.4, Numba 0.59.1, pytest 8.3.3.
No timed benchmark or performance comparison was run.

`PYTHONPATH=src python -m pytest -q tests/test_tie_runs.py`: **23 passed**.

Independent script: `/tmp/tie_run_adversarial_review_20261023.py`, SHA-256
`bde0650bd09d725f4629a8b2d2a1b4587ede7a934e1f6be4f0c6160dcecefce1`.
Random seed: `2026102303`. The `/tmp` script is transient review evidence; this
report records its scope and outcomes, and does not treat it as a frozen
reproducibility artifact.

| Check | Observed result |
| --- | --- |
| Exact real prefixes, all entries 1 through 150,000, against Python integers | All equal; 9,455 low-limb carries |
| Last 1,001 singleton ranges in that table | Exactly equal to `math.sqrt(j)` |
| 20,009 synthetic monotone 192-bit prefix pairs, including double borrow | Maximum 1 ULP from `ldexp(float(right-left), -52)`; all within 2 ULP |
| 35 layout/width combinations | Dense parity within `1e-11`; includes negative/nonunit strides, read-only scores, byte-swapped input, widths 0/1 and `L=10000` with `n=11` |
| 650 randomized valid one-interval cases | Maximum ROC/PR absolute dense discrepancy `3.3306690738754696e-16` |
| All 650 profiles and PR-only calls | Event bound respected; PR-only result exactly equal to paired route |
| 6,569 individual widths in 35 cases, using independent score/position-mask counter reconstruction | Exact equality of events, whole-class run inspections, and aggregated positions |
| First 35 randomized cases against the Python dense reference as well | Within `1e-11` |

Random cases included unique scores, fragmented ties, long temporal runs,
all-tied signed zeros, subnormals, both finite binary64 extremes, edge intervals,
and widths larger than the sequence. Existing repository cases additionally
cover integer-to-binary64 score collapse and rejection of multiple intervals,
nonfinite scores, invalid class labels, mismatched lengths, and negative widths.
The numerical thresholds above are empirical test criteria, not global error
bounds. A real high-limb prefix and an independent high-precision integral were
not computed.

Minimal deterministic regression for the synthetic borrow gap:

```python
import math
import numpy as np
from sparse_vus.tie_runs import _sqrt_range

mask = (1 << 64) - 1
pairs = [
    ((1 << 64) - 1, 1 << 64),
    ((1 << 128) - 1, 1 << 128),  # low and middle borrow; answer 2**-52
    ((1 << 128) + 3, (2 << 128) + 1),
    ((1 << 192) - 2, (1 << 192) - 1),
]
for left, right in pairs:
    table = np.zeros((3, 3), dtype=np.uint64)
    for k in range(3):
        table[k, 1] = (left >> (64*k)) & mask
        table[k, 2] = (right >> (64*k)) & mask
    expected = math.ldexp(float(right-left), -52)
    actual = _sqrt_range(table, 2, 2)
    assert abs(actual-expected) <= 2*math.ulp(expected)
```
