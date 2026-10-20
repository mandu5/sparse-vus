# Merge-aware certificates for adaptive VUS width evaluation

Status: derived and implemented on 20 October 2026. This is a new extension
of the pinned exact scalar target, not a new metric. Performance conclusions
must come from the separately frozen experiment; small prototype examples
below establish behavior, not controlled speed claims.

Implementation: `src/sparse_vus/certified.py`.
Independent direct-ramp/linear-program tests: `tests/test_certified.py`.

## 1. Why this direction

The existing sparse algorithm removes inactive threshold events exactly, but
still visits every integer buffer width. Its width-dependent work is
`(L+1)Q`. Caching label geometry across detectors would save repeated
preprocessing and some constant factors; it would not remove this term.
Similarly, certified threshold bins require computing their endpoint label
mass and segment hits. A naive endpoint evaluator still scans the support
at every width, so threshold certificates alone do not establish a further
asymptotic improvement over the exact sparse sweep.

The proposed extension removes **width evaluations**, with deterministic
bounds on the resulting scalar error and on detector orders. It exploits
properties specific to the pinned dynamic-label VUS:

1. Expanded segments only merge, at explicitly computable integer widths.
2. Inside an interval with no merge, ROC area is monotone in width.
3. Inside the same interval, the recall and precision at every fixed score
   threshold are monotone in width, although PR area itself need not be.
4. Endpoint recall curves define a finite probability box. Its extremal
   expectations yield PR bounds without evaluating intermediate widths.

The general probability-box expectation method is prior art, attributed
below. The candidate research contribution is the merge-aware VUS structure,
its use to certify both scalar integrals and rankings, and the adaptive
algorithm that evaluates only the necessary widths.

## 2. Notation and elementary monotonicities

Use the definitions in `docs/theory.md`. Fix an arbitrary score threshold
and write

\[
O=\sum_i y_i\,1\{s_i\ge t\},\quad
B_w=\sum_i(1-y_i)a_w(i)\,1\{s_i\ge t\},\quad
C=\sum_i1\{s_i\ge t\}.
\]

Thus `T_w=O+B_w`, `P_w=p+B_w/2`, and `N_w=n-p-B_w/2`.
All weights lie in `[0,1]`; `0≤O≤p` and `0≤C-O≤n-p`.
For every position, its weight is nondecreasing with width: active ramps
increase, new ramps become active, and sum-and-clip preserves this order.

### Lemma A: coordinates are monotone over descending thresholds

Recall and the false-positive coordinate are nondecreasing as the threshold
decreases. Precision need not be monotone.

For the unclipped recall factor

\[
g(O,B)=\frac{O+B}{p+B/2},
\qquad
\frac{\partial g}{\partial O}=\frac1{p+B/2}>0,\qquad
\frac{\partial g}{\partial B}
 =\frac{p-O/2}{(p+B/2)^2}>0.
\]

Admitting points can only increase `O`, `B`, and the segment-hit count.
Clipping at one and multiplying nonnegative nondecreasing factors preserve
monotonicity. The false-positive numerator `C-O-B` adds `1-a_w(i)≥0`
for each newly admitted point, while its denominator is positive and can
only decrease. This establishes the false-positive monotonicity as well,
including tied events.

After the final support event, recall is exactly one: all original positives
and all positive-weight positions have entered, every segment is hit, and
`(p+B)/(p+B/2)≥1`. Consequently, the support-event recall increments form
a probability distribution. Both scalar integrals lie in `[0,1]`.

### Lemma B: coordinate order across merge-free widths

Let `a≤w≤b` and suppose the expanded-segment partition undergoes no merge
between widths `a` and `b`. For every fixed threshold,

\[
R_a\le R_w\le R_b,\qquad A_a\le A_w\le A_b,\qquad
F_a\ge F_w\ge F_b.
\]

The segment count is constant and corresponding segments expand by inclusion.
Their hit indicators therefore cannot decrease. Combined with increasing
`B_w` and Lemma A's derivative, this proves recall order. Precision
`(O+B_w)/C` also increases. Finally,

