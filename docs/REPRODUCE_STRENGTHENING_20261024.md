# Reproduce the weighted range and native TimeEval evidence

This guide covers the separately selected 26-recording follow-up. The earlier
73-recording VUS/range studies retain their own commands and frozen protocols in
[the original reproduction guide](REPRODUCE_PVLDB_20261024.md). The new workload
does not replace those observations or their unfavorable controls.

## Main table to fresh-execution map

The unified manuscript is `paper/exact_metrics_strengthened20261024.pdf`.
The following are separate, complete drivers for separate frozen studies;
none silently fills missing timings from the archived results. Each command
needs a new output directory and the corresponding pinned dependencies.

| Manuscript table | Operator and reported output | Fresh driver from repository root |
|---|---|---|
| 1, original VUS | Integrated dynamic VUS-PR values and same-output complete-call ratios; the operator also supports ROC | `python experiments/reproduce_range_sweep.py --include-vus --output /tmp/exact-metrics-replica` |
| 2, original range | Flat/reciprocal strict-query trajectories and F1 selection, grid100 and all observed scores | Same combined driver above |
| 3, weighted original | Twelve weighted/cardinality strict-query contracts, curves and selection, grid100 and all observed scores | `python experiments/reproduce_strengthening.py --output /tmp/weighted-native-replica` |
| 4–5, native original | Native ROC-AUC, PR-AUC and flat/cardinality-one range PR-AUC, nominal 50 and inclusive all-observed queries | Same weighted/native driver above |
| 6, conventional controls | Weighted raster/closed-form interval/incremental comparisons on the fixed separate panel | `python experiments/reproduce_interval_control.py --output /tmp/interval-control-replica`; the dagger-marked exploratory raster intervals additionally require the saved-output analysis below |
| 7, combined native executions | Original rows: weighted/native driver; control rows: interval-control driver | Both corresponding drivers, run serially |

A new execution supplies measurements for its own host only. It does not
recreate the historical Apple/Linux numbers or concatenate two hosts into
one inferential sample. The primary JSON reports reconstruct the prospective
contrasts; the post-hoc raster intervals have a separate analysis. Compiling
the paper and rendering its table layout are
separate operations. The original VUS/range guide gives the first driver's
requirements and complete auxiliary-study outputs.

### Reconstruct the exploratory Table 6 raster intervals and Figure 1

These two commands analyze the saved, separately audited Apple/Linux control
archives. They do not refit detectors, evaluate metrics, or acquire new timing
observations. The first exports the directly reconstructed median-ratio CSVs
and descriptive figure; the second checks those CSVs and resamples the saved
paired trials for the dagger-marked Table 6 contrasts. Both destinations must
be new. NumPy and Matplotlib are required for this analysis/presentation step.

```sh
python experiments/render_strengthening_evidence.py \
  --mac artifacts/pvldb-research-20261024/strengthening/weighted-control-mac-v1 \
  --linux artifacts/pvldb-research-20261024/strengthening/linux-interval-replay/weighted-control-linux-v1 \
  --output /tmp/interval-control-presentation
python experiments/audit_weighted_direct_comparison.py \
  --mac artifacts/pvldb-research-20261024/strengthening/weighted-control-mac-v1 \
  --linux artifacts/pvldb-research-20261024/strengthening/linux-interval-replay/weighted-control-linux-v1 \
  --presentation /tmp/interval-control-presentation \
  --out /tmp/interval-control-raster-posthoc
```

The resulting `posthoc-direct-raster-incremental.json` contains the twelve
host/collection/query estimates. Adjustment covers six contrasts per host,
not post-hoc comparator selection. These commands reconstruct the two
historical archives; they are explicitly additional to the fresh single-host
drivers and do not merge their workloads or timing uncertainty.

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

## Finite five-process Linux follow-up

The strict prior-score v1 stopped during preparation, before any warm-up or
metric call: 25 COPOD profiles differed from both earlier Linux score
realizations, including one changed distinct-score count. The immutable
failed archive and its SHA receipt are under `strengthening/affinity-failed-v1`
and `strengthening/affinity-failed-v1-archive-receipt.json`. The v1 command and
protocol below remain available as historical evidence; a successful v2 must
not be described as completing v1's failed same-score requirement.

The separately declared v2 tests one newly generated, fixed score realization
on the same 26 recordings. It retains strict raw/label/template/row identity
and preserves all prior score/query differences as diagnostics. It makes
exactly one generation attempt; a failed or missing fit aborts preparation.
It does not retry to find a matching or favorable realization. See the
[prospective v2 specification](superpowers/specs/2026-10-24-affinity-realization-v2.md).

