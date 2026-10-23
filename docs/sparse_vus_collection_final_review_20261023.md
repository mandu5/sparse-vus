# Final scholarly delta review: measured collection workflow

Reviewed 23 October 2026. This is an internal scholarly assessment of the
unified manuscript and its new collection experiment, not external peer review,
an acceptance forecast, an authorship declaration, or permission to submit.
Only this review document was written. No paper, frozen source, protocol, or
measurement was changed, and no benchmark or heavy verification was run.

## Recommendation

**The corrected unified paper is a defensible submission to PVLDB Regular
Research, Foundations and Algorithms. I recommend proceeding to that scientific
review after the small wording corrections below and completion of the separate
artifact-delivery work. My internal assessment is borderline positive on
significance, not a strong-accept assessment.** There is a coherent algorithmic
contribution with real implementation evidence; there remains a reasonable
rejection case about the breadth and importance of this particular operator.

The new experiment does resolve the specific missing-evidence objection in
the [prior final review](sparse_vus_final_review_20261023.md): the paper now
measures an actual stored-score collection operation, including file loading,
full metric evaluation, model-set selection, and output writing. It is no
longer relying only on a sum of independently timed case medians to suggest
application benefit. A reviewer may still find that application too narrow,
but should not describe the paper as having no directly timed collection
workflow.

I found no new fatal mathematical error, fabricated performance result, or
body-level attribution of the collection speedups to the prefix/tie-run
extensions. I would not require another improvised benchmark merely to make
the present, carefully limited claim submit-worthy. Stronger general-purpose
or deployment claims would require additional research.

## What the new evidence establishes

The reviewed Section 6.2 and Table 5 are present in the actual PDF, as is the
new abstract result. The experiment uses the unchanged released sparse-radix
evaluator, matched nearest-distance dense radix PR, and pinned Klein PR with
exhaustive thresholds. It processes the original 308 series in 17 families,
all three original score vectors, and only maximum width 30. Each pass reads
308 NPZ files totaling 379,354,532 bytes, makes 924 complete PR calls, selects
308 best-model sets under the stated tolerance, and writes one JSON result.

| Method | Three directly measured whole-pass times, seconds | Median, seconds |
| --- | --- | --- |
| Released sparse radix PR | 2.902273833; 3.186659042; 3.720735917 | 3.186659042 |
| Matched nearest dense radix PR | 11.456034167; 10.944225833; 11.297516583 | 11.297516583 |
| Klein PR | 59.041194209; 63.647341375; 63.749285917 | 63.647341375 |

The median ratios are 3.5452542723 and 19.9730628649. Differences between
the reported medians are approximately 8.11 and 60.46 seconds per collection
operation. These are observable savings for this task, not an extrapolation
to an invented collection size or execution frequency. All selected-model
sets agree across all nine passes; the maximum pairwise PR difference is
`1.3322676295501878e-15`, below the frozen `1e-11` bound.

These statements agree with both the cache-backed
[driver report](../artifacts/collection-workflow/mac-20261023/report.json) and
the [independent public-receipt audit](../artifacts/collection-workflow/mac-20261023/public_audit.json).
The earlier audit task already established exact agreement between their
pass records, decisions, and complete per-series numeric comparisons. This
review inspected those retained results and the rendered paper; it did not
recompute metric values or rerun timings.

The per-pass phase clocks show that metric calls account for about 85.9–89.7%
of sparse-radix wall time, 93.4–93.9% of dense wall time, and 98.2–98.4% of
Klein wall time. This supports the narrower statement that evaluation is the
dominant cost of this measured stored-score operation. It does not show that
evaluation dominates detector training, inference, network ingestion, or an
organization's broader analysis process. Separately summarized phase medians
must not be added to manufacture a whole-workflow estimate; the table correctly
warns against that interpretation.

## PVLDB fit after the change