\[
\frac{\partial}{\partial B}
 \frac{C-O-B}{n-p-B/2}
 =
\frac{-(n-p)+(C-O)/2}{(n-p-B/2)^2}<0,
\]

because `C-O≤n-p` and both classes are present.

This lemma remains true when new support points appear, when their scores
tie existing scores, and at the discontinuous entry of a new ramp. It is
an order argument, not a differentiability assumption about integer width.

## 3. Exactly where to split

Let consecutive original positive intervals have endpoints `e_i` and
`s_{i+1}`. Under the pinned reference's convention, expanded intervals merge
when

\[
e_i+\lfloor w/2\rfloor
\ \ge\ s_{i+1}-\lfloor w/2\rfloor.
\]

The first merging width for this gap is therefore

\[
\tau_i=2\left\lceil\frac{s_{i+1}-e_i}{2}\right\rceil.
\]

The expression uses endpoint distance, **not the count of negative positions
in the gap**. Merely adjacent expansions remain separate. Clip the distinct
critical widths to `1,…,L`; use those widths as the **starts** of new blocks.
For example, cuts at `2,4` partition the integer widths into
`[0,1]`, `[2,3]`, `[4,L]`. Simultaneous merges use a single cut.

All expansions only grow and merge. Thus constant segment count across two
ordered widths implies the same original-interval grouping across the
entire interval, not merely an accidental equality of counts.

The number of blocks is at most the number of original positive intervals.
The geometry can be prepared before examining detector scores and reused
across all detectors for a label sequence.

## 4. ROC interval theorem

**Theorem 1.** On a merge-free width interval `[a,b]`,

\[
\operatorname{ROC}_a\le\operatorname{ROC}_w
\le\operatorname{ROC}_b\qquad(a\le w\le b).
\]

**Proof.** Consider the full shared sequence of distinct score thresholds,
including the origin and prescribed terminal point `(1,1)`. Its ROC integral
is the ordered polygonal trapezoid sum. For an interior vertex `j`,

\[
\frac{\partial \operatorname{ROC}}{\partial R_j}
 =\frac{F_{j+1}-F_{j-1}}2\ge0,\qquad
\frac{\partial \operatorname{ROC}}{\partial F_j}
 =\frac{R_{j-1}-R_{j+1}}2\le0.
\]

Both coordinate sequences are nondecreasing over thresholds by Lemma A.
Linear interpolation between the endpoint coordinate sequences preserves
this property. Along that interpolation, Lemma B moves every recall
coordinate upward and every false-positive coordinate leftward. The
directional derivative of the area is consequently nonnegative. Applying
the same argument between `a,w` and between `w,b` proves the result.
The sparse endpoint evaluator returns this same area by the event
elimination identity. ∎

The terminal ROC point is essential to specifying the target and is included
in this proof. Inactive support-threshold steps have zero recall change and
can be retained for the proof even though implementation eliminates them.

### A finite counterexample to global ROC monotonicity

Take length 20, positive labels only at zero-based indices `0,2,19`, and

```text
scores = [20,4,19,3,18,17,16,15,14,13,12,11,10,9,8,7,6,5,2,1]
```

At width one, `K=3` and ROC is `0.4444444444444445`. At width two, the first
two expansions merge, `K=2`, and ROC is `0.40555697298022475`.
The two early-hit segments become one early-hit segment while another
segment remains unhit. An algorithm that bounds all widths by global
endpoints without the merge partition can therefore be incorrect.

## 5. PR bounds from a recall probability box

Let `j=1,…,G` be the shared descending maximum-support score events.
Set `R_{w,0}=0` and define `q_{w,j}=R_{w,j}-R_{w,j-1}`. Lemma A gives
`q_{w,j}≥0` and `sum_j q_{w,j}=1`. The pinned PR integral is

\[
\operatorname{PR}_w=\sum_{j=1}^G q_{w,j}A_{w,j}.
\]

Thus the event index carrying a unit of recall can be viewed as a finite
random variable whose CDF is `R_w`. This is an algebraic representation;
it introduces no data-generating or sampling assumption.

