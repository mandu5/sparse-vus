# Final adversarial review of the unified Sparse VUS manuscript

Reviewed 23 October 2026. This is an internal scholarly review of the new unified manuscript, not external peer review, acceptance, or a publication clearance. Only this review document was written. No frozen evidence, implementation, or manuscript source was edited by this reviewer; no benchmarks were rerun.

## Assessment

The unified paper has a substantially stronger defensible contribution than the incremental saturation paper alone. Its coherent contribution is the exact support-event representation, including the omitted ROC rectangles and global tie counts, composed with interval geometry and standard ranking; the prefix and run-based constructions are refinements with separately qualified results. The older whole-evaluator primary PASS and the later incremental primary FAIL are different hypotheses and are now reported correctly.

**I found no demonstrated fatal proof error or fabricated performance claim. The coordinating authoring agent corrected the substantive presentation requests below, and I reread those corrections.** No additional mandatory claim correction emerged from this final pass. The remaining scholarly concern is the significance of the evaluator in a motivating data-management workload, not the correctness of the elementary saturation inequality. The latest tied-score contribution has a valid structural result but weak practical evidence beyond constructed compressible ties. Correctness, unusually detailed receipts, and candid failures do not settle that significance question or establish a strong acceptance prediction.

## Prioritized review requests and final disposition

The requests below retain the initial findings so the changes are reviewable. The absolute-time, tolerance, abstract-balance, independent-check, count-notation, and DTAI-attribution requests are now resolved in the manuscript. Only the explicitly optional wording cleanup and the substantive research-significance concern remain.

### P1 — Make the practical scale inspectable with absolute times

**Resolved for the existing evidence.** The body now includes `paper/sparse_vus_absolute_results.tex`, with width-30 and width-300 sums for both hosts and an explicit exclusion of batch-wall-time or detector-pipeline claims. I checked these values against the frozen reports and checked the output/generator/frozen-fragment hashes in `paper/sparse_vus_context.receipt.json`. A motivating-workflow experiment remains additional research, not an unfulfilled correction to a claimed result.

Locations: `paper/sparse_vus_body.tex`, whole-evaluator experimental design and results; the included `paper/sparse_vus_engine_results.tex` (a layout-only copy of frozen `pr_engine_results.tex`).

At review time the unified paper reports extensive ratios but no absolute task-time context. A 20× ratio is insufficient to assess whether the operator saves milliseconds, minutes, or material collection-level effort. This weakness is especially relevant because the introduction explicitly excludes ingestion, score generation, and downstream model-selection work.

**Concrete correction requiring no new benchmark:** add the recorded median complete-task times and/or sums of case medians for the main candidate and closest matched control, keeping the sum explicitly separate from a measured batch. The retained `report.json` files give, at primary width 30:

| Host; 308 three-vector tasks | Sparse radix | Nearest dense radix PR | Klein PR |
|---|---:|---:|---:|
| Mac median task, ms | 3.736 | 8.737 | 91.541 |
| Mac sum of task medians, s | 3.094 | 10.204 | 60.186 |
| Linux median task, ms | 2.248 | 10.717 | 29.519 |
| Linux sum of task medians, s | 2.318 | 11.610 | 26.032 |

These values were read directly from `groups["30"].methods` in the frozen Mac/Linux reports. A median of paired ratios need not equal a ratio of these marginal medians; the existing reported ratios should remain unchanged.

For a stronger practical-impact claim, explain why exhaustive evaluation and the selected widths arise in a real analysis task. A measured collection workflow or a measured share of evaluator time would strengthen that claim, but the current manuscript does not claim to have such an experiment. Do not convert sums of separately timed calls into an end-to-end application result. This is a research-significance recommendation, not a claim that the venue mandates a DBMS implementation or a particular new experiment.

### P1 — Put the whole-evaluator correctness and selection tolerances in the paper

**Resolved.** The whole-evaluator design now states absolute parity tolerance `1e-11` and selected-model tie tolerance `1e-10`.

