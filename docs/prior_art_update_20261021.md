# Sparse VUS prior-art update — 2026-10-21

This update supersedes the 2026-10-20 audit's statement that no attributable Sylligardos acceleration implementation had been located. It does **not** establish that the located code is the exact revision used for the 2025 workshop timing figure. No performance benchmarks were run for this audit; only small correctness witnesses were executed.

## Findings that change the comparator set

1. **Actual Sylligardos-attributed FF-VUS CPU/GPU code is publicly fetchable.** Both `vus_numpy.py` and `vus_torch.py` identify Emmanouil Sylligardos and FF-VUS in their headers. They appear in coauthor Thu T. H. Doan's aVUSi repository, whose README lists Sylligardos among the authors. The native metric differs from the pinned original VUS target; the public wrapper additionally rounds scores, and Torch has a memory-triggered approximation. It must be acknowledged and characterized rather than described as unavailable or inserted into an exact-equality timing leaderboard without qualification.
2. **Benchopt has an external, same-task dense cumulative-sum implementation.** Its `_range_auc_volume(..., thre=n)` computes both original VUS-ROC and VUS-PR using the same summed/clipped square-root buffers, threshold-dependent positive denominator and overlap-only interval merging. It is a stronger independent comparator than reporting only our own dense implementation. The 15 adapter tests pass, including full/sampled thresholds, ties, boundaries and a tampered-source rejection.
3. **Klein fast-VUS remains current at the previously measured revision.** There are no later commits in its public default branch as of this check. It remains a PR-only comparator, unlike the Benchopt pair output.

## Pinned sources and lineage

