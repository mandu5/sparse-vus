# Independent theory audit and tie-run candidate, 2026-10-23

Scope: targeted review of `paper/saturation_method.tex`,
`paper/saturation_mass_bound.tex`, `src/sparse_vus/saturation.py`, and the
weight/metric definitions in `src/sparse_vus/core.py` at
`78974a3387b1600c31d5efaf56341a769d9618cb`. CodeGraph was unavailable.
The frozen implementation, proof files, and evidence were not modified by
this audit. `paper/tie_run_method.tex` is a new, separate proof fragment.
No runtime benchmark was performed and no firstness claim is made.

## Audit result

I found no counterexample to the stated permanent-saturation identity,
complete-tie mass bound, one-interval distinct-score bound, or deterministic
singleton score-query lower bound under their stated exact-arithmetic
assumptions. The strongest new direction is a one-interval evaluator that
aggregates score ties by contiguous spatial runs and uses an integer
saturation certificate. It removes the tie-cardinality restriction for
bounded-fragmentation score classes. It does not solve arbitrary fragmented
ties or the general many-component problem.

The frozen evaluator's floating test is not a mathematical certificate for
all permitted integer widths. A direct arithmetic counterexample exists,
although it does not demonstrate a practical-size scalar-output failure.
The new integer stopping test avoids that particular limitation.

## What the frozen statements actually establish

At a complete threshold, exact recall is
`min((A+B)/(P0+B/2), 1) * H/Kw`. Both mass and coverage are monotone.
Thus `A+B/2 >= P0` and `H == Kw` imply permanently unit recall. The
remaining ROC increments telescope even if FPR itself moves backward;
monotonic FPR is unnecessary. Completing the global numerical tie is
essential for the metric's threshold semantics.

The uniform lower bound on an active non-original weight is
`1/sqrt(2)`, because the support uses distances at most `floor(w/2)`.
That makes the per-position contribution to `A+B/2` at least
`1/(2*sqrt(2))`. It does not bound the cost of completing a huge active tie,
or the time until a low-scoring component is first hit. The frozen proof
explicitly preserves both restrictions.

The lower bound is an input-inspection result for a promised distinct-score
singleton subclass. Raising an unread point outside the maximum support
above the original changes every width's PR from one to one half. This is a
valid adversary for that model. It is not a lower bound on all possible
width computations, on randomized algorithms, or on already summarized
inputs. Calling the result a general VUS optimality theorem would be wrong.

The current finite-precision implementation computes exhaustive-threshold
semantics with ordinary numerical error. Its module documentation already
disclaims symbolic floating-point exactness. Exact-arithmetic identities,
measured parity, and correctly rounded output are three different claims.
Only the first two have evidence in this package; a correctly rounded
scalar guarantee is not established.

## Arithmetic counterexample to the floating stop predicate

Consider a valid singleton label vector `[0, 1, 0]`, scores `[1, 0, 1]`,
and the particular width `w = 2**54`. The first complete active score tie
contains the two immediate buffer neighbors and no original. Consequently
`A=0`, `P0=1`, `C=2`, and the only expanded component has been hit.

In real arithmetic each weight is `sqrt(1 - 2**-54) < 1`, so `B < 2` and
the mass predicate is false. In binary64 round-to-nearest arithmetic,
`1.0 - 1.0/(2**54)` rounds to one and both evaluated weights equal one.
The frozen predicate therefore evaluates `A+B/2 >= P0` as true.

This is a reachable per-width state for a mathematically valid input and
an int64 width. The full wrapper through `2**54 + 1` widths was not run.
The missed exact deficit is tiny and may disappear in correctly rounded
final outputs. The finding establishes an invalid universal floating
certificate; it does not establish a material observed output error or a
failure of the exact-arithmetic theorem.

Adding a generic tolerance would not repair this rigorously without an
error model. A one-sided count certificate does.

## Integer stopping certificate

Let `C` count admitted active non-original positions, separately from their
floating buffer mass. At a complete active class, stop when

```python
C // 3 >= P0 - A
```