For endpoint CDFs `l_j=R_{a,j}` and `u_j=R_{b,j}`, define, for `0<z≤1`,

\[
i_-(z)=\min\{j:u_j\ge z\},\qquad
i_+(z)=\min\{j:l_j\ge z\}.
\]

The quantile index `J_w(z)=min{j:R_{w,j}≥z}` satisfies
`i_-(z)≤J_w(z)≤i_+(z)`. This permits the following bound.

**Theorem 2.** Every width inside a merge-free block obeys

\[
\boxed{
\int_0^1\min_{i_-(z)\le j\le i_+(z)} A_{a,j}\,dz
\ \le\operatorname{PR}_w\le\
\int_0^1\max_{i_-(z)\le j\le i_+(z)} A_{b,j}\,dz
}.
\]

**Proof.** The finite quantile expectation identity gives
`PR_w=∫ A_{w,J_w(z)} dz`. By Lemma B, for every fixed event,
`A_a≤A_w≤A_b`; the feasible event index lies in the displayed quantile
interval. Pointwise minimization and maximization followed by integration
give the inequalities. ∎

These are exact extremal expectations for a finite CDF p-box with fixed
endpoint precision vector. They are **not** asserted to be the tightest
possible bounds over the actual set of VUS widths: the endpoint envelopes
relax the coupling between precision and recall.

For completeness, extremality for the p-box follows because both ends of
the admissible index window move only right as `z` increases. Choose the
largest maximizer of the precision vector in each such window. That index
cannot move left: an earlier index feasible in the later window was also
feasible in the earlier window, and the earlier maximizing index remains
feasible whenever that earlier index does. The selected indices therefore
form a valid nondecreasing quantile function. The same argument applies to
the largest minimizer. No linear program is needed in production.

### Linear-time evaluation

All changes occur at the sorted union of endpoint recall values
`{0,l_1,…,l_G,u_1,…,u_G}`. Merge the two already sorted arrays in `O(G)`.
Between consecutive distinct values, the admissible index window is constant.
Maintain a deque of candidate precision indices:

```text
for each consecutive recall-level interval (z0,z1]:
    left  = first index with upper_recall[index] > z0
    right = first index with lower_recall[index] > z0
    append every new index through right:
        discard dominated indices from deque tail
        append new index
    discard indices smaller than left from deque head
    bound += (z1-z0) * precision[deque.head]
```

Each index is appended and removed at most once. The lower and upper
expectations each cost `O(G)` time and `O(G)` temporary memory.
Repeated recalls, zero initial recalls, zero increments, and tied scores
are handled by the strict comparison with `z0`.

### PR really can decrease without a merge

Take length 30, positive labels only at zero-based indices `1,27`, and

```text
scores = [4,3,3,5,6,4,4,5,2,9,4,9,8,4,2,9,4,5,2,3,5,5,7,6,1,1,4,0,6,8]
```

PR decreases from `0.4139362433120056` at width 15 to
`0.3887805232027892` at width 16, while both widths have `K=2`.
Recall and precision increase coordinatewise, but redistributing recall
increments among nonmonotone precision coordinates can decrease PR area.
Thus a monotone-increasing PR endpoint shortcut is incorrect. The displayed
two-width example alone does not show an interior value outside both scalar
endpoints; a general endpoint-minimum/maximum certificate would require a
separate proof. The p-box theorem supplies a valid enclosure without relying
on either scalar monotonicity claim.

An independent three-width construction closes that gap. Set `n=700`,
`y[100:200]=1`, and `y[600]=1`, using Python half-open slice notation.
Set all scores to zero, then assign

```text
scores[100:150] = 3
scores[150:200] = scores[600] = 1
scores[0:100] = scores[200:550] = scores[599] = 2
```

The two segments first merge at width 402. Define
`c=sqrt(1/2)`, `r=25/101`, and `u=(50+3c)/(101+3c/2)`.
Direct threshold accounting gives

