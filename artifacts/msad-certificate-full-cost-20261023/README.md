# Complete-call cost of integer certification

All **5,400 / 5,400 calls** completed successfully: the same fixed thirty series, twelve published score configurations, five repetitions, and three methods. This is 360 complete three-way series/model comparisons. Every timed integer endpoint and retained-state count matches the corresponding frozen accuracy ledger; every timed numerical answer matches the main study exactly. An independent standard-library auditor reconstructed the full result without importing producer or metric code.

| Time ratio | Median | Geometric mean | Equal-family geometric mean |
| --- | ---: | ---: | ---: |
| 250-rank certificate / full-grid certificate | 0.826371 | 0.815328 | 0.819679 |
| 250-rank certificate / numerical exhaustive | 2.063173 | 2.682586 | 2.666981 |
| Full-grid certificate / numerical exhaustive | 2.712854 | 3.290191 | 3.253689 |

Ratios below one favor the numerator. These are descriptive summaries on this fixed one-host panel; no confidence interval was specified. Partial certification saves modest time compared with full certification, while the full-grid accuracy study certifies many more decisions. Both integer methods cost more than numerical exhaustive evaluation. The guarantee differs: integer intervals enclose the ideal real-arithmetic target, while the floating evaluator is numerically exhaustive.

The sum of 360 per-case median seconds is 4.685883 (partial certificate), 5.637602 (full certificate), and 3.126725 (numerical exhaustive). These sums are **not** measured disk-to-result workflow times. The complete recorded collection took 71.918064 seconds including loading/hashing, source checks, synthetic warmup, IPC, and durable result writes.

## Fixed protocol and output checks

- Protocol: `protocol.json`, SHA256 `651cb0cc4d5bde61195f8ef0da64a76694886dc06412b6314e3be22c27467c7a`.
- Records: `records.jsonl`, SHA256 `f837144c4d4d08fd1dc00b647f563145defc99e39d64b02a61636155542b1c31`.
- Report: `report-f837144c4d4d08fd.json`, SHA256 `ec1baed881703f27427f6ef23762547de6cc66a81a853063eedf6ed5dfddd1ec`.
- Independent audit: `independent-cost-ledger-audit.json`, SHA256 `0370f1839715ac68d8f5a875ba08b76c4b794da1e8347c793d9e5a96c1b81cc9`.
- `run-inputs.json` binds the three completed reference logs and records the host/software environment. `collection.jsonl` records overall collection wall time separately.

The acquisition panel and thirty-case subset predate metric outcomes. The earlier two-method cost protocol is preserved at `../msad-certificate-cost-20261023/protocol.json` and remains unexecuted. Independent review requested the full-grid integer baseline before any cost calls. The three-method design retained the same cases/repetitions; full-grid accuracy aggregates arrived while its implementation was being finished, before the final protocol hash. No timing result existed before this addendum froze. No observed timed run was discarded or selected between these protocols.

Each randomized block contains `certified_sampled_pr(..., thresholds=250)`, the same function at `thresholds=n`, and `sparse_pr_radix_jit`. Scores and labels are already loaded outside the timer. Every timed call includes its own public-API validation/preparation, integration, and (for certificates) integer root brackets and endpoint assembly. The reused worker warms both code paths on a fixed synthetic input, limits native/Numba thread pools to one, and has a thirty-second per-call watchdog. Other research computation was paused for this run.

Hardware was an Apple M1 Pro (`MacBookPro18,3`), 16 GiB memory, ten physical/logical CPUs, macOS 26.6.1 (25G76). The timer uses one compute thread. This is a warm desktop measurement, not a cross-hardware result.

## Verification and reproduction

From the repository root, the deterministic reporting audit is:

```sh
python experiments/msad_certificate_full_cost.py report
python experiments/exploration/audit_msad_certificate_full_cost_20261023.py
```

The producer command below resumes only missing scheduled records; it deliberately does not rerun or overwrite completed timed cases:

```sh
python experiments/msad_certificate_full_cost.py run \
  --protocol-sha256 651cb0cc4d5bde61195f8ef0da64a76694886dc06412b6314e3be22c27467c7a \
  --idle-host-confirmed
```

To perform fresh measurements without changing the evidence, save the following as a Python file and run it on an idle host after restoring the hash-verified corpus. It changes only the output location in the imported driver; all frozen sources, inputs, parameters, and reference logs are still verified. Choose a new cache directory for each independent repetition. The filename must be a real file because the worker uses Python multiprocessing `spawn`.

```python
from pathlib import Path
import shutil
import sys

ROOT = Path.cwd()  # repository root
sys.path.insert(0, str(ROOT / "experiments"))
import msad_certificate_full_cost as study

if __name__ == "__main__":
    original_protocol = study.OUT / "protocol.json"
    study.OUT = ROOT / ".cache" / "certificate-cost-independent-repetition-1"
    study.OUT.mkdir(exist_ok=False)
    shutil.copyfile(original_protocol, study.OUT / "protocol.json")
    study.run(
        "651cb0cc4d5bde61195f8ef0da64a76694886dc06412b6314e3be22c27467c7a",
        idle=True,
    )
```

See `../../docs/msad_score_corpus_reproduction_20261023.md` for input acquisition and `../../docs/msad_score_interpretation_20261023.md` for precision/orientation/source-overlap limits. Fresh timings vary by host; the integer/scalar output identity checks remain required.

## Source and data attribution

The scores come from the authors’ [MSAD release](https://github.com/boniolp/MSAD/tree/8141b94eb3d2b1811f81ffcf7bc8aa5dcbd6c204): Sylligardos et al., *Choose Wisely: An Extensive Evaluation of Model Selection for Anomaly Detection in Time Series*, PVLDB 16(11), 2023, 3418–3432, [DOI 10.14778/3611479.3611536](https://doi.org/10.14778/3611479.3611536). Raw observations and published score vectors remain in ignored cache; this directory contains derived measurements, protocols, and audit receipts. The source repository’s MIT code license is not interpreted as relicensing underlying datasets. See `../msad-corpus-20261023/ATTRIBUTION.md` for the original release and licensing scope.