Locations: `paper/sparse_vus_body.tex`, whole-evaluator paragraph describing the frozen tie convention and five-control decision.

The task includes returning a best-PR model set under numerical ties, but the paper delegates the numerical convention to the artifact. That convention affects the task's answer and belongs in the main description. The frozen Mac protocol explicitly records `exact_parity_tolerance = 1e-11` and `tie_atol = 1e-10`.

**Concrete correction:** state both the absolute PR-agreement tolerance and the model-selection tie tolerance. Distinguish them from exact equality of mathematical integrals. This improves the self-contained specification without changing any historical decision.

### P1 — Keep the new tie-run result balanced on the first page

**Resolved.** The abstract now states that run aggregation helps structured large ties but does not broadly improve the measured corpus-score runtimes. The body still retains the 0.857×/0.835× medians and loss counts.

Locations: abstract, `paper/tie_run_results.tex`, conclusion.

The abstract's tie-run sentences are mathematically qualified and do not explicitly claim a runtime win. Nevertheless, the title and first page elevate complete ties as a central advance, while the first page currently gives no empirical outcome for that new candidate. The body correctly reports 8.816× versus active prefix on the all-tied singleton at width 2048, but also 0.857×/0.835× at width 300 on reused development/external cases, with 16/21 and 14/16 losses.

**Concrete correction:** add one short abstract or conclusion qualification that run aggregation helps structured, compressible ties in the constructed study but is slower on most reused width-300 cases. Do not promote the constructed 8.816× as a general expected gain, and do not assign the older 308-series performance to this new implementation. No new runtime selector is established.

This is a balance/significance concern, not a finding that the current abstract asserts a false speedup. The body already preserves the relevant negative evidence.

### P2 — Report the candidate's independent numerical checks in its own validation paragraph

**Resolved.** The generated tie-results fragment now reports the 650 dense and 36 Decimal-80 checks, the prefix/subtraction/counter checks, and their separate scope. Displayed maximum errors are rounded upward to `3.34e-16` and `2.60e-16`.

Location: immediately after the 131-case tie-run agreement/work result, or a nearby numerical-validation paragraph in the unified body.

The tie-run results presently describe agreement with released radix. The new `artifacts/tie-runs/independent-audit-20261023.json` supplies stronger, separate evidence: 650 randomized dense-oracle cases, maximum difference `3.3306690738754696e-16`; 36 complete-integral cases using 80-digit Decimal arithmetic, maximum absolute error `2.590520390792031927655140559E-16`; exact checks of 150,000 prefix entries; and 20,009 synthetic accumulator subtractions.

**Concrete correction:** briefly report the 650 and 36 cases with their separate units and retain a receipt pointer. Do not add them to the 131 benchmark population, describe Decimal-80 as exact symbolic arithmetic, or describe internal separate implementations as independent laboratory replication. I inspected this receipt; I did not rerun the audit or benchmarks. The source hashes in the receipt bind the checked candidate.

### P2 — Remove an avoidable collision in the stopping-certificate notation

**Resolved.** The integer lemma and proof now consistently use `D` for non-original active positions, leaving global `C(t)` unchanged.

Locations: `paper/sparse_vus_body.tex`, target definition; `paper/tie_run_method.tex`, integer saturation lemma.

The target uses `C(t)` for all globally predicted positions. The tie-run lemma locally redefines `C` as admitted non-original active positions. The local definition makes the lemma mathematically correct, but the certificate would be invalid if read with the earlier global `C`, since inactive predictions supply no buffer mass.

**Concrete correction:** rename the lemma's non-original active count to `D` or another unused symbol throughout the certificate and its proof. Keep the global prediction counts in the event-integration formulas distinct.

### P2 — Finish attribution and presentation cleanup

**Material items resolved.** DTAI is cited; the redundant heading is removed; the layout copy preserves the original engine-result content. The remaining wording suggestions below are optional precision improvements, not mathematical or evidence defects.

