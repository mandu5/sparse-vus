# Independent range-sweep code and feasibility review

Date: 2026-10-24, 03:56 UTC. This reviews the new range-metric prototype, not the VUS manuscript or its previous scores. I did not read another internal review or its score. The primary timing study was running at this cutoff; I inspected no timing outcomes and ran no computations during that timing run.

**Judgment: algorithmically feasible for the declared flat, reciprocal-cardinality metric on real binary64 inputs. I found no correctness blocker in the frozen endpoint or query-bucket updates.** The fused compiled raster is now a credible simple control. This judgment is limited to algorithmic feasibility; speed, novelty, detector accuracy, and publication readiness require their own evidence. The largest unresolved technical issue is the numerical contract: algebraic equivalence does not guarantee bitwise curves or identical maximizing thresholds, and the present API accepts some inputs whose meaning changes during binary64 coercion.

## Reviewed snapshot and verification boundary

The frozen protocol is `artifacts/pvldb-research-20261024/range-sweep/main-study/protocol.json`, dated `2026-10-24T03:52:37.263312+00:00`. Its core and producer hashes match the files I inspected:

| File | SHA-256 |
|---|---|
| `src/sparse_vus/range_sweep.py` | `2e75e1afd2b86d4450afc43aaba3a892fd998f4fd5cfe7edda2b155bba479ccb` |
| `tests/test_range_sweep.py` | `88c0c67cf65af04d4a237ce37a7e5f094c3b86d0517070ad89e5eb5e39a49674` |
| `experiments/range_sweep_study.py` | `74ea8b546ef1de8384a15e675d6584616011092e4b2eb887c0b3531ed237e57c` |
| `experiments/audit_range_sweep_study.py` | `2c4711f9f58ce5a6bc521eb3bf7a0d5a956464fc82acbc5f1719c5d534809377` |

Before the fused-raster and bucket revisions, I independently ran `python -m pytest -q tests/test_range_sweep.py`: 14 passed. That execution validates the earlier three-method snapshot, **not an independent execution of the frozen four-method snapshot**. The author reports passing tests after the revisions; my final-snapshot assessment is static because serial timing had begun. The current test source contains a set-intersection oracle independent of candidate preprocessing, exhaustive binary labels and ternary tied scores for lengths 1–4, random arbitrary query order with duplicates/infinities and alpha in `{0,.2,1}`, and explicit parser-compatibility corners (`tests/test_range_sweep.py:10–75`). This is useful semantic coverage, not a long-input numerical-error bound or an all-input proof.

## Mathematical target and update invariants

For a threshold `t`, predictions are exactly `x[i] > t` after the API's conversion to binary64. Let the true intervals be `T_j`, predicted intervals be `P_l`, and their counts be `K` and `J`. Write `m_j` for predicted mass inside `T_j`, `c_j` for the number of predicted intervals meeting `T_j`, `u_l` for true mass inside `P_l`, and `h_l` for the number of true intervals meeting `P_l`. The standard target is

```text
R = (1/K) sum_j [alpha * 1(m_j > 0)
                 + (1-alpha) * m_j / (|T_j| * c_j)],
P = (1/J) sum_l u_l / (|P_l| * h_l),
F1 = 2 P R / (P + R).
```

An empty outer collection or a zero-overlap term contributes zero. These are flat positional rewards and reciprocal cardinality; this code does not implement arbitrary positional weights or cardinality functions.

The implementation supports the following proof sketch.

1. **Endpoint information is sufficient.** When an inactive position `i` is inserted, an active `i-1` must be the right endpoint of its component, and an active `i+1` must be the left endpoint of its component. Reading `left[i-1]` and `right[i+1]` therefore obtains valid current endpoints. Updating only `left[b]` and `right[a]` for the merged component preserves precisely the information later insertions need. Stale interior entries are never used as endpoints. A disjoint-set structure is unnecessary (`range_sweep.py:110–139`).

2. **The precision sum changes locally.** The code subtracts the contributions of the zero, one, or two old neighboring components and adds the merged interval's contribution. `_component` obtains its true mass from a prefix sum and counts true-interval starts, adding a truth interval already in progress at the left endpoint. This implements `u_l/(|P_l| h_l)` in constant time. Updating `pc` by `1-left_active-right_active` gives the correct denominator (`:35–43`, `:111–122`).

