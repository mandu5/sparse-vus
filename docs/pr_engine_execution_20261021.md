# PR engine execution record — 21 October 2026

The measured implementation and protocol-v2 harness are committed as
`06a14d04e59a62ef0840aae837107bfd85c4400b` on
`research/pr-engine-20261021`. The released main branch was not changed.

## Verification before formal development

- Root's integrated run: 3012 passed in 58.72 seconds. Collection preceded
  the last two pipeline rejection-test additions.
- Final scoped baseline/pipeline run: 196 passed in 6.60 seconds, including
  all 13 actual method adapters, hidden-fallback rejection, cleanup outside
  the timer, and the strengthened radix decision test.
- GitHub [run 39520717555](https://github.com/mandu5/sparse-vus/actions/runs/39520717555)
  succeeded at the measured commit. Python 3.12: 3012 passed, 2 skipped in
  111.86 seconds. Python 3.11: 3012 passed, 2 skipped in 96.53 seconds.
  The optional Torch semantic probes were skipped on these environments;
  they were exercised locally. The installed base-wheel check also passed.
- Independent source review is recorded in
  `pr_protocol_independent_review_20261021.md`; it is an in-session AI
  review, not journal peer review.

## Frozen v2 development run

Location: `artifacts/pr-engine/mac-development/`.
Protocol SHA-256:
`e8197bcd29c1209bddd57d442823d5fefc08a87e330a199ec0c4d79f385ba8b9`.
The local protocol and input identities were frozen before this run's first
outcome. This development experiment is not claimed externally preregistered.
It includes the 42 preselected development series, widths 30/100/300, three
models, 13 methods, and three randomized serial repetitions.

All agent tests and local heavy work stopped during timing. An unrelated
user background worker and normal desktop processes remained active, as
disclosed in `environment.json` and the sanitized starting load snapshot.
The Mac is not claimed to be a dedicated or isolated CPU. A separate Linux
run is planned for confirmation. Raw rows were appended and never replaced. All 126 tasks completed with zero
semantic violations; the independent audit passed. Maximum exact PR difference
was 1.3322676295501878e-15. At L=30 the exact radix path versus comparison-sort
PR had median speedup 1.919217, aggregate speedup 2.553586, and 41/42 wins.
The v2 radix decision passed; both racing decisions failed. These are development
results, not evidence from the new 308-series holdout.

## Pre-holdout strengthening

The independent review identified a fairer control: dense PR evaluation must
also receive the generic radix optimization, and the nearest-distance dense
control must not perform unnecessary ROC work. Two new controls were implemented only after v2 timing ended:
direct-ramp dense radix PR and nearest-distance dense radix PR. Their 130
correctness tests passed. The v3 integration and audit tests passed 40 checks,
including all 15 actual adapters on tiny fixtures. They change no v2 measured
source; the all-position controls use neither sparse event pruning nor ROC work.

Protocol v3 retains all existing controls and adds these two before any
new holdout outcomes. They have no fitted parameters. The 308-series holdout
will retain all widths, with the primary width 30 executed before widths 100
and 300. The v2 history will remain auditable against its original sources;
timings from the different versions will not be silently pooled. The exact original v2 auditor and required source/release files are preserved
in artifacts/pr-engine/source-v2; the current auditor deliberately requires v3.
The historical auditor independently reconstructed the original development
run successfully. Its source-manifest SHA-256 is
61ef071126f3a7c054518e8ab75b5fea6050feb7fcd510c18c97fc485dc7516b.

This record reports completed checks and planned gates separately. It does
not replace the raw timing/audit receipts or establish external acceptance.

The Linux workflow downloads in a separate staging workspace and links only
its verified cache into the checkout, so fresh download timestamps cannot
overwrite the hash-locked historical release receipts. New download receipts
are copied separately into the new run folder after protocol creation.

## V3 prospective holdout freeze

The integrated pre-holdout suite passed **3150 tests in 60.65 seconds**.
A subsequent source change corrected only the word “upstream” to “existing
direct” in the new dense control's module documentation. No executable
statement changed. Both independent static reviews found no mathematical or
fair-comparison blocker. The workflow's YAML and embedded Python parsed.

The Mac protocol/input manifest was frozen without computing holdout outcomes:
`artifacts/pr-engine/mac-holdout/`, protocol SHA-256
`5417a38ec43cc4471e17a0ca7d6af0b11ef448689042a1c5dec4fa8ef2dffb07`.
This freeze and the measured source are committed/pushed before starting
the run. The same commit starts the Linux workflow, which freezes its own
protocol/environment before executing the identical fixed comparison.
Each run retains 308 series, three widths, 14 methods, three models, and
three serial randomized repetitions; the primary L=30 block comes first.

The public freeze commit is `91696f79726ca83973cbda834e4ecf60c28441c8`.
[CI run 39523992605](https://github.com/mandu5/sparse-vus/actions/runs/39523992605)
passed: Python 3.12 had 3148 passed/2 optional Torch skips in 118.71 seconds,
Python 3.11 had 3148 passed/2 skips in 114.22 seconds, and the isolated
NumPy-only installed-wheel probe passed. The two Torch probes passed locally.

[Linux run 39523992616](https://github.com/mandu5/sparse-vus/actions/runs/39523992616)
successfully fetched all source bytes in its separate workspace and entered
the frozen experiment. The Mac run began at 2026-10-21 00:56:59 UTC after all
agent test/report work stopped. Lightweight document edits and status reads
continue; no benchmark source is changed. The starting snapshot shows an
unrelated Python worker at approximately 100 percent CPU, so the Mac remains
explicitly non-isolated. The full 924-case outcomes and audit remain pending.

## Report-only descriptive comparator

After execution began, a report-only diagnostic was added: the fastest
eligible PR-only exhaustive comparator for each complete task, chosen from
the fixed existing method set. It includes the three prior PR-only controls
and, for v3, both matched dense radix controls. Paired ROC/PR outputs and
adaptive winner-only engines are excluded from this particular comparison.
No holdout timing outcomes were inspected to select this rule. It is a
post-protocol descriptive minimum with no confidence interval or change to
the frozen decisions; it can expose heterogeneity hidden by separate
pairwise aggregate wins. Complete choices and losses remain in the report.
Report fixtures specifically include such a pairwise-win/oracle-loss case.

The report/primary-manuscript follow-up is committed as `f253ab1`, with
the descriptive-oracle report addition at
`06fab4679dbded59617468787a98ab982e065d38`. Neither changes a measured
benchmark source. [CI run 39525537293](https://github.com/mandu5/sparse-vus/actions/runs/39525537293)
passed on the latter commit: Python 3.11 had 3163 passed/2 skips in 59.36
seconds and Python 3.12 had 3163 passed/2 skips in 62.12 seconds. The real
v2 report also regenerated successfully from its original source snapshot
and raw receipts in that remote job. Local timing was not interrupted.

At 2026-10-21 01:12:28 UTC the Mac had completed all 308 primary-width
cases and reached 354/924 total cases with zero reported semantic
violations. This is a progress record, not the final independent audit
or a performance decision.
