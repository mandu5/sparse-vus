# Mathematical self-audit of active-prefix VUS

Date: 2026-10-21. Scope: read-only review of `paper/saturation_method.tex` and
`src/sparse_vus/saturation.py` during a controlled Mac timing run. This reviewer
also authored the implementation: this is a fresh mathematical self-audit, not
an independent author, laboratory, or peer review. No CPU experiment was run.
The requested new mass-bound appendix was written separately as
`paper/saturation_mass_bound.tex`; the measured sources and original theorem
file were not changed.

## Findings by consequence

1. **No real-arithmetic counterexample found within the pinned domain.** The
   stopping condition, global-tie accounting, activation schedule, and DSU state
   admit a consistent proof. This is not a formal verification or an exhaustive
   assurance about implementation defects.
2. **The existing proof should explicitly bridge maximum support to current
   active support.** The earlier negative-only lemma is stated for positions
   outside `S_L`; this evaluator also omits `S_L \ S_w`. Establish
   `S_w = {i: a_i^(w)>0} = union of expanded components`. It follows that every
   omitted position changes only the global prediction count, and the same
   rectangle formula remains valid for the active-event subsequence. The new
   appendix states and proves this missing bridge. This is a proof-completeness
   issue, not a discovered algorithmic failure.
3. **Define existence of the first saturated tie explicitly.** At the final
   active tie all original positives have been admitted, giving `A=P0`; every
   expanded component contains an original, giving `H=K_w`. Therefore the first
   saturated event always exists. The current proof uses `J_w` before spelling
   out this argument. The new appendix supplies it.
4. **Use the accurate union-find citation and terminology.** `_root` performs
   path halving with union by size. It is covered by Tarjan–van Leeuwen 1984,
   Theorem 3; “path compression” is acceptable as an umbrella phrase but should
   be made precise. The standard inverse-Ackermann factor must be taken at least
   one, including `K=1`. The prior-art note contains primary sources.
5. **The new uniform mass bound is stronger than the crafted separation.** Every
   active position contributes at least `1/(2 sqrt(2))` to `A+B/2`. Thus mass
   saturates by the complete tie containing active rank `ceil(2 sqrt(2) P0)`, or
   by the final active event if fewer positions exist. With one original
   interval and distinct converted support scores, this gives
   `J_w <= min(Q_w, ceil(2 sqrt(2) P0))` for every ordering and hence
   `O(n+L P0)` time. The singleton bound is `J_w<=3`, not a dependence on detector
   quality. Complete-tie rounding and an all-tied counterexample are essential.
6. **Do not extend the exact-arithmetic statement to IEEE bitwise correctness.**
   `A+B/2 >= P0` is a floating comparison, sums change order, and the suffix is
   telescoped. The current final paragraph correctly separates this from the
   real-arithmetic theorem. No universal floating error bound or correctly
   rounded result has been proved. Numerical parity tests cannot supply one.
7. **The first-saturation work bound applies to the default mass-and-coverage
   mode.** `stop=False` and `stop='last_positive'` use longer prefixes. Their
   complexity must use their actual visited counts, not the default `J_w`.
   Diagnostics intentionally add `O(L)` storage and output.

## Re-derived stopping proof

Fix a width; its geometry does not change while thresholds decrease. Let
`A` count admitted original positives and `B` sum admitted non-original weights.
Both are nondecreasing. Put `D=A+B/2`. Since `P0>0`,

`(A+B)/(P0+B/2) >= 1` if and only if `D>=P0`.

Coverage `H/K_w` is also nondecreasing and at most one. Hence
`D>=P0 AND H=K_w` is equivalent to recall being exactly one, and once true it
stays true. The mass condition without coverage is insufficient. The negative
normalizer is positive because

`N = n-P0-B/2 >= (n-P0)/2 > 0`.

After stopping at FPR `F`, every subsequent ROC trapezoid has both endpoint
heights one, including the required terminal `(1,1)`. The signed widths sum to
`1-F`. This proof does not need globally increasing FPR or a constant negative
denominator. Every subsequent PR increment has zero recall width. Stopping at
`A=P0` is also safe: every component contains at least one original, so all
components have been hit automatically.

## Complete global ties and inactive thresholds

At an active event of score `v`, every active position with score `v` is visited
before testing saturation. Positions outside `S_w` tied at `v` have zero mass
and no component, but they must contribute to `C`; the `after[event]` count
includes them. The gap before the event uses `before[event]`, which excludes
them. Consequently an omitted point tied with the event is included in the
trapezoid transition rather than incorrectly moved into its preceding
rectangle. Intermediate maximum-support groups with no active points can be
skipped because their mass, coverage, and recall remain fixed. This remains
valid when all global scores are tied.

