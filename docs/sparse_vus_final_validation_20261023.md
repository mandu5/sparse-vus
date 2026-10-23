# Final research validation — 23 October 2026

## Scientific decision

**Proceed to PVLDB Volume 20 Regular Research, Foundations and Algorithms.**
The unified paper has a defensible algorithmic contribution, explicit proofs,
matched-control performance evidence, a directly measured collection operation,
and an executed portable reproduction route. The internal scholarly recommendation
is **borderline positive on significance**, not a strong-accept prediction.
This is a research-readiness decision made from evidence, not an editorial result.

The contribution is exact scalar VUS event elimination and its composition with
interval geometry, fixed-key ranking, reversible width activation, and complete
tied-class runs. It is not the invention of sorting, recall stopping, cumulative
sums, union-find, or superaccumulators. The inspected prior algorithms do not
supply the same complete construction and guarantees. See the
[primary-source novelty audit](active_prefix_novelty_audit_20261023.md),
[theory review](active_prefix_theory_audit_20261023.md),
[new-code review](tie_run_code_review_20261023.md), and
[final scholarly review](sparse_vus_collection_final_review_20261023.md).
The public software precursor is dated and cited; its results are not assigned
to the new tie-run code.

The strongest remaining scientific objection is the **breadth and importance
of this exact analytics operator**, together with the restricted applicability
of the refinements. The directly timed collection study supplies an actual
application result, while the negative experiments constrain generality.
Neither more unit tests nor a successful file upload answers that significance
question. The current paper provides sufficient evidence to argue it through
scientific review without suppressing those facts.

## Verified evidence

| Claim | Completed check and result | Evidence |
|---|---|---|
| Exact semantics and work bounds | Global ties, omitted ROC rectangles, dynamic mass, component merging, activation cost, integer stopping, and run fragmentation were separately challenged; real-arithmetic identities and finite-precision claims remain distinct | [Unified manuscript](../paper/sparse_vus.pdf), [theory review](active_prefix_theory_audit_20261023.md) |
| Numerical implementation | 650 independently implemented dense comparisons; 36 complete Decimal-80 integrals; 150,000 exact integer prefixes; 20,009 limb subtractions; 6,569 counter reconstructions | [Independent numerical audit](../artifacts/tie-runs/independent-audit-20261023.json) |
| Whole evaluator | 308 series, 17 families, 924 three-score tasks per CPU; frozen five-control primary criterion passes on both recorded hosts | [Coherent evidence audit](coherent_vus_evidence_audit_20261023.md) |
| Actual collection operation | 308 NPZ reads, 924 complete PR calls, 308 model-set selections, JSON output; nine passes agree; maximum pairwise PR difference 1.3322676295501878e-15 | [Frozen report](../artifacts/collection-workflow/mac-20261023/report.json), [independent recorded-output audit](../artifacts/collection-workflow/mac-20261023/public_audit.json) |
| Collection performance | Median whole times 3.186659042 / 11.297516583 / 63.647341375 seconds for sparse radix / matched dense radix / Klein; ratios 3.5452542723 and 19.9730628649 | Same collection report; warm filesystem/JIT, three repeats, active Mac desktop, order imbalance disclosed |
| Original complete-tie study | All 131 prespecified cases pass parity/work checks; structured-tie improvements and fragmented/real-score regressions retained | [Frozen 131-case report](../artifacts/tie-runs/mac-20261023/report.json) |
| Portable Mac replication | 68 cases × 5 repetitions × 4 methods = 1,360 timed calls; PASS; max discrepancy from radix 2.220446049250313e-16 | [Report](../artifacts/tie-runs/mac-regenerated-20261023-retry1/report.json), [independent audit](../artifacts/tie-runs/mac-regenerated-20261023-retry1/post-run-verification.json) |
| Fresh Linux replication | Pinned source acquisition, score generation, input freeze, all 1,360 timed calls and report reconstruction completed; PASS; same maximum discrepancy | [Executed workflow](https://github.com/mandu5/sparse-vus/actions/runs/39900063718), [report](../artifacts/tie-runs/linux-39900063718/report.json), [downloaded-evidence audit](../artifacts/tie-runs/linux-39900063718/independent-verification.json) |
| Automated suite and distribution | Python 3.11 and 3.12 each: 3,363 passed, 2 optional skips. Installed base/accelerated/tie-run wheel checks and source identity pass | [CI 39900069998](https://github.com/mandu5/sparse-vus/actions/runs/39900069998), source checkpoint `ac7f5f4f4314340c5204ffc3504243d1ad001148` |

The new Mac and Linux replication sets reuse previously studied data and exclude
all 63 historical development cases. Raw observations and labels match frozen
identities. Generated score-byte identity to historical Mac is 48/48 on Mac and
9/48 on Linux: these are procedural replications, not identical-input cross-host
replays. Downloaded public receipts do not contain third-party observational
arrays. The remote acquisition job checked them while available; the downloaded
evidence auditor distinguishes those recorded checks from rereading local bytes.

The old active-prefix default-width performance criterion remains **FAIL in all
three studies**. Whole-evaluator gains and complete-tie structured gains do not
convert those failures into successes. The new run method is not supported as a
broad replacement for active prefix on real scores.

## Venue and manuscript

The current [PVLDB research call](https://www.vldb.org/2027/call-for-research-track.html)
expressly includes conceptual and algorithmic contributions with theoretical
formalism and prototype evaluation under Foundations and Algorithms. The
[scope policy](https://www.vldb.org/2027/submission-guidelines.html) also requires
a substantive database-literature connection and motivating data-management
evaluation. The paper directly builds on VUS from PVLDB/VLDB Journal and measures
a stored-score comparison/selection operation. This supports the chosen flavor;
it does not make scope or significance an automatic pass. TMLR is not the
selected destination for this final unified version.

Final PDF SHA-256:
`4ce84a495efffde4910ffd42ce4b8b08f8839b9ad0bcde63165605ca2f298f4b`.
It has 13 physical pages; **all non-reference content ends on page 12**, and
page 13 contains references only. The current template is preserved, all fonts
are embedded, and the build reports no overfull boxes, undefined references or
missing characters. The generated result fragments reconstruct from frozen
evidence. Rendered pages were inspected, including the final replication text.

The final wording attributes collection gains to released sparse radix, separates
once-per-process JIT warmup from per-pass filesystem warming, and describes the
public auditor as checking recorded clocks rather than independently measuring
them. The unsupported word “unsubmitted” was removed from the precursor
description; its actual public release and source revision remain cited.

The manuscript identifies Youngmin Ko, Independent Researcher, Republic of Korea,
and discloses the full role of AI assistance. These internal checks are not
external peer review. Actual author attestations and any portal submission
receipt are separate records and are not manufactured by this validation.

## Reproduction and integrity

Use the [reproduction guide](sparse_vus_reproduction_20261023.md) for exact commands,
input acquisition boundaries, historical versus fresh runs, and retained failures.
The source and artifact inventory accompanying this revision is
[`SHA256SUMS`](../artifacts/unified-validation-20261023/SHA256SUMS).
It records this deliverable snapshot; each earlier experiment retains its own
unchanged protocol and source bindings. GitHub's commit-specific CI checks and
the final public-download receipt establish the delivered revision separately.