3. **Only one truth interval's recall term changes.** If `i` lies in `T_j`, its predicted mass increases by one and its number of predicted fragments changes by `1` minus the active same-truth-interval neighbors. Replacing its old overlap term by the new one and incrementing the existence count on its first hit is correct. Inserting outside every truth interval cannot merge two fragments within the same contiguous truth interval. This justifies leaving all recall terms unchanged on a negative-label insertion (`:123–138`).

4. **Queries and ties preserve the prediction set.** The score sweep processes every point with score strictly above the current descending query before emitting a result. Equal-score points may be inserted in any internal order because no output is emitted partway through a tied group. Sorting/restoring the queries handles arbitrary order and duplicates (`:106–107`, `:212–220`).

5. **Query buckets can reuse the same kernel.** With ascending queries, `searchsorted(..., side='left')` counts queries strictly below a score. Thus `H-count` is the first descending query at which the point is eligible. Counting-sort groups points by this index. Scores need not be ordered inside a bucket: all members become eligible at the same query, and the next noneligible bucket stops the existing while-loop. Index `H` contains points eligible for no supplied query. Duplicate thresholds, exact score/threshold ties, and infinite thresholds are consistent with this construction (`:180–193`, `:215–218`). This is standard offline query grouping; the implementation by itself establishes no novelty claim.

The revised raster is also coherent. Its per-query pass maintains predicted-run mass and truth-overlap counts together with truth-run mass and prediction-overlap counts. A new true interval or a new predicted interval increments the relevant intersection count exactly once. End-of-run flushes use the correct lengths, including intervals ending at the final position (`:46–92`). It no longer allocates per-threshold truth-interval arrays or performs candidate prefix lookups.

The `tsb_compat` exceptions agree with the inspected pinned TSB-AD source: its all-one range parser returns no intervals, while existence rewards inspect the raw prediction raster. Consequently all-one truth gives zeros; nontrivial truth with all-one prediction gives `P=0`, `R=alpha`, `F1=0`. The ordinary interval definition gives different answers and is correctly the default. Relevant cached public-source locations are `.cache/tsbad-consumer/pkg/TSB_AD/evaluation/basic_metrics.py:23–26,44–77,257–276,362–381,542–557`. This is source-level semantic comparison, not a newly executed public-reference parity experiment.

## Complexity and strength of the control

Let `n` be the sequence length, `H` the supplied query count, and `K<=n` the number of true intervals. The following are worst-case bounds for the current arbitrary-query API, including validation and method-specific preparation; output storage is included. They assume array indices and integer products fit their machine types.

| Method | Time | Memory |
|---|---|---|
| Vectorized `prefix` | `O(nH+n+H)` | `O(n+H)` |
| Fused compiled `raster` | `O(nH+n+H)` | `O(n+H)` for the public call; `O(1)` reducer state besides output |
| Score-sorted `sweep` | `O(n log(n+1)+H log(H+1)+n+H)` | `O(n+H)` |
| Query-aware `bucket` | `O(n log(H+1)+H log(H+1)+n+H)` | `O(n+H)` |

The `H log H` term must be retained for the current arbitrary-query wrapper; `O(n log H+n+H)` requires preordered queries or another stated condition such as `H<=n`. The kernel's endpoint updates themselves take `O(n+H)`, with no inverse-Ackermann factor. `_validate` copies labels, scores, and queries (`:19`), so the raster's constant reducer space must not be described as constant total API memory.

For fixed `H=100`, the raster and bucket have linear growth in `n`, while comparison-sorting all scores costs `O(n log n)`. There is no universal asymptotic advantage for the score-sorted sweep in this regime. For `H` proportional to `n`, the conventional raster becomes quadratic and the sweep has a clear algorithmic advantage. Actual constants, ties, and short inputs still need measurement. The distinct-query producer also constructs `np.unique(scores)` inside every timed call, so that query-generation cost is paid by both methods.

The current raster is a substantially stronger comparator than a Python/vectorized implementation alone: it uses the same compiler, fuses the scan, has constant reducer workspace, and receives only validated `y,x,t`. Only methods needing truth intervals and prefixes pay `_prepare` (`:204–209`). The bucket is an appropriate additional simple control against unnecessary score sorting for a small known query set. These changes remove the principal baseline concern raised during review. Obvious future engineering, such as sharing label preparation across eight score vectors, is separate from the presently frozen single-profile API composition.

