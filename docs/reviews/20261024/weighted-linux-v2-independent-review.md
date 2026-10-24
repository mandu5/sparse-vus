# Independent original Linux weighted-v2 reconstruction

The original fresh Linux replay completed successfully in CI run 40079636938 from source commit `f7c900b0c1a22f965eacd859f83da2f58efd8b40`. The original CI report is preserved. A separate `archived-output-report.json` passes the unchanged auditor over 26 recordings, 11,232 records and 156 complete curve files. Maximum curve error is `2.4980018054066022e-15`; detector-winner disagreements are zero. This is the original raster/sweep/bucket study, separate from the later interval-control supplement.

All nine collection/comparison aggregate paired-order intervals are above one. Uniform semantic or recording wins do not follow: MSL grid100 sweep/bucket has one collection-semantic point estimate below one and ten of its twelve semantic intervals include one. MSL id7 loses sweep/bucket on grid100 and raster/sweep on distinct queries. These losses are retained.

A second standard-library reconstruction from saved durations reproduced all 108 semantic and nine aggregate centers within relative/absolute tolerance 1e-13, using `statistics.median` and equal-log geometric aggregation without importing metric or producer code. The CI and archive auditor reports differ in 217 floating-point fields, with maximum absolute difference 1.4210854715202004e-14 and relative difference 9.554457944604463e-16. The only nonnumeric difference is the intended `local_input_bytes_verified`: true in CI and false in the archive-only audit.

Ratios are control time divided by candidate time, so a value above one favors the right-hand method. Six balanced trial orders are summarized by medians; twelve semantic settings receive equal log weight within a recording. The fixed-panel paired-order bootstrap shares sampled trial indices across methods and semantic settings within each recording. Seed 20261024 and 10,000 resamples match the frozen protocol. Original multiplicity correction is three collection aggregates or 36 semantic estimates within each of three comparisons, not jointly across all comparisons or hosts. Recording-reweighting intervals below are sensitivity summaries, not population confidence statements. Six orders and two MSL recordings limit interpretation.

| Collection | Query | Control / candidate | Aggregate ratio | Paired-order interval | Recording sensitivity | Semantic point range | Recording W/L/T |
|---|---|---|---:|---|---|---|---:|
| WSD | grid100 | raster / bucket | 2.09672386 | [2.08107408, 2.10110447] | [1.8082628, 2.3589592] | [2.03084786, 2.15162311] | 12/0/0 |
| WSD | grid100 | sweep / bucket | 1.30738546 | [1.29553698, 1.31107614] | [1.19031031, 1.42802325] | [1.30102032, 1.31567514] | 12/0/0 |
| WSD | distinct | raster / sweep | 7.45954146 | [7.36657504, 7.4836742] | [4.28968511, 12.4537099] | [7.27308216, 7.56206498] | 12/0/0 |
| Stock | grid100 | raster / bucket | 1.73774034 | [1.73443352, 1.74220812] | [1.67560329, 1.81396653] | [1.70495392, 1.7591632] | 12/0/0 |
| Stock | grid100 | sweep / bucket | 1.19387337 | [1.19174024, 1.19739777] | [1.16738993, 1.22624455] | [1.16517562, 1.21394322] | 12/0/0 |
| Stock | distinct | raster / sweep | 15.8481353 | [15.6281555, 15.8752557] | [13.0430683, 19.3731329] | [15.1281056, 16.4947144] | 12/0/0 |
| MSL | grid100 | raster / bucket | 2.0723573 | [2.04453901, 2.09029624] | [1.80422089, 2.38034312] | [1.99208322, 2.13067273] | 2/0/0 |
| MSL | grid100 | sweep / bucket | 1.0226073 | [1.01204577, 1.03704517] | [0.963354658, 1.08550438] | [0.996634517, 1.05589051] | 1/1/0 |
| MSL | distinct | raster / sweep | 1.6695392 | [1.65922092, 1.68228582] | [0.859332188, 3.24363639] | [1.60222224, 1.70767403] | 1/1/0 |

Across 108 collection-semantic estimates, 98 paired-order intervals lie wholly above one, none lies wholly below one, and ten include one. All ten are MSL grid100 sweep/bucket. The sole collection-semantic point loss is flat/one: 0.9966345168, paired-order interval [0.9730114011, 1.083296343]. Thus the evidence supports a small fixed-panel average for that ablation, not a uniform semantic advantage.

