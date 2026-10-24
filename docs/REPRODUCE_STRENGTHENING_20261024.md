# Reproduce the weighted range and native TimeEval evidence

This guide covers the separately selected 26-recording follow-up. The earlier
73-recording VUS/range studies retain their own commands and frozen protocols in
[the original reproduction guide](REPRODUCE_PVLDB_20261024.md). The new workload
does not replace those observations or their unfavorable controls.

## Fresh execution

Use a fresh Python 3.11.9 environment. Install the pinned core requirements and
the CPU detector import dependency, then run the driver from the repository:

```sh
python -m pip install -r requirements-strengthening.txt
python -m pip install torch==2.10.0 --index-url https://download.pytorch.org/whl/cpu
python experiments/reproduce_strengthening.py --output /tmp/weighted-native-replica
```

The destination must not exist. The last command downloads the raw archive and
public sources, regenerates all FFT/COPOD scores, verifies inputs independently,
runs the weighted study and the unchanged native TimeEval consumer with the
alternative curve backends, and reconstructs the results with separate auditors.
There is no reuse of saved detector scores. All numerical stages are serial;
do not run another benchmark or a test suite on the same host concurrently.
The frozen 600-second native workflow censoring rule can make the complete run
take more than an hour. `--archive /path/to/TSB-AD-U.zip` can reuse only a raw
archive whose exact checksum matches; it does not reuse fits or timings.

The GitHub workflow is
[`weighted-range-reproduce.yml`](../.github/workflows/weighted-range-reproduce.yml).
Core package versions are pinned. The full observed environment, including
the CPU Torch dependency closure, is retained as `environment-freeze.txt`;
transitive Torch packages are not claimed to have a complete lockfile.

The supplemental conventional interval control has a separate fresh driver
and requires another new destination:

```sh
python experiments/reproduce_interval_control.py --output /tmp/interval-control-replica
```

Its workflow is
[`interval-control-reproduce.yml`](../.github/workflows/interval-control-reproduce.yml).
It regenerates the same selected profiles and compares the compiled raster,
conventional interval, and incremental methods under a separate frozen protocol.
It does not repeat public range-callback timings or replace the original study.
Run the two drivers serially; do not pool their timings or their hosts.

## What is frozen and checked

- Raw TSB-AD-U archive SHA-256:
  `0c47020d3423723c70773736dbd800369f2b487328becbf339450d1ae5020961`.
- TSB-AD detector revision: `ed74348e7876c9268b7a737c77f2f5f56f7fa458`;
  all 11 downloaded source members have fixed hashes.
- TimeEval revision: `7c3622757b1a3afa9a84cbc97ce132d9e379f715`;
  the exact set and hashes of 425 extracted files must match the original
  manifest before installation. GitHub's gzip container bytes can change
  without changing these source files; transport hashes remain recorded.
- The 26 recording identifiers, raw arrays, labels, two public detectors,
  semantic choices, method orders, censoring rule and runtime source hashes
  are checked. Fresh scores and their actual query counts are recorded by host.
- One explicitly source-bound input compatibility rule replays an original
  Mac binary64 observation that fresh CSV decoders round one ULP differently.
  The rule was added after a failed replay and diagnostic, before the fresh
  Linux detector fits. It preserves the original complete typed-input hash.
  It does not claim that the original decimal parser is platform invariant.
  See [the descriptor](../artifacts/pvldb-research-20261024/strengthening/provenance/float-decoding-contract.json).

The weighted study evaluates all 12 prespecified combinations of four equal
precision/recall biases and three cardinality factors, two query contracts,
three same-compiler backends and six orders. It is macro precision with recall
alpha 0.2. Mixed precision/recall biases and length-weighted precision have
correctness checks but are not extra timed workloads.

The native study instantiates TimeEval's real `MetricComputor` and configured
`DefaultMetrics.RANGE_PR_AUC`, with ROC-AUC and PR-AUC also requested. It compares
the public callback, compiled raster and buckets at nominal 50 and all
nonminimum observed-score queries, retaining native synthetic endpoints.
Each of four batches has six method permutations. The clock
includes label/score CSV loading, all three metrics and result CSV write/close;
imports, JIT warm-up, directory preparation and audits are outside it. It does
not measure detector training, cold caches or storage durability.

## Independent reports and interpretation

Under the output's `artifacts/pvldb-research-20261024/strengthening/` directory:

