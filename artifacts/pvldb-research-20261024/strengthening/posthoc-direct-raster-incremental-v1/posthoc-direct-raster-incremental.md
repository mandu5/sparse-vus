# Exploratory post-hoc direct raster/incremental comparison

These additional contrasts were specified after examining the supplemental interval-control results. They are exploratory post-hoc analyses, not prospectively frozen findings. Only saved durations are resampled; there are no new detector fits, metric evaluations or timing runs.

Each ratio is raster time divided by incremental time, using the median of six balanced orders for each recording and semantic setting, then equal log weight over all twelve settings and all recordings in the collection. Incremental means bucket for grid100 and sweep for distinct. The original independent auditor's byte-pinned bootstrap resamples six paired trial indices separately within each recording and shares those indices across both methods and all twelve semantics. Recording membership is fixed.

Intervals use 10,000 resamples, seed 20261024, and Bonferroni tails 0.025/6 and 1−0.025/6 over the three collections × two query contracts within each host. They are not jointly adjusted across hosts or the other reported contrasts. Six balanced orders support limited approximate timing uncertainty; these intervals do not give population coverage or correct post-hoc comparator selection. No interval is assigned to the minimum-control scatter.

| Host | Collection | Query | Raster / incremental | Paired-order interval | Recording W/L/T | Semantic ratio range |
|---|---|---|---:|---|---:|---|
| Mac (arm64) | WSD | grid100 | 1.5261735 | [1.5177417, 1.5310871] | 12/0/0 | [1.4884143, 1.549476] |
| Mac (arm64) | WSD | distinct | 8.6079854 | [8.5490627, 8.6391211] | 12/0/0 | [8.1892109, 8.8285914] |
| Mac (arm64) | Stock | grid100 | 1.6110841 | [1.6015019, 1.6178918] | 12/0/0 | [1.4789806, 1.6998865] |
| Mac (arm64) | Stock | distinct | 21.990719 | [21.907944, 22.050494] | 12/0/0 | [20.37766, 22.799231] |
| Mac (arm64) | MSL | grid100 | 1.570581 | [1.5521913, 1.5840473] | 2/0/0 | [1.5316954, 1.5938663] |
| Mac (arm64) | MSL | distinct | 1.4205216 | [1.4025404, 1.4610007] | 1/1/0 | [1.3567347, 1.4618408] |
| Linux (x86_64) | WSD | grid100 | 1.6720505 | [1.6612465, 1.6797909] | 12/0/0 | [1.657187, 1.6844816] |
| Linux (x86_64) | WSD | distinct | 11.621357 | [11.111286, 11.667514] | 12/0/0 | [11.313475, 11.900747] |
| Linux (x86_64) | Stock | grid100 | 1.5481183 | [1.5426858, 1.5553391] | 12/0/0 | [1.4948098, 1.5936629] |
| Linux (x86_64) | Stock | distinct | 26.71685 | [26.579055, 26.786263] | 12/0/0 | [25.56905, 28.440426] |
| Linux (x86_64) | MSL | grid100 | 1.6648495 | [1.6537802, 1.6898782] | 2/0/0 | [1.6096993, 1.6973844] |
| Linux (x86_64) | MSL | distinct | 1.7262432 | [1.6952394, 1.7760578] | 1/1/0 | [1.7064028, 1.7518593] |

All twelve point estimates were cross-checked against the independently exported direct-median CSVs. Raster is faster than interval for every Linux recording after semantic aggregation, but not every Mac recording; this report retains a fixed raster comparison and does not substitute an observed minimum comparator into the bootstrap. Both hosts retain the distinct-query MSL id7 raster/incremental loss. MSL contains only two selected recordings.

Frozen bootstrap auditor SHA256: `2285fbb8b79aab3a9d365ac0cf7097b9b33098abc1fa78424a3ceaf138724923`.
Report source SHA256: `c85176b3e88d33a32e2fe674f25d44666ea59dc0e3e203decebbb2aca53912fc`.
Presentation CSV SHA256: `f5363d4ad01bfc7cadaa8b44b42bbe62aa8bba8df7e1085205dc5491da67ab46`.
