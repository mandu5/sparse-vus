# Certified threshold-sampling study: reproduction and evidence

This research branch accompanies **When Threshold Sampling Reverses VUS Rankings: Exact and Certified Evaluation of Anomaly Scores**. The [manuscript](../paper/certified_sampling.pdf) is the integrated scientific account; the previous exact-evaluator manuscripts remain separate precursors. Author: Youngmin Ko, Independent Researcher, Republic of Korea.

## Executed findings

The original dynamic VUS-PR contract is pinned: sum-clipped square-root buffers, threshold-dependent positive mass, overlap-only merged components, complete global score ties, right-step PR integration and every integer width from zero through the maximum. The released MSAD scores are reevaluated under this contract; their historical metric tables used a different implementation.

The fixed 128-series panel contains twelve published score configurations per series from sixteen source families. At primary `L=30,H=250`, exactly eight selections have ideal exhaustive regret at least0.01. Full-grid integer endpoints prove this cutoff on all 128 cases (eight above,120 below), certify all 128 unique exhaustive winners, and enclose maximum regret in `[0.3985750301665,0.3985750302756]`. All 36,864 numerical calls,720 independent exhaustive controls and 9,000 main timing calls completed without failures or timeouts. See the [complete main study](../artifacts/msad-sampling-20261023/README.md).

The [full-grid study](msad_full_certificate_study_20261023.md) compares the same rigorous guarantee at partial and exhaustive grids. All 1,536 full-grid and 3,072 partial-grid calls complete. The [mechanism audit](msad_saturation_and_empirical_review_20261023.md) independently verifies all2,976 first-saturation events using raw integer witnesses; adding the first saturation threshold restores three of the eight affected selections and leaves five wrong.

All published score vectors have at most 101 distinct values. A250-rank grid can still omit rare classes. The unchanged128-case primary panel contains 20 bounded endpoint-shift overlaps with earlier physical inputs; the 108 nonmatching descriptive subgroup has four practical errors in two families. Neither quantization nor overlap is hidden by replacing cases.

## Install and test the branch

Use Python 3.11 or 3.12 and a virtual environment. The older `v0.3.0` tag predates the new sampling APIs and evidence.

```sh
git clone --branch research/saturation-20261021 https://github.com/mandu5/sparse-vus.git
cd sparse-vus
git checkout 60e68af3cb2534aa7a889b5a3e177633ce7d12b8
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install '.[accelerate,research]'
python experiments/fetch_reference.py
python experiments/fast_vus_adapter.py --fetch
python experiments/dtaianomaly_adapter.py --fetch
python experiments/benchopt_vus_adapter.py --fetch
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

The continuous-integration workflow tests Python 3.11/3.12, installs the actual built wheel outside the source checkout, and checks rational certificate containment and exact integer ordering. Runtime benchmarks use the recorded Mac environment; a passing Linux test run is not a Linux timing replication.

## Audit the public evidence without downloading the score corpus

```sh
python experiments/audit_certified_sampling_bundle.py \
  --output /tmp/certified-sampling-audit.json
PYTHONPATH=src python experiments/msad_sampling_study.py report
```

The first command uses only Python's standard library. It verifies repository-source/protocol/ledger commitments, all declared keys, eighteen sensitivity cells, exact integer winner/regret comparisons, the 2,976 saturation witnesses, the overlap subgroup and the 5,400-call certificate-cost coverage. It does not execute the original metrics or claim to reacquire the raw data. An ignored upstream-cache source is identified by its pinned digest as an external commitment; the second command verifies that fetched source and reconstructs the original report with the analysis implementation. Neither command appends metric/timing records.

The primary report is [report-283ccfafa5b712e2.json](../artifacts/msad-sampling-20261023/report-283ccfafa5b712e2.json), bound by [completion.json](../artifacts/msad-sampling-20261023/completion.json). Original protocols and earlier partial reports remain immutable. The primary-first execution-order adjustment is documented; it changed no case, criterion, method or retained outcome.

## Reacquire and independently inspect the numerical inputs

Follow [the acquisition reproduction guide](msad_score_corpus_reproduction_20261023.md). The fixed manifest SHA256 is:

```
5617e4fdc0bb082ac910144212546e05cc009622e45b07b672e562a999e6bc59
```

```sh
python experiments/reproduce_msad_corpus.py \
  --manifest-sha256 5617e4fdc0bb082ac910144212546e05cc009622e45b07b672e562a999e6bc59 \
  --cache .cache/msad-reproduction/fresh-check