The current scope policy asks about a core data-management contribution,
substantive connection to database research, and evaluation in motivating
data-management contexts. It expressly does not decide scope from topic labels
or the existence of a related PVLDB paper alone.
[Official PVLDB v20 submission guidance](https://vldb.org/2027/submission-guidelines.html).

| Scope consideration | Evidence in this manuscript | Assessment |
| --- | --- | --- |
| Efficiency of a data-processing operation | Exact evaluation over stored labels/scores; support-event compression and prefix-sensitive work bounds | Defensible algorithmic efficiency contribution |
| Substantive database-literature connection | Formal treatment of the dynamic VUS target from PVLDB/VLDB Journal work, with explicit comparison to its support/threshold algorithms | More than adding a database citation to an unrelated task |
| Evaluation in a motivating context | Direct disk-to-JSON comparison/selection on a real stored-score collection, with matched controls and preserved decisions | The earlier concrete evidence gap is materially addressed |
| Breadth and practical importance | One collection size, three models, one width, one host for the new workflow; other operator experiments are separately reported | Still a judgment call and the strongest rejection risk |

Foundations and Algorithms papers may have their primary contribution in
formal foundations or algorithms, with prototype evaluation encouraged. That
flavor does not impose the same end-to-end system contribution expected of
Systems papers. The current paper belongs in the former flavor; changing its
label to EA&B or SDS would not strengthen the underlying contribution.
[Official PVLDB research call](https://www.vldb.org/2027/call-for-research-track.html).

My judgment is that the coherent event evaluator plus this application
demonstration can satisfy a reasonable reading of those scope dimensions.
This is a reviewer judgment, not an assertion that the editors must accept
the scope or that a public scoring rubric supplies a pass threshold. The
broader scientific significance remains contestable.

## Proof, novelty, and attribution remain separate

The new workflow is an evaluation contribution, not a new algorithm or a
proof of novelty. The strongest scientific account remains:

1. Exact scalar event elimination for the pinned dynamic metric, preserving
   omitted ROC rectangles and complete global ties.
2. Support-sensitive evaluation with standard fixed-binary64 ranking and
   the two-distance geometry, with explicit arithmetic-model qualifications.
3. Reversible support activation and component maintenance yielding the
   prefix-sensitive work bound without a full per-width preparation scan.
4. A restricted one-original-interval run construction, integer stopping
   certificate, and local finite-precision mass analysis.

I reread the current proof statements and their caveats against the prior
review. No scope upgrade is justified by the collection experiment. The
`O(n + (L+1)Q)` support bound, `O(n + L + alpha(K) sum_w J_w)` prefix bound,
and run-fragmentation-sensitive bound concern their specified models and
constructions. The one-interval assumption, complete terminating ties,
fragmentation cost, and binary64/unit-cost assumptions remain material. The
local range-mass error bound is not an end-to-end scalar error certificate.

Known sorting, recall stopping, cumulative sums, reversible updates,
union-find, and superaccumulators remain prior techniques. The paper's claim
is the metric-specific reduction and composition with its guarantees, not
invention of those tools. This review is not a fresh exhaustive literature
search establishing global firstness.

The new collection win belongs to the released whole evaluator. The three
default-width incremental failures remain failures, and the run candidate's
losses on most reused width-300 cases remain negative evidence. Its strongest
gains on compressible constructed ties do not become population-level gains
because the released evaluator is fast on 308 series. The current body keeps
these distinctions; the abstract should make the new timing attribution
equally explicit.

A disclosed public software/working-paper precursor is compatible with a
first archival account; posting a technical report is distinguished from
prior refereed publication by PVLDB's publication policy.
[Official originality policy](https://vldb.org/pvldb/general-information/publication-policies).
That general rule does not establish this author's complete submission or
publication history. The earlier private overlap audit was bounded, and this
review has not authenticated accounts or supplied a new human declaration.
The factual “unsubmitted” description therefore remains subject to the
author's final verification, independent of this scientific assessment.

## Small claim corrections before the final PDF

These requests concern the reviewed snapshot, not a request to alter frozen
measurements or the frozen protocol.

1. **Attribute the collection result explicitly in the abstract.** The current
   sentence giving 3.187 seconds immediately follows the tie-run discussion
   and leaves the measured method implicit. Prefer wording such as “Using
   the released sparse-radix evaluator, a separate warm-filesystem, 308-file
   evaluation, selection and JSON-output workflow takes 3.187 seconds at the
   median on the M1 Pro…”. Keep the median-of-three scope clear. The body
   already attributes this correctly.
2. **Correct the startup description in the collection fragment.** Imports
   and synthetic dtype-matched JIT warmup occur once before all timings.
   Input hashing and explicit filesystem-cache warming precede every pass.
   The current combined sentence can be read as saying all those operations
   happen before each pass. All remain outside timing; no reported result or
   decision changes.
3. **Prefer a precise auditor description.** “Checks receipt consistency and
   recomputes comparisons and decision criteria” is clearer than “reconstructs
   … clocks.” The auditor validates recorded clock fields and their consistency;
   it does not independently measure elapsed time, rerun metrics, or establish
   machine isolation. The audit receipt already states this boundary. This
   third request is a precision improvement rather than a result defect.

The active-desktop/background-process limitation, warm-filesystem condition,
absence of `fsync`, three-repetition limit, and dense-last order imbalance
are already disclosed in the PDF. Preserve them. No confidence interval,
significance claim, cold-storage claim, or training-pipeline speedup should
be added to this experiment.

## Strongest remaining rejection argument

The following is a constructed adversarial assessment, not an actual review:

> The paper supplies a sound and useful optimized implementation of one
> evaluation metric, with clear exact identities and substantial matched-control
> gains. The added collection wrapper shows those gains survive loading and
> serialization, but uses the same corpus, score vectors, and width; it does
> not establish broad workload importance. Much of the machinery is familiar,
> while the most distinctive prefix/tie refinements have restricted assumptions
> or weak practical gains. The resulting contribution may be too specialized
> for this venue's significance threshold.

That is a credible review position. An equally defensible response is that
an exact analytics operator with a nontrivial dynamic semantic target,
explicitly isolated support-event savings, two-host operator evidence, and
a concrete collection demonstration constitutes useful foundations and
algorithm research. The paper now has evidence for that response. Detailed
receipts and honest negative results increase credibility; they do not force
either significance judgment.

## Scientific review versus artifact delivery

The coordinating agent reports that new clean-environment replication-driver
integration is under repair. This review did not test or certify that path.
That is an outstanding artifact portability task, distinct from the original
run's source-bound inputs, completed measurements, and consistent reports.
It would be incorrect to invalidate the original measured result merely
because a new replication entry point needs integration work. It would also
be incorrect to advertise successful clean-environment reproduction before
that integration is verified.

Before final delivery, complete the portability repair, regenerate and check
the rendered paper/fragment receipts, and ensure the stated public artifact
URL actually serves the final source and evidence. Those steps establish
delivery readiness. The scientific recommendation above does not complete
them, resolve account/cap/conflict declarations, or authorize an external
submission. The reviewed PDF has 12 physical pages including references;
the current Regular Research limit is 12 pages excluding references, but
this text inspection is not a complete format/layout certification.
[Official page-limit guidance](https://vldb.org/2027/submission-guidelines.html).

## Reviewed snapshot and limits

Read the wrapper/body, collection fragment and receipt, exact/prefix/tie-run
proof fragments, earlier review and coherent-evidence audit; inspected the
actual PDF text and retained collection reports. A second internal reviewer
independently checked the collection claims and identified the same attribution
and startup-wording issues. Neither review was independent laboratory
replication or external peer review. Official scope, category, and originality
pages were refreshed on the review date.

Snapshot before the requested wording corrections:

- `paper/sparse_vus.tex`: `ab15abc9dfbb5d2f81a064b75e63e3283fd04b5d9b38eed2687a6191d551f2bc`
- `paper/sparse_vus_body.tex`: `382d484a96ac869624241b7609be89a827036166b8c67b99a21f97752a20e088`
- `paper/sparse_vus_collection_results.tex`: `d25f0e8952d43bdf0eb6c9013aeeed774100bd6f78b4e066a58601cb9b712f18`
- `paper/sparse_vus.pdf`: `dfce3f2f62210fed633b2872e30ae30967b17c2e3a6f39e0bef5f92383146e13`
- `paper/tie_run_method.tex`: `19caf24fbe216ed0d3e0d665aa0434d5388e302dc2cf2772a838511b6eb9befa`
- `paper/saturation_method.tex`: `3671bc35cc55b9238128d36db3792464c9a338244eb680f781cc9f998280ecda`
- Collection protocol: `69ee646b505297e0feb124cb3206b0d600a6ad2a0a021c8fcea1c195dd4f56ea`

The scientific recommendation is conditional on preserving the reviewed
claims and evidence separation. Subsequent source/PDF edits require checking
their relevant differences; the hashes above identify what was actually read.

### Source-correction follow-up

After this review, the coordinator applied all three wording corrections.
I verified that the abstract source now explicitly names released sparse
radix as the 3.187-second method, and that `render_collection_results.py`
distinguishes one-time imports/JIT warmup from per-pass hashing/cache warming
and describes the auditor as checking recorded clock consistency and
recomputing numeric comparisons/decisions. These are source/renderer
corrections; the generated collection fragment and PDF still showed the older
wording when checked. Regeneration and PDF refresh are pending completion of
the coordinator's active Mac replication timing. No compilation, tests, or
timing were started by this reviewer during that run. The scientific verdict
and significance risks above are unchanged; the three wording requests are
addressed in their authoring sources, pending verification of the final PDF.

## Coordinating-agent closeout after the reviewed snapshot

The three requested wording corrections are applied in both source and rendered
PDF. The final PDF SHA-256 is
`4ce84a495efffde4910ffd42ce4b8b08f8839b9ad0bcde63165605ca2f298f4b`.
Its 13 physical pages contain all non-reference material by page 12; page 13
contains references only. No template compression was introduced. The additional
text reports separate Mac and fresh-Linux acquisition-to-timing replications:
68 cases and 1,360 timed calls per host, both passing parity/work assertions.
The original 131-case results remain unchanged. Linux score-byte differences
are disclosed. The unsupported precursor qualifier “unsubmitted” was removed;
the public release chronology remains explicit.

The portability integration described above is now executed and verified,
including the fresh Linux job
[39900063718](https://github.com/mandu5/sparse-vus/actions/runs/39900063718).
See the [final validation ledger](sparse_vus_final_validation_20261023.md) and
its run-specific receipts. These completion facts close the identified wording
and portability tasks; they do not upgrade the scholarly significance judgment
to a strong-accept prediction or supply personal author declarations.
