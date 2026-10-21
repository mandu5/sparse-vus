# Independent static review of the PR engine — 2026-10-21

Scope: `src/sparse_vus/fast_racing.py` and `src/sparse_vus/pr_compiled.py`, including the fused quantile traversal, exact completion reuse, winner policy, and resource claims. This is an in-session independent review by a separate AI agent, not external peer review or laboratory reproduction. No timing experiments were run by this reviewer. The root agent owns numerical and benchmark validation.

Reviewed source SHA-256: `fast_racing.py` = `08c292094bb6db85eba681441fc3987d41d3767a70882a0e87c5f0ced91174cf`; `pr_compiled.py` = `60afd9a2bc584bf670500d772552625064cdec01bb00ae76246006c163b70646`. These identify the version with separate adaptive/completion counters and exact remainder reuse.

## Result

No real-arithmetic correctness defect was identified in the reviewed fused p-box traversal or completion path. The arguments below explain why; passing random tests alone is not the basis of this conclusion. The machine-floating-point winner guarantee remains conditional on empirically guarded bounds and is not formal interval arithmetic.

One substantive limitation was identified and acknowledged by the implementer: the endpoint budget bounds metric query counts and retained coordinate storage, but **does not bound wall-clock overhead by a constant factor of exhaustive evaluation**. The current bookkeeping can be quadratic in the maximum width. This must remain explicit in performance claims and analysis.

## Definitions

- `M`: number of candidate models.
- `W=L+1`: number of integer widths.
- `Q=len(pos)`: number of time positions inside the maximum-buffer support.
- `G=len(after)`: number of distinct score values on that support, so `G <= Q <= n`.
- `K`: number of original anomaly intervals.
- `C_m`: coordinate capacity for model `m` after both budget limits.

`Q` and `G` must not be interchanged: preparation and geometry scan support positions, while precision/recall curves and monotone queues are indexed by distinct support-score groups. Their values differ substantially on tied/discretized inputs.

## Fused PR bounds

For endpoint curves `a` and `b`, define threshold-index CDF envelopes `F_low(j)=min(a.recall[j],b.recall[j])` and `F_high(j)=max(...)`. Each is nondecreasing in threshold index. On a merge-free width interval, every intermediate recall CDF lies between these envelopes by the width-monotonicity theorem. Precision is pointwise enclosed by the endpoint minima and maxima.

For a probability coordinate `z` between endpoint breakpoints, the allowed quantile indices range from the first `j` with `F_high(j)>z` through the first `j` with `F_low(j)>z`. The implementation's `left` and `right` loops compute precisely these indices. Strict `>` versus `>=` only changes breakpoint values on a set of measure zero. Both pointers advance monotonically; `left <= right` follows from `F_high >= F_low`. The stored final recall is one, so while `z<1` a valid next breakpoint exists and the loop progresses.

The minimum queue keeps indices in `[left,right]` ordered by increasing endpoint precision minimum; the maximum queue keeps the analogous decreasing maxima. Each threshold index is inserted once, dominated tails are removed, and expired heads are discarded. Popping equal values retains the newer valid representative and does not change either extremum. Both queues need at most `G` slots. The next probability breakpoint is the smaller current envelope value; integrating the queue-front extrema over its positive span yields the same lower/upper expectation bounds as separate p-box traversals. Complexity per call is `O(G)` time and `O(G)` temporary queue storage.

These statements require finite normalized nondecreasing recall arrays. `_pr_curve` applies a cumulative maximum and sets final recall to one before exposing them. This stabilizes computed coordinates but is not a proof that all floating-point perturbations are smaller than `1e-12`.

## Merge partition, ties, and width reuse

For consecutive original intervals ending at `b` and starting at `a`, overlap begins when `2*floor(w/2) >= a-b`. The first such width is `2*ceil((a-b)/2)`, exactly the implemented `2*((a-b+1)//2)`. Splitting immediately before these cuts keeps interval count fixed within every block. Adjacent but nonoverlapping integer intervals remain separate under the official target.

Every expanded interval contains an original positive position; all original positives occur in `pos`. Therefore each segment's first-hit sentinel is replaced by a valid support group before indexing `hit_group`, including widths zero/one and boundary clipping.

