# Reproduce the 24 October PVLDB evidence

This is the complete exact-evaluator study, distinct from the narrower
`certified_sampling` manuscript. The original recorded evidence is immutable.
The command below generates new scores, executes the complete primary and
supplementary experiments, and reconstructs their tables in a **new directory**.

## Recorded environment and command

Python 3.12.4; NumPy 1.26.4; Numba 0.59.1; pandas 3.0.1;
scikit-learn 1.8.0; SciPy 1.17.1; threadpoolctl 3.6.0. Install these exact
versions in a dedicated environment. No GPU, model API or private dataset is
required. The public TSB-AD-U archive is approximately 73 MB. Keep other CPU
workloads idle during measurements. Public hosted CI cannot guarantee an idle
physical host and is identified separately in its receipt.

From the repository root, with those dependencies installed:

```sh
python experiments/reproduce_pvldb20261024.py --output /tmp/pvldb-independent-replica
```

Choose a path that does not already exist. The command never deletes or reuses
an existing destination. It downloads the pinned public raw archive if the
repository's existing copy is unavailable, fetches the two hash-checked public
comparator sources, creates separate source/cache/output directories, and runs
the stages serially. It excludes imported/compiled-cache state when copying the
project. JIT compilation is warmed consistently before timing; this is not a
cold-start latency benchmark. Expect tens of minutes, depending on CPU and
public network access. `--primary-only` deliberately omits the supplemental
comparison and is not the complete reproduction.

The destination contains:

- `artifacts/pvldb-research-20261024/full-precision/report.json`: primary paired
  case intervals, exact-value checks and directly timed collection workflows.
- `full-precision/independent-audit.json` under the same evidence directory:
  complete principal-table reconstruction, raw/input/source binding checks,
  identical-label blocks and development-geometry exclusion sensitivity.
- `supplement/independent-report.json`: Benchopt native-consumer and matched
  ROC+PR comparisons, Klein exact/250/1000 accuracy-cost results, all numerical
  winner changes and selection regret.
- `reproduction-complete.json`: CPU, platform, package versions and the hashes
  of both reports and audits. A start receipt alone does not mean completion.
- Raw `records.jsonl` and `workflows.jsonl`, frozen protocols and all stored
  scores in `.cache/pvldb-full-precision-20261024/`.

Fresh scores may differ in floating-point rounding across platforms. The
source, cohort, methods, parameters, method orders, widths and measurement
contracts must match the recorded design. Scores are never rounded or jittered
to manufacture cardinality. Public-call correctness is checked against exact
numerical reference values at tolerance `1e-11`; numerical winner sets use
`1e-10`. These tolerances do not constitute a real-arithmetic certificate.

## Read the results with the correct units

Primary results use 73 series, not 10,512 independent datasets. NAB/SMAP/SMD
have 20/17/36 cases. Eight fixed CPU procedures provide evaluator inputs; this
is not a detector-accuracy competition. The recorded LOF novelty scoring also
includes fit points and must not be described as a validated detection protocol.
Of the 73 recordings, 62 were previously measured by name. SMD has nine exact
label geometries; 18 cases share a development label geometry. Both ordinary
paired-case intervals and explicitly limited equal-label-block sensitivity are
reported. No physical-source independence is inferred from distinct filenames.

Case intervals resample paired median times over cases. Workflow intervals
resample explicitly paired timing trials on each fixed collection; repeated
timings are not new datasets. The three-collection familywise adjustment does
not automatically cover every exploratory method and width. The supplement is
explicitly frozen after the primary outcomes, before its own measurement.

Timing includes validation, preparation, allocation and winner selection.
Workflow timing additionally includes reading all stored-score files and
writing/closing the decision JSON, without training, cold storage or `fsync`.
Benchopt returns both ROC and PR: its native PR-consumer ratio is separate from
the matched two-output radix comparison. Klein exact is a PR-only comparison.

## Audit existing records without remeasuring

The following is a distinct, faster operation and requires the stored input
arrays. Each output path must be new:

```sh
python experiments/audit_pvldb20261024.py --root /tmp/pvldb-independent-replica --output /tmp/primary-record-audit.json
python experiments/audit_pvldb_supplement.py --root /tmp/pvldb-independent-replica --output /tmp/supplement-record-audit.json
```

The auditors import no metric producer/kernel. They validate coverage, finite
values, actual arrays against the frozen cohort, archive members, source hashes,
run/parent bindings, winner sets, and all reported primary statistics. Supplement
ROC arrays are independently compared in workflow records; per-case ROC error
fields are checked against those same deterministic outputs. Mutation tests
exercise wrong CI/workflow values, replaced inputs, missing/duplicated records,
changed protocol links and falsified regret. An audit reconstructs records; it
does not independently rerun the numerical operator or recover unrecorded data.

`audit-history/audit-v1.py` and the initial audit receipt remain historical.
The v3 receipt supersedes v1's incomplete statistical/input-binding coverage and
v2's missing rejection of additional unmeasured summary entries.
The frozen timing producers and metric sources were not changed by this repair.
