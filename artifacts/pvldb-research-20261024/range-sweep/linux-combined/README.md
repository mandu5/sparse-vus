# Canonical combined Linux reproduction

Run [40062043152](https://github.com/mandu5/sparse-vus/actions/runs/40062043152),
source `e2405e39ec23486a3d228240569b48785de32cb4`, completed successfully on
24 October 2026 at 05:07:05 UTC, AMD EPYC 7763, Linux. The selection of this
combined run as canonical precedes inspection of either new Linux timing report;
see `../linux-reproduction-selection.json`. The auxiliary range-only result is
retained separately rather than substituted for this run.

- `github-run.json` and `github-artifact.json`: remote execution and artifact metadata.
- Downloaded ZIP: 111,403,544 bytes, SHA-256
  `cf9e0531b3ab00bc9f3f6d28113d62497f1ebe1c66b5eae2fe0fae915c898ec7`.
- `manifest.json`: 568 files / 147,330,993 bytes retained below `replica/`,
  including all 73 generated NPZ inputs, 438 canonical range curves, timing
  records, frozen protocols, reports and pinned external source snapshots.
- `local-reaudit.json`: four independent saved-record reconstructions, each
  byte-identical to its archived report; validation arithmetic and parent checks.
- `score-comparison.json`: hash-bound post hoc accounting against the original
  Apple panel. Raw observations/labels match; no complete score matrix matches.
  Two SMD selection indicators change despite equal aggregate 24/15/12 counts.

No Python bytecode/JIT cache is retained. The project source and public raw ZIP
are deliberately restored from their pinned identities rather than duplicated
inside this archive. External source licenses accompany their snapshots where
provided upstream. The exact GitHub ZIP itself is not duplicated in Git.

## Fresh execution

In the documented pinned Python environment, from a project checkout:

```sh
python experiments/reproduce_range_sweep.py --include-vus --output /tmp/exact-metrics-replica
```

This regenerates scores and principal numerical VUS/range tables. It does not
rerun every separately frozen follow-up or typeset the manuscript. Dependency
installation is recorded in `.github/workflows/range-sweep-reproduce.yml`; the
full guide is `docs/REPRODUCE_PVLDB_20261024.md`.

## Re-audit these saved observations

Copy `replica/` to a new writable directory, including its hidden `.cache/`.
Restore `src/`, `experiments/`, and `artifacts/selected_series.json` from the exact
source commit above into that copy. Download
`https://www.thedatum.org/datasets/TSB-AD-U.zip` to `cache/TSB-AD-U.zip` and check
SHA-256 `0c47020d3423723c70773736dbd800369f2b487328becbf339450d1ae5020961`.
The primary auditor checks individual archive members, not only the ZIP name.
Use the pinned dependencies, run from the restored tree, set `PYTHONOPTIMIZE=0`
and `PYTHONPATH` to its `src/`, then execute:

```sh
python experiments/audit_pvldb20261024.py --root . --output vus-primary-reaudit.json
python experiments/audit_pvldb_supplement.py --root . --output vus-supplement-reaudit.json
python experiments/audit_range_sweep_study.py > range-main-reaudit.json
python experiments/audit_range_sweep_public.py > range-public-reaudit.json
```

The files to compare are listed in `local-reaudit.json`. The validation report
is a separate selected-cut/stress receipt, not a fifth independent saved-record
auditor. Fresh metric execution and record reconstruction have separate receipts.
Some other hosts may differ in the last bit of derived log/exp summaries; all
hashes/discrete fields remain exact. This canonical local re-audit had no such
differences. Public timeouts remain censored, with two in this canonical run.