\[
\operatorname{PR}_1=r+(1-r)\frac{101}{552},
\]

\[
\operatorname{PR}_2=
r+(u-r)\frac{50+3c}{501}
 +(1-u)\frac{101+3c}{552}.
\]

These are approximately `0.3852` and `0.3663`. At width 400, all 451
score-two negative points have weight at least `c`, both segments are hit
at that threshold, and clipped recall reaches one. Therefore

\[
\operatorname{PR}_{400}
\ge r+(1-r)\frac{50+451c}{501}>0.80.
\]

Thus the interior width two has PR below both endpoint values at widths one
and 400, with no segment merge anywhere between them. Scalar endpoint
minimum/maximum interpolation fails on this construction; the p-box
enclosure remains valid. The packaged theory-verification script evaluates
all three curves independently and checks these formulas.

## 6. Adaptive VUS averaging and detector orders

Maintain exact scalar values for evaluated widths and disjoint open interiors
`a+1,…,b-1` whose endpoints have been evaluated. Every interior lies within
one merge-free block. Let `[l^M_{a,b},u^M_{a,b}]` denote its ROC or PR
bound from Theorem 1 or Theorem 2. If `E` is the set of evaluated widths,

\[
\underline V^M =
\frac{\sum_{w\in E}M_w+
 \sum_{(a,b)}(b-a-1)l^M_{a,b}}{L+1},
\qquad
\overline V^M =
\frac{\sum_{w\in E}M_w+
 \sum_{(a,b)}(b-a-1)u^M_{a,b}}{L+1}.
\]

Every integer width occurs exactly once, so
`lowerV≤exactV≤upperV`. Return the midpoint when both metric half-widths
are at most the requested `atol`. The absolute midpoint errors are then
at most `atol` in real arithmetic.

The implementation starts with both endpoints of each merge-free block.
It bisects the block interior with the largest weighted uncertainty,

\[
(b-a-1)\max_M\{u^M_{a,b}-l^M_{a,b}\}.
\]

New scalar values and bounds replace the parent's contribution. No claim
of optimal query allocation is made for this greedy rule. It is deterministic
and terminates after at most `L+1` unique width evaluations. `atol=0`
explicitly evaluates all widths.

For two detectors, a strict order for metric `M` is certified whenever
`lowerV_A^M > upperV_B^M`. This certifies the computation of the pinned
metric, not a statistical population-performance difference. Near ties may
require full evaluation. If intervals overlap, report the order unresolved;
do not use midpoint order as a certificate.

## 7. Interface and complexity

```python
from sparse_vus.certified import PreparedEvaluator, certified_vus, width_bounds

result = certified_vus(labels, scores, max_buffer=300, atol=1e-3)
result.estimate                 # (ROC midpoint, PR midpoint)
result.roc_lower, result.roc_upper
result.pr_lower, result.pr_upper
result.evaluated_widths         # unique integer widths, sorted
result.curve_evaluations        # includes recomputation after cache eviction
result.total_widths             # L + 1
result.exact                    # whether every width was evaluated

prepared = PreparedEvaluator(labels, scores, 300, cache_size=8)
prepared.merge_free_intervals   # inclusive (a,b) geometry blocks
curve = prepared.evaluate(17)  # exact scalar plus support-event coordinates
curve.roc, curve.pr
curve.recall, curve.precision, curve.fpr, curve.segments
```

`width_bounds(left,right)` rejects curves from different prepared evaluators,
reversed width order, and a change in segment count. Endpoint arrays are
read-only to prevent accidental mutation of a cached certificate input.
Numba is optional; the same kernels execute in Python without it.

Let `m` be the number of unique queried widths. Preparation costs the
existing `O(n log(Q+1))` bound. One exact endpoint costs `O(Q)`, and each
new bound costs `O(G)≤O(Q)`. With the fixed-size LRU cache, a split evaluates
its middle and may recompute its two endpoints, so the number of curve
computations is `O(m)`. A priority heap contributes `O(m log(m+1))`.
The total is

\[
O(n\log(Q+1)+mQ+m\log(m+1)).
\]

