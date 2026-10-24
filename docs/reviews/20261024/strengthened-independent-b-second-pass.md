# Independent review B — second assessment, 24 October 2026

This is an **AI-simulated research review**, not human peer review. It updates my initial review after the conventional-control experiments and tied-winner reconstruction. The initial file is preserved. I have not read another simulated reviewer's recommendation or score. The two specifically authorized Mac audit summaries were treated as artifact reconstructions, not as peer-review opinions. I again used static source/record inspection and public sources; I did not run metrics, numerical reconstruction, tests or benchmarks.

**Current assessment:** the two concrete source/evidence defects I raised are addressed. I have not found a new mathematical counterexample or a substantive experimental blocker to the manuscript's now-bounded exact-evaluation claims. The remaining central judgment is the significance of a specialized algorithmic augmentation of established techniques. Final recommendation and score remain withheld until the immutable PDF/evidence snapshot is supplied.

## Resolution of initial findings

| Initial issue | Current status | Basis |
|---|---|---|
| B1: missing closed-form conventional weighted control | Addressed for the measured workload | New `weighted_range_control.py` rebuilds predicted intervals per query, evaluates precision with label prefixes, and traverses ordered true/predicted intersections using closed-form positional masses. It maintains no metric state across thresholds. Its cost includes complete score scanning and preprocessing. Both raster and interval controls are retained, with the faster control varying by workload/host. |
| B2: best tied winner presented as both ends | Addressed | The main text now states the prespecified best-tie definition. The separate post-hoc auditor computes both extrema from saved complete-curve maxima and checks repeat records. Its reports find singleton grid winner sets in all 312 case/semantic combinations on each inspected panel; therefore the two regrets coincide. This has not been relabeled prospective. |
| B3: six-order uncertainty limitation | Retained, appropriately scoped | Intervals remain conditional approximate paired-order summaries. Recording reweighting is separate; MSL's two-recording sensitivity and actual losses remain visible. I do not interpret these intervals as population guarantees. |
| B4: unfinished native/fresh evidence | Addressed for the compiled-control contribution; original public-reference replay still pending | Both-host control receipts report all 144 native workflows complete, full compiled output coverage, and fresh raw-data/score generation on Linux. Original Mac public coverage is explicitly 28/52 per contract; the control study adds none. The other Linux public-reference run has not been used as completed evidence in this assessment. |
| B5: classical-technique/novelty attribution | Substantially clarified, remains a merit judgment | The manuscript now gives constructive component-tree augmentation, pseudocode, an off-label bridge witness, an explicit cardinality-cost term, and a scoped comparison lower bound. It continues to disclaim new sorting, new component trees, generic callback implementation, and universal fastest-evaluator status. |

## What the new evidence establishes

The new control is a credible implementation of the previously missing conventional alternative. I checked the temporal cursor logic in recall: a prediction spanning a later true interval is retained, while completed predictions advance. Each intersection has an explicit closed-form weighted sum. Shared arithmetic helpers do not make this an incremental method; they do mean the separate pointwise raster and rational oracle remain important correctness checks.

The Linux source/input audit records verification of 26 typed inputs and 52 freshly generated profiles, and its complete source-tree receipt records 425 TimeEval files. The live public CI page independently reports successful run `40081512476` at commit `b0063f5`, with the matching conventional-control workflow. I inspected the workflow and replay driver; the driver performs fresh acquisition/generation before either timed study. These are consistent provenance layers, not external independent scientific replication. [Public CI run](https://github.com/mandu5/sparse-vus/actions/runs/40081512476)

The retained operator reports give interval/incremental exhaustive geometric ratios of 7.323/26.339/1.706 on Mac and 12.945/36.149/2.381 on Linux for WSD/Stock/MSL. Those ratios are not necessarily against the faster of both controls: the manuscript correctly retains raster/interval ordering and the individual MSL loss. The control therefore closes the causal ambiguity identified in B1 without supporting a universal per-recording win.

The stronger practical result is complete native exhaustive evaluation: combined raster/bucket is approximately 2.732 on Mac and 2.756 on Linux, while interval/bucket is approximately 3.034 and 3.190. This improvement includes the declared reads, three metrics and CSV write/close. At native default sampling, the corresponding raster/bucket intervals include one on both hosts. The surviving distinction is therefore **useful exhaustive evaluation**, not a general acceleration of default metric pipelines. The older 1.031-fold nine-metric consumer result is still relevant and is not superseded.

These values were read from the audit records and compared with the manuscript, not recomputed by this reviewer. The archive-only Linux reconstruction explicitly does not reverify raw input/source bytes; the CI-side audit does. Their scopes should continue to be distinguished.

## New mathematical material

The `C_gamma(n)` correction is sound. The first two canonical factors use constant arithmetic work; exact repeated squaring supports the improved factor in logarithmically many arithmetic operations. This preserves an `O(n log n)` complete-trajectory upper bound under the stated unit-cost arithmetic model, without claiming constant-cost exact exponentiation or bounded rational bit complexity.

The padded sorting reduction is valid: one true interval with `n-1` distinct positive scores and one negative zero-score point retains both label classes, and recall at each input-associated score reveals its rank. This establishes the comparison lower bound for complete query-associated outputs. It does not establish a new general sorting result, a lower bound for maximum-only queries, or an advantage over fixed-width radix methods. The text says so.

The off-label bridge example is also valid. Adding the middle negative point changes the predicted component's normalization and number of true intervals intersected while leaving each true interval's recall state unchanged. Together with the middle-weight count/moment witness, it makes the required state easier to understand.

## Merit and remaining limits

PVLDB's Foundations and Algorithms flavor permits a conceptual algorithmic contribution with a prototype; a full DBMS is not necessary. The data-management link is substantive because the algorithm accelerates an existing database-published metric and a native evaluation consumer. [Official research criteria](https://vldb.org/2027/call-for-research-track.html)

Novelty remains modest in breadth: this is a carefully derived specialization of offline activation, interval components, prefix sums and local aggregate maintenance. The lower bound and added experiments improve rigor; they do not transform that specialization into a new general algorithmic paradigm. On the other hand, I do not find it fair to dismiss the work as merely a faster compiler implementation: the same-compiler conventional controls and whole-workflow exhaustive gains now demonstrate work avoided by the maintained state.

The adjacent public-review calibration supports precisely this distinction: specialized combinations can have value, but novelty and benefit require explicit attribution and suitable baselines. B1 was material under that standard, and its resolution is substantive. The remaining limitations—two public detectors in the separate panel, only two MSL recordings, repeated physical sources not excluded, narrow default-consumer benefit, and partial completed public parity—limit external generality rather than contradict the scoped algorithm.

For the final snapshot I will check that the figure and abstract use the declared comparator/contracts, both control orderings and losses remain visible, the final public-reference run's outcomes are not silently omitted, the reproducibility entry points match the archived sources, and the PDF satisfies the 12 non-reference-page limit. I am not requesting further outcome-driven cohort enlargement or indefinite benchmarking. [Official submission requirements](https://www.vldb.org/2027/submission-guidelines.html)
