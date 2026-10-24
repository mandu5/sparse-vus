# Independent Mac weighted interval-control reconstruction

The completed supplemental study passes saved-output and input/source identity auditing. Incremental evaluation beats the interval control in all six collection/query aggregates and all 72 collection/semantic/query estimates, with their prespecified paired-order intervals above one. This does not imply a win on every recording: MSL id7 loses all twelve distinct-query settings. The conventional interval control is also slower than raster in five of the six collection/query aggregates; it is an additional conventional control, not uniformly the fastest measured baseline.

This control was added after review and prospectively frozen before its own timings. The original weighted v2 outputs are unchanged. The control implements closed-form per-query interval/prefix evaluation for the same canonical positional metric semantics; it is an authored conventional implementation, not a separately published detector or a newly acquired dataset.

The unchanged auditor verified **11,232 records, 156 complete curve files and 26 recordings**, including local input bytes and all protocol-pinned sources. Maximum curve error is `2.3869795029440866e-15` and detector winner disagreements are `0`. A separate standard-library reconstruction using `statistics.median` and `math.fsum` reproduced all 144 semantic and 12 aggregate point estimates within relative/absolute tolerance 1e-13, without importing any metric or study implementation.

All speed ratios are **left/control time divided by right/candidate time**. A value above one favors the right-hand method. `incremental` means bucket for grid100 and sweep for distinct queries. Each estimate uses six balanced trial orders; aggregate ratios give equal log weight to twelve semantic settings per recording. The intervals condition on this fixed panel and host. Recording-reweighting intervals are separate sensitivity summaries, not population confidence statements. Bonferroni adjustment is 36 semantic estimates or 3 collection aggregates **within each of the four comparisons**, not jointly across all four. Six orders and 10,000 resamples provide limited approximate uncertainty evidence.

| Collection | Query | Control / candidate | Aggregate ratio | Paired-order 95% interval | Recording-reweighting interval | Semantic ratio range | Semantic W/L/T | Recording W/L/T |
|---|---|---|---:|---|---|---|---:|---:|
| WSD | grid100 | interval / incremental | 1.66502 | [1.65762, 1.67096] | [1.58849, 1.73637] | [1.64486, 1.67985] | 12/0/0 | 12/0/0 |
| WSD | distinct | interval / incremental | 7.32273 | [7.27747, 7.34245] | [4.29034, 11.9187] | [7.26039, 7.39654] | 12/0/0 | 12/0/0 |
| WSD | grid100 | raster / interval | 0.916609 | [0.912974, 0.919301] | [0.897577, 0.942242] | [0.902516, 0.927272] | 0/12/0 | 1/11/0 |
| WSD | distinct | raster / interval | 1.17552 | [1.17357, 1.17931] | [1.11904, 1.23002] | [1.12561, 1.19605] | 12/0/0 | 12/0/0 |
| Stock | grid100 | interval / incremental | 2.05057 | [2.03962, 2.05876] | [1.99052, 2.10891] | [1.96977, 2.12424] | 12/0/0 | 12/0/0 |
| Stock | distinct | interval / incremental | 26.3391 | [26.2444, 26.3875] | [19.4723, 35.5749] | [25.5811, 27.7571] | 12/0/0 | 12/0/0 |
| Stock | grid100 | raster / interval | 0.785675 | [0.782748, 0.788433] | [0.771445, 0.79971] | [0.716669, 0.835551] | 0/12/0 | 0/12/0 |
| Stock | distinct | raster / interval | 0.834906 | [0.833118, 0.83726] | [0.815145, 0.857315] | [0.796591, 0.87745] | 0/12/0 | 0/12/0 |
| MSL | grid100 | interval / incremental | 1.75294 | [1.72545, 1.75921] | [1.69467, 1.81322] | [1.72792, 1.7742] | 12/0/0 | 2/0/0 |
| MSL | distinct | interval / incremental | 1.70643 | [1.67884, 1.72755] | [0.774661, 3.75892] | [1.65408, 1.74779] | 12/0/0 | 1/1/0 |
| MSL | grid100 | raster / interval | 0.895969 | [0.891779, 0.905394] | [0.891757, 0.900201] | [0.868437, 0.906974] | 0/12/0 | 0/2/0 |
| MSL | distinct | raster / interval | 0.832454 | [0.827725, 0.846656] | [0.726603, 0.953725] | [0.813143, 0.842271] | 0/12/0 | 0/2/0 |

W/L/T counts favor the right-hand candidate. Recording counts average its twelve semantic log ratios before classifying the recording; semantic counts classify each collection-level semantic estimate.