```

The cache must be new. Omitting `--limit` requests all 128 inputs; a smoke prefix is explicitly labeled partial. The downloader checks original member CRC/SHA and numerical array identity. An independently implemented full-input parser already checked all 1,664 raw/score members and 1,792 arrays, including 189,522,168 score scalars; its receipt is public. Raw observations and scores remain outside Git. Attribution is in [ATTRIBUTION.md](../artifacts/msad-corpus-20261023/ATTRIBUTION.md).

For a new experiment, use a separately named output directory and source/host freeze. The finalized study's paths are deliberately fixed: do not append a new host's timings to the published ledger or silently replace original NPZ paths/digests. Freshly reacquired arrays can directly exercise the public APIs below without modifying any receipt.

```python
from fractions import Fraction
import numpy as np
from sparse_vus.radix import sparse_pr_radix_jit
from sparse_vus.sampling import sampled_pr_radix_jit
from sparse_vus.sampling_bounds import certified_sampled_pr

# Load labels and one named model from a freshly reacquired NPZ.
with np.load("path/to/reacquired.npz", allow_pickle=False) as data:
    labels, scores = data["labels"], data["CNN"]
    numerical = sparse_pr_radix_jit(labels, scores, 30)
    sampled = sampled_pr_radix_jit(labels, scores, 30, thresholds=250)
    bound = certified_sampled_pr(labels, scores, 30, thresholds=len(labels))
    lower = Fraction(bound.lower_numerator, bound.scale)
    upper = Fraction(bound.upper_numerator, bound.scale)
```

The integer interval encloses the **ideal real-arithmetic target**, not necessarily the bit pattern of a particular floating sum. Exact score ties follow binary64 input conversion. For strict comparisons use `cert_a.certifies_greater_than(cert_b)`; do not turn a displayed decimal or epsilon into a proof. Inputs require both binary label classes, finite scores, integer maximum width, and length below 2^31 for fixed-point accumulator safety.

## Timing interpretation

The main fixed subset has 30 series and 360 score vectors, each timed five times per method in randomized order. All calls include validation/preparation/integration, with input decoding and JIT warmup excluded. Exact numerical evaluation's geometric speed ratio against the matched compiled 250-rank evaluator is 1.044, with family-bootstrap interval [1.029,1.062]. The dense comparator computes ROC as well as PR and is not a matched PR-only baseline.

The separately frozen three-method certificate-cost addendum completed 5,400 calls. Geometric cost ratios are 0.815 for partial/full certificate,2.683 for partial certificate/numerical exact, and3.290 for full certificate/numerical exact. These are descriptive one-host ratios. The original two-method proposal remains unexecuted; the addendum specifies all three methods before observing cost outcomes. Full-grid accuracy was already known at final protocol freeze. This stronger audit output costs extra; partial certification is not promoted as a better model selector.

## Manuscript build

```sh
cd paper
tectonic certified_sampling.tex --keep-logs --keep-intermediates
```

The vendored official TMLR template is pinned in `paper/tmlr-style/source.json`. The public manuscript uses its **preprint** mode. Local tests, integer proofs and internal agent reviews are evidence for the manuscript; editorial outcomes are tracked separately. AI assistance in derivation, implementation, orchestration and drafting is disclosed. A submission's author-review declarations must reflect the author's actual review and responsibility.