| File | Evidence |
|---|---|
| `native-input-audit.json` | Raw member, decoded input, score receipt and native loader identity checks |
| `weighted-linux-v2/independent-report.json` | Saved-curve parity, complete coverage, winner sets, selection regret, paired-order intervals and recording sensitivity |
| `native-output-audit.json` | Native schedule, completed/censored coverage, CSV/result values, complete-workflow ratios and intervals |
| `reproduction-complete.json` | Successful driver completion and hashes of the above receipts |
| `weighted-control-linux-v1/independent-report.json` | Supplemental compiled interval-control curve and timing reconstruction |
| `native-control-output-audit.json` | Supplemental native raster/interval/bucket audit; no public-reference claims |
| `control-reproduction-complete.json` | Successful supplemental-driver completion and bound receipt hashes |

The weighted auditor imports neither the metric kernel nor experiment producer.
The native output auditor imports neither the runner, metric kernel, TimeEval
nor `prts`. These independent implementations are automated internal checks,
not external peer review. A mathematical oracle is a separate correctness test.

Primary paired-order intervals are conditional timing uncertainty on a fixed
panel and host. Recording-reweighting intervals are workload sensitivity, not
population coverage. The two MSL recordings do not establish a broad new-domain
sample. Mac and Linux intervals are not pooled, and fresh generated scores may
differ across environments. Public callbacks censored at 600 seconds do not
receive fictional completed runtimes or timing confidence intervals. A matching
output from a completed family batch can verify values for that same profile
in a combined batch, but cannot reconstruct the combined public workflow time.

## Archived-output reconstruction

The public artifact contains saved metric curves and consumer result CSVs,
identifiers, hashes, acquisition code, protocols and receipts. New raw data and
detector score vectors are not redistributed because their redistribution terms
have not been confirmed. The fresh command reacquires them from the source.

For the original downloaded study, set the paths below to its extracted
artifact directory. Write new audit receipts; preserve the original CI receipts:

```sh
python experiments/audit_weighted_range_study.py \
  --output /path/to/original-archive/weighted-linux-v2 \
  --without-local-inputs --report /tmp/weighted-archive-audit.json
python experiments/audit_timeeval_archived_outputs.py \
  --run /path/to/original-archive/timeeval-linux-v1 \
  --protocol /path/to/original-archive/timeeval-global.json \
  --manifest /path/to/original-archive/timeeval-manifest.json \
  --out /tmp/native-archive-audit.json
```

For the separately downloaded interval-control study:

```sh
python experiments/audit_weighted_range_study.py \
  --output /path/to/control-archive/weighted-control-linux-v1 \
  --without-local-inputs --report /tmp/weighted-control-archive-audit.json
python experiments/audit_timeeval_archived_outputs.py \
  --run /path/to/control-archive/timeeval-control-linux-v1 \
  --protocol /path/to/control-archive/timeeval-control-global.json \
  --manifest /path/to/control-archive/timeeval-control-manifest.json \
  --out /tmp/native-control-archive-audit.json
```

The native archive auditor is standalone: it imports neither a study runner nor
TimeEval, `prts`, or a metric kernel. It checks that the saved standalone manifest
equals the embedded frozen protocol, verifies protocol/run/record and completed
CSV hashes, checks all 144 scheduled identities and censor dependencies, compares
all three saved metric values, and reconstructs each same-contract matched timing
ratio and interval against the saved summary. It also checks declared profile and
query-count coverage. Those declared counts are not recomputed from score bytes.
Supplemental archives must have false public-reference flags throughout.

These archive receipts explicitly report `local_input_bytes_verified=false`.
The native receipt also reports `local_source_bytes_verified=false`; absolute
source and input paths from the originating host are never followed. Saved
workload receipts beside the protocol are hash-checked when present, but that
does not independently verify the raw data or scores they describe. Censored
workflows supply no completed scalar vector or ordinary timing interval.

Each successful fresh Linux run performs the stronger local-input audit before
archiving, retained in its original CI receipt. Use the original
`audit_timeeval_strengthening.py` or `audit_timeeval_interval_control.py` only
where their bound source, input, and trial-score files remain available. An
archived-output check does not repeat raw-data acquisition, detector fitting, or
metric evaluation. Preceding failed reproduction attempts and their repairs
remain part of the provenance; successful replays do not erase them.