`J_w` must count active POSITIONS, including the entire terminating active tie.
Counting events alone invalidates the bound when a tie contains many active
positions. Ties only outside the current active support do not add to `J_w`.

## Activation and geometry invariants

- Let the activation sequence sort nodes by integer `d1`, with a fixed order
  within equal radii. Reverse deletion records the neighbors that exist just
  before each deletion. Reversing the operations restores exactly the list
  induced by the inserted nodes. The list therefore remains in score order.
  The stored forward `next` pointer of an active node always points to an active
  node or the sentinel. It never needs an uninitialized pointer of an inactive
  node. Whole buckets are inserted before evaluation.
- Widths `2r` and `2r+1` share an active list and component partition, but their
  ramp weights generally differ. The code reuses geometry and recomputes
  weights. Reusing the metric value across that pair would be false except for
  special cases; widths zero and one contain only originals and do agree.
- Expanded neighboring intervals overlap exactly when
  `start[k+1]-end[k] <= 2r`. If their endpoints differ by one after expansion,
  they are adjacent and must remain separate. The scheduled radius
  `gap//2 + gap%2` implements the correct inequality.
- Components of the union of ordered expanded intervals equal components of
  the path containing these eligible adjacent-interval edges. If a point lies
  in two expanded intervals, they overlap at that point and are connected.
  An active point's nearest original interval contains it after expansion, so
  its DSU root identifies the same component as explicit expanded segments.
- All unions occur before processing a width. Path halving changes intermediate
  pointers but not the representative during that width. Epoch stamps therefore
  count each component once. Width epochs are distinct under the machine-word
  restriction; no `K`-sized clearing is needed between widths.

## Complexity and storage accounting

Let `V = sum_w J_w`. Preparation performs input validation/conversion, interval
extraction, maximum-support extraction, a monotone nearest-interval scan, eight
radix passes, a complete-tie scan, and a global-order support filter. All cost
`O(n+Q+K)` under the stated model. Counting activation radii and reverse deletion
cost `O(Q+min(L,n))`. Merge scheduling costs `O(K+min(L,n))`.

Over all widths, there are exactly `Q` insertions, at most `K-1` unions, at most
`2(K-1)+V` finds, and at most `V` active events. The last inequality holds because
an event contains at least one visited active position. Width-loop overhead is
`O(L+1)`. A width can receive many insertions; these are charged once globally,
not described as absent work. The DSU contribution is
`O((K+V) alpha(K))`. At width zero, `J_0=P0>=K`, so it reduces to
`O(V alpha(K))`. This yields `O(n+L+alpha(K)V)`; no per-width `Q` or `K` clearing
was found in the code.

Peak working arrays are `O(n)` ranking/index state, `O(Q)` geometry/list/event
state, `O(K)` DSU state, and `O(min(L,n))` schedule buckets. Old and reordered
arrays can coexist during preparation, increasing constants but not order.
Scalar APIs allocate zero-length diagnostic arrays and stream the width sum.
The profile API holds two width vectors and converts them to lists, requiring
`O(L)` additional storage. The result is not an `O(Q)`-memory algorithm and does
not produce the full threshold-by-width surface.

## Exact restrictions recommended for the theorem

1. One-dimensional binary labels, `n>=2`, with `0<P0<n`; original intervals are
   the maximal ordered runs of ones. These assumptions ensure `K>=1`, nonempty
   support, and positive metric denominators.
2. Finite scores after the public binary64 conversion; signed zeros compare
   equal. “Distinct scores” in the corollary means distinct converted scores on
   `S_L`, not distinct arbitrary-precision integer inputs. NaN/Inf are excluded.
3. Nonnegative integer maximum width `L`; evaluate every integer width `0..L`.
   Addresses, counts, `L+1`, epochs, and intermediate index arithmetic fit the
   chosen machine words. The mathematical asymptotics fix the score key width
   at 64 bits while allowing address words sufficient for the input size; this
   is not an asymptotic claim over literally unbounded arrays on one fixed Mac.
4. Exactly the stated half-width square-root ramps, summed then clipped at one;
   original weights one; dynamic denominator `P0+B/2`; component hits defined by
   overlap-merged expanded intervals with adjacent nonoverlap kept separate.
   Other ramp definitions can break the uniform mass bound.
5. Complete numerical threshold ties; ROC signed trapezoids with explicit
   terminal `(1,1)`; PR right-endpoint step integral; arithmetic mean over
   widths. Other VUS variants or truncated threshold budgets are separate
   targets. The theorem concerns scalar outputs.
6. Unit-cost exact real arithmetic for metric sums, square roots, division,
   and comparisons, plus constant-cost fixed-key radix operations. It is not a
   bit-complexity bound for exact algebraic sums, arbitrary-precision scores, or
   a floating-point error theorem. Take `alpha(K)>=1`.