- Cite `dtaianomaly` at the first DTAI supplement mention. The bibliography entry exists but was uncited in the reviewed source, leaving a named measured implementation without its bibliography attribution.
- Prefer “maximum-buffer support size” for `Q` in the abstract and “matched nearest-distance dense radix” for the specific abstract comparator.
- Prefer “reused corpus-score results” to “real-score results” if the latter could imply every source series is nonsynthetic; the corpus limitations already acknowledge synthetic and reused sources.
- The coordinator has already removed the redundant parent subsection immediately preceding the tie-run fragment and made the older engine tables/figure span both columns through a layout-only copy. Do not modify the frozen result fragment to achieve formatting changes.

Unused bibliography keys are not missing references: `boxer`, `esa2024`, `troffaes2011`, and `utkin2009` are leftover entries that BibTeX does not render unless cited. They may be removed from the new bibliography for clarity; no citation should be invented merely to use them.

## Claims that survived this review

### Exact target and operation counts

The inactive-threshold lemma preserves the relevant state, adds the horizontal ROC rectangle, and retains complete global ties. The example with `y=(1,0,1,0)`, `s=(3,2,1,0)`, `L=0` correctly gives 0.625 for the pinned dynamic target: the existence factor makes recall 0.25 after the first original, so the ordinary binary-AUC value is not the applicable answer. Simply reconnecting the support endpoints gives the stated erroneous 0.8125.

The two-distance lemma follows from every active ramp having weight at least `1/sqrt(2)`, so two contributions clip to one. The comparison-based and fixed-binary64 preparation statements charge ranking/global counts, and the latter explicitly disclaims arbitrary-real linear sorting. The active-prefix bound accounts for activation, component unions, complete terminating ties, and the width loop; it does not hide a per-width full-support or component clear. The two-original separating family is an operation-count witness, not a real-data frequency or timing result.

A second internal reviewer independently checked the tie-run proof and its implementation. For `K=1`, after `q=A+D >= 3P0` admitted active positions, `D >= 3(P0-A)` implies the integer certificate; support exhaustion also certifies because all originals have been admitted. Each visited active class adds at least one position, giving the claimed complete-class bound without limiting tie cardinality. All stored maximum-support runs of each visited class are actually charged, including inactive runs. Alternating score patterns remain an explicit adverse case. The run-sensitive bound is not a universal linear bound for arbitrary tied arrangements.

### Numerical scope

The three-limb range is sufficient under the stated domain: each `2^52 q_j` is an integer below `2^84`; at most `2^63-1` such terms give a prefix below `2^147`. The reconstruction exponents 76, 12, and -52 follow from the limb representation. The local factor count supports `gamma_8`, or `gamma_6` when index/width conversion is exact; positive sequential summation of `t` fragments gives `gamma_(t+7)` under its stated condition.

These are local rounded-root mass bounds. They do not propagate through recall/FPR ratios, signed ROC increments, integration, and averaging to an all-input scalar error certificate. The manuscript says this explicitly. Integer stopping certifies a sufficient exact mass/coverage condition; it does not make the remaining floating arithmetic exact. I found no need to retract the local proposition, and no basis to upgrade it to end-to-end correct rounding.

### Empirical units and negative findings

The whole-evaluator workload is correctly 308 series, 17 families, and 924 series–maximum-width tasks per host, each with three score vectors; it is not 924 single-score calls. The five-control PASS is supported by the separate reconstruction audit. Its external library ratios are descriptive, and the paired-output control is marked.

The later position-prefix workload uses individual score-vector calls, retains all three failed width-30 primary decisions, distinguishes last-positive and released-radix controls, reports losses against the retrospective fastest control, and does not make that oracle a deployable selector. The DTAI median is correctly restricted to ten completed series with two censored cases. Linux-generated external score arrays are not falsely described as an identical-array replay.

