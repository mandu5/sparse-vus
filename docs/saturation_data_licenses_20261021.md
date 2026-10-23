# External saturation inputs: attribution and redistribution scope

Checked 2026-10-21. The sparse-vus project's MIT license covers its own code;
it does not relicense third-party observations, labels, metadata, or rights
that may apply to derived score arrays. No blanket MIT claim is made for the
external inputs. Raw CSV observations and generated NPZ arrays remain in the
ignored cache and are not included in GitHub Actions artifacts.

## mTSBench attribution and pinned sources

Xiaona Zhou, Constantin Brif, and Ismini Lourentzou, *mTSBench: Benchmarking
Multivariate Time Series Anomaly Detection and Model Selection at Scale*,
Transactions on Machine Learning Research, 2026.
[Paper](https://openreview.net/forum?id=8LfB8HD1WU),
[project](https://plan-lab.github.io/projects/mtsbench/).

The [pinned dataset card](https://huggingface.co/datasets/PLAN-Lab/mTSBench/blob/8dea9af65a9895f39e9e76f118cf23a94d2d4d0a/README.md)
declares CC BY-NC 4.0 and separately lists original dataset terms. The
[pinned repository license](https://github.com/PLAN-Lab/mTSBench/blob/0ebf90da7642e103192e05971fdb44e3149bcd51/LICENSE)
is also CC BY-NC 4.0. Its code and copied metadata are not MIT-licensed.
The raw pinned card has SHA-256
`36df51b40134ad04e5519f46af11d07fbd18c6ac83fe85d081da0536017651f1`.

Copied mTSBench metadata in selection and acquisition receipts is attributed
to these authors under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
Our modifications select 12 test files from nine source families, normalize
family aliases, append integrity and environment receipts, and generate four
classical control scores per series. These modifications and measurements
do not imply endorsement by mTSBench or the original data creators.

## Selected original dataset terms

The card's family terms are recorded below as upstream statements, not an
independent grant from this project. A compilation-level license does not
resolve a more restrictive or missing source-specific permission.

| Source family | Original dataset terms reported by the pinned card | Additional primary evidence |
| --- | --- | --- |
| CalIt2 | CC BY 4.0 | Pinned card, original dataset terms column |
| GECCO | Citation Required | [Original Zenodo record](https://zenodo.org/records/3884398) and its [API metadata](https://zenodo.org/api/records/3884398) explicitly identify CC BY 4.0 (`license.id=cc-by-4.0`). Creators: Steffen Moritz, Frederik Rehbach, Sowmya Chandrasekaran, Margarita Rebolledo, Thomas Bartz-Beielstein; data provided by Thüringer Fernwasserversorgung and IMProvT. |
| GHL | Contact Authors | [Original download endpoint](https://kas.pr/ics-research/dataset_ghl_1) provides a download, but an explicit redistribution grant was not identified. Permission to publish our labels-plus-scores bundle is **unknown**. |
| Genesis | CC BY-NC-SA 4.0 | [Original inIT-OWL dataset](https://www.kaggle.com/datasets/inIT-OWL/genesis-demonstrator-data-for-machine-learning) also identifies CC BY-NC-SA 4.0 in its public API metadata. |
| GutenTAG | MIT | Pinned card, original dataset terms column |
| Metro | CC BY 4.0 | Pinned card, original dataset terms column |
| Occupancy (`room-occupancy`) | CC BY 4.0 | Pinned card, original dataset terms column |
| PSM | CC BY 4.0 | Pinned card, original dataset terms column |
| SWAN-SF (`swan`) | MIT | Pinned card, original dataset terms column |

The [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/), and
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)
terms differ in attribution, noncommercial, and ShareAlike obligations.
GHL's missing explicit grant means permission to publish the complete
9.6 MB derived NPZ collection is not established by this review. Whether
particular generated scores independently carry source-data rights is not
assumed either way. No such collection is published by this workflow.

## Reproduction transport

The Linux workflow downloads the same revision-pinned public source files
and regenerates scores with the frozen procedure. It uploads JSON metadata,
hashes, benchmark outcomes, scripts, and this notice. It uploads no raw CSV,
NPY, or NPZ files. This preserves the download-and-regenerate route without
claiming that every input can be redistributed under a common license.

Raw-byte SHA-256, binary-label SHA-256, series identity, family, row count,
and model definitions must match the Mac reference. All 48 generated score
hashes are compared and differences recorded; numerical library/platform
differences can change floating-point bytes. Linux regeneration must not
be described as an identical-input replay unless the recorded hashes prove it.
