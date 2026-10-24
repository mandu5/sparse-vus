# Weighted range-metric feasibility, 24 October 2026

**Conclusion: the extension is valid.** All four canonical Tatbul positional biases, independently chosen for precision and recall, admit constant work per activation after fixed-label preprocessing. A pure constant-time cardinality factor can depend on both overlap count and the scored interval's length. The strongest useful formulation is a finite-feature interval-weight theorem; constant-piece, fixed-degree polynomial weights are a corollary. This is a substantive expansion of the existing flat/reciprocal operator, but the defensible contribution remains metric-specific maintenance across thresholds, not new component trees, new positional biases, or the first use of closed-form overlap sums.

The derivation supports a bounded implementation of the canonical four biases and the length-aware/length-weighted variant, followed by semantic differential checks and matched runtime comparisons. A new implementation was subsequently inspected as recorded below. The polynomial theorem should explain the common sufficient statistics. Its abstraction alone is not evidence of a large novelty increase.

This memo inspected the named implementation, its method section, the relevant bibliography entries, primary external sources, and subsequently the new weighted implementation and its oracle tests at the parent agent's request. It did not inspect other review scores or modify metric/manuscript files. No timing or dataset experiments were run. CodeGraph was not available. Firecrawl retrieval was unavailable because its account had no credits; web and direct primary-source retrieval supplied the evidence instead.

## Exact metric and canonical formulas

Use zero-based global indices and inclusive intervals. Let the binary fixed label vector be `y`, and let its maximal positive intervals be `T_j=[a_j,b_j]`. Predictions at a query are `p_i=1[s_i>t]`, with maximal positive intervals `C`. Define `L=b-a+1` and local one-based position `q=i-a+1`.

The four weights in Tatbul's Figure 2 are the following. The normalizers below are independently derived sums of those weights. [Tatbul et al., NeurIPS 2018, Figure 2](https://papers.nips.cc/paper_files/paper/2018/file/8f468c873a32bb0619eaeb2050ba45d1-Paper.pdf)

| Bias | Unnormalized weight `w(q,L)` | Exact normalizer `Z(L)` |
|---|---|---|
| flat | `1` | `L` |
| front | `L+1-q` | `L(L+1)/2` |
| back | `q` | `L(L+1)/2` |
| middle | `min(q,L+1-q)` | `floor((L+1)^2/4)` |

For middle, put `u=floor(L/2)` and `v=ceil(L/2)`. Its normalizer is also `u(u+1)/2+v(v+1)/2`. Thus lengths 1 through 6 have middle weights `[1]`, `[1,1]`, `[1,2,1]`, `[1,2,2,1]`, `[1,2,3,2,1]`, and `[1,2,3,3,2,1]`. Odd lengths must not use `L^2/4`, and length one must not receive a zero denominator.

Let `g_R(c,L)` and `g_P(h,L)` denote the **effective** cardinality factors. Zero-overlap terms are defined to be zero without evaluating either factor at zero. For canonical Tatbul semantics, impose `g(1,L)=1`; the framework also evaluates other explicitly defined local factors. Restrict `0<=g<=1` if bounded metric scores are required. Monotonicity of `g` is not needed for the algorithm.

For a true interval, maintain weighted active mass and fragmentation count:

\[
 W_j=\sum_{i\in T_j}p_i w_R(i-a_j+1,L_j),\qquad
 c_j=\#\{C:C\cap T_j\ne\varnothing\}.
\]

Its contribution is

\[
 r_j=\alpha\mathbf1[c_j>0]
 +(1-\alpha)\mathbf1[c_j>0]g_R(c_j,L_j)W_j/Z_R(L_j),
 \qquad R=K^{-1}\sum_j r_j.
\]

For a predicted interval `C=[a,b]`, let

\[
 N(C)=\sum_{i=a}^{b}y_iw_P(i-a+1,L),\qquad
 h(C)=\#\{T_j:T_j\cap C\ne\varnothing\},
\]