| MSL recording | Query | Control / candidate | Ratio over twelve settings | Semantic ratio range | Semantic W/L/T |
|---|---|---|---:|---|---:|
| id7 | grid100 | raster / bucket | 1.80422089 | [1.70207618, 1.88133231] | 12/0/0 |
| id7 | grid100 | sweep / bucket | 0.963354658 | [0.919222652, 1.00711892] | 2/10/0 |
| id7 | distinct | raster / sweep | 0.859332188 | [0.837749811, 0.886689677] | 0/12/0 |
| id3 | grid100 | raster / bucket | 2.38034312 | [2.33150289, 2.45420262] | 12/0/0 |
| id3 | grid100 | sweep / bucket | 1.08550438 | [1.06730605, 1.10702396] | 12/0/0 |
| id3 | distinct | raster / sweep | 3.24363639 | [3.06130647, 3.30839334] | 12/0/0 |

`id7` is `146_MSL_id_7_Sensor_tr_554_1st_1172`; `id3` is `142_MSL_id_3_Sensor_tr_1525_1st_4575`. All 22 individual recording/semantic losses are on id7: ten grid100 sweep/bucket settings and twelve distinct raster/sweep settings. No other recording has an individual semantic loss in the three declared comparisons. Both id7 score profiles are bitwise identical between Mac and Linux, so its timing-ratio change cannot be attributed to a changed score vector. Ratios remain host/run specific.

The primary best-grid-winner regret is zero in eleven semantic settings. Middle/one has one nonoverlap, on MSL id3, with regret 0.00141219497462175. The separate descriptive post-hoc tie auditor validates all repeated records and curves and finds no grid-winner ties in any of 26×12 settings. Best and worst tie regrets therefore coincide; neither reaches 0.01 on any recording. This does not demonstrate a material model-selection improvement from complete distinct queries on this panel. Queries use strict `score > threshold`; distinct covers observed thresholds and excludes a below-minimum/all-positive state.

The frozen weighted producer, two runtime source files and independent auditor have exactly the same hashes as Mac v2. All non-host-binding protocol fields match: only the freeze time, input receipt path/hash and per-case cache bindings differ. The model order, case identities/lengths, hypotheses, semantics, comparators, method orders and uncertainty design are unchanged. Linux weighted freeze was 08:54:28.341338 UTC, run start 08:54:28.447771 UTC, and weighted completion 08:57:04.380402 UTC; the full replay completed at 10:21:11.206582 UTC after the native consumer.

The full completion receipt links the generation, weighted report, native completion and both native audit receipts by SHA256. The replay driver, current generator and native input auditor match the bytes in commit f7c900b as well as the local source files. TimeEval acquisition records exact verification of 425 source files against the frozen Mac manifest; compressed transport bytes are recorded separately.

All 26 raw archive member hashes, original observation hashes, labels, raw NPZ hashes and native raw CSV hashes agree between Mac and Linux receipts. TSB-AD source revision, its dependency-closure manifest, detector defaults, score/raw contracts, seed, one-thread policy and timeout are unchanged. Linux native input audit verified all 52 score profiles and 26 label vectors (386,447 rows) on that host. This archive audit does not load Linux raw or score vectors locally; equality claims here compare source-bound receipts, while curve bytes and timing records are verified directly.

Fresh Linux generation uses the current producer (SHA256 `09da5fc196b2f8f11280c307a4ee81cbe62a3f61d860a2b282ed203ab26dd20c`) and the explicit source-bound one-ULP decoding replay contract (SHA256 `514614e9711e87d12ab978a60316f40532324d6bf15f7a64ba7eed7d86ad08d8`). The contract restores the original frozen observation at WSD id29 row 13920 and is verified before fresh Linux fitting. It is legacy typed-input compatibility, not canonical decimal rounding and not an original Mac preregistration. Historical Mac producer/packaging-recovery archives and their hashes remain verified; the historical receipt’s path to a then-current generator is not treated as the current source identity.

Mac detector generation used Python 3.12.4 / pandas 3.0.1 / scipy 1.17.1 / scikit-learn 1.8.0; Linux used Python 3.11.9 / pandas 2.2.3 / scipy 1.14.1 / scikit-learn 1.5.2. All 26 FFT profiles match bitwise across hosts; COPOD matches only MSL id7 and differs on 25 recordings. WSD id6 COPOD distinct count changes from 1686 to 1687; other counts agree. Hash differences do not quantify numerical score distance. The original and supplemental Linux generations match all 52 score-array and native-text hashes despite their independent generation receipts. Host results are not pooled, and the shared selected panel is not an additional independent population sample.

