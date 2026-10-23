# Unified Sparse VUS submission packet

Prepared 23 October 2026 from `paper/sparse_vus.tex` and its included sources. This is prepared submission material, not evidence of submission, editorial review, or acceptance. The separately frozen collection-workflow experiment is complete, with all nine passes retained and its measured result integrated into the manuscript.

## Submission metadata

| Field | Prepared value |
|---|---|
| Title | Sparse Events and Complete-Tie Prefixes for Exact VUS Evaluation |
| Author | Youngmin Ko |
| Affiliation | Independent Researcher |
| Country | Republic of Korea |
| Correspondence | rhdudals0505@naver.com |
| Target | PVLDB Volume 20, Regular Research |
| Research flavor | Foundations and Algorithms |
| Suggested topical descriptions | Time-series analytics; exact metric evaluation; algorithm engineering; data management for ML |
| Main PDF | [`paper/sparse_vus.pdf`](../paper/sparse_vus.pdf) |
| Main source | [`paper/sparse_vus.tex`](../paper/sparse_vus.tex), [`paper/sparse_vus_body.tex`](../paper/sparse_vus_body.tex), [`paper/sparse_vus_references.bib`](../paper/sparse_vus_references.bib) |
| Repository | [Sparse VUS](https://github.com/mandu5/sparse-vus) |
| Reproduction guide | [`sparse_vus_reproduction_20261023.md`](sparse_vus_reproduction_20261023.md) |

These identity fields reproduce supplied manuscript metadata. They do not attest to human contribution, approval, or the truth of declarations that the author must make personally.

The current [research call](https://vldb.org/2027/call-for-research-track.html) places formal algorithmic work under the Foundations and Algorithms flavor of Regular Research. The [submission guidelines](https://vldb.org/2027/submission-guidelines.html) allow 12 pages excluding references for Regular Research and require author identification because review is single blind. The [formatting guidelines](https://vldb.org/2027/formatting-guidelines.html) require the current PVLDB template and its mandatory blocks. These official pages were checked on 23 October 2026.

For the November cycle, the published schedule requires an abstract by **25 October 2026** and the full paper by **1 November 2026, 5:00 PM Pacific Time**. The official [submission guidelines](https://vldb.org/2027/submission-guidelines.html) and the selected portal cycle control the actual deadlines. This packet does not create a submission or reserve a cycle.

## Full abstract

The following is the current manuscript abstract with LaTeX notation transcribed into Markdown mathematics. The separately measured collection result is included.

Volume Under the Surface (VUS) evaluates anomaly scores across thresholds and temporal tolerance widths. We derive an exact scalar event representation for a pinned dynamic VUS definition: thresholds without active support have analytically integrable contributions, while retained events preserve complete global score ties. With standard binary64 radix ranking and interval geometry, the evaluator takes $O(n+(L+1)Q)$ time, where $Q$ is maximum-buffer support. Reversible activation and incremental component unions further reduce this to $O(n+L+\alpha(K)\sum_w J_w)$, where $J_w$ counts the active prefix through recall saturation. For one original interval, spatial runs aggregate complete score classes; an integer stopping certificate gives a run-sensitive bound without restricting tie cardinality. A fixed-point range-sum implementation has a local mass-error bound, distinct from exact real-arithmetic evaluation. A frozen three-score-vector workload covers 308 series in 17 families and 924 series–width tasks per CPU platform. At primary width 30, sparse radix passes its five-control criterion; median ratios against released fast-VUS are $20.925\times$ and $14.538\times$, and against matched dense radix $2.599\times$ and $4.791\times$. A separate incremental study finds that saturation fails its default-width runtime criterion in all three runs, with qualified gains at larger widths. Exactness concerns the exhaustive mathematical target. Run aggregation helps structured large ties but does not broadly improve the measured real-score runtimes. Numerical parity and practical speed are separate claims. A directly timed 308-file evaluation, selection and output workflow takes 3.187 seconds at the median, versus 11.298 seconds for matched dense radix and 63.647 seconds for fast-VUS, with identical selected-model sets across all nine passes.

## Self-Assessment of Relevance: prepared text

**Data-management challenge.** This paper optimizes an exact time-series analytics operator over stored labels and anomaly-score arrays. Exhaustive VUS evaluation combines every distinct global score threshold with every integer temporal-tolerance width. The challenge is to remove threshold states and repeated width preparation that cannot change the returned scalar, while preserving dynamic denominators, merged interval components, and complete global ties. “Target and exact event representation” and “Prefix evaluation without full-support setup” define the operator and prove support-sensitive and prefix-sensitive bounds. The contribution is an exact evaluation algorithm rather than a new anomaly detector.

**Engagement with database research.** The target comes from the PVLDB VUS work and its optimized VLDB Journal treatment. “Prior algorithms and comparison scope” identifies the support restriction and static-work reuse already present in those algorithms, and compares their threshold/width work with fast-VUS, Benchopt, and the proposed event representation. The paper credits established ranking, union-find, reversible updates, ROC integration, and accumulator methods. Its metric-specific contribution is the complete scalar event reduction and its composition with width activation and tied-class run aggregation.

**Evaluation in a data-management context.** “Experimental design and evidence separation” and “Results” evaluate the cost of this operator across stored-score collections, using complete calls with validation and preparation, matched dense/ranking controls, pinned external implementations, and retained slower cases. The whole-evaluator experiment has 308 series and 924 three-score series–width tasks per platform; the later single-score and tied-class experiments have separate units and decisions. Absolute sums of separately timed task medians quantify operator cost, not a measured batch or detector-pipeline speedup. All three incremental width-30 primary decisions fail, and tied-run gains are limited by score-class fragmentation. The separate “Directly timed stored-score collection workflow” loads all 308 stored input files, evaluates 924 model score vectors, selects best-model sets, and serializes results. Its three whole-operation medians are 3.187 seconds for sparse radix, 11.298 seconds for matched dense radix, and 63.647 seconds for fast-VUS. All nine passes agree on selected sets. Filesystem/JIT state is warm, inference is excluded, and the three repeats support descriptive timing comparisons rather than confidence intervals.

This SAR is a scoped argument based on the current paper, not a certification that the editorial scope or significance criteria are satisfied. The three scope dimensions follow the current [PVLDB submission guidelines](https://vldb.org/2027/submission-guidelines.html).

## Contribution and evidence boundaries

| Contribution or result | Evidence and limitation |
|---|---|
| Exact scalar support events | Complete global ties and inactive ROC rectangles; comparison-based and fixed-binary64 bounds under the stated arithmetic model |
| Active-prefix refinement | Avoids full-support setup per width; bound depends on complete visited active ties and component coverage |
| One-interval complete-tie runs | Integer sufficient stopping condition; at most `3P0` active classes; charges all stored runs of every visited class; no universal linear bound for fragmented classes |
| Local arithmetic result | Three-limb exact accumulation of rounded roots and a local mass-error bound; no final-scalar correct-rounding certificate |
| Whole evaluator | Separate five-control primary PASS on both recorded CPU runs; 924 tasks per host, each evaluating three score vectors |
| Incremental saturation | Default-width primary FAIL in all three studies; qualified larger-width benefits and losses retained |
| Tie candidate | 20 constructed and 111 reused cases; structured gains, fragmentation regression, and width-300 losses on 16/21 and 14/16 reused cases |
| Numerical checking | Separate internal oracles, including 650 randomized dense checks and 36 Decimal-80 integral checks for the new candidate; neither external peer review nor all-input error certification |
| Collection workflow | Frozen criterion PASS: all selected sets agree; pairwise PR difference 1.333e-15; whole-operation median ratios 3.545x against dense radix and 19.973x against Klein, on the specified warm-filesystem Mac workflow |

The paper cites the [Sparse VUS 0.3.0 public precursor](https://github.com/mandu5/sparse-vus/releases/tag/v0.3.0), released 21 October 2026. Its software/working-manuscript chronology must remain distinct from refereed publication and from the new candidate's measurement dates.

## AI-assistance disclosure carried by the manuscript

OpenAI Codex assisted with literature retrieval, algorithm and proof development, implementation, experiment orchestration, testing and manuscript drafting. Separately prompted agent contexts constructed oracles and reviewed claims within the same workflow. These checks are internal verification, not independent laboratory replication or external peer review. The artifact records code and measured evidence; AI tools are not listed as authors.

## Declarations that require the author's actual facts

The author must supply truthful portal declarations about substantial intellectual contribution, meaningful drafting/revision, awareness of submission, and accountability for correctness and integrity. The author must also supply actual conflicts of interest, all relevant overlapping work and concurrent consideration, and any applicable submission-history or submission-cap facts requested by the venue. This document neither fills those declarations with assumed answers nor certifies personal eligibility. Automated assistance must remain disclosed and cannot supply human authorship. See the current [PVLDB publication policy](https://vldb.org/pvldb/general-information/publication-policies).

Before an actual upload, use the final reviewed PDF and record its SHA-256 and source revision; reconcile the portal title/abstract/author fields with that snapshot; verify the final content-page count and current template; and provide the artifact revision containing the claimed new files. A software version number or historical release URL alone does not show that the new unified manuscript and tie-run implementation are present in the submitted artifact. A real submission is established by the venue's submission receipt for that uploaded file, not by this prepared packet.

## Collection-workflow evidence

- Protocol: [`vus_collection_protocol_20261023.md`](vus_collection_protocol_20261023.md), frozen machine-readable digest `69ee646b505297e0feb124cb3206b0d600a6ad2a0a021c8fcea1c195dd4f56ea`.
- Complete result: [`report.json`](../artifacts/collection-workflow/mac-20261023/report.json); 308 series, 17 families, 15,161,812 label rows, all three original score vectors, 379,354,532 stored NPZ bytes.
- Per-method whole-operation seconds, in trial order: radix `[2.902273833, 3.186659042, 3.720735917]`; dense `[11.456034167, 10.944225833, 11.297516583]`; Klein `[59.041194209, 63.647341375, 63.749285917]`.
- All nine selected-model sets agree per series; maximum pairwise PR difference `1.3322676295501878e-15`.
- Whole clocks include file reads, all metric calls, selection and JSON serialization/write/close. No fsync, detector inference, network, imports or compilation is timed. Inputs were explicitly warmed and reopened each pass.
- Dense was last in every frozen randomized order; repetitions were not position-balanced. The active workstation had background activity. Every timing is retained, and no timing CI is inferred from three replications.
- The new public-record auditor independently reconstructs ordering, counts, phase/whole clock consistency, hashes, numeric differences and the decision. Raw source arrays are verified by the original run/report path but are outside the cache-free auditor's scope.
