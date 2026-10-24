# Weighted range trajectories: proof and novelty boundary

Evidence date: 24 October 2026. This is a separate technical note for the existing submission work, not a new paper or a claim of acceptance. It strengthens the flat/reciprocal proposition in `paper/range_sweep_method.tex`; no manuscript, benchmark, or metric implementation was edited for this note. The current range definitions and the VUS definitions in `paper/exact_metrics_pvldb20261024_body.tex` were read before developing the extension. The four-bias implementation was inspected, including the stable improved-cardinality formula subsequently committed by the parent as `f68f4e4`.

**Result.** The canonical four positional biases admit exact local updates. More generally, endpoint-dependent weights with at most `q` polynomial pieces and degree at most `d-1`, with `q,d >= 1`, admit `O(qd)` work per insertion. A pure local constant-time cardinality function can be different for recall and precision in the theorem. The implemented API supports a smaller, explicit family. The strongest defensible contribution is maintaining the *joint label-conditioned precision/recall trajectory* across thresholds. Closed-form overlap evaluation, positional biases, weighted range curves, and one-dimensional component trees all predate this work.

## 1. Standalone definitions and assumptions

Let `y in {0,1}^n`, `n >= 1`, be fixed labels on the path with vertices `0,...,n-1`. Let `T_1,...,T_K` be their maximal positive intervals, with inclusive endpoints. Scores are fixed and totally ordered; predictions at query `t` are

\[
 p_i(t)=\mathbf 1\{s_i>t\}.
\]

Let `C_1,...,C_J` be the current maximal predicted-positive intervals. For a nonempty interval `I=[a,b]`, write `L(I)=b-a+1`. Precision and recall may use different weight families `w_P(i;a,b)` and `w_R(i;a,b)`. Each family is fixed before the sweep and depends on the scored interval's endpoints and the position, not on the rest of the active prediction mask. Require nonnegative weights at the integer positions and a positive normalizer

\[
 Z_X(a,b)=\sum_{i=a}^b w_X(i;a,b)>0,\qquad X\in\{P,R\}.
\]

For each true interval, define

\[
 W_j=\sum_{i\in T_j}p_i w_R(i;a_j,b_j),\qquad
 c_j=\#\{C:C\cap T_j\ne\varnothing\}.
\]

For a predicted interval, define

\[
 N(C)=\sum_{i\in C}y_i w_P(i;a,b),\qquad
 h(C)=\#\{j:T_j\cap C\ne\varnothing\}.
\]

Let `g_R(c,L)` and `g_P(h,L)` be **effective cardinality factors**, each a deterministic, pure `O(1)` function of the displayed local arguments and fixed configuration. The formulas below never evaluate a factor at count zero. The usual Tatbul convention has `g(1,L)=1`; `0 <= g <= 1` keeps these scores bounded. These restrictions concern metric interpretation; monotonicity of the factors is unnecessary for the update proof. A callback that scans intervals, depends on the global mask, or has unbounded evaluation cost is outside this assumption.

For `alpha in [0,1]`, set

\[
 r_j=\begin{cases}
 \alpha+(1-\alpha)g_R(c_j,L_j)W_j/Z_R(a_j,b_j),&c_j>0,\\
 0,&c_j=0,
 \end{cases}\qquad
 \psi(C)=\begin{cases}
 g_P(h(C),L(C))N(C)/Z_P(a,b),&h(C)>0,\\
 0,&h(C)=0.
 \end{cases}
\]

The requested range recall and macro precision are

\[
 R=\frac1K\sum_j r_j,\qquad P=\frac1J\sum_C\psi(C).
\]

An empty outer collection has value zero. A harmless generalization replaces macro precision by

\[
 P_\rho=\frac{\sum_C\rho(C)\psi(C)}{\sum_C\rho(C)},
\]

where `rho(C)>0` is pure, endpoint-local, and computable in constant time. The denominator is zero only for an empty prediction. Macro precision uses `rho=1`; mathematical length-weighted precision uses `rho=L`. The latter includes **every** predicted component in its denominator, including components with no label overlap. Recall remains a macro average. Any fixed constant-time function of the emitted pair, such as `F1=2PR/(P+R)` with zero at `P+R=0`, adds constant cost per query.

Disjoint maximal intervals are essential to these definitions: their overlap rewards sum to the single weighted masses above without double-counting. An annotation format that preserves overlapping events with multiplicities needs a separate theorem. Binary-vector reduction would change that metric.