The new tie study has 20 constructed plus 111 reused cases. Its `5.56e-16` displayed maximum is an upward rounding of the recorded maximum, not a discrepancy with `5.551...e-16`. Its large constructed gains, fragmentation regression, and real-corpus losses are all retained. Failed optional racing decisions remain visible in the older included result fragment.

### Attribution and publication claims

The manuscript credits support restriction/cumsums, ROC sweeps, recall stopping, radix ordering, reversible updates, union-find, and superaccumulators as existing techniques. The candidate novelty is their metric-specific composition and derived guarantees. Neal's cited [2015 paper](https://arxiv.org/abs/1505.05571) explicitly describes fixed-point superaccumulators, so attribution is appropriate. Prefix range queries or multiword accumulation should not be presented as newly invented.

The software/working-manuscript precursor is explicitly disclosed with its actual release. The current draft does not equate a release, CI pass, prepared packet, or internal review with a refereed publication. The existing evidence audit is bounded: it found no overlapping accepted-paper blocker in the records inspected, but did not establish a complete current submission history. This review did not authenticate venue accounts or make any author-level declaration.

## Strongest remaining rejection argument

The following is a constructed adversarial assessment, not an actual review:

> The paper carefully composes known sorting, support restriction, interval bookkeeping, and range-sum techniques for one VUS definition. Its exact event reduction and matched-control performance are credible, but it does not yet establish that the optimized operator is a material bottleneck in a motivating data-management workload. The new prefix mechanism fails its primary incremental test, and the latest run aggregation mostly loses on reused corpus cases; its strongest asymptotic and measured advantages occur in restricted constructed regimes. The contribution may therefore be useful algorithm engineering without sufficient demonstrated breadth or significance for this venue.

That argument is materially weaker against the unified paper than against an incremental-only paper: the unified support evaluator has a general exact event identity and substantial matched-radix gains, not merely a recall cutoff. A fair review must acknowledge those facts. It remains a real concern because the manuscript's strongest new tied-score result and its strongest broad empirical result belong to different versions and populations.

Current [PVLDB submission guidance](https://vldb.org/2027/submission-guidelines.html) evaluates data-management contribution, substantive engagement with the literature, and motivating application context; the [research call](https://vldb.org/2027/call-for-research-track.html) accommodates algorithmic papers with formal contributions and encourages prototype evaluation. These official sources were refreshed in this review. They support a plausible Foundations and Algorithms fit; they do not establish acceptance or require an end-to-end DBMS. My unresolved concern is the third dimension and overall significance, rather than keyword scope alone.

## Review boundary and reproducibility of this review

Read the new wrapper/body/bibliography and the saturation, tie-run, primary-engine, active-prefix-table, absolute-time, and tie-result fragments; read the coherent evidence, novelty, and venue audits; inspected the old protocol/report fields, the new independent-audit receipt, and the context-generation receipt. A final recursive source-graph scan after the corrections found **zero missing citation keys, zero unresolved reference labels, and zero duplicate labels**. DTAI is now cited; the remaining four unused bibliography entries are harmless. PDF rendering and final layout inspection remain the coordinator's verification task.

Final reviewed source SHA-256 values: `sparse_vus.tex` = `88fb8bbca9e2bc3f9e823133a115e2b5bf8cdbf85571bce0c56956be9168416e`; `sparse_vus_body.tex` = `52f9c08ddbe82895464c1fbd8bbd80fb9879f9dc356be5b8fee30e7588854b72`; `tie_run_method.tex` = `194690d3153018a04cf70df4e9b03d68b5e20e797d928fbdd2bd204d07238dfc`; `tie_run_results.tex` = `d026a08501c7482a226aaf767a0a75dce3f7e21eed30830ab3c19e330d1d1901`.

The OpenReview source page for the cited foundation-model score study returned a browser challenge during this pass, so its live publication metadata was not independently reconfirmed here. The pre-existing evidence/source audit remains the basis for that citation; this review is not a complete new literature search or a claim of global firstness. No new metric values or runtime results were generated by this reviewer.