```sh
python experiments/reproduce_affinity_blocks_v2.py --output /tmp/affinity-blocks-v2-replica --run
```

The v2 command uses the same 180-workflow/five-process schedule and statistics
below, under distinct `affinity-design-v2.json`, `affinity-blocks-protocol-v2.json`
and `affinity-blocks-linux-v2/` names. Its complete identity diagnostic lists
old/new score and threshold hashes; the fresh current hashes remain mandatory
through all five processes. The dedicated tag is `strength/affinity-blocks-linux-v2`, source commit
`d8494c25a8c6fe44616a34bdded375dc3993d048`. Its independent premeasurement
audit is [retained here](reviews/20261024/affinity-v2-premeasurement-audit.md).
The [single v2 execution](https://github.com/mandu5/sparse-vus/actions/runs/40091476529)
completed all five blocks, 180 timed workflows and 30 full warm-ups. Its saved
archive is `strengthening/affinity-linux-v2-replay`; the ZIP and every extracted
file are bound by `strengthening/affinity-linux-v2-archive-receipt.json`.
The separately authored, standard-library-only saved-output audit can be run
after downloading that run's artifact ZIP:

```bash
python experiments/audit_affinity_v2_saved_a.py \
  --archive artifacts/pvldb-research-20261024/strengthening/affinity-linux-v2-replay \
  --zip /path/to/affinity-blocks-linux-v2.zip \
  --out /tmp/affinity-v2-independent-reconstruction.json
```

The output path must be new. This checks the exact published ZIP and saved
records without fitting detectors or running metric timings; it does not
independently reread unredistributed raw observations or score vectors.
The first new generation happened to match both prior Linux score/query
identities; this was not a v2 inclusion criterion. Exhaustive raster/bucket is
1.919 [1.906,1.932] and interval/bucket 2.216 [2.201,2.227]. These are the
specified descriptive process-block intervals, not guaranteed coverage or
an explanation of prior host/run differences. All raw results are retained.

The additional same-runner robustness study has a separate driver. It needs
Linux CPU-affinity APIs, Python 3.11.9, the same pinned dependencies above,
committed study source files, and a new destination:

```sh
python experiments/reproduce_affinity_blocks.py --output /tmp/affinity-blocks-replica --run
```

The command generates the fixed 52 profiles once and verifies both prior
Linux array/native-CSV hash sets before any metric measurement. A mismatch
stops preparation and is recorded; there is no replacement fit or rounding of
the score outputs. Omitting `--run` still downloads sources and fits detectors,
but stops after freezing the protocol and printing the later run command.

The full run starts exactly five new processes on one permitted logical CPU,
with fixed warm-up and balanced method orders. It schedules 180 measured
workflows and 30 full-workflow warm-ups, retaining every actual observation
and incomplete attempt. It measures the combined batch only;
it adds neither recordings nor public-reference coverage. The analysis unit
is the process block, with all five block estimates retained. Its exact
empirical block-bootstrap enumeration describes this small fixed-runner
sample and does not guarantee statistical coverage or host generalization.

Under the new output's `artifacts/pvldb-research-20261024/strengthening/`:

| Receipt | Meaning |
|---|---|
| `affinity-design-v1.json`, `affinity-blocks-protocol-v1.json` | Frozen schedule, source/input identities, logical-CPU policy and analysis |
| `native-input-audit.json`, `affinity-blocks-protocol-v1.input-identity.json` | Fresh input checks and matches to both prior Linux profile sets |
| `affinity-blocks-linux-v1/blocks/` | Child process receipts, every actual trial, scalar result CSVs, warm-ups, affinity/pool checks and logs |
| `affinity-blocks-linux-v1/cross-block-output-parity.json` | Saved CSV/hash/coverage and across-process scalar checks |
| `affinity-blocks-linux-v1/block-eligibility.json`, `summary.json` | Explicit block eligibility and the four block-level timing contrasts |
| `affinity-blocks-linux-v1/complete.json`, `affinity-reproduction-complete.json` | Successful execution only if all required blocks, bindings and output checks complete |

The frozen source tag is `strength/affinity-blocks-linux-v1`, commit
`ee3031aafb5cc30c7928d36e965d2156cf3ac2ca`. Its workflow responds only to that
explicit tag or an explicit dispatch at that tag. The
[prospective scope and stopping rule](superpowers/specs/2026-10-24-affinity-blocks-followup.md)
and [independent pre-measurement audit](reviews/20261024/affinity-blocks-premeasurement-audit.md)
state the failure policy and verified bounds. A launched workflow or prepared
protocol is not a completion receipt.

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