| Source | Revision/date | Relevant code and status |
|---|---|---|
| aVUSi FF-VUS | `facf4362092525671215031048a75842b9d6d632`, 2026-06-23 | [Torch](https://github.com/doanthihoaithu/aVUSi/blob/facf4362092525671215031048a75842b9d6d632/3_metric_calculator/metrics/ffvus/vus_torch.py), [NumPy](https://github.com/doanthihoaithu/aVUSi/blob/facf4362092525671215031048a75842b9d6d632/3_metric_calculator/metrics/ffvus/vus_numpy.py), [wrapper](https://github.com/doanthihoaithu/aVUSi/blob/facf4362092525671215031048a75842b9d6d632/3_metric_calculator/metrics/ffvus/ffvus_metrics.py), [MIT license](https://github.com/doanthihoaithu/aVUSi/blob/facf4362092525671215031048a75842b9d6d632/LICENSE). File introduction `921e3bc2ec7b9484733a976434b9390fdacaa56d`, 2026-06-13. |
| cloudens FF-VUS copy | `cd6d424e0b3c82a1696f92c5626d2adf9c1a28a2`, 2026-10-07 | [Torch](https://github.com/doanthihoaithu/cloudens/blob/cd6d424e0b3c82a1696f92c5626d2adf9c1a28a2/src/metrics/ffvus/vus_torch.py), [NumPy](https://github.com/doanthihoaithu/cloudens/blob/cd6d424e0b3c82a1696f92c5626d2adf9c1a28a2/src/metrics/ffvus/vus_numpy.py). Both files byte-identical to aVUSi. Introduced `324b1f8ada4313a2772f2cea92aa59cd232df543`, 2026-06-22. No license detected here; aVUSi is the preferred provenance source. |
| Benchopt benchmark_tsfm | `2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94`, 2026-09-29 | [metrics.py](https://github.com/benchopt/benchmark_tsfm/blob/2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94/benchmark_utils/metrics.py#L325). VUS introduced by [commit 2283ad02](https://github.com/benchopt/benchmark_tsfm/commit/2283ad02a6e4546430ea9611fd336d65f4297638), 2026-05-29. Latest metrics-file change 2026-07-09. No repository license file detected; fetch to ignored cache only, do not vendor. |
| Klein fast-VUS | `1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00`, 2026-10-16 | [fast_vus.py](https://github.com/tomlouisklein/fast-VUS/blob/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py). Exact target when `thre=n`; PR scalar only. Prior pin unchanged. |
| Official VUS numerical reference | `467bace0c103f5c2bdb4900306d82939bcac8ff9`, 2026-08-12 | [metrics.py](https://github.com/thedatumorg/VUS/blob/467bace0c103f5c2bdb4900306d82939bcac8ff9/vus/utils/metrics.py). `RangeAUC_volume_opt`, `thre=n`. |

SHA-256 receipts:

| File | SHA-256 |
|---|---|
| aVUSi `vus_numpy.py` | `5140c7e1e0ad4d83f3a256cce3a7bafeff4fe4df0e360cb98c24153958fcf973` |
| aVUSi `vus_torch.py` | `bed53590c5981fbb06eb858007869a90617730f9c5a2738595352323b93e0224` |
| aVUSi `ffvus_metrics.py` | `49cd9c46b2af1dea338f39c36dd4c91e88fe728eed1421aeba0951db9a2dd446` |
| aVUSi `LICENSE` | `034cb0ba268aa950853dace0de40ac90173dff46fae558e49ae3f6f1f6b80815` |
| Benchopt `metrics.py` | `298c746c84a28f9296b015bd70eac984d27be5452e3ca42c853de05328c194a8` |
| official VUS `metrics.py` | `bd547c9746fc1b9bbce2895e20cb156f97d23365d5dce8c2a3fab90622ccdced` |

## Algorithm and semantic comparison

Let `n` be input length, `H` the number of unique thresholds, `L` the maximum width, and `Q` the maximum-buffer support size. Complexity descriptions below are static code analyses, not measured speed claims.

| Property | Original target / Sparse VUS | FF-VUS NumPy/Torch | Benchopt | Klein |
|---|---|---|---|---|
| Thresholds | All original score tie groups for exact target | Native all unique scores; public wrapper rounds to two decimals first | Rank grid, default 250; `thre=n` covers exact tie groups | Rank grid, default 250; `thre=n` exact |
| Buffer length | Radius `floor(w/2)` for width `w=0..L` | Radius `s` for slope `s=0..L`, optional step | Original | Original |
| Ramp at distance `d` | `sqrt(1-d/w)` | `1-(1-zita)d/s`, default `zita=1/sqrt(2)` | Original | Original |
| Overlapping ramp values | Add then clip to one | Maximum / nearest boundary | Original | Original |
| Positive denominator | `p+B_predicted/2` | Same denominator in dynamic/dynamic_plus | Same | Same |
| Existence segments | Expanded original intervals merge only on overlap | NumPy optimized uses explicit overlap geometry; Torch labels connected components, including adjacent support | Original | Original |
| PR integration | Right endpoint staircase | Default right endpoint; NumPy has optional trapezoids | Right endpoint | Right endpoint |
| Native output | ROC+PR | Actual compute is PR only; NumPy accepts a metric flag but does not use it in compute | ROC+PR | PR only |
| Main acceleration | Remove thresholds without support events; retain exact off-support counts | Dense width/threshold matrices, safe support masks, batched matrix multiplication; GPU tensor operations | Full-series sorted cumsums, per-segment maxima + binary searches | Maximum-support sorted cumsums plus global score sort |
| Numerical/approximation contract | Float64 algorithmic exactness, explicit bounds in optional approximation | Torch creates float32 buffers and automatically interpolates existence across widths when memory estimate exceeds a threshold; no supplied error bound | Float64 NumPy | Float64 NumPy |

FF-VUS's global mask does not eliminate all off-support threshold work: it constructs score-threshold masks for off-support scores to accumulate false-positive counts. Its unapproximated Torch existence stage can construct a width × threshold × support tensor. Native `max_thresholds=200` only emits a warning, recommending score rounding; it is not an exact event-elimination mechanism. The NumPy default precomputed slopes do not offer square-root/sum-and-clip geometry. Changing `zita`, `existence`, `conf_matrix` or `interpolation` cannot generally restore all original semantics. The NumPy module's relative `.utils.utils` dependency is absent from the pinned `ffvus` subtree, so it is not importable as packaged without resolving that missing utility. Torch includes its timing decorator and ran directly.

## Reproducible semantic witnesses

`experiments/ff_vus_audit.py` fetches verified source into `.cache/ff_vus`, executes the unchanged Torch implementation on CPU and the unchanged pinned official implementation, and writes a receipt. These are numerical correctness probes, **not** CPU/GPU speed comparisons.

```sh
python experiments/ff_vus_audit.py --fetch --output artifacts/ff_vus_audit_20261021.json
python experiments/benchopt_vus_adapter.py --fetch
python -m pytest tests/test_ff_vus_audit.py tests/test_benchopt_vus_adapter.py -q
```

Observed with NumPy 1.26.4 / PyTorch 2.10.0 on CPU:

- **Wrapper rounding at width zero:** labels `[0,1,0]`, scores `[.101,.102,.001]`. The wrapper-equivalent two-decimal scores are `[.10,.10,0]`; FF-VUS PR is `0.5`, original exact PR is `1.0`. This does not depend on buffer shape.
- **Native unrounded input:** labels `[0,0,0,1,0,0,0]`, scores `[0,1,5,4,3,2,-1]`, maximum parameter 2. FF-VUS PR `0.7200067639350891`; original/Sparse PR `0.5923495156295323`. Same numerical width is not the same physical radius.
- **Matching physical radius still differs:** on that seven-point input, FF slope 2 has distance-one weight `0.8535534143447876`, while original width 4 has `sqrt(.75)=0.8660254037844386`. Their single-width PRs are `0.8829716444015503` and `0.8925296679207713`. Hence a width rescaling alone is insufficient.
- **Memory approximation:** a single anomaly at index 2, prediction only at index 4, slopes 0/1/2. Calling the unchanged existence function with a large memory allowance yields `[0,0,1]`; forcing its documented low-memory branch yields `[0,.5,1]`. This shows an actual intermediate-width change, not only a floating-point discrepancy. The probe changes the allowance for the internal function to exercise both branches; it does not claim the small full input triggers fallback under normal RAM availability.

The combined scoped run passed **17 tests** (one third-party dateutil deprecation warning). This is not a claim that the whole evolving research branch was tested by this agent. No GPU execution or timing evidence was obtained.

## What remains unknown

The primary [2025 PhD workshop paper, Section 4](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/PhD/PhD25_17.pdf) reports preliminary CPU/GPU speedups, but does not pin code, threshold granularity, data types or equality/error contracts. The located header attribution and coauthor repository establish relevant prior code. They do **not** prove this exact revision produced that figure, nor that no newer private or unindexed implementation exists. The aVUSi README has a commented-out ICDE citation; that is not evidence of accepted publication. No public follow-up with the exact original-metric GPU contract was located in the inspected author publication lists and code search.

The previously inaccessible [tutorial repository](https://github.com/sylligardos/anomaly-detection-tutorial/tree/14f4d663df154a2bc8e8d9789485798bd4b052e4) is now inspected. Its Paris notebook imports `tsb_kit.vus.metrics.get_metrics`; its newer notebook uses sklearn and commented aeon range-metric imports. It does not contain FF-VUS.

Other discovered candidates screened:

- [aeon `_vus_metrics.py`](https://github.com/aeon-toolkit/aeon/blob/fdac066b39d311ecae2d284c8d49a3173488b62a/aeon/benchmarking/metrics/anomaly_detection/_vus_metrics.py) uses a static positive denominator, fixed 250 threshold sampling and trapezoidal PR. It is a different target and a nested threshold/width implementation.
- [KDIS TSADMetrics](https://github.com/kdis-lab/TSADMetrics/blob/7b200ba1f90b25c53059c12458ec151b263e2c6d/tsadmetrics/utils/functions_vus.py) contains the original nested threshold/width algorithm, not another sparse cumsum accelerator.
- [FTSAD](https://github.com/EmorZz1G/FTSAD/blob/b6eda3ff334f282044587e27e55a92ca0f7cbfa1/src/metrics/basic_metrics.py) imports Torch but its VUS functions retain NumPy nested loops; a Torch import alone does not establish GPU VUS.
- [ISTAD diagnostic](https://github.com/yuanyuanyuantang/ISTAD/blob/6695cf44266436598fa031d6bb9910abb9be08d9/analysis/compute_vus.py) implements a different range-coverage PR diagnostic with 120 quantile thresholds.
- [HVUS](https://github.com/mike2016/HVUS/blob/7c45dae54b925dcb38bbb5ac57f39e7c7ec1794a/HVUS.py) concerns ordered multiclass ROC hypervolume, not anomaly-buffer VUS.

## Credible research delta and decision

**Go:** exact original-metric evaluation, compared with actual Klein and Benchopt sources and the official reference; explicitly separate PR-only and paired outputs. The narrow algorithmic contribution is event elimination beyond generic/support cumsums, exact treatment of off-support negatives and ties, and reuse in a proved error-bounded width evaluator. A compiled PR-only implementation can make model-selection comparisons materially fairer. Show prep and fallback costs, compilation policy, peak memory, held-out domains, full widths and hardware configuration. A data-dependent dispatcher should be fixed using development cases before held-out evaluation.

**Do not claim:** first fast VUS, first support restriction, first cumulative-sum VUS, fastest VUS regardless of semantics/hardware, or acceptance. The current discoveries strengthen the prior-art discussion while expanding required comparisons. FF-VUS's native approximation cannot be called faster or slower for the exact original task without a separately defined fidelity contract. An original-semantics adaptation of FF-VUS matrix kernels would be a new adapted baseline, clearly labeled and parity-tested, not the unmodified prior method.

A defensible SOTA claim would require a predeclared, bounded task such as full-threshold original VUS-PR CPU evaluation on a specified held-out benchmark, beats the strongest measured same-task baselines with uncertainty and total-time accounting, and states unresolved GPU/private-code scope. Whether the current research clears that gate remains open; it has not been demonstrated by this audit.
