# External workload feasibility and frozen raw selection

2026-10-24. This is source discovery and an executable workload design, not a measured performance result. No new detector scores, metric outcomes, or timings were generated. No mock-review files were used to select the workload.

The immediately executable choice is **26 cached real-data arrays from WSD (12), Stock (12), and MSL (2), scored by unchanged public TSB-AD FFT and COPOD implementations and imported into the native TimeEval recalculation workflow**. It adds three collections absent from the current NAB/SMAP/SMD panel and two public score-producing procedures absent from the eight authored procedures. Its inference target is the fixed workload: repeated wall-clock uncertainty does not establish generalization to a population of independent recordings. WSD and Stock raw-data licensing remains unresolved; publish references, acquisition instructions, hashes, and the adapter rather than redistributing their arrays.

## Frozen selection and reuse audit

The machine-readable receipt is [source-discovery.json](../../../artifacts/pvldb-research-20261024/strengthening/source-discovery.json). Its selection SHA-256 is `ed9eb0e9d906c3bd321bf6446cb4bfbbabdeddef154e17fa8ef1fb2f9e5e196c`.

Before score generation or timing, prespecify WSD, Stock, and MSL. Exclude prior selected names and every candidate with an exact binary-label match, exact float64 observation match, or per-vector z-normalized observation match after rounding to ten decimal places. Sort remaining members by `(length, ID)`; if there are more than twelve, select indices `floor(i*(m-1)/11)` for `i=0..11`; otherwise retain all. This is a length-spanning selection, not a random or representative sample. Neither score cardinality nor metric values nor timings enter selection.

Compared against 563 provenance entries: 350 previously selected TSB-AD names, including cases excluded from the older 308 valid score panel; 12 mTSBench external inputs; 128 MSAD published-score cases; and all 73 current full-precision cases. This is deliberately broader than comparing only the 308 successful cases. The current raw input/protocol and prior identity-index sources are named in the JSON. The prior MSAD index was reused as an existing receipt; the new candidate comparisons and current73 hashes were recomputed from locally cached raw arrays.

All 26 selected arrays have no match under the stated contract. This does **not** rule out arbitrary cropping, transformations beyond affine standardization, another sensor from the same source recording, or common underlying events. Source-family reuse remains: earlier experiments already included WSD, Stock, and MSL. The TSB-AD paper itself describes WSD time series as similar. Do not call this a wholly new benchmark source, an independent population, or an original-recording holdout.

The complete residual inventory is preserved in the JSON. Counts after prior-name and identity exclusions are WSD91, Stock12, YAHOO150, UCR120, IOPS2, MSL2, SVDB2, MITDB1, NEK1, TAO1, SED1, MGAB1, TODS1. YAHOO mixes real and synthetic data; UCR is predominantly artificially anomalous; SED/MGAB/TODS are not appropriate for a claim requiring new real recordings. Every remaining Exathlon, LTDB, and OPPORTUNITY candidate matched prior observations or labels and was excluded. No claim about the 150 Yahoo cases being A1-real is justified by their curated numeric IDs.