## 2. Prefix lemma for endpoint-dependent piecewise polynomials

Assume that for each scored interval `[a,b]`, a weight family specifies a partition into at most `q` contiguous integer pieces `[u_r(a,b),v_r(a,b)]`, and on piece `r`

\[
 w(i;a,b)=\sum_{k=0}^{d-1}\theta_{rk}(a,b)i^k.
\]

The partition endpoints and all coefficients can be produced in `O(qd)` arithmetic operations from `(a,b)` and fixed configuration. This includes floor/ceiling midpoint splits. Empty pieces may be skipped. It does **not** assume that arbitrary polynomial roots, optimization problems, or arbitrary user programs can be solved in constant time. Here `d` is the number of coefficients, not the degree, so flat weights have `d=1`, not zero.

Precompute the fixed-label and unweighted moment prefixes

\[
 A_k(t)=\sum_{0\le i<t}y_i i^k,\qquad
 B_k(t)=\sum_{0\le i<t}i^k,\qquad 0\le k<d,
\]

using `i^0=1`, including at zero. These tables take `O(dn)` arithmetic operations and words. Then

\[
 \begin{split}
 N([a,b])&=\sum_{r=1}^{q}\sum_{k=0}^{d-1}\theta_{rk}(a,b)
       \bigl(A_k(v_r+1)-A_k(u_r)\bigr),\\
 Z(a,b)&=\sum_{r=1}^{q}\sum_{k=0}^{d-1}\theta_{rk}(a,b)
       \bigl(B_k(v_r+1)-B_k(u_r)\bigr).
 \end{split}
\]

Both are evaluated in `O(qd)` operations even when the pieces move after a merge. This is a range-sum identity, not a new prefix-sum technique. Crucially, the prefixes are over **fixed labels in physical position order**, not over the evolving active mask or score order. No dynamic range-sum structure is needed for precision.

Let `sigma_i=1` at each true-interval start and zero otherwise, and let `D(t)=sum_{i<t} sigma_i`. The number of true intervals intersecting any nonempty `[a,b]` is

\[
 h([a,b])=D(b+1)-D(a)+y_a-\sigma_a.
\]

The last term counts the one true interval already in progress at the left endpoint. Every other intersecting true interval has exactly one start in `[a,b]`. Thus `h` costs constant time regardless of the number of intersections.

Recall uses fixed endpoints: precompute `v_i=w_R(i;a_j,b_j)` for each point in `T_j`, and the fixed `Z_R(a_j,b_j)`. Processing one true interval's coefficient list at a time needs only `O(qd)` scratch space; store the resulting `n` point weights and `K` normalizers, not a separate polynomial expansion per future state. Straightforward preprocessing is at most `O(qdn)` operations. More efficient piecewise scans are possible but are not necessary for the claimed bound.

## 3. Update invariants and proof

Maintain the following state after each completed insertion:

1. `active[i]` equals the current prediction mask. For every active component `[a,b]`, `left[b]=a` and `right[a]=b`. Entries at non-endpoints may be stale.
2. For every true interval, the stored `W_j` and `c_j` equal the definitions in Section 1. A precomputed owner array identifies the unique true interval of a labeled point in constant time.
3. `S_R=sum_j r_j`, `S_P=sum_C rho(C) psi(C)`, and `D_P=sum_C rho(C)` equal the current global aggregates. Optionally maintain the component count `J` and first-hit count separately; this is equivalent bookkeeping.

All invariants hold in the empty prediction, with zero masses, counts, and sums. Consider inserting an inactive point `i`.

**Recall update.** If `i` belongs to `T_j`, subtract its old `r_j`, add `v_i` to `W_j`, and replace

\[
 c_j\leftarrow c_j+1
 -\mathbf1\{i-1\text{ active and in }T_j\}
 -\mathbf1\{i+1\text{ active and in }T_j\}.
\]

Then add the new `r_j`. Out-of-domain neighbors are inactive. Restricted to a contiguous true interval, each active run corresponds to exactly one global predicted component intersecting it. Zero active neighbors create a run; one extends a run; two merge two runs. The latter runs are distinct, since an inactive point separates them on a path. This proves the count update. The weight update is additive because the true interval's endpoints do not move.

If `i` lies outside all true intervals, it cannot connect two different active fragments inside a single true interval: the unique path between two points of that interval lies inside it. All recall terms therefore remain unchanged. A merge can join components that intersect different true intervals, but neither interval's number of intersecting components changes. Thus at most one recall contribution changes per insertion.

