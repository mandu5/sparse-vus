# Adversarial focused-manuscript review — 21 October 2026

**Verdict:** no mathematical blocker was found in the active-prefix theorem,
the complete-tie mass/coverage proposition, the single-interval corollary, or
the restricted singleton input-query lower bound. The manuscript supports a
focused algorithmic claim, with explicitly failed default-width empirical
criteria and positive prespecified secondary results. It does not establish
general optimality, uniform runtime dominance, external peer review, or a
submission-ready human authorship declaration.

This was a static review of the TeX, bibliography, recorded numerical results,
and current primary sources. No build, test, timed call or new metric experiment
was run. The results and structural-results fragments were reread after they
appeared. Root owns the paper; this review changed no manuscript source.

## Actionable findings and their status

| Priority | Finding | Action/status |
|---|---|---|
| Required factual correction — resolved | The first abstract said both 378 development and 144 external cases ran on each of two environments; the evidence contains one development run and two external runs. | The reread abstract correctly says 378 development cases on macOS and 144 external cases on each platform. Preserve that wording. |
| Required numerical scope — resolved | An unqualified maximum PR error below `3.67e-15` excluded the new paired supplement. Its maximum PR error is `3.9968028886505635e-15`; maximum ROC error is `8.215650382226158e-15`. | The abstract now qualifies its error by the three main runs; the supplement states its larger paired maximum separately. |
| Required reference precision — resolved | “Pinned original target” and “our earlier public version” were not directly traceable from the focused bibliography. | Root added the official source/function/revision and the v0.3 software citation. The official `RangeAUC_volume_opt` target with `thre=n` is the relevant contract; other functions in the same source have different denominator/integration choices. |
| Required mechanism wording — text resolved, figure regeneration to verify | The first work figure compared `active_full` visit counts with fastest-of-eight runtime, mixing distinct controls. Such a plot cannot isolate saturation savings. | Text/caption now specify matched full-active runtime and call the relationship descriptive. Regenerate the actual figure from the revised renderer, then verify its axes and source binding. This review did not render it. |
| Reproducibility correction — resolved in text | The first draft omitted CPU/software identities from the paper itself. | Setup now names Apple M1 Pro, hosted AMD EPYC 9V74, Python versions, NumPy/Numba, and one compute thread. These match the inspected environment receipts. |
| Theorem applicability — resolved in text | Counts of single-interval series alone did not establish that their active scores satisfy the distinctness hypothesis. | Results now say interval count alone is insufficient. Do not imply that all seven development/four external single-interval series receive the theorem's no-ties bound. |
| Bibliographic correction — addressed during review | `boniol2025` used incomplete journal metadata. | Use volume 34, article 32, DOI `10.1007/s00778-025-00907-x`; the publisher page verifies this. The author list is correct. |
| Release check, not an algorithm defect | The artifact-availability block asserts public availability at a branch URL. The browser tool could not retrieve that URL in this pass. | Verify the published branch/bundle and every paper artifact before distributing the PDF as a reproducible release. Retrieval failure here is not evidence of absence. Do not fabricate a DOI or publication status. |

The resolved entries are not open blockers. I found no remaining scientific
correctness defect requiring another algorithm change or another favorable
benchmark run. The pending figure/build/release checks are concrete validation
steps after the controlled timing window, not reasons to restart measurement.

## Formal argument audit

**Target and event elimination.** The algebra uses the threshold-dependent
positive denominator `P0+B/2`, not a static soft-label total. Inactive points
cannot alter mass or component hits, but change global prediction counts.
The negative-run rectangle followed by the complete global tied transition
correctly preserves the omitted ROC contribution. The explicit final `(1,1)`
ROC endpoint is necessary. The four-point example's `0.625` area is correct
for the range-existence recall, even though ordinary pointwise ROC AUC on the
same labels/scores would differ.