The preserved partial Mac pilot (`weighted-mac/ABORTED.md`) contains 5,400 records / 75 curves, no MSL trials and no completion receipt. It preceded the v2 uncertainty-plan freeze. V2 retained the workload and runtime while adding paired-order uncertainty, explicit bootstrap settings and auditor binding; the partial observations are excluded from all estimates here. Therefore v2 is frozen before its complete rerun, not before every prior observation in the research process.

No source/runtime was edited, detector fitted, metric recomputed or timing rerun by this review. No provenance or parity blocker was found. The substantive limits are the MSL losses, weak semantic evidence for MSL sweep/bucket, small selection regret, host-dependent COPOD bytes and the bounded fixed panel.

New detailed exports: `weighted-linux-v2/archived-recording-summary.csv` contains 78 recording/comparison rows; `archived-semantic-summary.csv` contains 108 semantic estimates with the original intervals. `archive-provenance-comparison.json` binds these exports, source/receipt comparisons and all 52 profile identities.

<details>
<summary>All 108 semantic estimates and original intervals</summary>

| Collection | Query | Control / candidate | Bias/cardinality | Ratio | Paired-order interval | Recording sensitivity | Recording range | Recording W/L/T |
|---|---|---|---|---:|---|---|---|---:|
| WSD | grid100 | raster / bucket | flat/one | 2.15162311 | [2.09331767, 2.16503934] | [1.75745284, 2.47362728] | [1.43988513, 2.65004913] | 12/0/0 |
| WSD | grid100 | raster / bucket | flat/reciprocal | 2.10099596 | [2.0655823, 2.11710442] | [1.74783482, 2.42957026] | [1.46961191, 2.60926549] | 12/0/0 |
| WSD | grid100 | raster / bucket | flat/improved | 2.12549439 | [2.07244797, 2.1364245] | [1.76410459, 2.40682147] | [1.46289789, 2.58739108] | 12/0/0 |
| WSD | grid100 | raster / bucket | front/one | 2.10109758 | [2.0762992, 2.12169998] | [1.7083585, 2.42135582] | [1.3386771, 2.61731378] | 12/0/0 |
| WSD | grid100 | raster / bucket | front/reciprocal | 2.05093607 | [2.018651, 2.08140795] | [1.68067019, 2.38682817] | [1.33241113, 2.61428732] | 12/0/0 |
| WSD | grid100 | raster / bucket | front/improved | 2.03084786 | [2.00060392, 2.0444425] | [1.66613296, 2.35608021] | [1.32664612, 2.57501177] | 12/0/0 |
| WSD | grid100 | raster / bucket | back/one | 2.0809995 | [2.06371968, 2.09834041] | [1.69744004, 2.43228258] | [1.33035118, 2.64422162] | 12/0/0 |
| WSD | grid100 | raster / bucket | back/reciprocal | 2.12007312 | [2.09662395, 2.1301431] | [1.724744, 2.43759055] | [1.36456015, 2.62152248] | 12/0/0 |
| WSD | grid100 | raster / bucket | back/improved | 2.10250819 | [2.07939421, 2.113886] | [1.71261868, 2.41834519] | [1.34158815, 2.63344234] | 12/0/0 |
| WSD | grid100 | raster / bucket | middle/one | 2.11700529 | [2.09527227, 2.1272411] | [1.72930074, 2.42873074] | [1.35620942, 2.61455602] | 12/0/0 |
| WSD | grid100 | raster / bucket | middle/reciprocal | 2.09588422 | [2.07635996, 2.10663853] | [1.69379577, 2.42599703] | [1.3462602, 2.61145681] | 12/0/0 |
| WSD | grid100 | raster / bucket | middle/improved | 2.08601768 | [2.06272814, 2.12123871] | [1.68956066, 2.40316559] | [1.34254244, 2.59926123] | 12/0/0 |
| WSD | grid100 | sweep / bucket | flat/one | 1.31072828 | [1.28635596, 1.34010503] | [1.14961793, 1.47266767] | [1.0006627, 1.5589282] | 12/0/0 |
| WSD | grid100 | sweep / bucket | flat/reciprocal | 1.30418001 | [1.27630143, 1.31358117] | [1.15380883, 1.45676504] | [1.01403538, 1.54910812] | 12/0/0 |
| WSD | grid100 | sweep / bucket | flat/improved | 1.30165421 | [1.2689124, 1.30970081] | [1.15095909, 1.45170084] | [1.01336492, 1.49564275] | 12/0/0 |
| WSD | grid100 | sweep / bucket | front/one | 1.31567514 | [1.28661081, 1.32684212] | [1.15837745, 1.46809603] | [1.01736056, 1.54716214] | 12/0/0 |
| WSD | grid100 | sweep / bucket | front/reciprocal | 1.30445879 | [1.27652042, 1.32045281] | [1.15652363, 1.45315909] | [1.01180965, 1.55565872] | 12/0/0 |
| WSD | grid100 | sweep / bucket | front/improved | 1.30102032 | [1.28266666, 1.31471626] | [1.15678373, 1.44569095] | [1.01694917, 1.52042259] | 12/0/0 |
| WSD | grid100 | sweep / bucket | back/one | 1.30488643 | [1.28938018, 1.31655693] | [1.15483728, 1.45482723] | [1.01957676, 1.55204052] | 12/0/0 |
| WSD | grid100 | sweep / bucket | back/reciprocal | 1.31525914 | [1.30023041, 1.32144947] | [1.1603896, 1.46377248] | [1.02014941, 1.53314121] | 12/0/0 |
| WSD | grid100 | sweep / bucket | back/improved | 1.30672094 | [1.29163543, 1.31343943] | [1.15868007, 1.44959369] | [1.02149613, 1.4974765] | 12/0/0 |
| WSD | grid100 | sweep / bucket | middle/one | 1.30744827 | [1.29277531, 1.31772142] | [1.15102389, 1.45978251] | [1.00671559, 1.53904139] | 12/0/0 |
| WSD | grid100 | sweep / bucket | middle/reciprocal | 1.31087467 | [1.29642634, 1.32121951] | [1.15881, 1.45812624] | [1.00954032, 1.54104568] | 12/0/0 |
| WSD | grid100 | sweep / bucket | middle/improved | 1.30581686 | [1.27398161, 1.31495298] | [1.15687475, 1.44914573] | [1.01618656, 1.49303489] | 12/0/0 |
| WSD | distinct | raster / sweep | flat/one | 7.43028063 | [7.31006879, 7.46669012] | [3.64612614, 13.9222343] | [2.08955207, 23.3380897] | 12/0/0 |
| WSD | distinct | raster / sweep | flat/reciprocal | 7.49357048 | [7.3530194, 7.52020454] | [3.65392266, 14.170853] | [2.08185264, 23.4698507] | 12/0/0 |
| WSD | distinct | raster / sweep | flat/improved | 7.48108968 | [7.35933679, 7.51411349] | [3.66246179, 14.1118678] | [2.07878693, 23.0436444] | 12/0/0 |
| WSD | distinct | raster / sweep | front/one | 7.32078668 | [7.17603979, 7.36565417] | [3.58685775, 14.0726373] | [1.99030066, 23.8958413] | 12/0/0 |
| WSD | distinct | raster / sweep | front/reciprocal | 7.27371274 | [7.1115355, 7.31677281] | [3.54716759, 14.0462206] | [1.98532543, 23.8238907] | 12/0/0 |
| WSD | distinct | raster / sweep | front/improved | 7.27308216 | [7.14512517, 7.31979818] | [3.57581312, 14.062663] | [1.99602395, 23.3846014] | 12/0/0 |
| WSD | distinct | raster / sweep | back/one | 7.53449701 | [7.43396915, 7.59340949] | [3.66223746, 14.7042801] | [2.02376571, 24.7130401] | 12/0/0 |
| WSD | distinct | raster / sweep | back/reciprocal | 7.55114046 | [7.40701417, 7.62000466] | [3.68022501, 14.7299673] | [2.03231923, 24.7894159] | 12/0/0 |
| WSD | distinct | raster / sweep | back/improved | 7.50199198 | [7.3969541, 7.59318178] | [3.65308836, 14.592671] | [2.02466386, 24.1598381] | 12/0/0 |
| WSD | distinct | raster / sweep | middle/one | 7.56206498 | [7.42325501, 7.61060742] | [3.70815739, 14.7056475] | [2.03985149, 24.770309] | 12/0/0 |
| WSD | distinct | raster / sweep | middle/reciprocal | 7.55466409 | [7.41484024, 7.61244172] | [3.68220113, 14.7339788] | [2.0280742, 25.0973725] | 12/0/0 |
| WSD | distinct | raster / sweep | middle/improved | 7.54666974 | [7.3907354, 7.5875385] | [3.71146321, 14.682113] | [2.03282601, 24.4728625] | 12/0/0 |
| Stock | grid100 | raster / bucket | flat/one | 1.7053912 | [1.69706546, 1.73433136] | [1.59283612, 1.85731239] | [1.54970039, 1.99856189] | 12/0/0 |
| Stock | grid100 | raster / bucket | flat/reciprocal | 1.70966147 | [1.683256, 1.71880852] | [1.61140296, 1.83663214] | [1.56802913, 1.94860281] | 12/0/0 |
| Stock | grid100 | raster / bucket | flat/improved | 1.70495392 | [1.69382396, 1.71336371] | [1.61979221, 1.82068228] | [1.55859391, 1.95192328] | 12/0/0 |
| Stock | grid100 | raster / bucket | front/one | 1.72974767 | [1.72122304, 1.78527631] | [1.64665757, 1.83280585] | [1.59093683, 1.92755349] | 12/0/0 |
| Stock | grid100 | raster / bucket | front/reciprocal | 1.74521027 | [1.73390634, 1.78151953] | [1.66909147, 1.84066715] | [1.61964075, 1.93792058] | 12/0/0 |
| Stock | grid100 | raster / bucket | front/improved | 1.74918411 | [1.7381214, 1.75836683] | [1.68340546, 1.84204386] | [1.63666308, 1.95695969] | 12/0/0 |
| Stock | grid100 | raster / bucket | back/one | 1.75653827 | [1.7233453, 1.76530574] | [1.67382466, 1.86215622] | [1.619144, 1.96700274] | 12/0/0 |
| Stock | grid100 | raster / bucket | back/reciprocal | 1.75392227 | [1.73933629, 1.76645748] | [1.67752876, 1.84602761] | [1.61478505, 1.93071329] | 12/0/0 |
| Stock | grid100 | raster / bucket | back/improved | 1.7591632 | [1.74208487, 1.77129617] | [1.69341545, 1.84361358] | [1.63823706, 1.938575] | 12/0/0 |
| Stock | grid100 | raster / bucket | middle/one | 1.75317751 | [1.74227758, 1.76019458] | [1.67225827, 1.85046873] | [1.5976217, 1.95246748] | 12/0/0 |
| Stock | grid100 | raster / bucket | middle/reciprocal | 1.73784461 | [1.72666051, 1.74671898] | [1.67083829, 1.81803495] | [1.61133177, 1.90051787] | 12/0/0 |
| Stock | grid100 | raster / bucket | middle/improved | 1.7494231 | [1.73913671, 1.75783838] | [1.68629145, 1.83639388] | [1.64117138, 1.92761025] | 12/0/0 |
| Stock | grid100 | sweep / bucket | flat/one | 1.21394322 | [1.20626483, 1.22911998] | [1.18080071, 1.25622175] | [1.15974072, 1.30441803] | 12/0/0 |
| Stock | grid100 | sweep / bucket | flat/reciprocal | 1.21068899 | [1.20156553, 1.24567823] | [1.17604521, 1.25565407] | [1.15857901, 1.31267843] | 12/0/0 |
| Stock | grid100 | sweep / bucket | flat/improved | 1.17327532 | [1.16564347, 1.18453589] | [1.14114191, 1.21274908] | [1.11874022, 1.25457409] | 12/0/0 |
| Stock | grid100 | sweep / bucket | front/one | 1.20465998 | [1.19716125, 1.21132536] | [1.16927136, 1.24599151] | [1.14866967, 1.28613398] | 12/0/0 |
| Stock | grid100 | sweep / bucket | front/reciprocal | 1.20194517 | [1.1941699, 1.21236057] | [1.16698255, 1.24834286] | [1.14307299, 1.3107882] | 12/0/0 |
| Stock | grid100 | sweep / bucket | front/improved | 1.17317475 | [1.16738338, 1.17921888] | [1.14476817, 1.20925316] | [1.1283197, 1.25161752] | 12/0/0 |
| Stock | grid100 | sweep / bucket | back/one | 1.208547 | [1.18298078, 1.21777316] | [1.17527891, 1.25375439] | [1.1543967, 1.31095342] | 12/0/0 |
| Stock | grid100 | sweep / bucket | back/reciprocal | 1.20244816 | [1.19415249, 1.21018941] | [1.16521513, 1.24921298] | [1.14331166, 1.30487868] | 12/0/0 |
| Stock | grid100 | sweep / bucket | back/improved | 1.1729139 | [1.16396454, 1.17921215] | [1.14245553, 1.21336344] | [1.12309745, 1.26353255] | 12/0/0 |
| Stock | grid100 | sweep / bucket | middle/one | 1.19988003 | [1.19378115, 1.20976708] | [1.16365515, 1.24689702] | [1.13806676, 1.29935208] | 12/0/0 |
| Stock | grid100 | sweep / bucket | middle/reciprocal | 1.20124386 | [1.19527477, 1.20872591] | [1.16728406, 1.24643176] | [1.14877945, 1.29749073] | 12/0/0 |
| Stock | grid100 | sweep / bucket | middle/improved | 1.16517562 | [1.15826818, 1.17096917] | [1.13638133, 1.2045975] | [1.12399602, 1.25156902] | 12/0/0 |
| Stock | distinct | raster / sweep | flat/one | 15.1281056 | [14.8735332, 15.1870573] | [12.0567339, 19.2479487] | [10.1789185, 23.7716392] | 12/0/0 |
| Stock | distinct | raster / sweep | flat/reciprocal | 15.5608211 | [15.3043189, 15.6121021] | [12.3264974, 19.8278566] | [10.3388445, 24.5584131] | 12/0/0 |
| Stock | distinct | raster / sweep | flat/improved | 15.6580402 | [15.4117004, 15.723526] | [12.329241, 20.089894] | [10.2156186, 25.0397827] | 12/0/0 |
| Stock | distinct | raster / sweep | front/one | 15.3422909 | [15.1080531, 15.4283031] | [11.9326457, 19.8752626] | [9.94926091, 24.6029222] | 12/0/0 |
| Stock | distinct | raster / sweep | front/reciprocal | 15.7229527 | [15.4314768, 15.8006249] | [12.1892186, 20.4347476] | [10.1370563, 25.2759575] | 12/0/0 |
| Stock | distinct | raster / sweep | front/improved | 15.9270219 | [15.6293831, 16.1110096] | [12.2020042, 20.8183765] | [10.0919347, 25.8441955] | 12/0/0 |
| Stock | distinct | raster / sweep | back/one | 15.6812867 | [15.4011232, 15.7350061] | [12.1928924, 20.2992731] | [10.0792099, 25.2510808] | 12/0/0 |
| Stock | distinct | raster / sweep | back/reciprocal | 16.1716558 | [15.8478079, 16.2225115] | [12.4307913, 21.056264] | [10.3580966, 26.1680129] | 12/0/0 |
| Stock | distinct | raster / sweep | back/improved | 16.2051185 | [15.9185525, 16.2738123] | [12.4723679, 21.1466126] | [10.2328945, 26.4281195] | 12/0/0 |
| Stock | distinct | raster / sweep | middle/one | 15.9786677 | [15.4291783, 16.0561636] | [12.3556309, 20.7801952] | [10.2312541, 25.7422362] | 12/0/0 |
| Stock | distinct | raster / sweep | middle/reciprocal | 16.3663153 | [15.9292543, 16.4611054] | [12.5897933, 21.4473427] | [10.3924286, 26.4758223] | 12/0/0 |
| Stock | distinct | raster / sweep | middle/improved | 16.4947144 | [16.1938297, 16.5567045] | [12.6203315, 21.6348678] | [10.4584678, 26.7537925] | 12/0/0 |
| MSL | grid100 | raster / bucket | flat/one | 2.04999898 | [1.97412672, 2.22623013] | [1.77784119, 2.36381959] | [1.77784119, 2.36381959] | 2/0/0 |
| MSL | grid100 | raster / bucket | flat/reciprocal | 2.06892369 | [2.02582267, 2.1730401] | [1.7902038, 2.39103797] | [1.7902038, 2.39103797] | 2/0/0 |
| MSL | grid100 | raster / bucket | flat/improved | 2.05025673 | [1.87598464, 2.11130256] | [1.76500191, 2.38161366] | [1.76500191, 2.38161366] | 2/0/0 |
| MSL | grid100 | raster / bucket | front/one | 2.11465399 | [2.00283135, 2.17967696] | [1.8600713, 2.40408069] | [1.8600713, 2.40408069] | 2/0/0 |
| MSL | grid100 | raster / bucket | front/reciprocal | 2.04604748 | [1.98087521, 2.09377471] | [1.77316639, 2.36092355] | [1.77316639, 2.36092355] | 2/0/0 |
| MSL | grid100 | raster / bucket | front/improved | 1.99208322 | [1.85979281, 2.09573718] | [1.70207618, 2.33150289] | [1.70207618, 2.33150289] | 2/0/0 |
| MSL | grid100 | raster / bucket | back/one | 2.13067273 | [2.04256584, 2.18893221] | [1.84979277, 2.45420262] | [1.84979277, 2.45420262] | 2/0/0 |
| MSL | grid100 | raster / bucket | back/reciprocal | 2.10233304 | [1.85077514, 2.14583285] | [1.88133231, 2.3492948] | [1.88133231, 2.3492948] | 2/0/0 |
| MSL | grid100 | raster / bucket | back/improved | 2.09773053 | [2.0523242, 2.13870228] | [1.84857433, 2.38046873] | [1.84857433, 2.38046873] | 2/0/0 |
| MSL | grid100 | raster / bucket | middle/one | 2.04660992 | [1.91845269, 2.16025549] | [1.75361743, 2.38855527] | [1.75361743, 2.38855527] | 2/0/0 |
| MSL | grid100 | raster / bucket | middle/reciprocal | 2.07640612 | [2.01635719, 2.15220804] | [1.78941409, 2.40942685] | [1.78941409, 2.40942685] | 2/0/0 |
| MSL | grid100 | raster / bucket | middle/improved | 2.09648339 | [2.0373547, 2.15044287] | [1.8689883, 2.3516694] | [1.8689883, 2.3516694] | 2/0/0 |
| MSL | grid100 | sweep / bucket | flat/one | 0.996634517 | [0.973011401, 1.08329634] | [0.919222652, 1.08056558] | [0.919222652, 1.08056558] | 1/1/0 |
| MSL | grid100 | sweep / bucket | flat/reciprocal | 1.00772184 | [0.983180142, 1.12459798] | [0.937245904, 1.08349719] | [0.937245904, 1.08349719] | 1/1/0 |
| MSL | grid100 | sweep / bucket | flat/improved | 1.01409978 | [0.954418119, 1.0425282] | [0.94738894, 1.0855081] | [0.94738894, 1.0855081] | 1/1/0 |
| MSL | grid100 | sweep / bucket | front/one | 1.03814702 | [0.982005133, 1.07443984] | [0.985691618, 1.09339394] | [0.985691618, 1.09339394] | 1/1/0 |
| MSL | grid100 | sweep / bucket | front/reciprocal | 1.05589051 | [1.00980687, 1.18940658] | [1.00711892, 1.10702396] | [1.00711892, 1.10702396] | 2/0/0 |
| MSL | grid100 | sweep / bucket | front/improved | 1.01742527 | [0.954354384, 1.06106395] | [0.957744931, 1.0808245] | [0.957744931, 1.0808245] | 1/1/0 |
| MSL | grid100 | sweep / bucket | back/one | 1.036872 | [0.986782464, 1.07837273] | [0.973690227, 1.10415358] | [0.973690227, 1.10415358] | 1/1/0 |
| MSL | grid100 | sweep / bucket | back/reciprocal | 1.02311348 | [0.930851766, 1.04759756] | [0.976140047, 1.07234736] | [0.976140047, 1.07234736] | 1/1/0 |
| MSL | grid100 | sweep / bucket | back/improved | 1.04081149 | [1.00719743, 1.07250704] | [1.0008411, 1.08237817] | [1.0008411, 1.08237817] | 2/0/0 |
| MSL | grid100 | sweep / bucket | middle/one | 1.00492046 | [0.944779028, 1.06335653] | [0.937014837, 1.07774722] | [0.937014837, 1.07774722] | 1/1/0 |
| MSL | grid100 | sweep / bucket | middle/reciprocal | 1.01115812 | [0.988155851, 1.04334918] | [0.936289024, 1.09201401] | [0.936289024, 1.09201401] | 1/1/0 |
| MSL | grid100 | sweep / bucket | middle/improved | 1.02611806 | [0.998663097, 1.08008004] | [0.986519531, 1.06730605] | [0.986519531, 1.06730605] | 1/1/0 |
| MSL | distinct | raster / sweep | flat/one | 1.65723854 | [1.61326275, 1.7668784] | [0.837749811, 3.27835295] | [0.837749811, 3.27835295] | 1/1/0 |
| MSL | distinct | raster / sweep | flat/reciprocal | 1.70767403 | [1.67175871, 1.72902716] | [0.886689677, 3.28880631] | [0.886689677, 3.28880631] | 1/1/0 |
| MSL | distinct | raster / sweep | flat/improved | 1.67343942 | [1.65119721, 1.71602055] | [0.850031815, 3.29446433] | [0.850031815, 3.29446433] | 1/1/0 |
| MSL | distinct | raster / sweep | front/one | 1.66206251 | [1.59602146, 1.68694922] | [0.881788724, 3.13278194] | [0.881788724, 3.13278194] | 1/1/0 |
| MSL | distinct | raster / sweep | front/reciprocal | 1.60222224 | [1.58706504, 1.66348612] | [0.838568805, 3.06130647] | [0.838568805, 3.06130647] | 1/1/0 |
| MSL | distinct | raster / sweep | front/improved | 1.6203332 | [1.56533465, 1.68039937] | [0.843347657, 3.11316412] | [0.843347657, 3.11316412] | 1/1/0 |
| MSL | distinct | raster / sweep | back/one | 1.69920927 | [1.64356376, 1.73502094] | [0.882092413, 3.27325356] | [0.882092413, 3.27325356] | 1/1/0 |
| MSL | distinct | raster / sweep | back/reciprocal | 1.66962965 | [1.63624111, 1.69262519] | [0.842603302, 3.30839334] | [0.842603302, 3.30839334] | 1/1/0 |
| MSL | distinct | raster / sweep | back/improved | 1.67147056 | [1.56377589, 1.71907398] | [0.846794588, 3.29928162] | [0.846794588, 3.29928162] | 1/1/0 |
| MSL | distinct | raster / sweep | middle/one | 1.70490213 | [1.65684189, 1.75977411] | [0.881121226, 3.29885514] | [0.881121226, 3.29885514] | 1/1/0 |
| MSL | distinct | raster / sweep | middle/reciprocal | 1.66991561 | [1.64796619, 1.74706483] | [0.846110961, 3.29580667] | [0.846110961, 3.29580667] | 1/1/0 |
| MSL | distinct | raster / sweep | middle/improved | 1.69990755 | [1.65066967, 1.72075813] | [0.877654523, 3.29250928] | [0.877654523, 3.29250928] | 1/1/0 |

