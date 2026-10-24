# Independent Linux weighted interval-control reconstruction

The fresh Linux replay completed in CI run 40081512476. Its unchanged independent auditor passed all 26 recordings, 11,232 records and 156 curve files with on-host input verification. A second archive-only audit on Mac preserved that CI report and independently reconstructed the saved outputs: maximum curve error 2.3869795029440866e-15 and zero detector-winner disagreements. No timings were rerun for this review.

The two reports have one intended nonnumeric difference: `local_input_bytes_verified` is true for CI and false for the Mac archive-only reconstruction. Their statistical values agree to maximum absolute difference 6.3948846218409017e-14 and relative difference 1.2935548113753007e-15; 337 serialized floating-point fields differ at this scale. Raw Linux inputs were verified by the CI native-input auditor, not downloaded or rechecked by this archive-only run.

All ratios below divide control time by candidate time; values above one favor the candidate. Incremental means bucket for grid100 and sweep for distinct. Six balanced trial orders are summarized by medians; twelve semantic settings receive equal log weight within each recording. The paired-order intervals condition on this fixed panel and host; separate recording-reweighting intervals are sensitivity summaries, not population confidence statements. The original correction is 36 semantic estimates or 3 collection aggregates within each of four comparisons, not jointly across all comparisons. MSL has only two selected recordings.

| Collection | Query | Control / candidate | Aggregate ratio | Paired-order interval | Recording-reweighting interval | Semantic ratio range | Recording W/L/T |
|---|---|---|---:|---|---|---|---:|
| WSD | grid100 | interval / incremental | 2.3079882 | [2.2933636, 2.3150832] | [2.1231602, 2.4881546] | [2.2949098, 2.3180002] | 12/0/0 |
| WSD | distinct | interval / incremental | 12.944875 | [12.395917, 12.990615] | [7.566455, 21.138969] | [12.806554, 13.112605] | 12/0/0 |
| WSD | grid100 | raster / interval | 0.72446233 | [0.72309199, 0.72780956] | [0.70021482, 0.75970668] | [0.71788858, 0.732569] | 0/12/0 |
| WSD | distinct | raster / interval | 0.89775742 | [0.89668394, 0.89873579] | [0.86313324, 0.9359612] | [0.87853236, 0.90888004] | 0/12/0 |
| Stock | grid100 | interval / incremental | 2.2893577 | [2.2821449, 2.2955121] | [2.2298406, 2.3724286] | [2.2177958, 2.3557286] | 12/0/0 |
| Stock | distinct | interval / incremental | 36.148889 | [35.976604, 36.224209] | [27.993798, 46.8626] | [34.698187, 37.945002] | 12/0/0 |
| Stock | grid100 | raster / interval | 0.67622384 | [0.67494371, 0.67876398] | [0.66603316, 0.68575984] | [0.65417202, 0.71530524] | 0/12/0 |
| Stock | distinct | raster / interval | 0.73907803 | [0.73866456, 0.7402837] | [0.72598859, 0.75271889] | [0.68272715, 0.79325612] | 0/12/0 |
| MSL | grid100 | interval / incremental | 2.3310406 | [2.3058255, 2.3480563] | [2.1399805, 2.5391587] | [2.2809466, 2.3647063] | 2/0/0 |
| MSL | distinct | interval / incremental | 2.3814768 | [2.3465676, 2.4178349] | [1.0244726, 5.5359523] | [2.3394926, 2.4367153] | 2/0/0 |
| MSL | grid100 | raster / interval | 0.71420872 | [0.71362569, 0.72420329] | [0.70597691, 0.72253652] | [0.70571546, 0.71840118] | 0/2/0 |
| MSL | distinct | raster / interval | 0.72486252 | [0.71451825, 0.73658102] | [0.66759657, 0.7870407] | [0.70484377, 0.74094618] | 0/2/0 |

All 72 interval/incremental collection/semantic/query estimates have paired-order lower limits above one. This does not mean every recording/semantic setting wins: MSL id7 loses three distinct-query settings against interval and all twelve against raster. Raster is faster than interval in every collection/query aggregate and every recording after semantic aggregation on this host. Thus an interval-only comparison would overstate advantage over the faster measured conventional control.

| MSL recording | Query | Control / candidate | Ratio over twelve settings | Semantic ratio range | Semantic W/L/T |
|---|---|---|---:|---|---:|
| id7 | grid100 | interval / incremental | 2.1399805 | [2.0801608, 2.2035472] | 12/0/0 |
| id7 | grid100 | raster / interval | 0.72253652 | [0.70858262, 0.73002213] | 0/12/0 |
| id7 | grid100 | raster / incremental | 1.5462141 | [1.4739658, 1.6072874] | 12/0/0 |
| id7 | distinct | interval / incremental | 1.0244726 | [0.99350958, 1.067727] | 9/3/0 |
| id7 | distinct | raster / interval | 0.66759657 | [0.64993405, 0.68675781] | 0/12/0 |
| id7 | distinct | raster / incremental | 0.68393441 | [0.67591051, 0.69738619] | 0/12/0 |
| id3 | grid100 | interval / incremental | 2.5391587 | [2.5011131, 2.5717287] | 12/0/0 |
| id3 | grid100 | raster / interval | 0.70597691 | [0.69942123, 0.71405896] | 0/12/0 |
| id3 | grid100 | raster / incremental | 1.7925874 | [1.7579321, 1.8257457] | 12/0/0 |
| id3 | distinct | interval / incremental | 5.5359523 | [5.4780552, 5.597729] | 12/0/0 |
| id3 | distinct | raster / interval | 0.7870407 | [0.76439254, 0.80914975] | 0/12/0 |
| id3 | distinct | raster / incremental | 4.3570197 | [4.2570556, 4.5173247] | 12/0/0 |