**Saturation.** `A+B/2 >= P0` is equivalent to the clipped overlap recall
being one, while `H=K_w` makes the existence factor one. Both remain true as
thresholds relax. The suffix identities use signed horizontal ROC increments
and need no fixed-negative-denominator assumption. They hold only after the
complete score tie. Stopping at the last original positive is valid and is
properly included as a matched control.

**Preparation and complexity.** Activation by `floor(w/2)`, reversible
deletion/insertion, strict overlap unions at `ceil((a_next-b_previous)/2)`,
and per-width hit stamps remove the hidden per-width support/component reset.
The bucket cap handles `L >> n`; one activation per support position and at
most `K-1` unions are charged. `J0=P0>=K` absorbs the union work. The
`O(n+Q)` storage claim excludes optional `O(L)` profiles, as stated. Fixed-key
radix preparation is explicitly separated from arbitrary-real comparison
sorting and growing-precision bit complexity.

**Mass, coverage and ties.** Every admitted buffer weight is at least
`1/sqrt(2)`, giving the half-mass increment bound. The earliest simultaneous
mass/coverage prefix is `max(M_w,E_w)`. The complete-tie rounding map and
additive maximum-tie term are valid. For one interval, first active admission
supplies coverage; distinct converted support scores then give the uniform
`O(n+L*P0)` result. Large ties and a delayed second component genuinely prevent
extending the constant-prefix guarantee without conditions. The all-tied
counterexample is correctly restricted to this position-by-position evaluator.

**Restricted optimality.** The boundary singleton adversary has
`n-floor(L/2)-1 >= n/4` off-support positions for `n>=4, L<=n`. Raising an
unread off-support score above the original changes each width's PR from one
to one-half while preserving the adaptive transcript. This proves the stated
deterministic coordinate-query lower bound with promised validity and no
precomputed summary. It is basic input-inspection optimality, not a general
VUS lower bound or a new comparison-sorting theorem. The finite binary64
distinctness and fixed-key operation-count caveats are present.

Two optional mathematical clarifications would improve precision without
changing the argument:

- Say explicitly that finite-precision rounding can change the stopping
  predicate as well as the final summation. No directed-rounding certificate
  or all-input floating-error bound is established. The current exact-arithmetic
  versus numerical-parity distinction is otherwise appropriate.
- Define `pi(t)=T(t)/C(t)` only for nonempty retained thresholds; the initial
  origin has `C=0` and needs no precision value for the right-step sum.

## Novelty and empirical claim audit

The novelty is the combination of an exact early cutoff with width-wise
activation and component bookkeeping that avoids paying for unvisited support,
plus its parameterized guarantee and matched-control separation. Radix keys,
complete ties, flat-recall truncation, reversible lists and union-find are
standard and are attributed. The manuscript does not claim to invent them.

The strongest likely rejection argument is significance, not a detected false
theorem: the metric-specific mass inequality is simple, the data structures
are established, and the default-width gain over released radix is negligible.
The single-component guarantee and constructed asymptotic separation answer
part of that concern, but not all of it. A compact comparison explaining the
remaining per-width work in Boniol's Algorithms 2–3, Klein, v0.3 and the new
method would make the nontrivial step easier to assess. Do not add unrelated
negative research branches merely to increase apparent breadth.

The new results section handles the principal empirical traps correctly:

- All three primary failures are prominent; width 300 remains secondary.
- Case counts are not presented as independent datasets.
- The fastest-of-eight control is identified as a post-measurement comparison,
  not a deployable selector; losses against it remain visible.
- Raw/label identity and 11/48 matching score arrays are distinguished from
  regeneration of the other 37 arrays on Linux.
- Large Benchopt/DTAI ratios are not attributed solely to saturation; the
  released paired-radix comparison and its 19/48 losses remain explicit.
- DTAI's two prescribed timeouts have no invented ratios; the 10-case median
  describes only completed cases.
- Structural timing results are described as constructed witnesses, with
  production radix rather than an independent dense oracle as their reference.

