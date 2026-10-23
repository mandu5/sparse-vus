# Coherent Sparse VUS paper: frozen-evidence audit

Date: 23 October 2026. Research snapshot: `78974a3387b1600c31d5efaf56341a769d9618cb`. This audit inspected and reconstructed recorded results without executing metric kernels, running benchmarks, changing original receipts, or submitting anything. It is internal verification, not independent laboratory replication or external peer review. Private correspondence and account details remain outside the research artifact.

## Finding

**The older whole-method performance result is supported by the retained evidence.** Both hosts completed 924 tasks on 308 series from 17 families, and the frozen exact-radix primary criterion passes against all five required controls on each host. This audit reconstructed both reports, independently recomputed the ten primary host/control confidence-interval pairs from raw measurements, and reproduced the manuscript fragment exactly.

This result concerns the support-sensitive exact radix evaluator. It is distinct from the later active-prefix study, whose three primary runtime criteria fail. A coherent paper can report both findings without contradiction: substantial benefit from the complete support-sensitive evaluator, followed by a conditional refinement whose overhead defeats its primary incremental criterion.

No prior-publication or substantial scientific-overlap blocker was identified in the specifically checked earlier manuscripts. That is a bounded finding, not proof that the complete current manuscript has never been submitted or published anywhere. The stored Sparse VUS submission packet records no external submission receipt as of 21 October; current account state was not authenticated in this audit.

## Exact evidence chain

The 308-series results in [paper/main.tex](../paper/main.tex) come from [paper/pr_engine_results.tex](../paper/pr_engine_results.tex), included at the main results section. [paper/results.tex](../paper/results.tex) only defines older 350-series/1,050-score summary macros; it is not the source of the 308-series holdout result. A combined manuscript should not silently substitute those populations.

| Evidence | Mac | Linux |
|---|---|---|
| Run directory | [artifacts/pr-engine/mac-holdout](../artifacts/pr-engine/mac-holdout/) | [artifacts/reproductions/linux-pr-engine-39523992616](../artifacts/reproductions/linux-pr-engine-39523992616/) |
| Frozen method/input specification | `protocol.json`, `inputs.json` | `protocol.json`, `inputs.json` |
| Raw timing and numeric outputs | `measurements.jsonl` | `measurements.jsonl` |
| Completed independent-code reconstruction | `audit.json` | `audit.json`, with subsequent `audit-rechecked.json` |
| Structured and readable reports | `report.json`, `report.md` | `report.json`, `report.md` |
| Transport/provenance receipts | Local run bindings | `github-artifact-receipt.json`, `archive-verification.json`, `verification-receipt.json`, `report-ci-receipt.json` |

“Independent-code reconstruction” means a separately implemented checker inside the same agent workflow. It does not imply an external research team.

The pre-run source commit is `91696f79726ca83973cbda834e4ecf60c28441c8`. This audit checked all 14 tracked measured files against that Git object and the research snapshot: all match their protocol hashes. The two pinned external source files also match locally, for **16/16 measured-source identities**. The report and auditor identities match their receipts.

| Bound object | SHA-256 verified in this audit |
|---|---|
| Mac `protocol.json` | `5417a38ec43cc4471e17a0ca7d6af0b11ef448689042a1c5dec4fa8ef2dffb07` |
| Linux `protocol.json` | `838c23163326fc1a71c3f2fbbc1a8245ed6f489d11b94a7c6d00d3cb2661bd45` |
| Both platforms' `inputs.json` | `783d6ec769682c8b0735fe4f4a17591ab4de042b2f2907e8ffbecbcc74690cd6` |
| Mac `measurements.jsonl` | `499f69e0e767f0c4971b8cc9cd839e3eedec3cb20f945b1cc6221f2604dd3228` |
| Linux `measurements.jsonl` | `a54fd4ec9107e2b9517b455d221c9f6dfbc7ae6f1f84070f0cb6a37ddbc62060` |
| Mac `audit.json` | `a9d44deb51fa3d764a923a52217012498a574847ebee798ddf343f1e90f0d28f` |
| Linux `audit.json` | `577dab610dd482defcdaa55996e9a71281e8ccccb9420b680790f41ab2b69708` |
| Mac `report.json` | `c72f2df666c49e58c7deb7fec72dc10d9d3bddcdcb05602fb787ac09c62af2aa` |
| Linux `report.json` | `46c6fba361e4e9f021781a08dd72050b43df8ded160883e35ed6a3594355f837` |
| `experiments/audit_pr_engine.py` | `d0def03dc7b7b7f90a8d879ce1b1aa400390111072a504c5e4bd3482b2c07fc0` |
| `experiments/report_pr_engine.py` | `8bdb7290d845837a69521ee7fc6375b55c4ef781016dd1d93d9e9c40917e10bb` |
| `experiments/build_pr_engine_paper.py` | `69f2d11b757209122ccc09e0f174df84eb9325658e6f53fe4395dfa6ef9689ab` |
| `paper/pr_engine_results.tex` | `e03f24e19114a05d3928f1f870bf5aa4072388676feabcfe7506d03313166ee9` |
| `paper/pr_engine_results.receipt.json` | `a2f38de2927114245640354b3d54282c569c61ef9fea04e01e1baf8a5d3564aa` |