MSL contains only two selected recordings. Their individual results below are descriptive; no new per-recording intervals are introduced. `id7` is `146_MSL_id_7_Sensor_tr_554_1st_1172`; `id3` is `142_MSL_id_3_Sensor_tr_1525_1st_4575`.

| Recording | Query | Control / candidate | Ratio over twelve settings | Semantic ratio range | Semantic W/L/T |
|---|---|---|---:|---|---:|
| id7 | grid100 | interval / incremental | 1.69467081 | [1.66761, 1.74257] | 12/0/0 |
| id7 | distinct | interval / incremental | 0.774661441 | [0.763244, 0.783028] | 0/12/0 |
| id7 | grid100 | raster / interval | 0.900201363 | [0.851588, 0.914501] | 0/12/0 |
| id7 | distinct | raster / interval | 0.726602842 | [0.699, 0.735947] | 0/12/0 |
| id3 | grid100 | interval / incremental | 1.81321514 | [1.77746, 1.85578] | 12/0/0 |
| id3 | distinct | interval / incremental | 3.75892181 | [3.50944, 3.97254] | 12/0/0 |
| id3 | grid100 | raster / interval | 0.891756599 | [0.876482, 0.908211] | 0/12/0 |
| id3 | distinct | raster / interval | 0.953725408 | [0.92475, 0.965596] | 0/12/0 |

In particular, interval/sweep on MSL id7 is **0.774661441**, with all twelve semantic ratios between 0.763244 and 0.783028. MSL id3 is 3.75892181. Their aggregate paired-order interval is above one, while the recording-reweighting interval spans [0.774661, 3.75892]. This is a fixed-panel average with an explicit per-recording loss.

The separately labeled post-hoc tie audit passed all repeated records and curves. There are `0` recordings with a tolerance-based grid tie in any setting. Best and worst grid-winner regret therefore coincide: maximum `0.00141219497462175`, with zero recordings reaching 0.01 under either choice. The only nonoverlap is middle bias/cardinality one. Queries use strict `score > threshold`; distinct means all observed thresholds, excluding the below-minimum/all-positive state. These sensitivity results were not retrospectively preregistered.

<details>
<summary>All 144 semantic estimates, per-recording ranges/losses, and both interval summaries</summary>