\[
 \psi(C)=\mathbf1[h(C)>0]g_P(h(C),L)N(C)/Z_P(L),
 \qquad P=J^{-1}\sum_C\psi(C).
\]

The reduction from a sum of overlap rewards to one weighted mass uses the disjointness of maximal predicted/true intervals. It is not valid to silently collapse overlapping annotated events into a binary vector if annotation multiplicity is part of the requested metric.

Precompute fixed-label prefixes

\[
 A(t)=\sum_{0\le i<t}y_i,\quad B(t)=\sum_{0\le i<t}i y_i,
 \quad D(t)=\sum_{0\le i<t}\sigma_i,
 \quad \sigma_i=\mathbf1[y_i=1\text{ and }(i=0\text{ or }y_{i-1}=0)].
\]

Write `U(a,b)=A(b+1)-A(a)` and `M(a,b)=B(b+1)-B(a)`, both zero for an empty interval. Then

\[
 h(C)=D(b+1)-D(a)+y_a-\sigma_a.
\]

The last correction counts a true interval that began before `a`. The weighted precision numerators are

\[
 \begin{array}{ll}
 N_{\rm flat}=U(a,b),&
 N_{\rm front}=(b+1)U(a,b)-M(a,b),\\
 N_{\rm back}=M(a,b)-(a-1)U(a,b).&
 \end{array}
\]

For middle, take `m=a+floor(L/2)-1`, so the left half is empty when `L=1`:

\[
 N_{\rm middle}=
 M(a,m)-(a-1)U(a,m)
 +(b+1)U(m+1,b)-M(m+1,b).
\]

These use constant numbers of prefix lookups and arithmetic operations. Separate precision and recall biases give all 16 bias pairs without changing the asymptotic cost for a fixed requested pair. Computing all 16 together also has a constant factor, but that factor must be measured, not described as free.

## Local-update proof and conditions

On inserting previously inactive position `i` in true interval `T_j`, add its **fixed true-interval weight** to `W_j`, and set

\[
 \Delta c_j=1-
 \mathbf1[i-1\text{ active and in }T_j]-
 \mathbf1[i+1\text{ active and in }T_j].
\]

Replace only `r_j` in the recall sum. Inserting outside the fixed label support changes no recall contribution: in one dimension it cannot connect two fragments of the same contiguous true interval by a path outside that interval. This remains true for arbitrary fixed per-position recall weights, not only the four canonical choices.

For precision, subtract the contributions of the zero, one, or two adjacent active components, then add the new interval's contribution using the formulas above. Recompute the new interval's positional weights from its endpoints. The weights of old points generally change when endpoints change; adding just the new point's weighted label is wrong. The existing endpoint arrays suffice to identify the adjacent intervals, because an active neighbor of an inactive point is necessarily a current component endpoint.

Consequently, the existing score ordering and query-bucket construction can be retained. Ordered-query costs remain

\[
 O(n\log(n+1)+n+H)
\]

for sorted scores, or

\[
 O(n\log(H+1)+n+H)
\]

for known-query bucketing. Arbitrarily ordered queries add `O(H log(H+1))`; space remains `O(n+H)`. These bounds count fixed-width/real arithmetic and constant-time factor evaluation. Exact arbitrary-precision rational powers and growing-degree polynomial arithmetic do not have the same unit-cost bound.

The assumptions are material:

- Cardinality factors must be pure local functions with the stated evaluation cost. A callback that scans all overlap fragments, depends on the entire prediction mask, or changes after unrelated activations does not satisfy this proof. Endpoint/length dependence is allowed because the replaced component can recompute it locally.
- Recall weights must be fixed for each fixed true interval. A recall rule that re-centers all weights on the currently detected portion needs a different argument.
- With general weights that can be zero, existence must use `c_j>0` or unweighted overlap count. `W_j>0` is not a correct existence test. For example, detecting only the first point under weights `[0,1]` earns the existence reward despite zero weighted mass.
- All eligible equal-score positions must activate before a state is emitted. Their internal insertion order is immaterial in exact arithmetic; emitted intermediate masks would be semantically wrong.
- Empty collections, all-one masks, strict versus non-strict comparison, and the below-minimum sentinel remain explicit API conventions. Extending the weighting rules does not resolve those semantic choices automatically.