Support groups admit complete score ties together. `after[g]` counts every original score at least as large as the group's score, including off-support negatives. Omitting intermediate unsupported thresholds preserves PR because their recall increment is zero; the next supported group's precision uses the complete threshold count. This is specific to right-endpoint PR and does not mean that intermediate false positives may be ignored in ROC.

An active unresolved interval has evaluated endpoints and no previously evaluated interior endpoint. Splitting at its strict midpoint introduces one new width and replaces the parent interval with two subintervals. `_read_endpoint` also returns immediately for an already-known scalar. When the capacity is exhausted, `_sparse_pr_complete` checks each slot and computes only NaNs, reusing preparation and scratch arrays; `_finish_model` then removes all pending interval entries. Existing endpoint scalars remain unchanged. Thus each model incurs at most `W` metric-width evaluations; no exact fallback restarts the public evaluator. The separate counters should sum to the number of unique evaluated widths.

## Winner and tie policy

A strict winner is accepted only when its lower bound exceeds every competitor's upper bound by more than `3e-10`. The final exact winner set includes every candidate within `1e-10` of the exact maximum. A model excluded by `upper < best_lower - 3e-10` cannot belong to that tie set under valid enclosures. Candidates are rescreened from current bounds, so a transient numerical change does not create an irreversible removal. When no candidate has an unresolved width, the final selection is over exact scalar means.

The margins provide separation between pruning and the declared tie tolerance; they do not independently bound floating-point error. Near-boundary score differences smaller than the numerical error envelope need special care. Documentation's `ordering_scope="numerically_audited_not_formal_float_certification"` accurately limits the machine claim. A proof of the real-arithmetic algorithm should not be presented as a directed-rounding certificate.

## Resource limitation requiring disclosure

Each coordinate array occupies `16*C_m*G_m` bytes (two Float64 curves per endpoint). The cap is per model, not a cap on process RSS. Other persistent arrays include model-by-width scalars, slots, interval rights and interval lower/upper bounds: `O(MW)`. Prepared geometry/ranks occupy approximately `O(sum_m(Q_m+G_m+K))` plus input data; preparation creates additional `O(n)` temporary arrays. Width and p-box kernels use `O(Q+G+K)` or smaller scratch storage, and result construction has its own small Python allocations. Report measured peak RSS separately from retained coordinate bytes.

`_all_bounds` scans all `M*W` scalar/interval entries on every refinement. Selecting a model scans `M` entries; selecting its interval scans `W`. There can be `Theta(MW)` adaptive steps when a fixed positive fraction of widths is retained, so the bookkeeping alone has an `O(M^2 W^2)` upper bound. This is not only a proof artifact: identical perfectly ranked models can have exact endpoint PR bounds of one, yet the current policy continues refinement because it requires exact completion for an unresolved tie. For small `G`, repeated full-array scans may dominate cheap metric evaluations. The coordinate fraction limits how many of those steps occur, without changing the quadratic worst-case order when the fraction stays fixed as `W` grows.

The implementer acknowledged this limitation during review. Optimizing global accumulators or the interval priority queue would be a separate measured change; no speedup from such an unimplemented change is assumed here. Current claims should say bounded query count / retained curves, not bounded total-runtime overhead.

## Comparison fairness

The mandatory comparison is whole-call cost of selecting among all model scores, including validation/preparation and any exact remainder. Source retrieval, imports and declared JIT compilation warm-up may be outside warm timings, but must be disclosed. Run the compiled exhaustive PR-only controls, actual Klein PR-only implementation and actual Benchopt evaluator; Benchopt computes ROC and PR internally even when selecting its PR result. Treat PR-only versus paired outputs explicitly.

The 308-series partition was included in earlier exact-evaluator reports. It can be held out from this policy's development phase, but is not wholly unseen external data. Freeze implementation and policy parameters before measuring it, report both median speedups and summed latency, and retain regressions. An oracle that chooses the fastest baseline separately after seeing each case is a useful diagnostic, not a deployable dispatcher.

## Evidence boundary

The mathematical review above is static. Scoped adapter/audit verification performed by this reviewer passed 17 tests (a dependency deprecation warning); it concerns external baseline integrity/parity and FF-VUS semantic witnesses, not the full racing engine. The root reports its separately executed engine tests and owns their receipts. The reviewed conclusions do not establish SOTA, publication acceptance, formal floating-point certification, or benefits on every workload.