The implementation deliberately records **both** `m` and the actual number
of curve computations. A constant cache has a constant multiple of `G`
coordinate storage; scalar values and heap entries use `O(m)`.
Peak auxiliary memory, including preparation, is `O(n+Q+m)`.
There is no `(L+1)×Q` preprocessing matrix or implicit all-width prefix
construction.

This is an adaptive, instance-dependent improvement. Worst-case `m=L+1`;
many merges, strict tolerances, or irregular PR behavior can remove the
advantage. The adaptive API also has allocation/certificate overhead absent
from the existing streaming scalar kernel. Reduced width count alone is
not evidence of lower elapsed time.

### An optional worst-case query guarantee at fixed accuracy

The same certificate oracle also supports a simple uniform-within-block
schedule with a query bound independent of `L` when the geometry/event
parameters and accuracy are fixed. This schedule is a theoretical corollary;
the current implementation uses the adaptive heap described above.

Let `B` denote the number of merge-free blocks here (not buffer mass).
For one endpoint pair, let `delta A=A_b-A_a` and
`delta R=R_b-R_a`, both coordinatewise nonnegative. Write `W_PR` for its
p-box upper bound minus lower bound. Discrete integration by parts gives

\[
\sum_j q_j A_{b,j}
 =A_{b,G}+\sum_{j<G}R_j(A_{b,j}-A_{b,j+1}).
\]

Varying `R` within its endpoint box, while keeping `A_b` fixed, changes
this expression by at most
`sum_{j<G}|A_{b,j}-A_{b,j+1}| delta R_j`.
Replacing `A_b` by `A_a` changes any expectation by at most
`max_j delta A_j`. Therefore

\[
W_{\rm PR}
\le \max_j\delta A_j+
 \sum_{j<G}|A_{b,j}-A_{b,j+1}|\,\delta R_j
\le \sum_j\delta A_j+\sum_{j<G}\delta R_j .
\]

Over any subdivision of all merge-free blocks, the precision increments
telescope to at most `G`: precision is nondecreasing with width even across
merges, and omitted jumps between blocks are nonnegative. The recall
increments telescope to at most `G-1` in each block. Thus the sum of
all PR-bound spans is at most `G+B(G-1)`. Similarly, the sum of ROC-bound
spans is at most `B`.

Choose endpoint spacing at most

\[
h=\left\lfloor\frac{2\varepsilon(L+1)}{D}\right\rfloor+1,\qquad
D=G(B+1),
\]

inside every merge-free block, retaining both block endpoints. Every
unqueried interior contains at most `h-1` widths. Its global uncertain
span for either metric is at most `(h-1)D/(L+1)≤2 epsilon`.
The number of queried widths is at most

\[
\min\!\left\{L+1,\ \frac{D}{2\varepsilon}+2B\right\}
=O\!\left(\min\{L+1,BG/\varepsilon+B\}\right).
\]

For ROC alone, replace `D` by `B`, giving
`O(min{L+1,B/epsilon+B})` queries. This is an upper bound for an available
schedule, not a claim that the current greedy allocation attains this
worst-case query count. It also does not remove the dependence of `G` and
`B` themselves on the input and chosen maximum width.

## 8. Floating-point scope

The theorems are real-arithmetic enclosures. Current endpoint and bound
kernels use Float64 without directed rounding. The implementation:

- normalizes recall monotonically and clips recall/precision to `[0,1]`
  to suppress ulp-scale drift;
- uses accurate scalar summation when assembling final bounds;
- expands nonexact results by `1e-12`, reported as `numerical_guard`;
- distinguishes all-width evaluation (`exact=True`) from bitwise equality.

The guard is an empirical numerical allowance, **not a proven bound on
all Float64 accumulation errors**. The current software therefore does
not constitute a formal machine-arithmetic interval verifier. This
limitation must remain explicit in paper and API claims. The real-arithmetic
certificate and numerical reference checks are separate evidence.