| Collection | Query | Control / candidate | Bias/cardinality | Ratio | Paired-order 95% interval | Recording-reweighting interval | Recording ratio range | Recording W/L/T |
|---|---|---|---|---:|---|---|---|---:|
| WSD | grid100 | interval / incremental | flat/one | 1.67044 | [1.63971, 1.69488] | [1.57024, 1.75362] | [1.45567, 1.80089] | 12/0/0 |
| WSD | grid100 | interval / incremental | flat/reciprocal | 1.67985 | [1.63899, 1.70548] | [1.55314, 1.77399] | [1.3918, 1.8534] | 12/0/0 |
| WSD | grid100 | interval / incremental | flat/improved | 1.64486 | [1.62045, 1.68092] | [1.53861, 1.7414] | [1.42641, 1.82785] | 12/0/0 |
| WSD | grid100 | interval / incremental | front/one | 1.65871 | [1.63758, 1.68316] | [1.54959, 1.76376] | [1.44039, 1.86559] | 12/0/0 |
| WSD | grid100 | interval / incremental | front/reciprocal | 1.67162 | [1.64724, 1.68807] | [1.56679, 1.77203] | [1.45472, 1.88761] | 12/0/0 |
| WSD | grid100 | interval / incremental | front/improved | 1.65668 | [1.62876, 1.68071] | [1.561, 1.75953] | [1.45763, 1.87467] | 12/0/0 |
| WSD | grid100 | interval / incremental | back/one | 1.67012 | [1.63063, 1.69644] | [1.57377, 1.76311] | [1.46652, 1.87705] | 12/0/0 |
| WSD | grid100 | interval / incremental | back/reciprocal | 1.64617 | [1.61856, 1.67833] | [1.55093, 1.72792] | [1.45237, 1.7806] | 12/0/0 |
| WSD | grid100 | interval / incremental | back/improved | 1.67102 | [1.65118, 1.69241] | [1.57635, 1.75886] | [1.47422, 1.8411] | 12/0/0 |
| WSD | grid100 | interval / incremental | middle/one | 1.66877 | [1.63081, 1.69539] | [1.55779, 1.76486] | [1.4102, 1.8744] | 12/0/0 |
| WSD | grid100 | interval / incremental | middle/reciprocal | 1.67694 | [1.65041, 1.71152] | [1.58559, 1.76188] | [1.49956, 1.83519] | 12/0/0 |
| WSD | grid100 | interval / incremental | middle/improved | 1.66548 | [1.61513, 1.69464] | [1.57669, 1.75585] | [1.46039, 1.86947] | 12/0/0 |
| WSD | distinct | interval / incremental | flat/one | 7.26278 | [6.6715, 7.36684] | [3.58434, 13.2732] | [2.02414, 22.8177] | 12/0/0 |
| WSD | distinct | interval / incremental | flat/reciprocal | 7.31852 | [7.22383, 7.43479] | [3.60138, 13.2892] | [1.95826, 22.2812] | 12/0/0 |
| WSD | distinct | interval / incremental | flat/improved | 7.35744 | [7.26449, 7.43127] | [3.66077, 13.3919] | [2.0526, 23.0636] | 12/0/0 |
| WSD | distinct | interval / incremental | front/one | 7.29648 | [7.19317, 7.39191] | [3.59103, 13.3981] | [1.97103, 23.5319] | 12/0/0 |
| WSD | distinct | interval / incremental | front/reciprocal | 7.30276 | [7.19489, 7.38392] | [3.6236, 13.3592] | [2.02482, 23.011] | 12/0/0 |
| WSD | distinct | interval / incremental | front/improved | 7.31699 | [7.17606, 7.39837] | [3.65708, 13.3342] | [2.10161, 23.0928] | 12/0/0 |
| WSD | distinct | interval / incremental | back/one | 7.26039 | [7.14857, 7.37569] | [3.57032, 13.364] | [1.97066, 23.1853] | 12/0/0 |
| WSD | distinct | interval / incremental | back/reciprocal | 7.29842 | [7.02481, 7.41182] | [3.606, 13.3786] | [1.99072, 22.9976] | 12/0/0 |
| WSD | distinct | interval / incremental | back/improved | 7.34085 | [7.2629, 7.42009] | [3.63503, 13.4779] | [2.01089, 23.3385] | 12/0/0 |
| WSD | distinct | interval / incremental | middle/one | 7.36624 | [7.24596, 7.45453] | [3.63318, 13.5798] | [2.05126, 23.8166] | 12/0/0 |
| WSD | distinct | interval / incremental | middle/reciprocal | 7.39654 | [7.29486, 7.48768] | [3.67136, 13.5415] | [2.06056, 23.6308] | 12/0/0 |
| WSD | distinct | interval / incremental | middle/improved | 7.3567 | [7.24081, 7.46923] | [3.59019, 13.4698] | [1.95673, 22.5449] | 12/0/0 |
| WSD | grid100 | raster / interval | flat/one | 0.908133 | [0.895543, 0.921443] | [0.884771, 0.941651] | [0.869393, 0.994625] | 0/12/0 |
| WSD | grid100 | raster / interval | flat/reciprocal | 0.902516 | [0.892277, 0.91742] | [0.884944, 0.924472] | [0.875186, 0.950913] | 0/12/0 |
| WSD | grid100 | raster / interval | flat/improved | 0.904887 | [0.890355, 0.918338] | [0.884474, 0.92944] | [0.872984, 0.960857] | 0/12/0 |
| WSD | grid100 | raster / interval | front/one | 0.923533 | [0.914188, 0.93498] | [0.896042, 0.95972] | [0.881153, 0.997375] | 0/12/0 |
| WSD | grid100 | raster / interval | front/reciprocal | 0.92061 | [0.913948, 0.925912] | [0.89601, 0.951128] | [0.875442, 0.989047] | 0/12/0 |
| WSD | grid100 | raster / interval | front/improved | 0.918994 | [0.903892, 0.929023] | [0.897594, 0.951384] | [0.882709, 0.999503] | 0/12/0 |
| WSD | grid100 | raster / interval | back/one | 0.917737 | [0.90437, 0.929068] | [0.885304, 0.96458] | [0.859171, 1.04175] | 1/11/0 |
| WSD | grid100 | raster / interval | back/reciprocal | 0.921605 | [0.90718, 0.932532] | [0.89104, 0.968875] | [0.878901, 1.05163] | 1/11/0 |
| WSD | grid100 | raster / interval | back/improved | 0.914833 | [0.905805, 0.928441] | [0.885372, 0.958649] | [0.872932, 1.03018] | 1/11/0 |
| WSD | grid100 | raster / interval | middle/one | 0.927272 | [0.91491, 0.940226] | [0.896032, 0.97161] | [0.865282, 1.04381] | 1/11/0 |
| WSD | grid100 | raster / interval | middle/reciprocal | 0.923989 | [0.901547, 0.938156] | [0.90189, 0.964217] | [0.883936, 1.03388] | 1/11/0 |
| WSD | grid100 | raster / interval | middle/improved | 0.915567 | [0.902707, 0.929192] | [0.88916, 0.956638] | [0.879435, 1.02145] | 1/11/0 |
| WSD | distinct | raster / interval | flat/one | 1.12756 | [1.11973, 1.135] | [1.06523, 1.18968] | [1.00068, 1.26317] | 12/0/0 |
| WSD | distinct | raster / interval | flat/reciprocal | 1.1265 | [1.11807, 1.13227] | [1.06782, 1.1883] | [1.01943, 1.26515] | 12/0/0 |
| WSD | distinct | raster / interval | flat/improved | 1.12561 | [1.11825, 1.13481] | [1.06074, 1.19124] | [0.991228, 1.26499] | 11/1/0 |
| WSD | distinct | raster / interval | front/one | 1.1877 | [1.17665, 1.19608] | [1.11375, 1.25914] | [1.02003, 1.34937] | 12/0/0 |
| WSD | distinct | raster / interval | front/reciprocal | 1.19225 | [1.17953, 1.1983] | [1.11677, 1.2614] | [1.0232, 1.34661] | 12/0/0 |
| WSD | distinct | raster / interval | front/improved | 1.18442 | [1.17729, 1.19503] | [1.10771, 1.2563] | [1.0378, 1.34171] | 12/0/0 |
| WSD | distinct | raster / interval | back/one | 1.19605 | [1.18852, 1.2255] | [1.11056, 1.27491] | [1.01203, 1.33481] | 12/0/0 |
| WSD | distinct | raster / interval | back/reciprocal | 1.19482 | [1.18546, 1.21114] | [1.11265, 1.27444] | [1.00989, 1.35469] | 12/0/0 |
| WSD | distinct | raster / interval | back/improved | 1.1957 | [1.18757, 1.24627] | [1.11001, 1.2756] | [1.00582, 1.33124] | 12/0/0 |
| WSD | distinct | raster / interval | middle/one | 1.19478 | [1.18802, 1.20235] | [1.10534, 1.27575] | [1.027, 1.34039] | 12/0/0 |
| WSD | distinct | raster / interval | middle/reciprocal | 1.19361 | [1.18336, 1.20481] | [1.10999, 1.27045] | [1.00265, 1.33337] | 12/0/0 |
| WSD | distinct | raster / interval | middle/improved | 1.19144 | [1.18622, 1.198] | [1.11204, 1.27295] | [1.03058, 1.33971] | 12/0/0 |
| Stock | grid100 | interval / incremental | flat/one | 2.11664 | [2.08127, 2.15153] | [2.03908, 2.18587] | [1.96928, 2.25335] | 12/0/0 |
| Stock | grid100 | interval / incremental | flat/reciprocal | 2.12424 | [2.08563, 2.16104] | [2.03209, 2.20013] | [1.9667, 2.22407] | 12/0/0 |
| Stock | grid100 | interval / incremental | flat/improved | 2.05227 | [2.00998, 2.08238] | [1.96378, 2.13112] | [1.88022, 2.22972] | 12/0/0 |
| Stock | grid100 | interval / incremental | front/one | 2.06006 | [2.01724, 2.14781] | [1.9895, 2.13745] | [1.92974, 2.22344] | 12/0/0 |
| Stock | grid100 | interval / incremental | front/reciprocal | 2.04562 | [2.01224, 2.07398] | [1.97024, 2.11725] | [1.89344, 2.17789] | 12/0/0 |
| Stock | grid100 | interval / incremental | front/improved | 1.96977 | [1.92885, 2.00742] | [1.87953, 2.05757] | [1.79994, 2.13393] | 12/0/0 |
| Stock | grid100 | interval / incremental | back/one | 2.03162 | [1.98922, 2.06501] | [1.94394, 2.12383] | [1.89059, 2.22525] | 12/0/0 |
| Stock | grid100 | interval / incremental | back/reciprocal | 2.04066 | [2.00256, 2.07174] | [1.97166, 2.109] | [1.91018, 2.19872] | 12/0/0 |
| Stock | grid100 | interval / incremental | back/improved | 1.97825 | [1.94828, 2.00786] | [1.89645, 2.0623] | [1.82071, 2.17031] | 12/0/0 |
| Stock | grid100 | interval / incremental | middle/one | 2.07729 | [2.03698, 2.11343] | [1.98372, 2.15744] | [1.90662, 2.21417] | 12/0/0 |
| Stock | grid100 | interval / incremental | middle/reciprocal | 2.09516 | [2.04439, 2.12305] | [1.99406, 2.1908] | [1.9471, 2.25774] | 12/0/0 |
| Stock | grid100 | interval / incremental | middle/improved | 2.02156 | [1.96036, 2.05084] | [1.91968, 2.11557] | [1.85448, 2.21817] | 12/0/0 |
| Stock | distinct | interval / incremental | flat/one | 25.615 | [25.1173, 25.9443] | [17.5923, 37.3788] | [14.4451, 47.1859] | 12/0/0 |
| Stock | distinct | interval / incremental | flat/reciprocal | 25.5811 | [25.16, 26.0863] | [17.508, 37.4129] | [14.2194, 46.8913] | 12/0/0 |
| Stock | distinct | interval / incremental | flat/improved | 25.7221 | [25.3108, 26.0081] | [17.5765, 37.4665] | [14.3463, 47.1388] | 12/0/0 |
| Stock | distinct | interval / incremental | front/one | 25.9135 | [25.6529, 26.1785] | [17.3487, 38.468] | [13.9682, 49.0756] | 12/0/0 |
| Stock | distinct | interval / incremental | front/reciprocal | 25.7095 | [25.1985, 26.0394] | [17.2046, 37.9722] | [13.8194, 48.7075] | 12/0/0 |
| Stock | distinct | interval / incremental | front/improved | 25.9925 | [25.6271, 26.3862] | [17.5291, 38.0219] | [14.2681, 48.3695] | 12/0/0 |
| Stock | distinct | interval / incremental | back/one | 26.1948 | [25.7988, 26.4361] | [17.6204, 38.4987] | [14.2739, 48.4124] | 12/0/0 |
| Stock | distinct | interval / incremental | back/reciprocal | 26.2353 | [25.8977, 26.5859] | [17.5291, 38.8647] | [14.1765, 49.3137] | 12/0/0 |
| Stock | distinct | interval / incremental | back/improved | 26.3762 | [25.9754, 26.7243] | [17.6118, 38.8344] | [14.0961, 49.312] | 12/0/0 |
| Stock | distinct | interval / incremental | middle/one | 27.7154 | [27.0709, 28.1176] | [18.4363, 40.9291] | [14.9467, 51.9393] | 12/0/0 |
| Stock | distinct | interval / incremental | middle/reciprocal | 27.3923 | [26.97, 27.6575] | [18.1694, 40.7848] | [14.5763, 51.7517] | 12/0/0 |
| Stock | distinct | interval / incremental | middle/improved | 27.7571 | [27.2975, 28.1284] | [18.5398, 40.7435] | [14.9385, 51.6177] | 12/0/0 |
| Stock | grid100 | raster / interval | flat/one | 0.719982 | [0.708817, 0.732333] | [0.687332, 0.75611] | [0.671879, 0.770967] | 0/12/0 |
| Stock | grid100 | raster / interval | flat/reciprocal | 0.716669 | [0.706631, 0.727621] | [0.686757, 0.751707] | [0.661943, 0.779702] | 0/12/0 |
| Stock | grid100 | raster / interval | flat/improved | 0.720657 | [0.711215, 0.729227] | [0.694151, 0.749269] | [0.67514, 0.765309] | 0/12/0 |
| Stock | grid100 | raster / interval | front/one | 0.795089 | [0.759827, 0.805132] | [0.773128, 0.824325] | [0.755713, 0.866706] | 0/12/0 |
| Stock | grid100 | raster / interval | front/reciprocal | 0.794421 | [0.782201, 0.802233] | [0.773775, 0.811557] | [0.755446, 0.822827] | 0/12/0 |
| Stock | grid100 | raster / interval | front/improved | 0.780401 | [0.766819, 0.796423] | [0.76012, 0.800073] | [0.743504, 0.815034] | 0/12/0 |
| Stock | grid100 | raster / interval | back/one | 0.835551 | [0.82513, 0.850345] | [0.811184, 0.87012] | [0.805702, 0.904866] | 0/12/0 |
| Stock | grid100 | raster / interval | back/reciprocal | 0.831416 | [0.819819, 0.842396] | [0.803136, 0.870932] | [0.791498, 0.905159] | 0/12/0 |
| Stock | grid100 | raster / interval | back/improved | 0.825519 | [0.813751, 0.833812] | [0.79913, 0.864781] | [0.784207, 0.904928] | 0/12/0 |
| Stock | grid100 | raster / interval | middle/one | 0.807513 | [0.797859, 0.820559] | [0.780616, 0.838306] | [0.754029, 0.866362] | 0/12/0 |
| Stock | grid100 | raster / interval | middle/reciprocal | 0.81134 | [0.800553, 0.829031] | [0.789783, 0.837075] | [0.774683, 0.874438] | 0/12/0 |
| Stock | grid100 | raster / interval | middle/improved | 0.803325 | [0.794204, 0.816747] | [0.776657, 0.836008] | [0.76714, 0.871427] | 0/12/0 |
| Stock | distinct | raster / interval | flat/one | 0.801615 | [0.790774, 0.814005] | [0.771867, 0.845321] | [0.758318, 0.910713] | 0/12/0 |
| Stock | distinct | raster / interval | flat/reciprocal | 0.796591 | [0.787511, 0.804553] | [0.769501, 0.841855] | [0.759303, 0.906354] | 0/12/0 |
| Stock | distinct | raster / interval | flat/improved | 0.809844 | [0.801771, 0.820288] | [0.787409, 0.849408] | [0.784591, 0.897292] | 0/12/0 |
| Stock | distinct | raster / interval | front/one | 0.87745 | [0.868304, 0.889014] | [0.852885, 0.898422] | [0.82108, 0.918893] | 0/12/0 |
| Stock | distinct | raster / interval | front/reciprocal | 0.874711 | [0.864112, 0.887102] | [0.854934, 0.895238] | [0.842737, 0.918877] | 0/12/0 |
| Stock | distinct | raster / interval | front/improved | 0.877148 | [0.864937, 0.886119] | [0.853636, 0.8992] | [0.833419, 0.911411] | 0/12/0 |
| Stock | distinct | raster / interval | back/one | 0.849312 | [0.841007, 0.860721] | [0.811391, 0.887289] | [0.785406, 0.910494] | 0/12/0 |
| Stock | distinct | raster / interval | back/reciprocal | 0.852985 | [0.843127, 0.86273] | [0.822981, 0.889089] | [0.804245, 0.913501] | 0/12/0 |
| Stock | distinct | raster / interval | back/improved | 0.846833 | [0.838679, 0.858104] | [0.815777, 0.880102] | [0.792161, 0.908433] | 0/12/0 |
| Stock | distinct | raster / interval | middle/one | 0.810673 | [0.800422, 0.826312] | [0.766727, 0.863357] | [0.738299, 0.903927] | 0/12/0 |
| Stock | distinct | raster / interval | middle/reciprocal | 0.818017 | [0.80822, 0.828702] | [0.781035, 0.862319] | [0.761253, 0.884411] | 0/12/0 |
| Stock | distinct | raster / interval | middle/improved | 0.809983 | [0.799195, 0.818945] | [0.774202, 0.848349] | [0.751826, 0.877232] | 0/12/0 |
| MSL | grid100 | interval / incremental | flat/one | 1.76374 | [1.7111, 1.82824] | [1.70968, 1.8195] | [1.70968, 1.8195] | 2/0/0 |
| MSL | grid100 | interval / incremental | flat/reciprocal | 1.75432 | [1.47677, 1.78669] | [1.67612, 1.83616] | [1.67612, 1.83616] | 2/0/0 |
| MSL | grid100 | interval / incremental | flat/improved | 1.77049 | [1.70978, 1.78778] | [1.70259, 1.8411] | [1.70259, 1.8411] | 2/0/0 |
| MSL | grid100 | interval / incremental | front/one | 1.76348 | [1.75443, 1.78019] | [1.68949, 1.8407] | [1.68949, 1.8407] | 2/0/0 |
| MSL | grid100 | interval / incremental | front/reciprocal | 1.75028 | [1.71303, 1.77732] | [1.66761, 1.83704] | [1.66761, 1.83704] | 2/0/0 |
| MSL | grid100 | interval / incremental | front/improved | 1.7742 | [1.75492, 1.80035] | [1.69621, 1.85578] | [1.69621, 1.85578] | 2/0/0 |
| MSL | grid100 | interval / incremental | back/one | 1.74495 | [1.68533, 1.78595] | [1.70759, 1.78313] | [1.70759, 1.78313] | 2/0/0 |
| MSL | grid100 | interval / incremental | back/reciprocal | 1.72792 | [1.68814, 1.78331] | [1.67473, 1.78279] | [1.67473, 1.78279] | 2/0/0 |
| MSL | grid100 | interval / incremental | back/improved | 1.73158 | [1.69605, 1.75876] | [1.68689, 1.77746] | [1.68689, 1.77746] | 2/0/0 |
| MSL | grid100 | interval / incremental | middle/one | 1.77192 | [1.65735, 1.79337] | [1.74257, 1.80177] | [1.74257, 1.80177] | 2/0/0 |
| MSL | grid100 | interval / incremental | middle/reciprocal | 1.75017 | [1.70912, 1.76734] | [1.6967, 1.80532] | [1.6967, 1.80532] | 2/0/0 |
| MSL | grid100 | interval / incremental | middle/improved | 1.73307 | [1.69775, 1.7895] | [1.68714, 1.78026] | [1.68714, 1.78026] | 2/0/0 |
| MSL | distinct | interval / incremental | flat/one | 1.73483 | [1.67725, 1.82383] | [0.78127, 3.85225] | [0.78127, 3.85225] | 1/1/0 |
| MSL | distinct | interval / incremental | flat/reciprocal | 1.70723 | [1.66668, 1.72831] | [0.774346, 3.76398] | [0.774346, 3.76398] | 1/1/0 |
| MSL | distinct | interval / incremental | flat/improved | 1.65408 | [1.57897, 1.7654] | [0.779607, 3.50944] | [0.779607, 3.50944] | 1/1/0 |
| MSL | distinct | interval / incremental | front/one | 1.71762 | [1.68111, 1.76612] | [0.777004, 3.79692] | [0.777004, 3.79692] | 1/1/0 |
| MSL | distinct | interval / incremental | front/reciprocal | 1.67148 | [1.50695, 1.70627] | [0.763244, 3.66047] | [0.763244, 3.66047] | 1/1/0 |
| MSL | distinct | interval / incremental | front/improved | 1.70367 | [1.64448, 1.76594] | [0.768204, 3.7783] | [0.768204, 3.7783] | 1/1/0 |
| MSL | distinct | interval / incremental | back/one | 1.72874 | [1.62561, 1.77056] | [0.783028, 3.81666] | [0.783028, 3.81666] | 1/1/0 |
| MSL | distinct | interval / incremental | back/reciprocal | 1.74779 | [1.69458, 1.78124] | [0.768976, 3.97254] | [0.768976, 3.97254] | 1/1/0 |
| MSL | distinct | interval / incremental | back/improved | 1.73559 | [1.68812, 1.77256] | [0.770524, 3.9094] | [0.770524, 3.9094] | 1/1/0 |
| MSL | distinct | interval / incremental | middle/one | 1.68396 | [1.58892, 1.74631] | [0.774657, 3.6606] | [0.774657, 3.6606] | 1/1/0 |
| MSL | distinct | interval / incremental | middle/reciprocal | 1.68312 | [1.64242, 1.73495] | [0.775206, 3.65437] | [0.775206, 3.65437] | 1/1/0 |
| MSL | distinct | interval / incremental | middle/improved | 1.71166 | [1.62445, 1.7795] | [0.780128, 3.75552] | [0.780128, 3.75552] | 1/1/0 |
| MSL | grid100 | raster / interval | flat/one | 0.868437 | [0.846505, 0.943785] | [0.851588, 0.885618] | [0.851588, 0.885618] | 0/2/0 |
| MSL | grid100 | raster / interval | flat/reciprocal | 0.887615 | [0.867972, 0.904918] | [0.876482, 0.89889] | [0.876482, 0.89889] | 0/2/0 |
| MSL | grid100 | raster / interval | flat/improved | 0.87645 | [0.873673, 0.889597] | [0.876059, 0.876842] | [0.876059, 0.876842] | 0/2/0 |
| MSL | grid100 | raster / interval | front/one | 0.900852 | [0.893728, 0.92371] | [0.894923, 0.906821] | [0.894923, 0.906821] | 0/2/0 |
| MSL | grid100 | raster / interval | front/reciprocal | 0.902241 | [0.88742, 0.916317] | [0.891764, 0.912841] | [0.891764, 0.912841] | 0/2/0 |
| MSL | grid100 | raster / interval | front/improved | 0.895387 | [0.885026, 0.908177] | [0.888834, 0.901988] | [0.888834, 0.901988] | 0/2/0 |
| MSL | grid100 | raster / interval | back/one | 0.904736 | [0.895431, 0.930797] | [0.897893, 0.911631] | [0.897893, 0.911631] | 0/2/0 |
| MSL | grid100 | raster / interval | back/reciprocal | 0.905625 | [0.887691, 0.923063] | [0.89921, 0.912085] | [0.89921, 0.912085] | 0/2/0 |
| MSL | grid100 | raster / interval | back/improved | 0.903182 | [0.890006, 0.914447] | [0.897228, 0.909177] | [0.897228, 0.909177] | 0/2/0 |
| MSL | grid100 | raster / interval | middle/one | 0.899512 | [0.875604, 0.918904] | [0.895808, 0.903232] | [0.895808, 0.903232] | 0/2/0 |
| MSL | grid100 | raster / interval | middle/reciprocal | 0.906974 | [0.893092, 0.977931] | [0.905739, 0.908211] | [0.905739, 0.908211] | 0/2/0 |
| MSL | grid100 | raster / interval | middle/improved | 0.901554 | [0.882183, 0.915663] | [0.88879, 0.914501] | [0.88879, 0.914501] | 0/2/0 |
| MSL | distinct | raster / interval | flat/one | 0.816644 | [0.791022, 0.969076] | [0.699, 0.954087] | [0.699, 0.954087] | 0/2/0 |
| MSL | distinct | raster / interval | flat/reciprocal | 0.813143 | [0.804966, 0.838612] | [0.715007, 0.92475] | [0.715007, 0.92475] | 0/2/0 |
| MSL | distinct | raster / interval | flat/improved | 0.820235 | [0.806919, 0.933917] | [0.706296, 0.952556] | [0.706296, 0.952556] | 0/2/0 |
| MSL | distinct | raster / interval | front/one | 0.833166 | [0.817042, 0.849523] | [0.732393, 0.947805] | [0.732393, 0.947805] | 0/2/0 |
| MSL | distinct | raster / interval | front/reciprocal | 0.841026 | [0.829649, 0.867131] | [0.733543, 0.964258] | [0.733543, 0.964258] | 0/2/0 |
| MSL | distinct | raster / interval | front/improved | 0.833135 | [0.810771, 0.844909] | [0.732785, 0.947227] | [0.732785, 0.947227] | 0/2/0 |
| MSL | distinct | raster / interval | back/one | 0.839904 | [0.809924, 0.862079] | [0.735947, 0.958546] | [0.735947, 0.958546] | 0/2/0 |
| MSL | distinct | raster / interval | back/reciprocal | 0.831447 | [0.820499, 0.849142] | [0.731573, 0.944956] | [0.731573, 0.944956] | 0/2/0 |
| MSL | distinct | raster / interval | back/improved | 0.842271 | [0.830426, 0.853084] | [0.734698, 0.965596] | [0.734698, 0.965596] | 0/2/0 |
| MSL | distinct | raster / interval | middle/one | 0.83905 | [0.818652, 0.851228] | [0.731018, 0.963048] | [0.731018, 0.963048] | 0/2/0 |
| MSL | distinct | raster / interval | middle/reciprocal | 0.840735 | [0.824961, 0.854629] | [0.734518, 0.962311] | [0.734518, 0.962311] | 0/2/0 |
| MSL | distinct | raster / interval | middle/improved | 0.839391 | [0.816867, 0.859588] | [0.73367, 0.960346] | [0.73367, 0.960346] | 0/2/0 |