The retained GitHub receipt identifies [Linux run 39523992616](https://github.com/mandu5/sparse-vus/actions/runs/39523992616), artifact `12315563163`, and original ZIP digest `8dd17716ce273e8ba02fbcdbc5f692aa4ed429b15fce7a8a40f0963946283ead`. All ten retained original members match the recorded byte sizes and SHA-256 values in this audit. The remote ZIP was not downloaded again, so its current availability and expiration status are not refreshed here. A later [report-verification run 39533404287](https://github.com/mandu5/sparse-vus/actions/runs/39533404287) is recorded in `report-ci-receipt.json`; its report hash matches the current retained report.

## Population, task, and timing units

- The population is the **308-series procedure holdout** from the previously studied 350-series corpus; 42 series were used for development. It is not a new external-domain dataset.
- The holdout contains 17 represented families, not all 23 families in the original corpus: Exathlon, IOPS, LTDB, MGAB, MITDB, MSL, NAB, NEK, OPPORTUNITY, SMAP, SMD, SVDB, Stock, TODS, UCR, WSD, and YAHOO.
- Each task is **one series, one maximum width, all three model score vectors, and best-PR selection with numerical ties retained**. Models are TimeMoE-200M, Chronos-Bolt, and TimesFM, identified in the receipts as `TimeMoE-200M_64`, `bolt_base_64`, and `timesfm-1.0-200m_64`.
- Thus 308 series times three widths gives **924 tasks per host**; it is not 924 independent datasets or 924 single-model calls. Each exact method evaluates three score vectors within each task.
- Width 30 is primary, 100 secondary, and 300 stress. Each task has three warmed serial timing repetitions for each of 14 methods, in the frozen randomized order.
- Timing includes validation, preparation/sorting, metric/controller work, and API result construction. Input loading, imports/JIT warm-up, and receipt serialization are excluded. Sums of case medians are not measured batch wall times.
- Mac used Python 3.12.4, NumPy 1.26.4, Numba 0.59.1 on an Apple M1 Pro. Linux used Python 3.12.15, NumPy 2.5.4, Numba 0.68.0. Both specified one compute thread. **Do not copy the later active-prefix Linux dependency versions into this experiment.** The active user Mac was not isolated from background processes.

The frozen input manifests are byte-identical between these two hosts. This differs from the later external active-prefix corpus, whose regenerated score arrays are not all byte-identical across platforms.

## Primary result reconstructed from raw records

The exact-radix decision requires numeric correctness and both the geometric-mean ratio and aggregate-ratio **lower 95% family-cluster bootstrap bounds above one against each of five controls**. Ratios are comparator time divided by `radix_pr` time. The bootstrap uses the 17 observed families, 2,000 resamples, and seed `2026102102`; entire family clusters are resampled, not individual timing repetitions.

The following values were independently recomputed or checked against the raw rows in this audit. Lower bounds are rounded for display; the checks used unrounded values.

| Host | Required control | Median ratio | Geomean lower bound | Aggregate lower bound | Faster / slower |
|---|---|---:|---:|---:|---:|
| Mac | Sparse comparison PR | 1.774311 | 1.420785 | 1.510731 | 271 / 37 |
| Mac | Dense direct PR | 3.330838 | 2.772137 | 3.348852 | 306 / 2 |
| Mac | Dense nearest ROC+PR | 5.049976 | 4.355938 | 4.974234 | 308 / 0 |
| Mac | Dense direct radix PR | 2.676501 | 2.317683 | 2.751592 | 303 / 5 |
| Mac | Dense nearest radix PR | 2.598515 | 2.297031 | 2.624467 | 307 / 1 |
| Linux | Sparse comparison PR | 1.986675 | 1.839007 | 1.744727 | 304 / 4 |
| Linux | Dense direct PR | 4.894056 | 3.169972 | 4.241058 | 308 / 0 |
| Linux | Dense nearest ROC+PR | 6.916549 | 4.639449 | 5.687771 | 308 / 0 |
| Linux | Dense direct radix PR | 4.418626 | 2.904108 | 3.793728 | 308 / 0 |
| Linux | Dense nearest radix PR | 4.790513 | 3.142138 | 3.933473 | 306 / 2 |

Both complete required-control intersections therefore pass. One required control computes both ROC and PR; the two **PR-only radix dense controls** are the fairer mechanism comparisons for separating support-event savings from generic ranking and output-work differences. Passing the intersection does not mean every individual case is faster.

Across all 924 recorded tasks per host, the largest PR discrepancy against the comparison-sort sparse reference is `1.5543122344752192e-15` on Mac and `1.3322676295501878e-15` on Linux, below the frozen `1e-11` tolerance. This audit recomputed those maxima from every exact method's recorded three-model outputs and checked the recorded selected-model sets. It did not recompute any VUS value from source scores.

The two other decisions, `primary_decision` for `fast_race` and `radix_racing_decision` for `fast_race_radix`, are **FAIL on both hosts**. The generic field name `primary_decision` must not be confused with `radix_primary_decision`, which is the explicitly frozen main exact-radix hypothesis in protocol v3.

## External comparisons and limits

At width 30, the released Klein PR-only comparator has median ratios `20.924899x` on Mac and approximately `14.538x` on Linux, with `308/308` wins on each. Benchopt ratios in this older experiment are approximately `35.420x` and `21.493x`, but Benchopt computes both ROC and PR while the reference is PR-only. Both external comparisons are **descriptive and outside the five-control primary decision**.

The pinned Klein revision is `1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00`, with source SHA-256 `15b7afb94da0e1f1b1c408fe44b937d910935c19f8eb76f42ae6719f9cfcb52b`. Benchopt revision is `2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94`, with source SHA-256 `298c746c84a28f9296b015bd70eac984d27be5452e3ca42c853de05328c194a8`. Both are configured for exhaustive thresholds in the retained protocol. External source files were read from the existing local cache; they were not modified or redistributed.

The descriptive fastest PR-only control oracle gives median ratios `1.709001x` and `1.985693x`, with **40/308 Mac losses and 6/308 Linux losses**. It is selected after measurement, has no confidence intervals, and is not a deployable method selector.

The later paired active-prefix supplement's Benchopt median `34.918x`, DTAI completed-subset median `101.106x`, and released-paired-radix median `1.017x` belong to a **different 48-score-vector external study**. Do not merge their units, sample counts, or ratios with this three-model 308-series study. The large external ratios support whole-implementation utility; they do not isolate the active-prefix increment.

## Verification performed on 23 October

1. Hashed the original protocol, input, raw-record, audit, report, measured-source, and manuscript-builder files; checked report bindings and both source commits.
2. Called `report_pr_engine.build_report()` in memory for each complete run. Reconstructed reports matched their retained counterparts after excluding only creation timestamps; floating fields used the reporter's `1e-12` absolute/relative comparison tolerance. This checks all report point estimates and negative-case lists; it normally copies confidence intervals from the bound audit.
3. Separately reconstructed the primary family-bootstrap intervals directly from raw rows using the frozen sampling specification. All ten host/control comparisons matched the recorded intervals to `1e-12`; all twenty lower-bound tests exceed one.
4. Independently checked every raw timing median/repetition count and every exact method's three-model PR outputs and selected-model set. Recomputed maximum discrepancies match the retained reports.
5. Reconciled the immutable release split and score/label identities through `validate_inputs_manifest(..., verify_members=False)`. The metadata result agrees with the existing full audit except that **source ZIP members were not reread in this pass**.
6. Called `build_pr_engine_paper.render()` in memory with both original report hashes. Its output exactly equals the committed `pr_engine_results.tex`. Builder, validator, and output hashes match `pr_engine_results.receipt.json`.
7. Checked all ten retained Linux archive-member files against their prior archive receipt. No remote archive or data source was redownloaded.

This was a small receipt/statistical reconstruction, not a timing rerun. It does not re-establish the original source ZIP bytes, reproduce host performance, validate figure pixels, prove all-input numerical exactness, or certify a new manuscript that changes the algorithms or claims.

## Prior-paper and submission-history boundary

A separate private overlap review inspected earlier contribution statements and
preserved source identities. The inspected work addressed different scientific
questions; no accepted overlapping exact-VUS algorithm paper was identified.
That bounded check is not a complete current publication/account search, and it
does not establish disjoint raw data. Current author-level declarations remain
part of the private submission workflow. Unpublished software is cited in the
manuscript with its public release chronology.

## Integration recommendation

Use the coherent progression **exact event representation → support-sensitive/radix evaluation → active-prefix refinement**. Cite the earlier public software and preserve version chronology. The primary empirical account can accurately say that the support-sensitive radix evaluator passed its five-control criterion on the 308-series procedure holdout, while the later active-prefix increment failed its own primary criterion and helped at secondary widths.

Keep the old three-model selection tasks, later single-score metric calls, and paired external supplement in separately labeled experiments. Keep the failed racing results as limitations of that optional branch, not evidence that the exact evaluator failed. If the new tie-handling algorithm changes the measured method, these frozen timings describe the historical method only; correctness tests or a new theorem cannot retroactively supply runtime evidence for the changed implementation.