The phrase “independently written dense oracle” refers to implementation
separation, not an independent research team. The new AI disclosure explains
the shared agent workflow and correctly avoids external-review claims. This
review cannot verify or supply the human author's contribution, accountability,
approval, conflicts or submission eligibility.

## Venue and primary-source checks

PVLDB 2027 is **volume 20**. Foundations and Algorithms is a flavor of Regular
Research, not a separate paper category requiring a title suffix. The 12-page
limit excludes references but includes appendices and acknowledgements.
Single-blind review requires named authors. The supplied style is marked
PVLDB volume 20 and uses the required top-matter mechanism; compilation and
page count were intentionally not checked here.
[Official call](https://www.vldb.org/2027/call-for-research-track.html),
[submission guidelines](https://www.vldb.org/2027/submission-guidelines.html),
[formatting guidelines](https://www.vldb.org/2027/formatting-guidelines.html).

Time-series analytics is in scope, but prior VUS publications do not guarantee
scope acceptance. The paper should retain its concrete data-management problem:
the cost of exhaustive evaluation over stored label/score collections, and
precisely how it advances the existing VUS analytics algorithms. It should not
claim an evaluated DBMS integration or model-selection pipeline. The current
theory-led structure is more suitable than an EA&B or deployed-systems pitch.

Primary metadata checks support mTSBench as TMLR 2026 and the foundation-model
score source as ICLR 2026. OpenReview forum pages presented a browser challenge;
the mTSBench published PDF, author project page, and KU Leuven repository record
provided the relevant primary evidence instead. No venue status was inferred
from a search-result title alone.
[mTSBench published PDF](https://openreview.net/pdf?id=8LfB8HD1WU),
[author project page](https://plan-lab.github.io/projects/mtsbench/),
[released-score repository](https://doi.org/10.48804/MCVI4N),
[Boniol version of record](https://doi.org/10.1007/s00778-025-00907-x),
[pinned official metric source](https://github.com/TheDatumOrg/VUS/blob/467bace0c103f5c2bdb4900306d82939bcac8ff9/vus/utils/metrics.py).

PVLDB's policy requires disclosure of material automated assistance and human
author responsibility. The manuscript now describes the assistance actually
observed in this workflow; it must not add an unverified human contribution or
approval claim. This is a document-integrity boundary, not a request to contact
anyone or change an account.
[Publication policies](https://vldb.org/pvldb/general-information/publication-policies).

## Snapshot and limits

Hashes captured during this review, after the initial findings were sent to
root. Root was editing concurrently, so later corrections require their own
final build/receipt and are not certified by these hashes:

| Source | SHA256 |
|---|---|
| `active_prefix.tex` | `af40010ec322af57a1867e3e52aae2cb9aa75c43b220695d92d9b2983dd75267` |
| `active_prefix_body.tex` | `f0968a267a8501a222fe9b822ced1c6fe762ddf368f95a32bf28a1489a27605b` |
| `active_prefix_abstract_results.tex` | `078cb880f5be8416f9f916284d93d1b552c51695814b0c6894222d590f6b9b97` |
| `active_prefix_results.tex` | `95152415eaa215d8141de2ec263f82c8297978a3346e5d5fa2cf907ec1afefc1` |
| `active_prefix_results_table.tex` | `a6cfafa016c12d2990f19b98297fd742af80ba3b3a0aaacbe0f1e4d1e09514cc` |
| `active_prefix_structural_results.tex` | `dcc50512945b7490477e5fc330ac80a11846a1227da5562521ad1e76fb81ffa2` |
| `saturation_method.tex` | `3671bc35cc55b9238128d36db3792464c9a338244eb680f781cc9f998280ecda` |
| `saturation_mass_bound.tex` | `59e9c47377a84779debb93c3851a1312c113f1128528ecc8183474a4813a4ebb` |
| `active_prefix_references.bib` | `5e170b7ef524c7e6b0ec215261a5e2e18a6532bc5f26900369a75e3764526725` |

This is an internal adversarial assessment, not a proof-assistant certificate,
numerical certification, external review, acceptance prediction, or publication.