## Strongest defensible general theorem

**Finite-feature interval-weight theorem.** Suppose fixed binary labels define disjoint true intervals; recall weights are precomputable in linear time; and for every predicted interval `C=[a,b]`, its positional weights have a representation

\[
 w(i;a,b)=\sum_{z=1}^{q}\mathbf1[i\in I_z(a,b)]
                 \sum_{\ell=1}^{d}\theta_{z\ell}(a,b)\phi_\ell(i).
\]

Here `q,d` are fixed constants; the `I_z` form a disjoint partition of `[a,b]` into integer intervals; the endpoints and coefficients are computable in constant time; the features `phi_l(i)` are independent of `a,b` and precomputable in linear time; weights are nonnegative; and the full-window weight sum is positive. Let the cardinality factors and any component aggregation weight be evaluable in constant time from locally maintained statistics.

Then weighted range precision and recall at all requested threshold masks admit constant arithmetic work per activation, after linear preprocessing, in addition to score/query ordering and result emission.

**Proof.** Precompute both `sum_{i<t} phi_l(i)` and `sum_{i<t} y_i phi_l(i)` for every feature. For each piece, the corresponding prefix difference supplies its unlabelled and label-weighted feature sums. Their coefficient-weighted totals give the normalizer and numerator in `O(qd)` operations. Local replacement touches at most three precision terms and one recall term. With fixed `q,d`, the work is constant. The existing endpoint argument supplies the components. This is a sufficient condition, not a characterization of every weight family that admits fast queries.

Constant-piece degree-`p` polynomials in position are a direct corollary using features `1,i,...,i^p`; coefficients may depend on endpoints. Canonical front/back need degree one and one piece, while canonical middle needs degree one and two pieces. Fixed-degree tapers and fixed piecewise polynomial urgency profiles therefore fit the theorem. An arbitrary length-dependent lookup table of weights, an unbounded number of pieces, or a polynomial whose degree grows with input size does not inherit the same constant bound. No lower bound for these excluded cases is asserted.

A useful aggregation extension is

\[
 P_\rho=\frac{\sum_C\rho(C)\psi(C)}{\sum_C\rho(C)}.
\]

For any nonnegative local `rho(C)` available in constant time, update its numerator and denominator by the same component removals/addition. `rho=1` is macro precision; `rho=L` is length-weighted precision. Fixed per-true-interval weights also extend recall by maintaining a weighted sum with a fixed denominator. An optional precision existence term is likewise local, but must be named as a metric variation rather than attributed to canonical Tatbul precision.

This theorem is an application of ordinary prefix aggregates and classical component maintenance. Its value is that it states exactly which endpoint-dependent metric customizations preserve the threshold-sweep cost.

## Three candidate extensions

| Candidate | Concrete result to build | Assessment and boundary |
|---|---|---|
| 1. Complete canonical weighted operator | All four biases on each side, independent local cardinality factors, integer canonical numerators/normalizers, exhaustive threshold evaluation | Valid and directly motivated by existing public metric options. The important extra step is changing-window precision, especially middle bias. Bias choices and custom cardinality themselves are old. Recommended first. |
| 2. Finite-feature/piecewise polynomial operator | The theorem above, plus one useful quadratic or piecewise-polynomial policy checked against a literal oracle | Strongest mathematical scope, but mostly a general sufficient-statistic observation. Include only supported families; do not claim arbitrary custom bias functions or a new component-tree framework. A second real use case would strengthen its practical value. |
| 3. Length-aware cardinality and aggregation | `g(c,L)=((L-1)/L)^(c-1)` for positive `c`, macro or length-weighted precision, and explicit empty/compatibility conventions | Covers the revised TimeSeAD metric family with the same local machinery. More directly useful than adding a synthetic weight solely to enlarge a theorem. Requires resolving the documented source discrepancy below; mathematical and compatibility outputs must be distinguished. |

