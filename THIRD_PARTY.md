# Sources, licenses, and provenance

The package under `src/sparse_vus` is independently written code. The MIT license
in this repository covers that code and the reproduction scripts, not external
datasets or upstream reference implementations.

| Material | Source and revision | Treatment |
|---|---|---|
| Numerical VUS reference | [TheDatumOrg/VUS](https://github.com/TheDatumOrg/VUS/tree/467bace0c103f5c2bdb4900306d82939bcac8ff9), commit `467bace0c103f5c2bdb4900306d82939bcac8ff9` | No repository LICENSE file was located in the pinned tree. Not vendored or relicensed. `experiments/fetch_reference.py` downloads the unmodified source to ignored `cache/` and verifies SHA-256. Cite Boniol et al. and Paparrizos et al. |
| dtaianomaly compiled reference | [ML-KULeuven/dtaianomaly](https://github.com/ML-KULeuven/dtaianomaly/tree/557b435790bebc57307d8e7f22047273ac923f36), commit `557b435790bebc57307d8e7f22047273ac923f36` | MIT; cached source and LICENSE are hash-checked. Adapter executes original function bodies and kernel decorators, omitting unrelated framework imports/classes. Attribution and exact source hash are in `artifacts/dtaianomaly_source.json`. |
| Klein fast-VUS | [tomlouisklein/fast-VUS](https://github.com/tomlouisklein/fast-VUS/tree/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00) | Apache-2.0. Unmodified source and license are downloaded to ignored cache, hash checked, and executed through `experiments/fast_vus_adapter.py`. It returns PR only. Support-score sorting and cumulative weighted sums are prior techniques, not our contribution. |
| Go semantic comparison | [stergiotis/boxer adscore](https://github.com/stergiotis/boxer/tree/v0.0.23/public/analytics/timeseries/adscore), `v0.0.23` | MIT, copyright Panos Stergiotis. Used as an unmodified Go module in ignored cache, not vendored. Our Go harness is original. `artifacts/native_go_audit.json` records actual execution. |
| Released model scores | [KU Leuven RDR, DOI 10.48804/MCVI4N](https://doi.org/10.48804/MCVI4N), V1.0 | CC BY 4.0. Credit Xiaokun Zhu, Louis Carpentier, Mathias Verbeke (2026), *When Foundation Models are One-Liners*. Three frozen model/context archives, all 350 common evaluation series. NPY scores are read unchanged with `allow_pickle=False`. Only score members are fetched; each ZIP CRC and SHA-256 is verified. Archive MD5 is source metadata, not claimed verified for partial range downloads. |
| Raw labels | [TSB-AD-U](https://www.thedatum.org/datasets/TSB-AD-U.zip), evaluation list pinned to TSB-AD commit `ed74348e7876c9268b7a737c77f2f5f56f7fa458` | Original dataset licenses vary. See [TSB-AD source/license inventory](https://thedatumorg.github.io/TSB-AD/). Raw labels and score vectors remain in ignored cache and are not redistributed. Derived metric results and source checksums are included. |

The score archive's README notes that released Chronos-Bolt and Time-MoE vectors
use leading zero padding, while its manuscript evaluations corrected that
padding. We preserve the released vectors: this project tests metric evaluators,
not the source paper's model leaderboard. No models were retrained or queried.

Additional material prior art: Emmanouil Sylligardos, *Fast or Accurate? Rethinking
Time Series Anomaly Detection*, VLDB PhD Workshop 2025, Section 4, already reports
large CPU/GPU VUS speedups. Its fast implementation was not located in the
2026-10-19 search and could not be benchmarked. This limits any SOTA or novelty
claim. See [the primary paper](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/PhD/PhD25_17.pdf).

The width-bound method applies established probability-box expectation bounds,
not a new general p-box theory: Utkin and Destercke (2009),
[DOI 10.1016/j.ijar.2009.02.004](https://doi.org/10.1016/j.ijar.2009.02.004),
and Troffaes and Destercke (2011), [arXiv:1103.1805](https://arxiv.org/abs/1103.1805).
Our code is an independent implementation of the VUS-specific construction.

The optional PVLDB manuscript uses the unmodified official template files.
Their source revision, hashes, and upstream license/source distribution are
recorded in [the manuscript packet](docs/submission_packet.md); the repository's
MIT license does not replace their original terms.
