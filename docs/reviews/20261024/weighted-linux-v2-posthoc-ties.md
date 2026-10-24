# Descriptive post-hoc tied-winner sensitivity

This analysis was added after review. It reconstructs saved trial-0 maxima and checks all repeated records and complete curves; it adds no detector fits, metric evaluations, timings or preregistered finding.

Verified 26 recordings, 12 semantic contracts, 11232 records and 156 curve files. Winner tolerance: `1e-10`. Reference: `raster`; model order: `['FFT', 'COPOD']`.

Best regret chooses the best observed-distinct performer among all grid winners. Worst regret chooses the worst among that same tolerance-based winner set. Both compare with the maximum over observed score thresholds; the below-minimum state is excluded.

| Bias | Cardinality | Grid ties | Nonoverlap | Best ≥ .01 | Worst ≥ .01 | Max best | Max worst |
|---|---|---:|---:|---:|---:|---:|---:|
| flat | one | 0 | 0 | 0 | 0 | 0 | 0 |
| flat | reciprocal | 0 | 0 | 0 | 0 | 0 | 0 |
| flat | improved | 0 | 0 | 0 | 0 | 0 | 0 |
| front | one | 0 | 0 | 0 | 0 | 0 | 0 |
| front | reciprocal | 0 | 0 | 0 | 0 | 0 | 0 |
| front | improved | 0 | 0 | 0 | 0 | 0 | 0 |
| back | one | 0 | 0 | 0 | 0 | 0 | 0 |
| back | reciprocal | 0 | 0 | 0 | 0 | 0 | 0 |
| back | improved | 0 | 0 | 0 | 0 | 0 | 0 |
| middle | one | 0 | 1 | 0 | 0 | 0.00141219497462 | 0.00141219497462 |
| middle | reciprocal | 0 | 0 | 0 | 0 | 0 | 0 |
| middle | improved | 0 | 0 | 0 | 0 | 0 | 0 |

Across settings, 0 distinct recordings have best regret ≥ .01 and 0 have worst regret ≥ .01. These are descriptive counts with no independence or population claim.

Completion SHA256: `f270a39a0e0604ede206632f51aa28557e7a13c1bd18fc55dba784b3796e77eb`. Protocol SHA256: `811c3cf6f9ad2b7183d3bdf308e2fcce8b7ed83eb247cff121ddc7df908a3a2a`. Records SHA256: `441c7524c6c2cdff7e490417c1314f6ba41c0065fc4195010666eb05cb914172`.

Archive-only consistency, not an independent raw-data metric recomputation. No confidence interval, population interpretation or practical-benefit hypothesis is added. Semantic settings and recordings are dependent; no post-hoc case selection or replacement is performed.