</details>

Frozen identities and generated audit receipts:

- Protocol: `5c7e404b8005670b3c78b6a3480faa6ac51447b79b4a78203bccd0109a18495b`; frozen `2026-10-24T09:19:02.351377+00:00`.
- Completion: `e412e0809d54bc29f36b465fa917d11318efb8135719e004ec21cb59e9ff26fa`; completed `2026-10-24T09:25:59.226251+00:00`.
- Records: `55f564fbbdcff56c1939b46bf79f9a8ec375a35a382b9be82e53794bf0ce11d1`.
- Unchanged statistical/output auditor: `2285fbb8b79aab3a9d365ac0cf7097b9b33098abc1fa78424a3ceaf138724923`.
- [Independent report](../../../artifacts/pvldb-research-20261024/strengthening/weighted-control-mac-v1/independent-report.json): `4dfce10ea4f3528caa9580ee5427f93eeda34fb0255f3b151fd306427682ca4b`.
- [Post-hoc tie report](../../../artifacts/pvldb-research-20261024/strengthening/weighted-control-mac-v1/posthoc-tie-sensitivity.json): `6b8b7f49f34cdaf1f6b1b2c573117023e51fa4e8e4d0f6fee3a960d78439acea`.

This reconstruction does not add timings, alter sources or protocols, or pool Mac and Linux measurements. The selected arrays are disjoint from the checked earlier panels, but shared physical sources remain possible. MSL is too small for population inference. Fresh Linux control results were still pending when this report was produced.