The chosen cohort has 386,447 rows, 3,857,983 raw CSV bytes, and 863,937 compressed ZIP-member bytes, already present in `cache/TSB-AD-U.zip`. No new raw download is needed. Full archive source: [TSB-AD-U.zip](https://www.thedatum.org/datasets/TSB-AD-U.zip). The earlier cached archive is 72,900,868 bytes; preserve its existing archive hash and each selected raw-member hash.

| Collection | Exact series ID | Rows |
| --- | --- | ---: |
| WSD | `096_WSD_id_68_WebService_tr_1341_1st_1441` | 10,744 |
| WSD | `076_WSD_id_48_WebService_tr_3821_1st_7083` | 15,285 |
| WSD | `120_WSD_id_92_WebService_tr_2329_1st_2429` | 17,438 |
| WSD | `038_WSD_id_10_WebService_tr_4042_1st_4142` | 18,084 |
| WSD | `115_WSD_id_87_WebService_tr_2252_1st_2352` | 18,214 |
| WSD | `034_WSD_id_6_WebService_tr_4559_1st_8461` | 18,236 |
| WSD | `057_WSD_id_29_WebService_tr_2229_1st_2329` | 18,236 |
| WSD | `071_WSD_id_43_WebService_tr_3387_1st_3487` | 18,236 |
| WSD | `101_WSD_id_73_WebService_tr_1513_1st_1613` | 18,236 |
| WSD | `124_WSD_id_96_WebService_tr_4559_1st_14350` | 18,236 |
| WSD | `066_WSD_id_38_WebService_tr_3320_1st_3420` | 18,302 |
| WSD | `126_WSD_id_98_WebService_tr_657_1st_757` | 18,883 |
| Stock | `150_Stock_id_2_Finance_tr_500_1st_7` | 10,000 |
| Stock | `153_Stock_id_5_Finance_tr_500_1st_1` | 10,000 |
| Stock | `157_Stock_id_9_Finance_tr_500_1st_19` | 10,000 |
| Stock | `161_Stock_id_13_Finance_tr_500_1st_3` | 10,000 |
| Stock | `163_Stock_id_15_Finance_tr_500_1st_3` | 10,000 |
| Stock | `167_Stock_id_19_Finance_tr_500_1st_7` | 10,000 |
| Stock | `168_Stock_id_20_Finance_tr_500_1st_1` | 10,000 |
| Stock | `152_Stock_id_4_Finance_tr_500_1st_2` | 20,000 |
| Stock | `154_Stock_id_6_Finance_tr_500_1st_38` | 20,000 |
| Stock | `158_Stock_id_10_Finance_tr_500_1st_2` | 20,000 |
| Stock | `159_Stock_id_11_Finance_tr_500_1st_5` | 20,000 |
| Stock | `164_Stock_id_16_Finance_tr_500_1st_8` | 20,000 |
| MSL | `146_MSL_id_7_Sensor_tr_554_1st_1172` | 2,217 |
| MSL | `142_MSL_id_3_Sensor_tr_1525_1st_4575` | 6,100 |

## Score generation contract

Pin [TSB-AD commit ed74348](https://github.com/TheDatumOrg/TSB-AD/tree/ed74348e7876c9268b7a737c77f2f5f56f7fa458), already used in previous source provenance. The live main revision was also checked and is `303dffbfc11612995b17b06633f8c9d0ea0e38e5` dated 2026-10-20. Pinning avoids silently adopting a later method revision. Source-file hashes for the wrapper, both detectors, HP list, and license are included in the JSON.

Use the public API, whose dispatch, normalization, score orientation, and alignment remain unchanged:

```python
from TSB_AD.model_wrapper import run_Unsupervise_AD
fft = run_Unsupervise_AD('FFT', X)
copod = run_Unsupervise_AD('COPOD', X, n_jobs=1)
```

FFT uses the published Fourier-based detector; COPOD uses the published empirical-copula detector. The current eight authored score procedures are isolation forest, LOF, kNN, one-class SVM, PCA reconstruction, k-means distance, histogram density, and shrinkage Mahalanobis. Thus this pair is not merely rerunning those eight with another seed. Source inspection supports lower implementation cost than matrix-profile/self-join or deep training, but no runtime bound has been measured here.

Read original CSV row order. Set `X` to all non-`Label` columns as float64 with shape `(n,1)` and `y` to `Label` as int8. Both public models internally apply the upstream `zscore(axis=0,ddof=0)`, including its existing `np.nan_to_num`; preserve that original implementation, without adding adapter-level repair. Require finite observations, binary labels with both classes, finite one-dimensional score output, and `len(score)==len(y)`. Do not silently drop rows, crop, repair NaNs, smooth scores, add jitter, or choose a replacement method based on its metric result. The public dispatcher can return an error string, so an array/shape/finite check is mandatory. Persist authoritative `.npy` arrays and their hashes before any metric evaluation. Preserve true ties and zero runs from FFT or COPOD; an output being full-precision floating point does not imply that all values are distinct.

The official `Run_Detector_U.py` saves `.npy` outputs without decimal quantization. However, its `Optimal_Uni_algo_HP_dict` has no COPOD entry. Therefore this plan uses the documented public API through a small data/serialization adapter, **not** the unchanged CLI. State that boundary explicitly. If a temporal third procedure is wanted, POLY has published parameters `periodicity=1,power=4`; freeze that addition before any outcomes. SAND and MatrixProfile are legitimate alternatives but introduce greater runtime/dependency uncertainty, particularly on the 650,000-row MITDB candidate.

## Native TimeEval import and whole-workflow comparison

The consumer investigation pins [TimeEval commit 7c36227](https://github.com/TimeEval/TimeEval/tree/7c3622757b1a3afa9a84cbc97ce132d9e379f715). The required reader is [scripts/recalculate_metrics.py](https://github.com/TimeEval/TimeEval/blob/7c3622757b1a3afa9a84cbc97ce132d9e379f715/scripts/recalculate_metrics.py). Source-bound schema details are in `artifacts/pvldb-research-20261024/strengthening/timeeval-schema-feasibility.json` from the separate consumer investigation.

A minimal layout illustration (placeholders, not executed data):

```text
raw/datasets.csv
raw/WSD/096_WSD.test.csv
results/results.csv
results/FFT/default/WSD/096_WSD/1/anomaly_scores.ts
```

```csv
# datasets.csv: comments are explanatory here, not literal CSV rows
collection_name,dataset_name,test_path,train_path
WSD,096_WSD,WSD/096_WSD.test.csv,
```

```csv
# raw test CSV
timestamp,value,is_anomaly
0,1.0,0
1,2.0,1
```

The consumer loads `is_anomaly`; for multivariate extensions retain all observation columns between timestamp and label.

```csv
# results.csv
algorithm,hyper_params_id,collection,dataset,repetition,status
FFT,default,WSD,096_WSD,1,Status.OK
```

`anomaly_scores.ts` contains one float per line and no header. Serialize float64 with `%.17g`, then read it through the actual native reader and require bit-preserving round-trip against the authoritative `.npy` before evaluation. Preserve the public consumer's score-normalization and threshold semantics. `metrics.csv` is optional. Native recalculation skips `Status.ERROR`/`Status.TIMEOUT` rows, and it writes `results.csv` at the end even when its save option is false: isolate writable copies for both arms.

Importing new public-pipeline outputs into this schema is a genuine public consumer experiment, but it is not evidence that the scores were originally produced by TimeEval. Report the import adapter, source commits, transformations, and measured boundary. TimeEval's default `RANGE_PR_AUC` uses `cardinality='one', r_alpha=0`; `FIXED_RANGE_PR_AUC` uses reciprocal cardinality and `r_alpha=.5`. Do not swap them, reuse a speed ratio across their contracts, or call a changed metric equivalent. The faster implementation must preserve the selected native contract, all thresholds, endpoint conventions, tie behavior, scalar aggregation, and winner sets.

The strongest relevant comparisons are (1) the unmodified native TimeEval complete metric list, (2) the same complete workflow with only the matching range-evaluation kernel replaced, and (3) the same-compiler fused-raster exact control under the same contract. Prefix recomputation, exhaustive sweep, and query bucket separate the mechanism; they are ablations, not replacements for the strongest compiled control. Add unchanged TSB-AD/TimeSeAD public checks only where query, alpha, positional weight, and cardinality contracts match. If the method cannot support native `cardinality='one'`, measure the explicitly named fixed-range workflow instead and preserve the native-default result as a failure or separate arm.

Freeze six paired complete-workflow repetitions with alternating arm order before timing. Separate score generation from the stored-score consumer boundary; include disk read, CSV parsing, normalization, all requested metrics, and output write equally in both consumer arms. Record warm-up separately, fixed thread counts, source hashes, hardware, and all failures. Report paired per-repetition total times, ratio, and interval describing repeat-run timing variation on these 26 fixed arrays. A bootstrap over detector outputs or repeated runs cannot create more independent recordings. With only two MSL arrays, show both case results and avoid a population-level MSL confidence claim. Use multiplicity adjustment if making collection-wise inferential statements, but that does not cure source dependence.

## Three materially distinct routes

| Route | Concrete data and score source | Feasibility and what it adds | Limitation |
| --- | --- | --- | --- |
| A: frozen public-pipeline import (recommended now) | The 26 IDs above, unchanged public FFT + COPOD, native TimeEval reader | Already cached; 386,447 rows; no score archive download; new score-producing procedures and 3 collections outside current73 | Same benchmark source and previously seen families; fixed-workload inference; WSD/Stock raw license unresolved |
| B: genuinely precomputed published scores | [MSAD pinned source](https://github.com/boniolp/MSAD/tree/8141b94eb3d2b1811f81ffcf7bc8aa5dcbd6c204), archive ID `1PQKwu5lZTnTmsmms1ipko9KF712Oc5DE`, 12 published methods | Existing ZIP central directory allows bounded member acquisition. Unused-recording candidates before the broader TSB reuse audit include MITDB100/109/111/118/119 and SVDB801/802/803/804/805. Those first five from each family need about 18.1 MB and 7.6 MB compressed raw+all-score payload respectively | Same source as old128; prior panel was rounded to at most101 values. Preserve quantization; useful real low-cardinality counterexample, not full-precision evidence. Daphnet has only4 unused eligible recordings after old128 source-block exclusions, not5. Exact/crop/label reuse audit still required before a final panel |
| C: native TimeEval or multivariate extension | [TimeEval public raw share](https://my.hidrive.com/share/ma4p8w4qqb), NASA-MSL/MITDB/SVDB or [TSB-AD-M](https://www.thedatum.org/datasets/TSB-AD-M.zip) | TimeEval supplies27 MSL,48 MITDB,78 SVDB source records before reuse exclusions; could select >=5 original records per family and run native algorithms. TSB-AD-M lists MSL16/MITDB13/SVDB31/Exathlon27 | Larger acquisition plus native score generation. Multivariate dimensions do not prove new source recordings. No public native score archive found. Not immediately executable within this discovery scope |

For route B the remaining Daphnet source blocks are `S06R01E2`, `S08R01E0`, `S09R01E2`, and `S09R01E4`; the first lexicographic eligible channel per block costs about 566 KB total compressed raw+12-score payload. Do not count different channels from a single recording as independent records. MITDB and SVDB examples are candidates, not yet certified disjoint from the 350-case TSB provenance index. No new score members were downloaded here.

The live TimeEval share was enumerated through its public, readable, password-free metadata interface: 29 root members, including raw ZIPs, dataset indexes, and `tsad-evaluation-results.csv` (20,689,358 bytes). It does not contain an `anomaly_scores.ts` tree or score archive. Aggregate metric CSV values are not substitute detector scores, and none were used for selection. Exact raw archive sizes: NASA-MSL754,244; Daphnet16,157,269; MITDB184,333,319; SVDB107,769,431; Exathlon110,922,091 bytes. See machine-readable direct URLs. MITDB ignored a one-byte Range request; three other probes timed out. Reads were bounded; no large archive was downloaded.

TSB-AD-M's advertised response size is540,383,983 bytes. A Range probe returned200 and was stopped after15,000 bytes. The full200-case metadata list was read, but no raw multivariate cohort or source-disjointness claim was produced. A full540 MB acquisition is unnecessary for route A.

## Provenance and license evidence

[TSB-AD's primary paper](https://papers.nips.cc/paper_files/paper/2024/file/c3f3c690b7a99fba16d0efd35cb83b2c-Paper-Datasets_and_Benchmarks_Track.pdf), AppendixD.1, identifies WSD as real KPIs from internet companies, Stock as transaction traces, and MSL as Mars telemetry. It also describes WSD similarity and the benchmark's curation, including possible segmentation and label changes. Thus “real observations” is supported, while independence of curated files is not.

The [official dataset table](https://thedatumorg.github.io/TSB-AD/) lists WSD and Stock license as `None`. The WSD original [AnoTransfer-data repository](https://github.com/alumik/AnoTransfer-data) is public and archived; its recursive512-entry tree has no license or README. Stock links to [WRDS](https://wrds-www.wharton.upenn.edu/), which is a data platform, not a dataset-level grant. Yahoo's original catalog was unavailable in this check, and no reliable curated-ID-to-A1 mapping was found. Therefore Yahoo is excluded from the real-data selection. TSB-AD's Apache2.0 code/curation license does not silently relicense these raw sources.

MSL's original [Caltech license text](https://github.com/khundman/telemanom/blob/master/LICENSE.txt) permits redistribution/use under its stated notice and endorsement conditions. [MITDB](https://physionet.org/content/mitdb/1.0.0/) and [SVDB](https://physionet.org/content/svdb/1.0.0/) are identified as Open Data Commons Attribution1.0 in the official benchmark table; SVDB's original PhysioNet license was directly verified. The MITDB original-page browser request timed out, so its original-page text was not independently re-read. [TimeEval's dataset page](https://timeeval.github.io/evaluation-paper/notebooks/Datasets.html) supplies source links and says its preprocessing uses MIT except stated exceptions; original dataset terms still require preservation.

No publication, detector-quality improvement, or end-to-end speedup is claimed by this report. The concrete next step is generate and freeze the52 public detector arrays, verify the TimeEval round-trip, then run the paired full-workflow comparison without changing the selected IDs or metric contracts based on outcomes.


## Source import receipt and builder check

At the parent's explicit follow-up request, the unchanged FFT/COPOD dependency closure was fetched to new `.cache/strengthening-tsbad`: 11 files, 103,299 bytes. `source-manifest.json` pins every URL/hash; `import-smoke.json` records a successful import-only check at 2026-10-24T07:33:44Z. No detector `fit`, score calculation, or numerical timing was run. Use `PYTHONPATH=.cache/strengthening-tsbad:.cache/pvldb-consumer-deps`; the second path supplies the already available statsmodels0.14.6. Original `.cache/tsbad-consumer` was untouched. This cache contains the dependency closure for these two methods only, not every lazily imported TSB-AD detector. The JSON receipt records actual Python and numerical-package versions. All selected within-panel exact-label, exact-observation, and normalized-observation hashes are distinct, subject to the source/crop dependence limits above.

Builder review of `docs/superpowers/specs/2026-10-24-pvldb-strengthening-design.md`: the three routes and preservation/no-concurrent-timing constraints are appropriate. Before measurement, the route-specific protocol still needs explicit (1) native metric list with alpha/cardinality/position/query contracts, (2) bound input/score/adapter hashes and hardware/thread/warm-up/timeout settings, (3) six paired fixed-workload trials plus the exact interval calculation, (4) failure handling for error strings, nonfinite/length-invalid outputs, all-tied profiles, timeouts, and partial cohorts, and (5) measured I/O boundary and WSD/Stock redistribution treatment. These are concrete measurement requirements, not requests to change the selected cohort after outcomes. The discovery receipt already binds the cohort and public score source; the consumer protocol should reference it rather than reselect cases.