A future formal implementation would require outward-rounded enclosures for
square roots, grouped sums, ratios, recall crossings, and p-box extrema, or a
proved error budget covering all of them. Merely applying `nextafter` to the
final answer would not establish such a guarantee.

## 9. Validation evidence and remaining experiment

Before production implementation, a throwaway prototype at
`/tmp/sparse-vus-theory-20261020/` checked:

- 760 finite p-box minima/maxima against independent `scipy.optimize.linprog`;
- 13,776 per-width enclosures, covering all nontrivial binary label vectors
  of lengths 2 through 7 with four seeded distinct/tied score patterns each;
- exact endpoint means against the existing NumPy sparse implementation;
- explicit counterexample searches for invalid monotonicity shortcuts.

Those scratch files are investigation aids, not release artifacts.
`experiments/verify_width_theory.py` now packages the same finite scope as a
source-controlled reproducer. It additionally compares every endpoint with
an independent full-rank direct-ramp construction and checks the three-width
PR endpoint failure described in the independent review. Its expected
coverage is 240 label vectors, 960 input cases, 13,776 per-width checks, and
760 LP comparisons. It writes a JSON receipt including source hashes,
dependency versions, numerical discrepancies, and counterexample values:

```text
python experiments/verify_width_theory.py --output results/width-theory-verification.json
```

The receipt from an executed command, rather than the expected counts, is
the evidence for the packaged reproducer.

The first committed-source test candidate adds 108 tests, including 100
independently seeded cases comparing every queried width against full-rank,
direct sum-and-clip ramp construction. It checks every merge-free block,
the adaptive aggregate, exact fallback, ties, boundary labels, zero/one
widths, invalid tolerance, and p-box extrema against LP. On 20 October 2026:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_certified.py -q
108 passed in 3.00s

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
2259 passed, 1 warning in 50.58s
```

The warning is the existing third-party `dateutil` use of deprecated
`datetime.datetime.utcfromtimestamp`, unrelated to the certificate algorithm.

The evidence needed for a research result remains:

1. An independently selected public-series benchmark against the same exact
   scalar target, reporting both runtime and unique/repeated width counts.
2. Absolute errors and enclosure violations checked against full evaluation
   for every timed case.
3. Error-tolerance curves, including cases where exact evaluation is faster.
4. Certified detector-order coverage, especially comparisons whose sampled
   250-threshold orders disagree with exact values.
5. A clear separation between real-arithmetic certificates and machine
   arithmetic validation.
6. Audit against the newly located `tomlouisklein/fast-VUS` implementation.

No acceptance venue or novelty conclusion follows solely from the derivation
or passing tests.

## 10. Prior art and contribution boundary

The original VUS metric and its optimization belong to its authors. Sparse
support and rank sweeps are also prior techniques. The new endpoint oracle
reuses this repository's already documented exact event-elimination identity.

General expectation bounds for p-boxes, including nonmonotone integrands,
are established imprecise-probability theory:

- Lev V. Utkin and Sébastien Destercke, *Computing expectations with continuous
  p-boxes: Univariate case*, International Journal of Approximate Reasoning
  50(5), 778–798, 2009.
  [arXiv primary manuscript](https://arxiv.org/abs/0906.1260),
  [DOI](https://doi.org/10.1016/j.ijar.2009.02.004).
- Matthias C. M. Troffaes and Sébastien Destercke, *Probability boxes on totally
  preordered spaces for multivariate modelling*, International Journal of
  Approximate Reasoning 52(6), 767–791, 2011.
  [arXiv primary manuscript](https://arxiv.org/abs/1103.1805),
  [DOI](https://doi.org/10.1016/j.ijar.2011.02.001).

The present quantile proof is included for self-contained correctness, not
claimed as a new theorem about p-boxes. The monotone-deque implementation is
a standard sliding-window extrema technique.

The defensible candidate contribution is the **VUS-specific merge partition,
coordinate monotonicity, resulting ROC/PR certificates, and adaptive
width-elimination algorithm with end-to-end error/order guarantees**.
Whether that combination is sufficiently novel and useful depends on the
prior-art audit and controlled empirical results, still being completed.
