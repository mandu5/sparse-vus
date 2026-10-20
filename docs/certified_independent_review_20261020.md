# Separate review of adaptive VUS width bounds

Review date: 20 October 2026. This is a separate **in-session mathematical
and source review**, not external peer review or a publication decision.
Reviewed files are `src/sparse_vus/certified.py` and
`docs/theory_advancement_20261020.md`. The source hash inspected was
`31135f790070a49d7480f0aa98f9696246cde13aad1410a1daeeb003fe214619`.

**Finding:** the merge-free ROC argument, PR probability-box bound, and
adaptive averaging invariant are mathematically valid for the pinned VUS
target in real arithmetic. No blocking algorithmic defect was identified.
The current Float64 implementation does **not** provide a proved
machine-arithmetic certificate; its `1e-12` guard remains empirical.
The VUS-specific construction is a research candidate. General p-box
expectation bounds, monotone deques, and adaptive interval subdivision are
not new contributions.

## 1. Independent check of the assumptions

The target is the dynamic-label evaluator specified in `docs/theory.md`,
not a generic weighted ROC. For a fixed nonempty threshold, write
`O` for predicted original positives, `B` for predicted buffer mass, and
`C` for all predicted positions. Then

```text
T = O + B
P = p + B/2
N = n - p - B/2
R = min(T/P, 1) * H/K
A = T/C
F = (C-T)/N
```

Both classes are required. Consequently `P≥p>0` and
`N≥(n-p)/2>0`; none of the derivative arguments crosses a singularity.

For fixed width and descending thresholds, `O,B,H` cannot decrease.
The unclipped recall factor increases in both `O` and `B`. The FPR
numerator adds `1-a(i)≥0` for every new point, and its denominator can
only decrease. Thus both `R` and `F` are nondecreasing along the curve.
This remains true when a whole tied group enters simultaneously.

At the final maximum-support event every positive-weight position has
entered and every segment is hit. Hence `R_G=1`, even if additional
off-support negatives remain below that score. The increments
`q_j=R_j-R_{j-1}` therefore are a probability distribution on support-event
indices. This is an algebraic device, with no statistical confidence
interpretation.

For fixed threshold, every buffer weight increases or stays fixed as width
grows: an existing square-root ramp increases and new ramps enter with
positive weight; summing and clipping preserves this order. Between merges,
each expanded segment grows by inclusion while its identity and `K` remain
fixed, so `H` cannot decrease. Therefore `R` and `A` increase. For FPR,

```text
dF/dB = (-(n-p) + (C-O)/2) / (n-p-B/2)^2 < 0,
```

since `C-O≤n-p`. This verifies the needed coordinate ordering; it does not
assert that PR area is monotone.

## 2. Merge boundaries and ROC area

An original gap with endpoints `e < s` merges when
`e+floor(w/2)≥s-floor(w/2)`, giving the first width
`2*ceil((s-e)/2)`. `PreparedEvaluator` uses the equivalent integer
expression and places the cut at the **start** of the new block.
Adjacency without overlap is correctly retained as two segments.
Clipping at the sequence boundaries does not change an interior gap's
merging width.

Segment count decreases monotonically as widths grow. Thus the same count
at two ordered endpoints implies no intervening merge; the `width_bounds`
count check is sufficient for genuine curves from the same evaluator.
The owner check prevents mixing curves from different score vectors.

For a full shared threshold grid, the ROC polygon has

```text
∂area/∂R_j = (F_{j+1}-F_{j-1})/2 ≥ 0
∂area/∂F_j = (R_{j-1}-R_{j+1})/2 ≤ 0.
```

Interpolating endpoint coordinate sequences preserves their threshold
ordering. Every vertex moves upward/leftward inside a merge-free block,
so area cannot decrease. The origin and terminal `(1,1)` are part of this
argument. Applying the old sparse-event identity after the proof is valid;
proving it only on retained support endpoints would overlook the negative
rectangles.

This theorem must not be extended over a merge. If two already-hit segments
merge while another remains unhit, `H/K` falls. The theory document includes
a compact ROC-decrease example; this reviewer checked the mechanism
analytically rather than treating that example as the proof.

## 3. PR bound and quantile implementation

For endpoint recalls `l=R_a`, `u=R_b`, every skipped curve satisfies
`l≤R_w≤u`. At recall level `z`, its event quantile lies between the first
index where `u` reaches `z` and the first where `l` reaches `z`.
Since endpoint precision also encloses every intermediate precision,

```text
min(lower_precision over feasible indices)
  ≤ precision_at_actual_quantile
  ≤ max(upper_precision over feasible indices).
```

Integrating this inequality over `z∈(0,1)` proves the proposed bound.
There is no requirement that precision itself be monotone along thresholds.
Off-support events have zero recall increment and contribute no PR mass;
including all tied positions in the prediction count remains necessary.

The `_pbox_extremum` implementation merges sorted recall breakpoints,
advances both quantile endpoints with strict `>z0` semantics, and uses a
monotone deque. Zero and repeated recalls do not create positive-length
unhandled integration intervals. Both endpoint indices only move right;
every precision index enters/leaves the deque at most once, giving `O(G)`.

The extrema are sharp for the relaxed finite CDF p-box and a fixed precision
vector: choosing the rightmost minimizer/maximizer in successive admissible
windows produces a nondecreasing quantile selection. They need not be sharp
over actual widths, because the relaxation discards dependence between
recall and precision. The current theory document makes that distinction.

One documentation inference was corrected during review: a decrease between
two widths disproves increasing PR, but does not alone disprove a bound
using the minimum and maximum of arbitrary endpoints. The independent
three-width construction below addresses the stronger issue.

## 4. Independent counterexample to PR endpoint min/max

