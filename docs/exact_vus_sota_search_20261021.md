# Exact VUS evaluator search — 21 October 2026

**Finding:** this additional, bounded primary-source search did not identify a
new eligible exact evaluator beyond official VUS, DTAIAnomaly, Klein fast-VUS
and Benchopt. It did identify more implementations carrying the VUS name,
including native Rust and an official vectorized routine, whose semantics
exclude them from this particular comparison. This is **not** verification of
a global speed record. No timing, correctness experiment, installation, large
download, GPU computation or author contact was performed for this search.

## Target and inclusion rule

The target is the numerical contract of official
[`RangeAUC_volume_opt(..., thre=n)` at `467bace`](https://github.com/thedatumorg/VUS/blob/467bace0c103f5c2bdb4900306d82939bcac8ff9/vus/utils/metrics.py#L382):
every original score tie group; every integer width `0..L`; square-root ramps
with radius `floor(w/2)`; summed ramps clipped at one; threshold-dependent
positive mass; overlap-based expanded-segment existence; trapezoidal ROC and
right-endpoint PR integration. Here “exact” concerns this exhaustive discrete
metric, subject to the declared floating-point implementation, not exact real
arithmetic. A different ramp, static denominator, score rounding, sampled
widths or different PR integration is a different task.

PR-only and paired ROC/PR outputs must be reported separately. Increasing a
grid parameter to `n` in unchanged upstream code is allowed; changing its
metric equations would create an adapted baseline.

## Current eligible sources

GitHub's public commits API was queried afresh on 21 October, with an explicit
cutoff and `per_page=1`. These default-branch revisions match the earlier
audits. Dates below are UTC commit dates, **not independently established
first-publication timestamps**.

| Source | Current revision and date | Inclusion and limitation |
|---|---|---|
| [Official VUS](https://github.com/thedatumorg/VUS/blob/467bace0c103f5c2bdb4900306d82939bcac8ff9/vus/utils/metrics.py#L382) | `467bace0c103f5c2bdb4900306d82939bcac8ff9`, 2026-08-12 | Reference `opt`/`opt_mem` paths; set `thre=n`. Their supplied grid is otherwise 250. Repeated threshold scans and, for `opt_mem`, stored predictions. The separate `opt_time` path is excluded below. |
| [Klein fast-VUS](https://github.com/tomlouisklein/fast-VUS/blob/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py) | `1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00`, 2026-10-16 | PR-only, `thre=n`; support restriction and cumulative sums are established prior code. Global sorting, threshold-length arrays and width-dependent dense coverage remain. |
| [Benchopt benchmark_tsfm](https://github.com/benchopt/benchmark_tsfm/blob/2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94/benchmark_utils/metrics.py#L325) | `2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94`, 2026-09-29 | Paired output, `thre=n`; independent dense sorted-prefix implementation. Latest metrics-file change: [`2065604c`](https://github.com/benchopt/benchmark_tsfm/commit/2065604c48695f71118b6e92f9e1b62978897798), 2026-07-09 (formatting). |
| [DTAIAnomaly](https://github.com/ML-KULeuven/dtaianomaly/blob/557b435790bebc57307d8e7f22047273ac923f36/dtaianomaly/evaluation/_volume_under_surface_metrics.py) | `557b435790bebc57307d8e7f22047273ac923f36`, 2026-10-13 | Set `max_samples=n`; Numba support scans remain per threshold. Its latest evaluator change is [`81b71289`](https://github.com/ML-KULeuven/dtaianomaly/commit/81b712891f977108a66f451a3c578bef54a0b025), 2026-10-13. `parallel=True, fastmath=True` and output scope must be disclosed; no runtime result is inferred from compiled code alone. |

Fresh source bytes matched the existing receipts for official VUS, Klein and
Benchopt. DTAIAnomaly's inspected file SHA-256 is
`728045cd8ddf0caa6aab10a9ab66f5f876ee77e5d0ae80dfbce5029eab9ed5b7`.
Previous adapter parity evidence and the fuller semantic comparison remain
in [the 20 October audit](fast_vus_prior_art_20261020.md) and
[the 21 October update](prior_art_update_20261021.md); those tests were not
rerun here.

## Additional code screened

These exclusions follow source inspection, not timing or assumptions about
implementation language.

| Candidate, pin and source | Finding |
|---|---|
| [Official `RangeAUC_volume_opt_time`](https://github.com/thedatumorg/VUS/blob/467bace0c103f5c2bdb4900306d82939bcac8ff9/vus/utils/metrics.py#L554), same official pin | Dense vectorized routine, but `N_labels` is computed outside the threshold calculation (lines 588–593), `P_new` is static (625), and PR uses adjacent-precision trapezoids (607–609). Exclude from the dynamic-label/right-step target even though it lives in the reference repository. |
| [TAB](https://github.com/decisionintelligence/TAB/blob/5a7e6f80c405eed7c4dd1390f69fbba2fd8ddcf2/ts_benchmark/evaluation/metrics/vus_metrics.py#L313), `5a7e6f80c405eed7c4dd1390f69fbba2fd8ddcf2`, 2025-11-26 | Static `P_new=(P+sum(labels))/2` and hardcoded 250 thresholds (317, 365, 418); repeated scans. The [PVLDB 2025 paper](https://www.vldb.org/pvldb/vol18/p2775-hu.pdf) contributes a detector benchmark, not a newly disclosed exact dynamic-label evaluator. |
| [ViCO](https://github.com/Cedarrr1/ViCO/blob/2c81ee8ec9dff2b607a0ad1a2340ca74e015c791/evaluation/metrics/vus_metrics.py#L313), `2c81ee8ec9dff2b607a0ad1a2340ca74e015c791`, 2026-10-09 | Its author README labels the detector CIKM 2026; evaluator code again has static positive mass (319) and hardcoded 250 thresholds (367, 420). No new eligible acceleration found. |
| [anomstream Rust VUS-PR](https://github.com/ebpfsentinel/anomstream/blob/85fac0f32549a2c3a1cf0394ff874a49605bb3c1/core/src/vus_pr.rs), `85fac0f32549a2c3a1cf0394ff874a49605bb3c1`, 2026-10-05 | Does visit all score-sorted prefixes, but uses binary dilation, covered-positive recall, trapezoidal PR, trapezoidal width integration, and individual points rather than atomic tie groups (83–93, 124–179). These are substantive differences. A direct algebraic witness, **not an executed test**: at width zero, labels `[0,1]`, scores `[2,1]` give its trapezoidal PR `1/4`, versus original right-step PR `1/2`. |
| [TSFM evaluation harness](https://github.com/Thanatosc/tsfm-anomaly-detection/blob/0df39db55c1fe5ca8bbb5080c2629efc647dcc46/killtest/metrics.py#L87), `0df39db55c1fe5ca8bbb5080c2629efc647dcc46`, 2026-08-06 | `vus_pr` averages eight sampled widths by default; `range_pr_auc` uses quantile thresholds. Its README reports rank correlation against reference, which is not numerical equality. Exclude native configuration. |
| [GraGOD](https://github.com/GraGODs/GraGOD/blob/ec8cd452a410ba903a31beb097a010ba0448c095/gragod/metrics/system_calculator.py#L182), `ec8cd452a410ba903a31beb097a010ba0448c095`, 2025-06-13 | The ICPRAM 2026 framework wraps TimeEval 1.4.2 in compatibility mode; its effective 250-threshold, static-mass, trapezoidal-PR contract is different. The SCITEPRESS trail is resolved below. |

The prior update already screens aeon, KDIS TSADMetrics, FTSAD and ISTAD;
this search did not uncover an eligible faster revision of those sources.
No new timing order is asserted for any row.

### SCITEPRESS 143120: evaluator trail resolved

The publisher's indexed primary text identifies
[Bello et al., *GNNs for Time Series Anomaly Detection: An Open-Source Framework and a Critical Evaluation*, ICPRAM 2026](https://www.scitepress.org/PublishedPapers/2026/143120/).
Direct PDF opening still returned HTTP 403 in this check; no full-PDF review
is claimed. Its GraGOD source, however, is inspectable at the pin above.

Both [system](https://github.com/GraGODs/GraGOD/blob/ec8cd452a410ba903a31beb097a010ba0448c095/gragod/metrics/system_calculator.py#L182)
and [per-class](https://github.com/GraGODs/GraGOD/blob/ec8cd452a410ba903a31beb097a010ba0448c095/gragod/metrics/per_class_calculator.py#L261)
wrappers import TimeEval's `RangeRocVUS`/`RangePrVUS` with
`compatibility_mode=True`. The [manifest](https://github.com/GraGODs/GraGOD/blob/ec8cd452a410ba903a31beb097a010ba0448c095/pyproject.toml#L28)
specifies `timeeval="^1.4.2"`; the [lockfile](https://github.com/GraGODs/GraGOD/blob/ec8cd452a410ba903a31beb097a010ba0448c095/poetry.lock#L4247)
resolves exactly 1.4.2.

GraGOD's default argument is 100 samples, but
[released TimeEval source](https://github.com/TimeEval/TimeEval/blob/4b4154199eb5dd438e25460307a26cc084cd02a7/timeeval/metrics/vus_metrics.py#L75)
**forces 250 in compatibility mode** (75–81), computes positive mass before
the threshold loop (91), and integrates PR trapezoidally (119). Consequently,
changing only `max_samples` cannot recover the present exhaustive target in
this mode. The `v1.4.2` tag resolves to `4b4154199eb5dd438e25460307a26cc084cd02a7`;
its evaluator bytes match the [PyPI 1.4.2](https://pypi.org/project/TimeEval/1.4.2/)
source distribution, whose SHA-256 is
`27cbafe885d157db872c594523eb978e8c3dceba710fddb594a7b3e8890ae718`.
Only the 146 KB archive was read in memory; nothing was installed or run.
This closes the implementation-screening gap without adding an exact
acceleration comparator.

## FF-VUS and the published acceleration claim

Public FF-VUS remains available in aVUSi at
[`facf4362092525671215031048a75842b9d6d632`](https://github.com/doanthihoaithu/aVUSi/tree/facf4362092525671215031048a75842b9d6d632/3_metric_calculator/metrics/ffvus)
(2026-06-23); the NumPy implementation's latest path commit is
[`921e3bc2`](https://github.com/doanthihoaithu/aVUSi/commit/921e3bc2ec7b9484733a976434b9390fdacaa56d)
(2026-06-13). The current cloudens copy remains at
[`cd6d424e`](https://github.com/doanthihoaithu/cloudens/tree/cd6d424e0b3c82a1696f92c5626d2adf9c1a28a2/src/metrics/ffvus)
(2026-10-07). Fresh aVUSi NumPy/Torch hashes match the prior audit.

Their headers attribute FF-VUS to Sylligardos. The native geometry is a
linear ramp combined by maximum, rather than square-root sum-and-clip; the
public wrapper rounds scores, and Torch has a memory-triggered existence
interpolation branch. Detailed source evidence and previously executed
counterexamples are in [the prior update](prior_art_update_20261021.md).
Thus FF-VUS is relevant acceleration prior art, but its native output does
not satisfy the present equality contract.

The [2025 VLDB Ph.D. workshop paper, Section 4](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/PhD/PhD25_17.pdf)
reports preliminary CPU/GPU VUS acceleration. It does not identify the code
revision, threshold resolution or numerical equality contract behind those
timings. The current public code cannot retrospectively establish these.
Do not call FF-VUS unavailable, or claim to outperform the reported GPU
result. An original-semantics adaptation would require a separately named,
parity-verified comparator and new measurements.

## Paper and FFT trails

- [VUS, VLDB Journal 2025, Section 4.3](https://arxiv.org/html/2502.13318v1#S4.SS3)
  already contributes static/dynamic region reuse and memory/time tradeoffs.
  Algorithms 2–3 retain threshold-by-width work. The version of record was
  [published 27 March 2025](https://doi.org/10.1007/s00778-025-00907-x).
  It prevents “first accelerated VUS” or “first support restriction” claims.
- The Fourier-transform passage in [Section 4.2](https://arxiv.org/html/2502.13318v1#S4.SS2)
  selects a time-series period/buffer length; it does not present FFT-based
  exhaustive metric integration. Searches below found detector FFT models,
  not another disclosed matching evaluator. This is a search finding, not a
  proof that an FFT acceleration is impossible.
- [EasyAD, PVLDB 2025](https://www.vldb.org/pvldb/vol18/p5431-liu.pdf)
  evaluates automated detector selection. Its method-runtime comparisons
  do not establish evaluator speed. Likewise, the
  [July 2026 adversarial metric audit](https://arxiv.org/html/2607.11969v2#S4.SS3)
  fixes VUS resolution at 250 and identifies TSB-UAD `313f0fd` in its
  availability statement; it is not a newly disclosed fast exact evaluator.
- The official [CIKM 2025 proceedings page](https://cikm2025.org/program/proceedings)
  had no `VUS` text match. The [CIKM 2026 accepted-papers page](https://cikm2026.diag.uniroma1.it/accepted-papers/)
  still displayed `TBD` when inspected, preventing a complete proceedings
  check. [Boniol's current publication list](https://boniolp.github.io/publi)
  was also checked; no new exact-computation follow-up was identified there.

## Search record and limits

Web queries included:

```text
"VUS" "exact" "fast" anomaly detection 2025 2026
"Volume Under the Surface" efficient algorithm all thresholds
"FF-VUS"
"VUS" "Benchopt" metrics
"VUS" "anomaly" "CIKM" 2025 2026 efficient
"VUS" "FFT" anomaly evaluation
"VUS" "fast" "PVLDB"
"VUS" "cumulative" "anomaly"   [github.com, arxiv.org]
"VUS" "efficient" "CIKM"     [dl.acm.org, arxiv.org, github.com]
"VUS" "convolution" "metric"
"VUS" "evaluation" site:vldb.org/pvldb/vol19
"Sylligardos" "2026" evaluation
```

GitHub repository searches used quoted `VUS-PR`, `fast-VUS`, `FF-VUS`,
`VUS anomaly`, and README combinations with `fast`, `Numba`, `FFT metric`,
`RangeAUC_volume`, `CIKM`, `GPU metric`, `Rust metric` and `exact`.
`fast-VUS` returned Klein; `FF-VUS` returned zero even though the known source
exists inside aVUSi. This directly demonstrates why a negative repository
search cannot establish absence. Searches returned at most 30 repositories
per query; broad queries had more results and were not exhaustively paged.
No authenticated global code search was performed.

Metadata was retrieved with
`https://api.github.com/repos/{owner}/{repo}/commits?per_page=1&until=2026-10-21T23:59:59Z`,
adding `path` for file history; source was read at immutable full hashes.
This verifies inspected default-branch history, not every branch, fork,
package mirror, private repository or public visibility date. The discovered
`avusi-icde2027/aVUSi` entry returned HTTP 409 for commits and 404 for README;
no implementation was available from that trail. The SCITEPRESS 143120
evaluator trail was subsequently resolved through indexed publisher text,
GraGOD's wrappers and its released TimeEval dependency, as documented above;
direct access to the publisher PDF remained blocked.

**Claim boundary:** if the formal experiment supports it, report “fastest
among the tested, pinned exact CPU implementations on [declared corpus,
widths, output and hardware]”, with losses, total evaluation cost and
compilation policy. A fixed-binary64 `O(n+(L+1)Q)` construction does not by
itself prove optimality, firstness or a universal runtime advantage; radix
sorting and floating-point key transforms are established techniques, as
documented in [the radix review](radix_prior_art_20261021.md). This search
neither establishes acceptance nor closes the unverified GPU comparison.

## Final lightweight source refresh — 21 October 2026

A fresh online default-branch HEAD check through GitHub's commits API found
no change to the measured/source-audited pins: Klein
[`1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00`](https://github.com/tomlouisklein/fast-VUS/commit/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00),
official VUS
[`467bace0c103f5c2bdb4900306d82939bcac8ff9`](https://github.com/thedatumorg/VUS/commit/467bace0c103f5c2bdb4900306d82939bcac8ff9),
Benchopt
[`2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94`](https://github.com/benchopt/benchmark_tsfm/commit/2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94),
aVUSi
[`facf4362092525671215031048a75842b9d6d632`](https://github.com/doanthihoaithu/aVUSi/commit/facf4362092525671215031048a75842b9d6d632),
and dtaianomaly
[`557b435790bebc57307d8e7f22047273ac923f36`](https://github.com/ML-KULeuven/dtaianomaly/commit/557b435790bebc57307d8e7f22047273ac923f36).
TSB-AD, cloudens, MSADv2 and tsad-template also remain at the already
documented revisions. No new source diff requires a metric or timing audit.

One additional 2026 model-selection trail was resolved:
[KDSelectorAlgorithm](https://github.com/chenyuanTKCY/KDSelectorAlgorithm/tree/c90342282b0ce38ed5e0cbd88982f08f208bec0c),
HEAD `c90342282b0ce38ed5e0cbd88982f08f208bec0c`, 2026-09-10.
Its [metrics.py](https://github.com/chenyuanTKCY/KDSelectorAlgorithm/blob/c90342282b0ce38ed5e0cbd88982f08f208bec0c/utils/metrics.py)
is a legacy nested VUS evaluator: line 294 fixes the positive denominator
using all buffered label mass, line 398 hardcodes 250 thresholds, and
lines 425–427 use trapezoidal PR. It supplies neither the pinned dynamic-mass
target nor a new exact full-threshold accelerator. Its source SHA-256 is
`45210ec762e00e63b052e721b7ee4c1136c1124ddee7baa2e669b4278467a60e`.
This conclusion is from unchanged source inspection; the evaluator was not run.

Primary paper revision checks remain unchanged:
[VUS](https://arxiv.org/abs/2502.13318) is v1 (18 February 2025),
[MSAD](https://arxiv.org/abs/2510.26643) is v2 (2 December 2025), and the
[adversarial metric audit](https://arxiv.org/abs/2607.11969) is v2
(19 July 2026). Boniol's publication list was refreshed; no additional exact
VUS computation method was identified there. The CIKM 2026 accepted-paper
page still displays `TBD`. This lightweight refresh identified no additional
eligible exact CPU comparator; it does not establish global absence.
No benchmark, test suite, measured-source edit or local heavy computation was
performed during the concurrent formal timing runs.