</details>

Artifact hashes:

- Original CI report: `94e8e89f59b8ad02ce0b4ac8ba9ed13e8d69fdbd5bd85df581eed4a700967599` (`artifacts/pvldb-research-20261024/strengthening/linux-original-replay/weighted-linux-v2/independent-report.json`).
- Archive reconstruction: `62fb2aa463446c706cc60ea4fa007ac654f8044ae2e36262d753747f071c158a` (`artifacts/pvldb-research-20261024/strengthening/linux-original-replay/weighted-linux-v2/archived-output-report.json`).
- Post-hoc tie sensitivity: `9ca51f3d61749f8765b5a416c7e2911ffd4fd3dbf5b3102571ea012138dece52` (`artifacts/pvldb-research-20261024/strengthening/linux-original-replay/weighted-linux-v2/posthoc-tie-sensitivity.json`).
- Provenance comparison: `b52dc1557f6c24ba2a95852bb3b001f6dbdd97c477597f42f1e1d6a4999a0c09` (`artifacts/pvldb-research-20261024/strengthening/linux-original-replay/weighted-linux-v2/archive-provenance-comparison.json`).
- Weighted completion: `f270a39a0e0604ede206632f51aa28557e7a13c1bd18fc55dba784b3796e77eb` (`artifacts/pvldb-research-20261024/strengthening/linux-original-replay/weighted-linux-v2/complete.json`).
- Full replay completion: `2d6c192ef8cc3fdc88338b141b4c4c7ca1533025791b2da8f83d3a550f35d439` (`artifacts/pvldb-research-20261024/strengthening/linux-original-replay/reproduction-complete.json`).
