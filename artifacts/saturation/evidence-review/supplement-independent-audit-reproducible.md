# Reproducible independent supplement audit

**PASS_RECORDED_SUPPLEMENT**

Cases: 48; series: 12; families: 9. Maximum completed paired-output discrepancy: 8.215650382226158e-15.

| Comparator | Completed / prescribed | Median | Geomean | Aggregate | Wins / losses / ties | Minimum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| radix_pair | 48/48 | 1.016526 | 1.035677 | 1.055205 | 29/19/0 | 0.911087 |
| benchopt_pair | 48/48 | 34.918408 | 35.880354 | 60.950994 | 48/0/0 | 20.078662 |
| dtaianomaly_pair | 10/12 | 101.106239 | 144.452780 | 318.384389 | 10/0/0 | 25.612268 |

Ratios are comparator median time / saturation median time.

dtaianomaly_pair incomplete cases (no inferred ratio): `PSM_test|isolation_forest|30` (0 completed repeats), `swan_sf_test|isolation_forest|30` (0 completed repeats)

Cache-free independent reconstruction of recorded receipt identities, seeded order, worker lifecycle, completed-output parity, censoring and paired timing statistics. No metric kernel or data array is loaded. Source hashes are recorded identities; cached source bytes and NPZ contents are not reverified. DTAI ratios describe only completed parity-valid pairs; no timeout is treated as an evaluator time or speed ratio. This descriptive supplement does not change the earlier primary criterion or its outcome.

Frozen protocol SHA-256: `8e9bf4a9e1d938f9b4467e46050ff5820ab04083d5cc8011cf770eb5083ae5ad`

Auditor SHA-256: `2a524c3c73b1a459ed5c6c4bd0746ec6d076ab32efacae25be507aa5326b8f43`