MSL id7 is `146_MSL_id_7_Sensor_tr_554_1st_1172`; id3 is `142_MSL_id_3_Sensor_tr_1525_1st_4575`. The three Linux interval/sweep losses on id7 are back/improved (0.999118387), middle/reciprocal (0.993509576), and middle/improved (0.999361111). Its aggregate interval/sweep ratio is 1.02447262, but raster/sweep is 0.683934407, so the descriptive faster-control scatter correctly retains this loss.

The separately labeled post-hoc tie audit passed. There are no grid-winner ties in any of the 26×12 settings, so best and worst tie regrets coincide: maximum 0.00141219497462175; neither reaches 0.01 on any recording. This is descriptive post-hoc sensitivity, not an original prespecified worst-tie result.

The renderer reconstructed all original semantic and aggregate point estimates from raw median durations. Its direct raster/incremental point estimates also equal products of the two original contrasts within 1e-12. The separately named [exploratory direct-comparison report](../../../artifacts/pvldb-research-20261024/strengthening/posthoc-direct-raster-incremental-v1/posthoc-direct-raster-incremental.md) adds paired-order intervals with six comparisons per host; it does not amend the original protocol or borrow an interval for the minimum-control scatter.

Cross-host generation receipts bind all 26 raw archive members, original observation hashes, labels, raw NPZ files and native raw CSVs identically. The explicitly declared one-ULP decoding compatibility restores the original frozen observation vector on Linux before fitting. All 26 FFT profiles match Mac bitwise. COPOD matches on one recording and differs on 25; only WSD id6 changes distinct count (1686 to 1687). Hash differences alone do not quantify numerical score differences. This is a fresh pipeline replay on the same typed input panel, not an exact-score clone or an additional independent dataset panel.

The two-host figure chooses the faster of raster and interval separately per recording after geometric aggregation over all twelve semantics. Its x-axis sums distinct queries across FFT and COPOD. It is descriptive post-hoc, has no confidence interval and does not pool hosts. All 26 grid100 cases win against this choice on each host; 25 of 26 distinct-query cases win, with MSL id7 retained as the loss on both.

Exact per-recording/semantic results, durations and both original interval summaries are exported to the [presentation CSV directory](../../../artifacts/pvldb-research-20261024/strengthening/figures/interval-control-two-host-v1/). The 52 plotted points are the same 26 selected recordings evaluated on each host.

Artifact identities:

- Linux complete: `artifacts/pvldb-research-20261024/strengthening/linux-interval-replay/weighted-control-linux-v1/complete.json` — SHA256 `e075913c0cd974241a9d91d6e78d57b620a765f098075de77e5cc97f2c8a27d3`.
- CI independent report: `artifacts/pvldb-research-20261024/strengthening/linux-interval-replay/weighted-control-linux-v1/independent-report.json` — SHA256 `12e16b3f2f0715b8a6dcc64cbfe526e58c3c8651cffe5137287e4152e749a050`.
- Archive-only independent report: `artifacts/pvldb-research-20261024/strengthening/linux-interval-replay/weighted-control-linux-v1/archived-output-report.json` — SHA256 `747f63634d80c3e31e321afef31c077994356b33cc78ac8d50f12a5c9d3e684c`.
- Post-hoc tie report: `artifacts/pvldb-research-20261024/strengthening/linux-interval-replay/weighted-control-linux-v1/posthoc-tie-sensitivity.json` — SHA256 `fa9be234611548743923e65e35dadeadc2bfa32fe49bfa0845fa34c298c5abf1`.
- Host input identity comparison: `artifacts/pvldb-research-20261024/strengthening/cross-host-input-identity.json` — SHA256 `b18a8dad732e6c9a7b593d3dcacda1fb02bfad8365a4d184f268f5a0fd52574e`.
- Presentation receipt: `artifacts/pvldb-research-20261024/strengthening/figures/interval-control-two-host-v1/presentation-receipt.json` — SHA256 `e43022a623fc906469b18391efd81625680000c5e8dc106d23b10ee766f09c58`.
- PDF: `artifacts/pvldb-research-20261024/strengthening/figures/interval-control-two-host-v1/interval-control-query-regime.pdf` — SHA256 `935f6308b8605500a541d1ec1ac6280547fe2e457a843b397206ff0b26ab90e1`.