For every active buffer point, its true weight is at least
`1/sqrt(2) > 2/3`. Hence `B/2 >= C/(2*sqrt(2)) >= C/3`, so the integer
condition certifies the true mass condition. For one original interval,
the first active class hits the only expanded component.

The certificate may be later than the real-mass cutoff. Nevertheless, if
`A+C >= 3*P0`, then `C >= 3*(P0-A)`, so the certificate holds. If there
are fewer than `3*P0` active positions, their final class contains every
original and also satisfies it. Each active class introduces at least one
position. Therefore at most `3*P0` complete active classes are visited,
independently of tie sizes. For a singleton the bound is still three.

The implementation comparison uses division and subtraction only; it does
not multiply a potentially large int64 count. The certificate assumes
correct integer geometry, counts, and complete-tie processing. It does not
certify the floating scalar integration.

## Tie-run aggregation and a stronger subclass

Assume exactly one original interval `[a,b]`. The maximum support is a
single spatial interval. Partition each score class in that support into
its maximal contiguous runs, and let `R_g` be its number of runs.
These are maximum-support runs, not runs recomputed at each width.

A run intersects the original interval, the left ramp, and the right ramp
in at most three fragments. Its original count is an integer interval
length. On either ramp a nonempty active fragment has consecutive distances
`dmin,...,dmax`, where `1 <= dmin <= dmax <= floor(w/2)`. Define
`U(t) = sum(sqrt(j) for j in 1..t)`, with `U(0)=0`. Its exact buffer mass is

```text
[U(w-dmin) - U(w-dmax-1)] / sqrt(w).
```

This follows directly from `sqrt(1-d/w) = sqrt(w-d)/sqrt(w)`.
Widths zero and one have no buffer fragments.

A score class activates at its minimum support distance. Use the existing
reverse-deletion idea on classes, keeping the active classes in score
order; each class is inserted once. Global before/after prediction counts
include all off-support members of its numerical tie. Processing a visited
class queries all its stored runs, including those currently inactive,
and then performs one complete metric event.

Writing `G_w` for the classes visited through the integer certificate,
the exact-arithmetic work bound is

```text
O(n + L + sum_w sum_{g in G_w} R_g),
```

with `O(n+L)` auxiliary words. Since `|G_w| <= 3*P0`, the simpler bound is
`O(n + L + (L+1)*P0*Rmax)`.

Consequences:

- A singleton with a bounded number of spatial runs per score class has
  `O(n+L)` work, even if a class contains arbitrarily many active points.
- All-tied support has one class and one run, giving `O(n+L)` for any
  length of the one original interval.
- Distinct support scores have one run per class and remain covered.
- When `L <= n`, the earlier singleton lower bound still applies through
  the distinct-score subclass; worst-case linear input inspection remains
  necessary within this broadened bounded-fragmentation class.

This is a genuine extension of the certified subclass, not a universal
arbitrary-tie solution. An alternating high/low score vector has a class
with linearly many spatial runs. Also, the prefix table introduces `O(L)`
storage even without diagnostics; the frozen `O(n+Q)` space bound does not
carry over. No runtime benefit follows automatically from this work bound.

## Stable constant-work range sums

Naive floating prefixes subtract large nearby numbers on short queries.
Replacing them with a positive segment tree avoids this cancellation but
adds `O(log L)` work per query. A fixed-point prefix table preserves
constant query work for the supported integer domain.

Let `q_j` be the binary64 evaluation of `sqrt(j)`. For int64-positive
`j <= L`, `1 <= q_j < 2**32`, and every `q_j * 2**52` is an exact integer
below `2**84`. The total prefix is below `2**147`, so three uint64 limbs
suffice. Decompose the floating mantissa and exponent, accumulate integer
limbs with carries, and subtract prefixes with borrows. Both operations
are exact. The scale is fixed; this is not a variable-precision symbolic
square-root computation.

For difference limbs `(hi, mid, lo)`, convert the nonnegative result with