For candidate 3, `L=1,c=1` takes the usual `0^0=1` branch of the effective factor; `c>1` cannot occur inside a singleton. Count-only penalties are a strict special case of the length-aware form. A different factor can be chosen independently for precision and recall.

## Primary-source positioning

| Source inspected | What already exists | Defensible distinction |
|---|---|---|
| [Tatbul et al. 2018](https://papers.nips.cc/paper_files/paper/2018/file/8f468c873a32bb0619eaeb2050ba45d1-Paper.pdf), Figure 2 and §5.5 | Four positional biases, customizable cardinality, sequential interval matching, and closed-form bias evaluation per overlap range | The closed-form weighting itself is prior art. The claimed delta is reusing sufficient statistics over changing threshold components. A strong single-mask comparator should include the paper's sorted-interval optimization. |
| [Menotti, Najman, Araújo 2007](http://urlib.net/dpi.inpe.br/ismm@80/2007/03.10.10.19), §§3.3–3.4, pp. 443–444 | Linear-time one-dimensional component-tree construction; height, surface and volume attributes can be maintained without changing time complexity. Their presented indexing structure has `O(max(n,m))` space for weight amplitude `m`. | Do not claim new connected-level-set maintenance or new constant-cost attributes. The additional work here is label-conditioned overlap, fragmentation, and normalized endpoint-dependent metric contributions. |
| [TimeSeAD overlap implementation, pinned `bb8efa9`](https://github.com/wagner-d/TimeSeAD/blob/bb8efa9ce17f9cfb0bab77df08c32d986de8429e/timesead/evaluation/ts_precision_recall.py), lines 24–148 and 175–286 | All four bias functions; direct sums/dot products over each scored window; local count/length cardinality callbacks; optional length-weighted precision | These are already expressible metric configurations. The inspected reducer does not maintain their weighted sums across activations. |
| [TimeSeAD evaluator, same pin](https://github.com/wagner-d/TimeSeAD/blob/bb8efa9ce17f9cfb0bab77df08c32d986de8429e/timesead/evaluation/evaluator.py), lines 237–318 | `__best_ts_fbeta_score` loops over unique score thresholds, constructs the strict prediction mask, and calls the metric; classic and revised variants exist | Exhaustive threshold optimization is prior art. The gap is repeated mask/window evaluation, not the ability to consider all observed thresholds. |
| [aeon range implementation, pinned `ac9abc3`](https://github.com/aeon-toolkit/aeon/blob/ac9abc36b1bd53aa98dc5c89062561cc7638f40b/aeon/benchmarking/metrics/anomaly_detection/_range_metrics.py), lines 257–387 and 421–559 | Four bias choices, normalized per-position overlap loops, and nested predicted/true range loops using overlap sets | The inspected file has no cross-threshold weighted-state maintenance. It is an API/semantic comparator, but its nested Python loops are insufficient as the sole runtime baseline. |

aeon's front/back/middle weights differ from the integer table by positive constants depending only on the scored interval length; normalizing by the full weight sum cancels those constants in real arithmetic. Canonical middle therefore agrees mathematically, including odd lengths. The pinned aeon precision helper rejects `udf_gamma` even though other helper/doc surfaces mention it, so arbitrary custom precision cardinality should not be advertised as verified aeon API parity.

The Menotti primary PDF was retrieved directly from the INPE proceedings URL and its text extracted in memory; the HAL metadata record is [hal-00622373](https://hal.science/hal-00622373). A bounded additional search for incremental/sweep implementations found no directly matching implementation, but search absence is not a novelty proof. The historical `IntelLabs/TSAD-Evaluator` repository returned HTTP 404 during this inspection, so its implementation was not verified. The absence claim in this memo is only about the specific TimeSeAD/aeon code inspected above.

## Counterexamples and numerical limits

**Whole-component moments do not suffice for middle.** On length four, label patterns `1001` and `0110` have the same count `2` and the same one-based first moment `5`, but their middle-weighted masses are `2` and `4`. A moving midpoint query, or an equivalent richer data structure, is required. The global prefixes above provide that query in constant time.

**Old component weighted masses are not additive under endpoint movement.** Under front bias, a labelled singleton `[a,a]` has unnormalized mass `1`. Append an unlabelled position to its right: its mass becomes `2`, despite the inserted point having zero label. Its normalized overlap changes from `1` to `2/3`. Prefix-derived recomputation handles this; merely adding the new label weight does not.

**Weighted recall is still nonmonotone.** In a true interval of length five with flat weights and reciprocal cardinality, prediction `11000` has overlap reward `2/5`. Activating the last point gives `11001`, weighted mass `3`, and two fragments, so the reward falls to `3/10`. For any `alpha<1`, its full recall contribution decreases as well. A general nonnegative weight or arbitrary local penalty does not justify a monotone-recall shortcut.

**Binary64 prefix cancellation can destroy a tiny numerator.** This algebraic witness requires no large array allocation. For dense labels before one-based position `a=2^27+1=134217729`, let `T(k)=k(k+1)/2`. Binary64 conversion gives

```python
a = 2**27 + 1
delta = float(a*(a+1)//2) - float((a-1)*a//2)
assert delta == 134217728.0
assert delta - float(a-1) == 0.0  # exact local singleton mass is 1
```

This is a precision loss in the prefix-derived numerator. Kahan accumulation of final component-score deltas cannot repair it. Use exact integer count/moment prefixes and integer numerator/normalizer arithmetic for canonical biases while every intermediate fits the chosen integer representation; convert only at division. Guard products as well as final values: computing `L*(L+1)` before halving can overflow even when the triangular result fits. A bound on stored moments alone does not bound `(b+1)*U`. Higher polynomial moments grow faster and need their own bounds or wider arithmetic.

For flat/front/back, relative component moments are another option: if a left component of length `l` and a right component merge through point `i`, then the new one-based local labelled moment is `T_left+(l+1)*y_i+T_right+(l+1)*U_right`. It avoids large global offsets but does not solve the middle split by itself. General floating weights still require a numerical error analysis; normalization and compensated accumulation are not an exact-arithmetic certificate. Tiny negative residuals should not be hidden by clipping without a stated tolerance/error policy.

**Pinned TimeSeAD revised precision needs a compatibility decision.** For `labels=10000` and `predictions=10101`, all predicted windows have length one, and correct length weighting over every predicted window gives precision `1/3`. The pinned `_compute_overlap` reducer returns `0.5` when invoked with `use_window_weight=True`: `total_gt_points` only accumulates windows visited before the other interval list is exhausted. This result was checked by extracting and executing only that pure reducer from the cited pin, with Python lists and simple bias/cardinality callbacks. It is not a claim about every TimeSeAD version. Macro precision uses the total window count and gives `1/3` on this witness. TimeSeAD also explicitly returns `(1,1)` when both masks are empty, whereas the current research API uses zero for empty outer collections. Neither difference should be silently folded into an equivalence claim.

## Checks performed and tests still needed

The local derivations were checked with small exact arithmetic, without changing repository tests or running performance jobs:

- Exhaustive labels of lengths 1–8, every subinterval, and all four biases: 59,384 numerator/normalizer equalities against literal weighted sums, with no mismatch.
- Exhaustive labels/prediction masks of lengths 1–6, every inactive-point insertion, every true interval, and all four weighted recall masses: 26,093 joint count/mass transition assertions, with no mismatch.
- The binary64 cancellation witness and the isolated pinned TimeSeAD trailing-window witness above both reproduced exactly as stated.

These checks support the formulas and exposed limits; they are not evidence of runtime advantage or submission readiness. A production extension still needs:

1. An independent literal interval oracle with rational arithmetic on small cases. Compare all 16 precision/recall bias pairs, `alpha` in `{0,1/5,1}`, and effective penalties `1`, `1/c`, `1/c^2`, and the length-aware factor. Use the same mathematical empty-mask rules on both sides.
2. Exhaustive activation-order checks on small tied scores, plus shuffled/duplicated query lists, strict endpoints, and lower sentinels. Include simultaneous left/right merges, a bridge outside labels, singleton true windows, all-zero/all-one labels, and odd/even midpoint crossings.
3. Numeric stress checks against integer/Fraction reference numerators: very short components at large offsets, sparse labels following dense prefixes, long merged intervals, alternating insertions, and integer overflow boundaries. These can test formulas with synthetic prefix values without allocating enormous arrays.
4. Source-pin differential checks against TimeSeAD and aeon on their shared semantics. Keep source discrepancies as explicit compatibility tests. The revised TimeSeAD denominator witness should be a named test before claiming compatibility.
5. A compiled fused per-threshold baseline and a sorted-interval/closed-form baseline reflecting Tatbul §5.5, as well as the existing implementations. Check equal outputs before timing. Compare at least three public dataset families with confidence intervals and record score cardinality, threshold count, fragmentation, and sequence length.
6. An ablation separating ordering cost, local component maintenance, weighted-prefix query cost, and cardinality/aggregation choice. A useful result would show that full canonical coverage retains the claimed scaling and identify when the simpler per-threshold baseline is faster.

The recommended claim is: **for the canonical range-metric family and a stated broader class of locally queryable weights, all threshold-query states can be evaluated using constant local update work per activation, with exact combinatorial/weighted sufficient statistics under an explicit arithmetic contract.** The inspected sources support the metric and component-tree antecedents; this memo establishes the algebraic extension and a bounded implementation gap, not global firstness.

## Subsequent review of the new implementation

The parent agent subsequently requested a read-only correctness review of `src/sparse_vus/weighted_range.py` and `tests/test_weighted_range.py`. No combinatorial or canonical-weight formula defect was found in the inspected version. Its odd-length middle split includes the center in the left half, whereas the derivation above places it in the right half; these are equivalent because both linear pieces give the same center weight. The independent Fraction oracle uses literal window sets and point weights, so it does not merely repeat the prefix derivation.

The implementation's domain bound `n<=2**31-1` safely bounds its int64 operations. In particular, `n(n+1)<2**62`, all first-moment prefixes are below `2**61`, and even a conservative `2n^2` bound for mixed intermediate expressions stays below `2**63-1`. Forty-four additional checks evaluated the actual scalar helper bodies with NumPy int64 arithmetic, synthetic analytic prefixes, and intervals near the maximum allowed coordinate. They covered full dense windows, short far-offset windows, and sparse middle-bias counterexamples; no overflow or mismatch occurred. This did not allocate arrays of that size or run performance measurements.

One numerical improvement was reported to the parent before timing: the initial improved-cardinality implementation raised the rounded base `(L-1.)/L` to `c-1`. For `L=1,000,000,c=500,000`, its factor differs from an 80-digit Decimal evaluation by approximately `-8.72e-12`; at `L=100,000,000,c=50,000,000`, the difference is approximately `-1.52e-9`. A stable real-valued evaluation is `exp((c-1)*log1p(-1./L))`, with an explicit `c==1` return of one to handle the singleton case. That evaluation rounded identically to the high-precision reference for the four large-length cases checked. This finding concerns floating factor evaluation, not the exactness of the integer overlap statistics; no uniform error certificate is claimed.

The implementation initially exposed one shared cardinality enum (`one`, `reciprocal`, `improved`) for both sides. Independent precision/recall penalties and arbitrary pure local callbacks remain supported by the theorem, but must not be described as current API features unless separately implemented. Likewise, no general polynomial callback engine was inspected. The reviewed length-weighted precision intentionally uses every predicted window in its denominator, agreeing with the mathematical variant rather than the pinned TimeSeAD discrepancy.