## Remaining findings and falsifiable follow-ups

1. **The input contract is narrower than validation currently suggests.** `_validate` checks the incoming arrays and only then casts scores and thresholds to float64 (`:11–19`). On the earlier snapshot, whose validation is unchanged, I directly observed that complex scores are accepted and their imaginary parts discarded with a warning; integer scores `[2**53,2**53+1]` at threshold `2**53` collapse to one binary64 value and lose the original integer strict inequality. This does not invalidate a study on stored finite float64 scores. Before presenting a general exact API, either explicitly restrict its contract to real binary64 comparisons or reject unsupported/coercive cases, including nonfinite values after conversion. Add the two concrete examples as regression cases when the frozen timing study is over; do not silently edit its source.

2. **Numerical equivalence is tolerance-based.** Kahan compensation protects the accumulated precision and recall sums, but the local change is first formed from rounded divisions and subtraction (`:113–120`, `:125–137`). It cannot recover error already introduced in that local expression. Different activation orders in the bucket and score sweep can consequently differ by rounding. The precision lower clamp also does not establish an upper bound or a certified recall bound. A meaningful later numerical stress check would compare whole curves against direct interval recomputation on long alternating, fragmented, and heavily tied inputs and report maximum absolute error, out-of-range values, and maximizing-threshold disagreements. No such long-input numerical result was independently established in this review. Avoid promising bitwise equality or a length-independent `1e-10` guarantee from the current tests.

3. **Observed strict thresholds are not all attainable masks.** The frozen distinct contract deliberately excludes a threshold below the minimum score. For `y=[1,0,1]`, `scores=[0,1,0]`, both observed thresholds yield F1 zero, while a threshold below zero gives standard `P=1/3`, `R=1`, `F1=1/2`. This is a concrete distinction, not a defect in the declared experiment. Report “maximum over observed strict thresholds,” not the unrestricted optimum over all real thresholds. The protocol's comparison to a TimeSeAD threshold domain does not make alpha `.2` equivalent to an alpha-zero public function; any public comparison must align these parameters explicitly.

4. **The revised curve audit resolves the earlier missing-output concern, with a limited meaning.** The producer now saves a full canonical PR/R/F1 curve for every method/profile/contract and a byte hash for every repetition (`range_sweep_study.py:73–77,108–122`). The auditor validates curve shapes/finiteness, hashes, complete-curve agreement, maxima, recorded maximizing thresholds, and model winner sets (`audit_range_sweep_study.py:48–75`). It reports cross-method winner-set differences rather than assuming them away (`:105–109`). This is a material improvement. It is explicitly not an independent mathematical oracle for all 73 inputs. Also, the returned `max_curve_error` still takes the maximum of producer-supplied fields (`:108`); the auditor separately bounds actual curve differences against the sweep reference but does not return their computed maximum. Report that field with its provenance, or add a separately named reconstructed maximum after preserving the frozen run. The disagreement count is per record, so nonzero counts need that denominator. Identical maximizing thresholds between methods are not asserted: each recorded threshold is checked against that method's own curve, which is appropriate given floating-point ties.

5. **The experiment can support a scoped runtime claim only after completion.** The protocol retains all 73 reused recordings and eight fixed scores, declares the successor study exploratory, includes query construction/preparation/selection in timings, and uses balanced four-method grid orders plus raster/sweep ABBA for distinct queries. It predeclares tolerance and retains losses. The statistical audit uses case medians and equal-label-block sensitivity, with correction over three collections separately for each comparison (`audit_range_sweep_study.py:17–24,76–88`); this is not one simultaneous confidence guarantee over every comparison. Two measurements per method in the distinct contract give limited within-case timing information. Neither those intervals nor reused cases imply unseen-data generalization. The test study and a public consumer comparison must remain distinct evidence.

## Decision for the next research step

Continue the already frozen experiment without changing the core, preserve partial records on any parity failure, and interpret results only after complete coverage and the saved-curve audit succeed. A parity failure, a changed maximizing threshold, or a raster/bucket win is a result to retain, not a reason to exclude an input. The current review supplies a credible correctness argument and a fair simple comparator; it does not supply a measured speedup or a new six-gate research assessment. Scientific significance still requires the separate nearest-prior-art analysis, matched public implementations, and evidence that this metric computation matters in an actual workflow.