```python
numerator = (ldexp(float(hi), 76)
             + ldexp(float(mid), 12)
             + ldexp(float(lo), -52))
mass = numerator / sqrt(w)
```

All terms are nonnegative and within the normal binary64 range. The
implementation must preserve uint64 carry/borrow behavior and avoid
fast-math reassociation. This procedure exactly sums the rounded square
roots before the final conversion; it does not make their original
rounding errors vanish.

Under ordinary round-to-nearest relative-error assumptions, with
`u=2**-53` and `gamma(k)=k*u/(1-k*u)`, a nonempty range query has relative
error at most `gamma(8)` against its real-arithmetic ramp mass. Integer
conversion plus square root contributes two factors for the numerator
terms and two for the denominator. Limb conversion and the two positive
additions contribute at most three factors; final division contributes
one. The ratio is bounded between `(1-u)**6/(1+u)**2` and
`(1+u)**6/(1-u)**2`, which lies inside `1 +/- gamma(8)`.
For indices and widths at most `2**53`, integer conversion is exact and
`gamma(6)` suffices. Summing `t` positive range results gives
`gamma(t+7)` when `(t+7)*u < 1`.

The bound is local to buffer-mass queries. It does not bound the complete
ROC/PR integral's error, and the transformed square-root expression need
not agree bit for bit with `sqrt(1-d/w)`. The independent integer stopping
test is useful precisely because its validity does not depend on these
floating query errors.

## Untimed checks

Reproduction script: `/tmp/active_prefix_theory_audit_20261023.py`.
This is throwaway correctness evidence, not a frozen benchmark artifact.

The script builds a prefix of length 200,000 and checks 500 deterministic
random nonempty ramp fragments against `math.fsum`; 100 also use 80-digit
`decimal` square roots of the original rational ramp arguments.

| Check | Observed result |
| --- | --- |
| Fixed-point query vs `fsum`, maximum relative discrepancy | `3.319818005566618e-16` |
| Fixed-point query vs Decimal-80, maximum relative discrepancy | `2.2866391738978603e-16` |
| Ordinary prefix subtraction vs `fsum`, maximum relative discrepancy | `3.6509604904416505e-12` |
| Largest integer prefix bit length in this check | 78 |
| Integer `3*P0` certificate cases | 5,049 passed |
| Frozen floating predicate arithmetic witness | Reproduced at `w=2**54` |

A subsequent targeted read of the new `src/sparse_vus/tie_runs.py` found
its fragment bounds, global counts, activation schedule, integer test,
and limb scaling consistent with this derivation. A separate untimed check
fed `_sqrt_range` 2,004 synthetic nonnegative three-limb prefix pairs,
including borrows across the 64-bit and 128-bit boundaries. Every result
agreed with Python's correctly rounded conversion of the exact integer
difference followed by the exact power-of-two scaling in that check.
These synthetic pairs exercise the high limb without allocating an
impossibly large square-root table; they do not test high-limb prefix
construction through a full large-width call.

These checks support the arithmetic implementation strategy. They are not
a replacement for the proof, tests of the final candidate module, full
scalar parity, performance measurements, or a full-width execution of the
huge-width floating witness.

## Remaining generalization barrier

After true mass saturation in a multi-component instance, recall becomes
`H/Kw`. Between first hits of additional components it is constant; PR
contributions vanish and ROC contributions telescope. Thus only component
first-hit events are needed after the mass cutoff if the required strict
and inclusive threshold buffer masses can be queried efficiently.

This is an event-compression identity, not yet a fast general evaluator.
An arbitrary score superlevel set can fragment into linearly many spatial
pieces, and multiple overlapping expansions change the mass geometry.
Computing the needed threshold masses can still cost the full support.
No general `O(n+L*P0)` result for arbitrary scores and multiple components
has been established by this audit.

The tie-run candidate should therefore remain explicitly one-interval,
with frozen behavior preserved, integer stopping, independent scalar parity
checks, and a separately fixed protocol before any runtime claim. Prior-art
assessment remains separate from the new derivation; fixed-point exact
summation itself must not be presented as a new numerical invention.