**Precision update.** If `i-1` is active, it must be the right endpoint of its component, since `i` is inactive; its left endpoint is `a=left[i-1]`. If `i+1` is active, it must be the left endpoint of its component; its right endpoint is `b=right[i+1]`. Missing components are omitted and their endpoint is replaced by `i`. Remove the zero, one, or two neighboring component terms from `S_P,D_P`; insert the new term for `[a,b]`. Evaluate each term from the fixed prefixes in Section 2. All other components retain their endpoints and hence their weights, normalizers, cardinalities, and contributions.

Finally set `left[b]=a`, `right[a]=b`, and `active[i]=true`. Only a component endpoint adjacent to an inactive point is ever queried, so stale interior entries cannot corrupt the next update. No union-find search is needed in this one-dimensional implementation. The component count changes by `1-left_active-right_active`. For length-weighted precision, the denominator simply increases by one; for general `rho`, removing and adding the corresponding local weights maintains it.

The update preserves every invariant. By induction, the stored pair equals a fresh application of the Section 1 formulas to the complete active mask after any insertion sequence. This establishes path independence in exact arithmetic. At most three precision evaluations, one recall replacement, and constant other work are required, so each insertion costs `O(qd)`.

Existence is tested with `c_j>0`, rather than `W_j>0`: nonnegative positional weights may be zero at a detected point. For a true interval of length two with weights `(0,1)`, prediction `(1,0)` has zero weighted mass but earns existence reward `alpha`. The canonical four biases are strictly positive, but the general theorem must not conflate weighted mass with detection existence.

## 4. Theorem and finite-grid corollary

**Theorem (joint weighted range trajectory).** Under Sections 1–2, for `n` points and `H` arbitrary query thresholds, all requested precision, recall, and F1 values can be computed exactly in the unit-cost exact-arithmetic/comparison model in

\[
 O\!\left(n\log(n+1)+H\log(H+1)+qdn+H\right)
 \subseteq
 O\!\left(n\log(n+1)+H\log(H+1)+qd(n+H)\right)
\]

time and `O(dn+n+H+qd)` words. For fixed `q,d`, this is `O(n log(n+1)+H log(H+1)+n+H)` time and `O(n+H)` space. If the queries are already ordered, their sorting term is unnecessary.

*Proof.* Perform the preprocessing in Section 2, sort points by decreasing score and queries by decreasing threshold, and start from the empty prediction. Before emitting query `t`, insert every remaining point satisfying `s_i>t`. Each point is inserted at most once. Emit only after every eligible score tie is complete, and restore original query order at the end. The induction in Section 3 proves equality with the requested mask, including duplicate queries. Preprocessing and all insertions cost `O(qdn)`, and the `H` emitted states cost `O(H)`. Sorting and output storage give the stated total. The memory includes two moment tables, label owners, endpoint arrays, true-interval statistics, orders/output, and one transient coefficient list. The convention for `K=0` also gives zero precision, since every `h(C)` is zero. QED.

**Finite-grid corollary.** If only a known list of `H` query thresholds is needed, full score sorting can be avoided. Order the queries `t_1 >= ... >= t_H`, and assign point `i` its first eligible query

\[
 e(i)=\min\{k:s_i>t_k\},
\]

using `H+1` when no query includes it. Find each `e(i)` by binary search, counting-bucket points by this integer, and process each complete bucket before emitting its query. The predicate is monotone in the query index. Before query `k`, exactly the points with `e(i)<=k`, equivalently `s_i>t_k`, have been inserted. The invariant proof allows arbitrary within-bucket order, even when distinct score levels share a bucket, because intermediate states are not returned. Therefore the time is

\[
 O\!\left(n\log(H+1)+H\log(H+1)+qdn+H\right),
\]

with the same space bound. For already ordered queries, remove `H log(H+1)`. This is exact for the supplied grid, not a claim that its optimum equals the optimum over all possible thresholds. Points in the never-eligible bucket need no activation. Empty query lists are trivial.

These are ordinary sorting and offline bucketing techniques. The theorem makes no lower-bound or optimality claim against classical one-dimensional component-tree construction or fixed-width radix sorting. The work being bounded is evaluating the specified joint metric trajectory.

An additional consumer that sorts emitted points by recall or constructs another ordered geometric object must pay its own cost. In particular, TimeEval's recall/precision sorting adds `O(H log(H+1))`; it is absorbed by the theorem's arbitrary-query bound but must be added to its already-ordered-query variant. A maximum over the returned F1 values costs only `O(H)`. Nonmonotone range recall means an AUC convention cannot be inferred merely from threshold order.

