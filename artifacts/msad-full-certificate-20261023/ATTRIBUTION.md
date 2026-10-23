# Source attribution and scope

Source: Emmanouil Sylligardos, Paul Boniol, John Paparrizos, Panos Trahanias, and Themis Palpanas, “Choose Wisely: An Extensive Evaluation of Model Selection for Anomaly Detection in Time Series,” PVLDB 16(11), 2023, 3418–3432, DOI [10.14778/3611479.3611536](https://doi.org/10.14778/3611479.3611536).

The source [MSAD repository](https://github.com/boniolp/MSAD/tree/8141b94eb3d2b1811f81ffcf7bc8aa5dcbd6c204) links the [TSB.zip archive](https://drive.google.com/file/d/1PQKwu5lZTnTmsmms1ipko9KF712Oc5DE/view). The code repository has an MIT license; this is not taken to relicense all underlying data sources. Raw data and original score arrays stay in ignored local cache and are not redistributed in this public directory. These are acquisition metadata and identity/validation receipts, not new detector predictions.

The pinned [score loader](https://github.com/boniolp/MSAD/blob/8141b94eb3d2b1811f81ffcf7bc8aa5dcbd6c204/utils/scores_loader.py#L79) parses headerless numeric files. Its writer uses `fmt='%.2f'` at line 116. Stored-score precision is preserved exactly as available; no additional rounding, inference, imputation, or padding is applied. The experiment reevaluates the published stored vectors and does not claim to recover unavailable full-precision original detector outputs.

The fixed primary selection is described in [the acquisition design](../../docs/msad_score_corpus_design_20261023.md). Candidate names and array identities differ from the earlier evaluated inputs after the declared conservative filter, but sources, parent recordings, and domains may overlap. Candidate exclusions retain reasons. No metric or model-ranking result is produced by this acquisition.
