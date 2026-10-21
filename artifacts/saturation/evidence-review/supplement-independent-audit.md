# Independent supplemental evidence audit

**PASS_RECORDED_SUPPLEMENT**: 48 cases, 12 series, 9 families; complete source/input/log hash chain and seeded method order verified.

All 462 completed paired-output repetitions satisfy absolute parity tolerance 1e-11; maximum discrepancy 8.215650382226158e-15. Two timed watchdog expirations and four subsequent unattempted repeats are recorded separately.

| Comparator | Completed / prescribed | Median ratio | Geomean | Aggregate | Wins / losses / ties | Minimum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| radix_pair | 48/48 | 1.016526 | 1.035677 | 1.055205 | 29/19/0 | 0.911087 |
| benchopt_pair | 48/48 | 34.918408 | 35.880354 | 60.950994 | 48/0/0 | 20.078662 |
| dtaianomaly_pair | 10/12 | 101.106239 | 144.452780 | 318.384389 | 10/0/0 | 25.612268 |

Ratios are comparator median time / saturation median time. DTAI PSM and swan cases each hit the first timed-call 30-second parent watchdog; no evaluator duration, value, ratio, or lower-bound ratio is manufactured for either. Their remaining repeats were not attempted, and worker restart history agrees with the recorded censoring.

This post-primary supplement returns both ROC and PR and uses persistent spawn workers; it does not replace, pool with, or reverse the earlier primary PR-only study and its failed primary criterion.

The audit uses only standard-library JSON, SHA-256 and scalar arithmetic. It verifies recorded parity rather than recomputing metrics from the original observations. Full per-case ratios, loss IDs and censor details are in the adjacent JSON.

Frozen protocol SHA-256: `8e9bf4a9e1d938f9b4467e46050ff5820ab04083d5cc8011cf770eb5083ae5ad`
