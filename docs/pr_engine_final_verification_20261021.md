# PR-engine completed-run verification — 21 October 2026

This records local reconstruction and transport checks after controlled timings
finished. It is not a new timing experiment, external laboratory reproduction,
peer review, or publication acceptance. Measured sources and original receipts
remain unchanged.

## Linux v3 policy holdout

The retained run is `artifacts/reproductions/linux-pr-engine-39523992616/`.
It contains all 924 tasks: 308 series, three model scores per task, and widths
30, 100, and 300. The holdout represents **17 observed families**, a subset of
the original 23-family corpus. CATSv2, Daphnet, Power, SED, SWaT, and TAO occur
only in the 42-series development partition. The 2,000-replicate bootstrap
resamples the 17 observed holdout clusters; development timings are not pooled.

At 2026-10-21 03:07 UTC, the unchanged v3 auditor was rerun with Python 3.12.4
on macOS after all formal timings had ended:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 \
python experiments/audit_pr_engine.py \
  artifacts/reproductions/linux-pr-engine-39523992616 \
  --output artifacts/reproductions/linux-pr-engine-39523992616/audit-rechecked.json
```

It returned PASS for all 924 tasks and the source-member provenance gate.
The new audit was compared recursively with the original `audit.json`,
excluding only the completion timestamp. All structure, nonfloating fields,
hash bindings, and source provenance agree exactly. The 9,028 floating fields
agree with absolute and relative tolerances of `1e-12`; the largest observed
absolute difference was `3.552713678800501e-15`, and the largest relative
difference was `1.9857448550905275e-16`. All 16 measured-source files and the
auditor still match their recorded hashes.

The original GitHub ZIP from run `39523992616`, artifact `12315563163`, has
SHA-256 `8dd17716ce273e8ba02fbcdbc5f692aa4ed429b15fce7a8a40f0963946283ead`.
This matches the retained GitHub artifact receipt. Every one of its 10 regular
members was read with ZIP CRC checking and compared by size and SHA-256 with
the retained original file: all 13,196,890 uncompressed bytes match. No original
member, including `audit.json`, was overwritten. The artifact records source
commit `91696f79726ca83973cbda834e4ecf60c28441c8`.

The frozen exact-radix primary decision passes; both racing decisions fail.
The largest exact PR discrepancy against the comparison-sort sparse reference
is `1.3322676295501878e-15`; maximum enclosure slack is
`3.3306690738754696e-16`. Decision success concerns the declared controls and
workload, not universal superiority or unseen-domain generalization.

Machine-readable evidence resides beside the original run:

- `audit-rechecked.json`: full local reconstruction, preserving the original audit.
- `archive-verification.json`: downloaded-ZIP digest and every original member hash.
- `verification-receipt.json`: complete comparison scope, tolerances, differences,
  source bindings, decision outcomes, and hashes of the verification outputs.

## Mac completed-audit binding inspection

The completed `artifacts/pr-engine/mac-holdout/audit.json` and its generated
report both record PASS for 924 tasks, 308 series, and 17 observed families.
The report's audit, protocol, raw-record, and measured-source bindings were
checked against the audit and local frozen sources. The report's decisions
agree with the audit: exact radix passes, and both racing decisions fail.
The maximum PR discrepancy is `1.5543122344752192e-15`, and maximum enclosure
slack is `3.3306690738754696e-16`.

The inspected audit SHA-256 is
`a9d44deb51fa3d764a923a52217012498a574847ebee798ddf343f1e90f0d28f`;
the report SHA-256 is
`c72f2df666c49e58c7deb7fec72dc10d9d3bddcdcb05602fb787ac09c62af2aa`.
This entry checks the completed audit/report bindings; it does not claim a
second current-tree Mac statistical reconstruction. That full recheck is
reserved for the extracted anonymous supplement, alongside its historical v2
and Linux v3 audits. Extracted-artifact verification remains pending.