7. The mass corollary uses the default mass-and-coverage stopping mode. For
   `K=1`, existence holds after the first active event. With unrestricted active
   ties, add the tie-rounding term; do not assert a score-order-uniform
   `O(n+L P0)` bound without controlling ties.

## Static edge-case challenges and future tiny regressions

These are derived cases to add only after controlled timing permits test work.
They were not executed in this review.

- **Constant singleton bound attained:** one singleton with at least three
  non-original active positions ranked above it at width at least four. Two
  such positions cannot reach `B>=2` for a single interval at finite width;
  three outer-edge positions can reach it. Verify complete-event visits never
  exceed three for unique converted support scores.
- **All scores tied:** `n=2L+1`, singleton at `L`, every score zero. Then
  `J_w=Q_w=2 floor(w/2)+1`; the sum is quadratic in `L`. This disproves the
  no-ties-restriction version for this evaluator, not a lower bound for every
  possible algorithm that could aggregate ties differently.
- **Converted integer collision:** use distinct integers above `2**53` that
  become equal in binary64. A raw-input distinctness assumption is invalid.
- **Odd/even geometry reuse:** a singleton and a high-scoring adjacent buffer
  point at widths two and three. Geometry agrees, ramp mass and metric differ.
- **Coverage lag:** two separated original intervals with all active scores of
  one component below many scores of the other. Mass can saturate early while
  the required coverage prefix remains large.
- **Both classes and endpoints:** `n=2`, labels `[1,0]` and `[0,1]`, widths zero,
  one, two, and greater than `2n`; one-interval sentinel must never create a
  nonexistent second contributing interval under permitted integer widths.

The separate appendix proves the mass and tie bounds and states the all-tied
limitation. It should be reviewed and integrated after the measured source
freeze; no claim here establishes firstness, practical SOTA, or acceptance.

## Singleton input-inspection lower bound (additional static audit)

The requested lower bound is sound with a precise deterministic input model.
`paper/saturation_mass_bound.tex` now states a finite-instance theorem and a
matching linear-time corollary. This addition used no experiment or build.

Fix `n>=4`, integer `0<=L<=n`, and labels `[1,0,...,0]` known to the algorithm
for free. An adaptive deterministic algorithm may inspect individual score
coordinates; valid finite pairwise-distinct converted binary64 inputs are
promised. It receives no precomputed ranks, summary, or certificate, and a
unit word operation reads only a constant number of score words. The lower
bound therefore concerns the metric itself, even if validation is omitted.

Let `r=floor(L/2)`. The maximum support is `0..r`, so its complement has
`n-r-1 >= ceil(n/2)-1 >= n/4` positions. On a base input give the original
score one and every other position a different score below one. Every width
then has PR one: recall first reaches one at the original with prediction
count one and zero admitted buffer mass. If any off-maximum-support
coordinate remains unread, replace its score with two. All adaptive queries
and answers remain identical by induction, but the changed input has PR
one-half at every width: the extra false positive is admitted first, then the
original causes the only nonzero recall increment at prediction count two.
Later buffer mass cannot undo permanent recall saturation. A correct
algorithm must therefore read every off-maximum-support coordinate on the
base input. The paired ROC/PR output inherits this lower bound from its PR
component; no separate ROC-only lower bound is needed for that claim.

Points checked against overstatement:

- The exact off-support count is `n-floor(L/2)-1`, not always `>=n/2`.
  Choosing `n>=4` permits the clean uniform lower bound `n/4`.
- The algorithm is correct on the entire stated score class. It is **not**
  promised that the original is highest; otherwise the modified input would
  violate the promise and this adversary would fail.
- The unread position is chosen after the base execution. Deterministic
  adaptivity does not invalidate the argument: equal prior answers entail the
  same subsequent query and termination action.
- The alternate input retains finite distinct binary64 scores. The explicit
  values `s0=1`, `si=-i`, and replacement two are exactly representable for
  `n<=2**53`. More generally the theorem assumes enough representable values
  below one. Distinct-input instances cannot grow beyond the finite score
  universe; the query bound is stated per feasible instance and the matching
  time order uses the already declared fixed-key operation-count convention.
- The upper bound holds for any singleton location and score ordering because
  `J_w<=3`. With `L<=n`, `O(n+L)=O(n)`; the boundary witness supplies the
  worst-case lower bound within that class.
- This is deterministic input-inspection optimality for singleton scalar PR
  or paired scalar ROC/PR. It is not a general VUS lower bound, a randomized
  bound, an `Omega(L)` claim when `L>>n`, a bit-complexity result, firstness, or
  evidence of measured SOTA. The arbitrary-active-tie limitation above remains.