This construction follows directly from the metric formulas and does not
rely on implementation output. Use length 700 and zero-based indexing:

```python
labels = zeros(700)
labels[100:200] = 1
labels[600] = 1
scores = zeros(700)
scores[100:150] = 3
scores[150:200] = 1
scores[600] = 1
scores[0:100] = 2
scores[200:550] = 2
scores[599] = 2
```

There are 101 original positives and 451 score-two negatives. The two
segments do not merge until width 402, so widths `1,2,400` belong to one
merge-free block. Let `a=sqrt(1/2)`, `r=25/101`, and
`u=(50+3a)/(101+3a/2)`.

At width one,

```text
PR_1 = r + (1-r)*101/552
     = 0.3852059118955374.
```

At width two the predicted buffer positions at score two are `99,200,599`,
each with weight `a`; both segments are now hit at that threshold:

```text
PR_2 = r + (u-r)*(50+3a)/501 + (1-u)*(101+3a)/552
     = 0.36631301878278155.
```

At width 400, every score-two negative lies in an expanded segment and
has weight at least `a`. Recall therefore saturates to one at score two,
and

```text
PR_400 ≥ r + (1-r)*(50+451a)/501
       = 0.8016006014100532.
```

The decimal values are evaluations of these displayed formulas, not timed
kernel results. Thus `PR_2 < min(PR_1,PR_400)`: scalar endpoint min/max
cannot replace the PR p-box bound, even within a merge-free block.
The discontinuous hit reward explains the drop.

## 5. Adaptive accounting and complexity

Initial blocks partition the integer widths. For each active pair `(a,b)`,
only the `b-a-1` interior widths use a bound; endpoints occur in the dictionary
of evaluated scalars. Bisection replaces those interior widths with the
new midpoint plus two disjoint child interiors. Repeated evaluation after
cache eviction overwrites a dictionary entry, so it does not double-count
that width in the final sum.

Accordingly, summing known scalars and multiplicity-weighted interval bounds,
then dividing by `L+1`, encloses the full average in real arithmetic.
Midpoint error is at most half the enclosure width. Nonoverlapping enclosures
certify a metric order in that arithmetic model, not a population-level
performance difference.

Let `m` be unique widths queried and `c` actual curve evaluations. The code
does not precompute a width-by-support matrix. With fixed cache capacity,
each split computes a midpoint and at most its two evicted endpoints, so
`c=O(m)`. Each curve costs `O(Q)`, each p-box bound `O(G)≤O(Q)`, and heap
bookkeeping `O(m log(m+1))`. Thus the stated

```text
time:   O(n log(Q+1) + mQ + m log(m+1))
memory: O(n + Q + m)
```

bounds are consistent with the implementation. `m` can equal `L+1`.
Distinct width count alone is not runtime evidence: array allocation,
bound computation, and endpoint recomputation add overhead. No sublinear
worst-case width count or optimality of the greedy split policy is proved.

## 6. Numerical and verification limits

The source uses ordinary Float64 square roots, grouped accumulation,
division, and comparisons. Recall normalization and precision clipping may
change coordinates slightly. `math.fsum` helps final aggregation but does
not retroactively enclose endpoint errors. A constant `1e-12` expansion
has no all-input error proof.

Therefore the code's explicit disclaimer is essential. “Certified” must
refer to the real-arithmetic method plus measured numerical checks, not a
machine-verified interval or a guaranteed floating-point detector order.
`exact=True` means all widths were queried, not exact real arithmetic.
Adding one final `nextafter` would not fix accumulated internal uncertainty.

This reviewer separately ran 100 bounded perfect-separation cases to look
for malformed exact-result intervals; none failed. The full 108-test/2,259-test
results were reported by the implementing agent and their test source was
inspected; they were not rerun independently here. Computational checks were
paused for the root agent's controlled timing. Mathematical validity above
rests on the derivation, not those finite tests.

## 7. Prior art and novelty assessment

Utkin and Destercke's
[*Computing Expectations with Continuous P-Boxes: Univariate Case*](https://arxiv.org/abs/0906.1260)
(2009; [publisher DOI](https://doi.org/10.1016/j.ijar.2009.02.004))
already treats lower/upper expectations for nonmonotone functions under
p-box uncertainty using linear-programming and random-set views.
Destercke, Dubois, and Chojnacki's
[*Unifying Practical Uncertainty Representations: I. Generalized P-Boxes*](https://arxiv.org/abs/0808.2747)
(2008) supplies the broader ordered-space/random-set context.
The general quantile-envelope extremum is not a new p-box theorem.

The [official VUS optimization paper](https://arxiv.org/html/2502.13318v1#S4.SS3)
and the inspected public optimized implementations retain explicit width
evaluation. Klein's
[fast-VUS source](https://github.com/tomlouisklein/fast-VUS/blob/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py)
also loops over every width. These inspected sources do not provide
merge-aware error enclosures for skipped widths.

Primary-source searches on 20 October 2026 included combinations of
`VUS-PR certificate`, `VUS-ROC monotonic`, `VUS p-box`, `VUS adaptive buffer`,
and `volume under the surface adaptive integration anomaly`. No matching
disclosed VUS certificate was located. This bounded search does not prove
priority. The undisclosed Sylligardos CPU/GPU mechanism remains unknown,
as detailed in [the fast-VUS audit](fast_vus_prior_art_20261020.md).

**Recommendation:** continue with this as a VUS-specific candidate result:
merge partition, coordinate ordering, scalar-error bounds, and adaptive
width elimination. Attribute the general tools and retain the floating-point
limitation. Controlled results must establish practical gains, failures,
enclosure accuracy, and detector-order coverage before making a stronger
research claim. No SOTA or conference acceptance claim follows from this
review.