**Finite-feature extension, theorem only.** The prefix lemma remains valid if `i^k` is replaced by a fixed endpoint-independent feature family `phi_k(i)` whose values and prefixes can be prepared in `O(dn)` work. The coefficients and pieces still obey the same cost restrictions. This includes suitable nonpolynomial separable weights, but it does not automatically cover arbitrary endpoint-dependent kernels or adaptive overlap rewards. The polynomial theorem is the more concrete manuscript statement; neither general engine is implemented in the current API.

## 5. Canonical corollary and exact normalizers

For local coordinate `u=i-a+1`, Tatbul's four canonical positional choices are the following. The normalizers and prefix formulas here follow by direct summation. [Tatbul et al., NeurIPS 2018, Figure 2 and positional-bias definition](https://papers.nips.cc/paper_files/paper/2018/file/8f468c873a32bb0619eaeb2050ba45d1-Paper.pdf)

| Bias | Weight | Normalizer | Pieces / coefficients |
|---|---|---|---|
| Flat | `1` | `L` | `q=1,d=1` |
| Front | `L+1-u` | `L(L+1)/2` | `q=1,d=2` |
| Back | `u` | `L(L+1)/2` | `q=1,d=2` |
| Middle | `min(u,L+1-u)` | `floor((L+1)^2/4)` | `q=2,d=2` |

Write `U(a,b)=A_0(b+1)-A_0(a)` and `M(a,b)=A_1(b+1)-A_1(a)`, with both zero for an empty interval. Then

\[
 \begin{array}{ll}
 N_{\rm flat}=U(a,b),&N_{\rm front}=(b+1)U(a,b)-M(a,b),\\
 N_{\rm back}=M(a,b)-(a-1)U(a,b).&
 \end{array}
\]

For middle, the current implementation uses `m=floor((a+b)/2)` and

\[
 N_{\rm middle}=M(a,m)-(a-1)U(a,m)
 +(b+1)U(m+1,b)-M(m+1,b).
\]

When `L` is odd, the center has the same value under either branch and may be assigned to either half. For `L=1`, these formulas give numerator `y_a` and normalizer one. Using only a component's *total* label count and first moment would be insufficient for middle: length-four labels `1001` and `0110` both have count two and one-based first moment five, but middle masses two and four. The split prefix query supplies the missing information.

Three implemented effective factors are `g=1`, `g=1/c`, and the TimeSeAD length-aware factor `((L-1)/L)^(c-1)` for positive counts. Their mathematical availability is prior art. The stable implementation of the last uses an explicit count-one branch and `exp((c-1)*log1p(-1/L))`. [TimeSeAD pinned positional/cardinality functions](https://github.com/wagner-d/TimeSeAD/blob/bb8efa9ce17f9cfb0bab77df08c32d986de8429e/timesead/evaluation/ts_precision_recall.py#L24-L148)

| Scope | Current implementation | Theorem |
|---|---|---|
| Four biases, independently for precision and recall | Yes | Yes |
| One / reciprocal / TimeSeAD-improved cardinality | Yes, one shared choice | Yes |
| Separate arbitrary pure local `g_P,g_R` callbacks | No | Yes, subject to evaluation cost |
| Macro or all-component length-weighted precision | Yes | Yes |
| Arbitrary endpoint-local precision aggregation weights | No | Yes |
| General piecewise polynomial / finite-feature engine | No | Yes |
| VUS, PATE, DQE, LARM/ALARM semantics | Not supplied by this range kernel | Not implied by this theorem |

The theoretical extension strengthens coverage; it is not evidence that all proposed customizations have been implemented or empirically evaluated. Even a strong generic theorem does not establish that a new positional preference improves detector evaluation quality.

## 6. Numerical and semantic limits

The theorem is an exact-arithmetic result. It is not a uniform binary64 error certificate or a bitwise-agreement claim. With polynomial degree growing, monomials and coefficients can need increasing bit length; the displayed bounds count arithmetic operations and words, not arbitrary-precision bit operations. Even fixed degree may require wider integers than the canonical implementation. Arbitrary `O(1)` gamma means constant cost in this declared model, not that every real-valued user function is computable exactly on hardware.

For the implemented canonical weights, integer prefix counts and first moments avoid catastrophic subtraction of rounded floating prefixes. At one-based position `a=2^27+1`, let `T(k)=k(k+1)/2`: binary64 evaluation of `float(T(a))-float(T(a-1))-(a-1)` is zero although the singleton's local back-weight is one. Compensating the final global sum would not repair that numerator. The current integer implementation avoids this case.

The `n <= 2^31-1` implementation restriction is a sufficient signed-int64 bound for these four biases: first moments are at most `n(n-1)/2`, `L(L+1) <= n(n+1) < 2^62`, and even the loose bound `2n^2` is below `2^63-1`. The weighted numerator subexpressions and recall masses therefore fit. This bound does not transfer to the general polynomial engine. A prior read-only check of the helper expressions at the integer limit, using analytic prefixes instead of allocating a length-`n` array, is recorded in the companion feasibility note.

Directly exponentiating the rounded near-one base of the improved factor amplifies error for large `L,c`. The inspected revision uses `log1p` and a count-one branch. Floating conversion, division, exponential evaluation, and accumulated local differences still incur rounding. In exact arithmetic within-bucket order is immaterial; binary64 summation order can change low bits.

Three other boundaries prevent incorrect shortcuts:

- Off-label insertions cannot be discarded. For `y=101`, changing prediction `101` to `111` leaves recall one but changes flat reciprocal precision from one to one-third. Front-weight numerators can change even on extending an interval with an unlabeled point.
- Recall can decrease: inside a true interval of length five, flat reciprocal overlap recall changes from `2/5` for prediction `11000` to `3/10` for `11001`. A monotone-recall shortcut is invalid.
- Strict queries at observed scores exclude the all-active mask below the minimum. Add a lower sentinel if the target optimization includes it. The current implementation permits infinite query sentinels and finite binary64 scores, handles complete ties, and rejects silently rounded large-integer or complex inputs.

## 7. Closest algorithmic antecedents and what remains different

The following are direct antecedents, irrespective of date; they should not be displaced by a list of more recent but less relevant metric papers.

| Primary source inspected | What is already present | Remaining distinction / implication |
|---|---|---|
| [Tatbul et al. 2018, Section 5.5](https://papers.nips.cc/paper_files/paper/2018/file/8f468c873a32bb0619eaeb2050ba45d1-Paper.pdf) | Sorted interval traversal and closed-form positional overlap computation | Do not claim the first closed forms or first efficient single-mask range evaluation. The present argument reuses fixed-label moments while intervals change across queries. |
| [Menotti, Najman, and Araujo 2007, Sections 3.3–3.4, pp. 443–444](http://urlib.net/dpi.inpe.br/ismm@80/2007/03.10.10.19) | Linear-time 1D component-tree construction and simultaneous height/surface/volume attributes; presented integer-weight structure has `O(max(n,m))` space for weight amplitude `m` | Connected superlevel sets and maintaining component attributes are classical. Claim neither a new tree nor faster tree construction. The coupled fixed-label fragmentation and endpoint-dependent normalized rewards are the specific state analyzed here. |
| [TimeSeAD evaluator, pinned lines 237–318](https://github.com/wagner-d/TimeSeAD/blob/bb8efa9ce17f9cfb0bab77df08c32d986de8429e/timesead/evaluation/evaluator.py#L237-L318) and [range evaluator](https://github.com/wagner-d/TimeSeAD/blob/bb8efa9ce17f9cfb0bab77df08c32d986de8429e/timesead/evaluation/ts_precision_recall.py) | Every observed score can already be evaluated; all four biases and improved cardinality exist | Inspected threshold maximization rebuilds a mask and calls the range metric at each score. Exhaustive threshold evaluation and customization are not new. |
| [TimeEval range PR curve, pinned lines 228–296](https://github.com/TimeEval/TimeEval/blob/7c3622757b1a3afa9a84cbc97ce132d9e379f715/timeeval/metrics/range_metrics.py#L228-L296) | Weighted Tatbul PR-AUC, a configurable threshold sample cap, per-threshold `prts` calls, and recall/precision sorting | This is the closest inspected curve consumer. It blocks a “first weighted range curve” claim; the local cross-threshold computation remains distinct. |
| [aeon range metric routines, pinned lines 257–559](https://github.com/aeon-toolkit/aeon/blob/ac9abc36b1bd53aa98dc5c89062561cc7638f40b/aeon/benchmarking/metrics/anomaly_detection/_range_metrics.py#L257-L559) | All four positional choices in single-mask precision/recall, interval extraction and overlap traversal | Same metric family; inspected routines do not expose the joint insertion state proved above. A meaningful baseline must include an efficient single-mask scan, not only a slow nested reference. |
| [TSB-AD range F1 and VUS routines, pinned source](https://github.com/TheDatumOrg/TSB-AD/blob/303dffbfc11612995b17b06633f8c9d0ea0e38e5/TSB_AD/evaluation/basic_metrics.py) | `metric_RF1` samples thresholds and recomputes range rewards; `RangeAUC_volume_opt/opt_mem` reuse selected VUS work | Different public workloads motivate separate operators. Do not silently equate their threshold, empty-mask, or denominator conventions. |

TimeEval's [issue #22](https://github.com/TimeEval/TimeEval/issues/22), opened in July 2022 and still open when checked, explicitly records slow repeated range-metric calls and threshold sampling as a workaround. It calls the quality decrease minor and is labeled very low / Wont-have priority. This is a precise public maintenance need, not evidence of broad industrial urgency. Its existence strengthens the choice of a real consumer; it does not establish the novelty of recognizing the problem.

## 8. Recent primary-paper screen, 2024–2026

The table separates direct computational predecessors from metric-design and benchmark context. It is a bounded screen of eleven recent papers, not a claim that eleven equally close algorithms exist. The taxonomy has a 2024 issue date but was published online in November 2023. Software companions are treated separately below. No detector-quality claim or reported speedup from another paper is adopted as a result of this project.

| Paper and inspected location | Relevance to the proposed result | What the inspected source establishes |
|---|---|---|
| [Boniol et al., *VUS: Effective and Efficient Accuracy Measures for Time-Series Anomaly Detection*, VLDB Journal 2025, Section 4.3 and Algorithms 2–3](https://arxiv.org/html/2502.13318v1#S4.SS3) | **Direct metric-computation prior** | Separates static/dynamic VUS work and supplies optimized implementations. The displayed algorithms retain threshold/buffer work. Their VUS operator differs from the Tatbul component-average operator proved here. |
| [Sylligardos, *Fast or Accurate? Rethinking Time Series Anomaly Detection*, VLDB PhD Workshop 2025, Section 4 and Figure 3](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/PhD/PhD25_17.pdf) | **Direct acceleration agenda** | Reports preliminary CPU/GPU VUS acceleration and planned detailed release. The four-page paper does not provide this Tatbul local-update theorem. Its efficiency agenda must be acknowledged. |
| [Ghorbani et al., *PATE*, KDD 2024, Sections 2.2–2.3 and Appendix E](https://arxiv.org/html/2405.12096v1) | **Adjacent weighted metric and computation** | Uses proximity-dependent weighted PR across thresholds and buffers; Appendix E reports runtime observations. PATE's state-dependent missed-anomaly weights do not automatically satisfy this theorem. Official code below reconstructs events per threshold. |
| [Li et al., *DQE*, March 2026 preprint, Sections 3.2–3.5](https://arxiv.org/html/2603.06131v1) | **Adjacent local metric and threshold aggregation** | Combines event capture, near-miss, and false-alarm scores across thresholds. This is a different metric, and the inspected implementation rebuilds event groups per threshold. No venue acceptance is inferred from its preprint. |
| [Wagner et al., *Formally Exploring Time-Series Anomaly Detection Evaluation Metrics*, AISTATS 2026, Sections 4 and 6, Theorems 6.1–6.2](https://proceedings.mlr.press/v300/wagner26a.html) | **Close theory of interval rewards** | Introduces LARM/ALARM and formal metric properties. Its official ALARM routine uses fixed prefix counts and exponential positional rewards. Those ingredients are prior; the inspected source is a scalar binary-mask evaluator, not a Tatbul threshold trajectory. |
| [Sørbø and Ruocco, *Navigating the metric maze*, DMKD 2024 issue, Sections 5.1.4 and 5.2](https://link.springer.com/article/10.1007/s10618-023-00988-8) | **Taxonomy and prior use of range curves** | Describes customizable Tatbul rewards, optimal-threshold metrics, and range PR-AUC usage. Further evidence against claiming the first weighting or curve construction. This is a taxonomy rather than a local-update algorithm. |
| [Liu and Paparrizos, *The Elephant in the Room: Towards A Reliable Time-Series Anomaly Detection Benchmark*, NeurIPS 2024, Sections 3.2 and 5.2.1](https://proceedings.neurips.cc/paper_files/paper/2024/file/c3f3c690b7a99fba16d0efd35cb83b2c-Paper-Datasets_and_Benchmarks_Track.pdf) | **Public workload and metric comparison** | Establishes the TSB-AD evaluation setting and discusses metric reliability. Its official range/VUS implementation is a relevant comparator; benchmark conclusions about preferred metrics are not computational novelty. |
| [Kotowski et al., *European Space Agency Benchmark for Anomaly Detection in Satellite Telemetry*, 2024 preprint / revised 2025, Methods: evaluation metrics](https://arxiv.org/abs/2406.17826) | **Operational constraints and TimeEval use** | Uses TimeEval and discusses metric computational cost, excluding VUS in its chosen evaluation. This supports practical relevance but neither supplies a same-semantic speed comparison nor proves all VUS evaluation must be expensive. |
| [Liu et al., *TSB-AutoAD*, PVLDB 2025, Section 4.3](https://www.vldb.org/pvldb/vol18/p4364-liu.pdf) | **Model-selection evaluation workload** | Uses VUS-PR for automated detector selection/generation evaluation. It motivates repeated evaluation but does not establish the weighted Tatbul update theorem. |
| [Zhou et al., *mTSBench*, TMLR 2026, Section 3.1 Evaluation Metrics and Section 4.1](https://arxiv.org/html/2506.21550v2) | **Recent direct consumer of range curves** | Reports range PR-AUC alongside VUS and other metrics. This is concrete evidence that the existing range-curve consumer is used; the inspected paper studies benchmark/model-selection behavior. |
| [Zhu et al., *When Foundation Models are One-Liners*, ICLR 2026, Section 5 and Appendix H](https://proceedings.iclr.cc/paper_files/paper/2026/file/cf70320e93c08b39b1b29a348097a376-Paper-Conference.pdf) | **Recent VUS evaluation and semantic caution** | Studies VUS-based detector comparisons and label/metric sensitivity. It is workload context, not a fast-metric algorithm; faster exact computation alone does not solve the metric-quality issues it discusses. |

Official recent implementations were also inspected:

- [PATE `PATE_metric.py`, revision `2d358ce1b065674fcdadda115a08bbe6376273d0`, lines 13–22 and 87–164](https://github.com/Raminghorbanii/PATE/blob/2d358ce1b065674fcdadda115a08bbe6376273d0/pate/PATE_metric.py): each threshold constructs `score>=threshold` and prediction events; the continuous wrapper parallelizes those calls and can sample thresholds. Its runtime evidence must be interpreted with that configuration.
- [DQE `dqe_metric.py`, revision `055c23eb6e061284021b7c37ecd6615c85d61837`, lines 701–785](https://github.com/Yueweilirepo/DQE/blob/055c23eb6e061284021b7c37ecd6615c85d61837/dqe/dqe_metric.py): a configured threshold grid, then per-threshold masks and intervals. The code is evidence about that implementation, not every possible DQE algorithm.
- [ALARM `alarm.py`, revision `05491ba0e7180d1c1b902857ea102ee18fbb2008`](https://github.com/wagner-d/tsadm/blob/05491ba0e7180d1c1b902857ea102ee18fbb2008/src/tsadm/alarm.py): binary segmentation, static cumulative counts, and interval rewards. Prefix-based labeled event evaluation alone is not a new contribution here.
- [Klein fast-VUS, revision `1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00`, `fast_vus.py` lines 56–113](https://github.com/tomlouisklein/fast-VUS/blob/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py): score ordering, support restriction, cumulative weights, and searches at all requested thresholds. This directly blocks novelty claims for generic sorting/cumulative-sum VUS acceleration.
- [Benchopt, revision `2b55ccb1`, `benchmark_utils/metrics.py` lines 325–389](https://github.com/benchopt/benchmark_tsfm/blob/2b55ccb1/benchmark_utils/metrics.py#L325-L389): score-ordered cumulative sums and per-segment maxima already accelerate VUS thresholds.
- [FF-VUS in aVUSi, revision `facf4362`, `vus_numpy.py` lines 92–168](https://github.com/doanthihoaithu/aVUSi/blob/facf4362/3_metric_calculator/metrics/ffvus/vus_numpy.py#L92-L168): obtains unique thresholds and forms a threshold-by-score mask matrix. It is a fast VUS implementation precedent, with a distinct memory strategy; semantic equality to this repository's VUS contract requires a separate audit.

No inspected source establishes the exact coupled update theorem in Sections 2–4. That bounded finding supports a narrowly stated comparison; it is not proof of worldwide novelty. The new TimeEval and ALARM evidence narrows the claim materially. A reviewer can reasonably see the extension as a useful application of classical component/attribute maintenance unless the consumer evidence demonstrates why the coupled metric state matters.

## 9. Prospective TimeEval consumer protocol and manuscript wording

The native consumer study being prepared by the parent uses the selected flat-bias, cardinality-one, `alpha=0` subset, comparing TimeEval's nominal default `max_samples=50` with an all-observed configuration `max_samples=np.inf`. The adapter deliberately rejects reciprocal cardinality. This note proposes no runtime or accuracy measurements for that study and did not run it. Record the actual emitted threshold count: the reference sampling rule is an interval stride with an optional final endpoint, not a proof of a hard cap of exactly 50.

For a matched replay, preserve the source's threshold construction, synthetic endpoints, and recall/precision ordering; replace only the per-threshold metric computation. The `>=` masks can be reproduced by the strict binary64 API with `nextafter(t,-inf)`. Preserve original point order and complete ties. Charge any output sorting to the consumer. [TimeEval's exact pinned consumer](https://github.com/TimeEval/TimeEval/blob/7c3622757b1a3afa9a84cbc97ce132d9e379f715/timeeval/metrics/range_metrics.py#L250-L296)

The source's initial precision equals class balance. For the chosen flat/cardinality-one subset this is the canonical all-active precision. Extending the adapter to reciprocal cardinality without revisiting its endpoint would mix conventions: `y=101` has all-active reciprocal precision `1/3`, whereas class balance is `2/3`. This is an extension boundary, not an error claim about the selected consumer. Front/back/middle endpoints also require checking because all-active positional precision need not equal unweighted class balance.

Suggested compact claim for a future manuscript revision:

> We maintain joint range precision and recall over threshold activations for endpoint-dependent positional weights with a constant number of fixed-degree polynomial pieces and pure local cardinality factors. Each activation replaces at most one true-interval reward and three predicted-component terms, yielding linear update work after ordering. The implementation covers all four canonical Tatbul biases; arbitrary piecewise-polynomial weights are a theoretical generalization. Existing weighted range curves and closed-form overlap evaluation are retained as antecedents.

This claim should be accompanied by the theorem's arithmetic model, query convention, and constant `q,d` qualification. The empirical claim must remain tied to measured consumer and configuration results. Do not claim a new metric, a new component-tree algorithm, first exhaustive range evaluation, first weighted PR curve, or coverage of every Tatbul customization. The VUS and range operators can remain in one workload-reduction paper, but this theorem should not be used as a proof of the separate VUS support reduction.

## 10. Focused verification needed for the extension

The companion feasibility note records the earlier canonical algebra/transition checks and read-only integer-bound review. A further tiny in-memory `Fraction` probe for this note checked 1,320 interval numerator/normalizer pairs and 360 insertion states with a two-piece quadratic/cubic weight, separate `g_R=1/c^2` and `g_P=L/(L+c-1)`, and `rho=L^2`. Direct rescanning agreed exactly with the prefix and update formulas. Labels and insertion orders used a fixed seed over lengths one through nine; this was not exhaustive, a benchmark, or a test of a shipped polynomial engine. Appropriate further checks, if the manuscript or API adopts the general theorem, are:

1. Compare the joint trajectory against an independent exact rational oracle for all four precision/recall bias combinations, including singleton and odd/even midpoint cases, both sides of a merge, and merges across distinct true intervals.
2. Exercise zero positional weights with positive detection counts, separate local cardinality functions, and nonconstant normalizers. For an actual polynomial engine, include degree two or three with moving piece boundaries and compare direct integer sums, since canonical linear tests cannot validate the unimplemented general case.
3. Check bucket/sorted/raster agreement for duplicate and arbitrary-order queries, equal scores, never-active points, lower sentinels, and a bucket containing many different score levels. Equality should be exact in rational arithmetic; specify a numerical tolerance for binary64 outputs.
4. Preserve a large-offset singleton case and the analytic int64-bound helper checks without allocating billion-point arrays. Retain the high-precision improved-gamma regression; compensated global sums do not replace these local checks.
5. For the real TimeEval consumer, compare the selected nominal-50 and all-observed states and final AUC under identical endpoint, comparator, parameter, and recall-sort conventions. Report actual threshold counts and any sampled-versus-full changes separately from runtime. Do not infer generic metric fidelity from a flat/cardinality-one consumer alone.

The proof makes the four-bias extension valid. Its publication value still depends on the measured workload benefit and on presenting the classical antecedents accurately.
