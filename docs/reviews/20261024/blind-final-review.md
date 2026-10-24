Five of six evidence gates are directly supported in this review; the aggregate three-review requirement in gate 5 is unverified here because other internal reviews were deliberately excluded. Next: resolve the remaining algorithmic-attribution/significance objection with a compilation-matched support-cumsum control and a concrete repeated-profile consumer workload.

# Independent final-artifact review, 24 October 2026

**Recommendation: Revise. Internal surrogate score: 6/10. Confidence: 4/5.**

This is an independent, evidence-based mock review, not an editorial decision or an acceptance probability. The confidential PVLDB CMT numeric form was unavailable. The surrogate scale used here is: 1-2 fundamentally unsound; 3-4 substantial deficiencies; 5 borderline below the publication threshold; 6 a credible, useful paper requiring focused substantive revision; 7-8 a clear publication case; 9-10 exceptional. Confidence 4 means the central derivation, implementation and recorded experiment were examined closely, while exhaustive literature novelty and general application impact remain less certain. This surrogate score is distinct from the repository's prospective internal **5-point/6-point investment gates**.

Target: PVLDB Volume 20, Regular Research, Foundations and Algorithms. Intended author: Youngmin Ko, Independent Researcher. Intended cycle: abstract 25 November 2026 and paper 1 December 2026, 17:00 America/Los_Angeles. The official monthly deadline rule supports these dates. This review does not verify CMT registration or submission. [PVLDB submission guidelines](https://www.vldb.org/2027/submission-guidelines.html)

## Independence and reviewed object

I read the final 10-page PDF, its wrapper/body/bibliography, generated tables and operating-range figure; the specified primary, supplement, Linux, operating-range, resource and minimal-Klein artifacts; the operator, comparator and reconstruction sources; the reproduction instructions; and the prospective evidence design. The manuscript version includes the editorial clarification that 0.01 is a predeclared metric-scale regret cutoff, rather than a claim of application significance. All ten rendered PDF pages were inspected; the tables, equations and references were readable, with no material clipping found.

I did not read other internal review files, scores or agent-status listings. Public-review calibration was restricted to `public-calibration.md` and `verified-note-metadata.json`. I reviewed the complete exact-evaluator contribution as a first archival candidate, including its disclosed public unrefereed v0.3 precursor. I did not redefine the contribution as only the new batch loop, or as the separate certified-sampling manuscript. File digests below identify the working artifacts more precisely than the checkout's HEAD, `e1d504aba90dfd5bf7eaf1e6eb64e5765f859a3f`.

## Summary and strongest contribution

The paper replaces a full threshold sweep of the pinned original dynamic VUS operator with a support-event representation. Complete global ties still determine prediction counts. Inactive events contribute zero PR area but require an explicitly derived ROC predecessor rectangle. A two-nearest-interval identity replaces repeated ramp construction, and ordinary binary64 radix preparation yields an `O(n + (L+1)Q)` evaluator. Shared-label geometry and width-major execution reduce repeated preparation across score columns, at a memory cost.

The strongest surviving distinction is: **the complete dynamic VUS scalar can be evaluated over support events while retaining off-support global tie counts and the omitted ROC rectangles, with support-sensitive per-width work instead of full-series per-width arrays.** This is a useful specialization and implementation of familiar sweep/compression ideas; radix sorting, caching, loop interchange and full-recall PR stopping are not themselves new contributions.

The original VUS optimization already separates static and dynamic regions and reuses work. Its Algorithms 2/3 nevertheless retain a threshold loop and dynamic-region work for each width/threshold. Klein already uses support cumulative sums, while the inspected Benchopt kernel already uses cumulative sums and segment maxima. These are serious antecedents, and the manuscript now treats them as such. [Boniol et al., Section 4.3](https://arxiv.org/html/2502.13318v1#S4.SS3), [pinned Klein source](https://github.com/tomlouisklein/fast-VUS/blob/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py), [pinned Benchopt source](https://github.com/benchopt/benchmark_tsfm/blob/2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94/benchmark_utils/metrics.py)

## Evidence-backed strengths

1. **The central identity and its implementation are convincing.** The inactive-run argument keeps the dynamic denominator fixed only while its contributing masses remain fixed. The ROC formula accounts separately for the omitted horizontal part and the complete active tie transition. The two-distance argument follows from two active square-root ramps each being at least `1/sqrt(2)`. The mathematical model explicitly treats metric arithmetic as unit cost and the linear ordering result as fixed-binary64, not arbitrary-real sorting. The public-call memory bound includes validation/conversion temporaries.

2. **The whole-method improvement is large and comparison contracts are unusually explicit.** On the Mac, exact Klein/stream complete workflow median ratios are 23.026, 22.156 and 22.574 for NAB/SMAP/SMD. Fresh Linux ratios are 20.057, 20.283 and 16.172. The matched ROC+PR Benchopt comparison is kept separate from a PR-only consumer comparison. The compilation-matched dense control is important: independent dense/released call ratios of 2.368, 2.905 and 3.279 show that support compression contributes beyond the implementation language. These are improvements to an evaluator, not detector SOTA claims.

3. **A simple competing explanation is measured.** Replacing only Klein's global threshold list by distinct maximum-support scores improves Klein by 1.654, 2.274 and 2.968. The residual patched-Klein/released ratios are 12.052, 9.067 and 6.969. The paper correctly says that the residual includes NumPy-versus-compiled implementation effects. Reporting this control materially improves credibility; suppressing it would have overstated the originality of PR threshold restriction.

4. **The experiment is broader than a toy correctness exercise.** The primary study contains 73 complete real series, three public collections and eight unrounded CPU score procedures. The separate follow-up reaches 419,919-650,000 points on nine real recordings. MITDB's measured collection latency falls from 53.141 to 2.300 seconds. Synthetic density, length, component, width and model-count studies describe operating regimes rather than being counted as extra real datasets.

5. **Reconstruction and reproduction have distinct, credible evidence.** I reran the current primary, supplementary, operating-range and minimal-Klein auditors into new temporary files. Their parsed results were exactly equal to the supplied authoritative reports, including the primary/supplement v3 reports. I independently reconstructed the resource medians from all 72 raw resource records and verified the Linux completion receipt's report/audit bindings. A fresh Linux execution receipt supports the full primary/supplement pipeline; this review itself did not perform a new timing run.

6. **An independent direct numerical check found no correctness counterexample.** I wrote a separate dense implementation directly from the stated definition, without producer or metric helper imports. It checked 6,570 exhaustive small scalar instances, 160 random three-model batch instances across both sharing strategies, and 240 scalar comparisons against both public comparators. Cases included ties, both signed zeros, subnormal and extreme finite binary64 values, overlapping/adjacent intervals and widths exceeding length. Maximum candidate discrepancy was `2.22e-16`; maximum external-comparator discrepancy was `3.33e-16`. This is bounded numerical evidence, not an all-input rounding certificate or a research-significance score.

## Principal weaknesses and requested revision

**Largest weakness: the remaining algorithmic significance is borderline for Foundations and Algorithms after the elementary support-threshold restriction and standard implementation techniques are separated.** The paper now establishes a real speed improvement, but the 16-43x public-library ratios should not determine the novelty judgment. Klein already contains support cumsums; deleting inactive PR thresholds is a short expression change. The nontrivial surviving package is the complete dynamic ROC handling, interval-geometry preparation and support-only width work. Its generalizable conceptual value is narrower than the headline runtime improvement.

The compiled dense control establishes that scanning irrelevant states is costly, but it is not a compiled version of the closest support-cumsum competitor. The minimal-Klein control remains a vectorized NumPy implementation with full-length coverage/segment work. Therefore the evidence does not yet cleanly allocate the residual gain among support-threshold restriction, avoiding full-length per-width coverage, two-distance ramp preparation and compiler effects. This is an attribution/significance objection, not evidence that the reported runtime ratios or parity results are invalid. A compilation-matched support-cumsum control, using the same global counts and scalar contract but conventional width geometry, would provide a decisive comparison. It should retain any unfavorable outcome and separate PR from ROC output work.

**Application significance remains plausible rather than demonstrated in a demanding consumer.** The stored-score read/evaluate/select/write workflow is legitimate, and the long-recording result supplies an absolute saving beyond milliseconds. However, these are purpose-built sequential workloads over NPZ score files, not evidence that a benchmark service, profile-selection system or repeated analysis task is actually constrained by this operator. The primary stream medians total only 0.382 seconds over the three separate collection operations. The paper carefully excludes training, cold storage and `fsync`; those qualifications should remain. A concrete repeated-profile consumer trace, with the number of evaluations and baseline time attributable to VUS, would make the data-management value persuasive without requiring a full DBMS or a new detector.

**Generality is limited by the fixed input panel and target semantics.** Sixty-two primary recordings were previously measured by name; SMD has nine identical-label blocks and eighteen development-matching geometries. The dependence sensitivities preserve the direction of the result but do not establish physical-recording independence or performance on unseen domains. The eight procedures are evaluator input generators, including transductive LOF novelty scoring of fit points; they are not eight validated detector deployments. This does not invalidate an operator study, but it limits the force of downstream model-selection claims. The fixed `L=30` primary and `L=100` secondary settings plus synthetic width stress do not establish the distribution of buffer widths in deployed benchmark workloads.

**Reproduction is strong but incomplete for one diagnosed uncertainty.** The archived Linux output omits generated NPZ arrays. Its records, hashes and completed fresh-run receipt are useful, but they cannot independently identify why one SVM score changes sufficiently to move exact VUS-PR from about 0.3093 to 0.3329, or inspect that numerical discrepancy now. Retaining the relevant score/input arrays and numerical-library backend information would close this gap. The operating-range wrapper has not itself received a second complete fresh execution; its executed stages and independent record reconstruction are a narrower claim. Neither limitation cancels the primary speed result.

The three requested substantive additions are therefore: a matched support-cumsum attribution control; one concrete repeated-profile consumer workload; and an archived, inspectable second-host score discrepancy. More repetitions of the existing favorable small workload would not answer these objections.

## Negative results and limits that must remain visible

- Sharing is a modest increment on the primary Mac: released/stream geometric factors are 1.496, 1.271 and 1.207. Most SMAP/SMD sharing gain is already obtained by geometry reuse; stream/geometry gains are only 1.024 and 1.025, with losses on 3/17 SMAP and 2/36 SMD cases. At width 100, stream loses to saturation on four cases, with a worst baseline/stream ratio of 0.919.
- The development certificate-plus-fallback route took 33.93 times as long and certified no selection early. The earlier active-prefix method failed its default-width runtime criterion in all three runs. On the million-point random-score diagnostic it visits 99.94% of active positions. Those diagnostic counters describe the prefix implementation, not the stream kernel.
- Long-recording released/stream workflow intervals include one: MITDB `[0.925, 1.340]`, SWaT `[0.955, 1.165]`. Three workflow orders are not fully position-balanced. Stream loses to geometry on one MITDB case. The long-recording evidence supports the whole evaluator much more strongly than the sharing increment.
- At positive fraction 0.9, dense/released paired geometric speedup is 0.980, CI `[0.962, 0.9994]`; sparse compression ceases to help. At `M=1`, released/stream is only 1.023. Changing `K` also changes support, so the component study does not isolate component overhead.
- Streaming consumes more memory: in the `n=500,000`, `M=8`, positive-fraction-0.5 stress case it peaks at 225.0 MiB, versus 175.2 MiB released and 210.6 MiB dense. Lifetime process RSS includes interpreter, libraries, input and warm-up, and is not exact auxiliary space. The repeated `M=32` real stress input does not add independent models or recordings.
- Approximation does not always change the selected model. NAB has no winner-set changes at either budget. On Mac, 250 thresholds change 14/73 sets with four regrets at least 0.01; 1,000 thresholds change three sets with none at that cutoff. On Linux, the 250-threshold counts are 13 and three. The 0.01 cutoff is a metric-scale choice, not demonstrated application loss; VUS itself is not established as the correct utility for every application.
- Warm serial CPU evaluation excludes fitting and cold JIT. The Linux runner has uncontrolled shared-host load, including the retained NAB outlier. Paired-case intervals concern this panel; workflow intervals concern timing trials on fixed inputs. Three-collection correction does not jointly cover every method, width or follow-up. Follow-ups were frozen after primary outcomes, before their own measurements.
- Unrounded inputs retain genuine ties, including one KMeans fit with five distinct clusters instead of the requested sixteen; the warning was retained. The operating-range controlled diagnostic ROC is only finite-checked because no corresponding reference was recorded, whereas real diagnostic ROC and the primary matched-output ROC comparisons have reference checks.
- The claims concern the pinned square-root/sum-and-clip dynamic VUS contract. The paper does not establish a speed ranking over GPU FF-VUS or over differing native metric semantics. Sylligardos's earlier preliminary CPU/GPU acceleration is relevant prior art, so a generic claim to be the first fast VUS would be unjustified. [Sylligardos, Section 4](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/PhD/PhD25_17.pdf)
- Mathematical exactness is an algebraic statement under the stated arithmetic model. Finite-precision parity is empirical; no all-input real-arithmetic rounding certificate was established. The public release is acknowledged and does not itself demonstrate novelty or external acceptance.

## Novelty screening and six evidence gates

The manuscript discusses thirteen relevant 2024-2026 papers without counting software releases as papers. The closest algorithmic comparisons are much fewer; the remaining papers concern metrics, benchmark infrastructure and model selection. They are relevant context, not thirteen independent competing exact evaluators. The following twelve comparisons make the distinction checkable; the additional mTSBench claim is in the manuscript, but direct OpenReview retrieval in this review reached browser verification, so I do not independently corroborate its current publication metadata here.

| Related primary work | Existing contribution and distinction of this manuscript |
| --- | --- |
| [Boniol et al. 2025](https://arxiv.org/html/2502.13318v1) | Original VUS and static/dynamic optimization; this manuscript reduces exhaustive scalar threshold events while preserving the pinned operator. |
| [Sylligardos 2025](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/PhD/PhD25_17.pdf) | Preliminary redesigned CPU/GPU evaluation; this manuscript supplies a specific exact-event derivation and qualified CPU comparison, not the first acceleration claim. |
| [PATE 2024](https://arxiv.org/abs/2405.12096) | Proximity-weighted PR metric; this manuscript preserves another metric instead of introducing temporal weighting. |
| [TSB-AD 2024](https://github.com/TheDatumOrg/TSB-AD) | Dataset/metric/detector benchmark; this manuscript accelerates one labeled-profile operator rather than improving detector accuracy. |
| [TAB 2025](https://arxiv.org/abs/2506.18046) | Unified data, methods and evaluation pipeline; this operator could be a component, not a replacement benchmark. |
| [TSB-AutoAD 2025](https://www.vldb.org/pvldb/vol18/p4364-liu.pdf) | Automated selection, ensembling and generation study; this manuscript computes fixed labeled scores more cheaply and makes no superior unsupervised-selection claim. |
| [When Foundation Models are One-Liners, 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/cf70320e93c08b39b1b29a348097a376-Abstract-Conference.html) | Analysis of detector pipelines and simple baselines; this manuscript changes evaluator cost at fixed detector scores. |
| [Formally Exploring Metrics, 2025](https://arxiv.org/abs/2510.17562) | Metric axioms and new LARM/ALARM definitions; the proposed claim is an implementation identity, not better metric axioms. |
| [CCE 2025](https://arxiv.org/abs/2509.01098) | A different confidence/consistency metric; its runtime is not a same-output VUS baseline. |
| [Problem-Oriented Taxonomy, 2026 revision](https://arxiv.org/abs/2511.18739) | Maps metric assumptions to application goals; exact computation here does not establish universal utility. |
| [Did We Actually Fix It?, 2026](https://arxiv.org/abs/2607.11969) | Adversarial evaluation-choice stress testing; this paper holds the scores and operator fixed while comparing approximation and exact computation. |
| [Retrieval Over Training, 2026](https://arxiv.org/abs/2610.20243) | Similarity-based model selection from historical profiles; this paper concerns labeled profile computation rather than a new retrieval selector. |

This is a bounded novelty screen. The detailed source/proof comparison was strongest for Boniol, Klein and Benchopt; the broader paper comparison was checked at manuscript/primary-source scope level, not through an exhaustive reconstruction of all twelve papers.

| User evidence gate | Assessment | Reason |
| --- | --- | --- |
| 1. At least ten recent related papers and one surviving distinction | **Pass, scoped** | The comparison above exceeds ten without software padding; the complete support-event/dynamic-integral distinction survives the inspected nearest sources. Its significance remains the main referee objection. |
| 2. Strongest eligible public baseline, three collections, uncertainty and ablation | **Pass for the CPU contract** | Unchanged exact Klein wins are supported on NAB/SMAP/SMD, with lower confidence bounds above one; Benchopt has an equal-two-output comparison. Dense, geometry and minimal-Klein controls are meaningful. This is not a universal hardware SOTA claim. |
| 3. Real-data generality and explicit failures | **Pass within stated scope** | Complete real recordings, eight full-precision procedures, long-series follow-up and adverse regimes are present. Dependence/reuse prevent an unseen-domain claim. |
| 4. One-command reconstruction/reproduction of the principal table | **Pass for primary/supplement numerical tables** | The driver builds a fresh workspace, verifies fixed design, regenerates scores, executes serial measurements and reconstructs JSON tables. Completed Linux evidence and reviewer reruns of record audits support it. TeX rendering and later studies are separate, as disclosed. |
| 5. Three independent venue-form calibrated reviews | **Aggregate unverified here** | This is one independent calibrated review. I intentionally did not inspect the other review outputs, so their number, independence and conclusions must be checked by the coordinator without treating this as an affirmative three-review certificate. |
| 6. Venue, category, scope, contribution and deadline | **Pass as a target declaration** | PVLDB Vol. 20 Regular Research / Foundations and Algorithms, the full exact evaluator, and the November/December cycle are explicit. The scope case is plausible but substantive application significance remains reviewable. |

The public call identifies conceptual/formal algorithmic contributions as the basis for Foundations and Algorithms papers and encourages implementation evidence. The scope policy asks for a real data-management contribution and evaluation, not merely familiar venue citations. Optimizing a repeated stored-profile aggregate engages efficiency and data access, while the direct continuation of VUS is more than a syntactic database citation. A DBMS implementation is not a stated prerequisite. [PVLDB research criteria](https://www.vldb.org/2027/call-for-research-track.html), [PVLDB scope policy](https://www.vldb.org/2027/submission-guidelines.html)

The unrefereed software/manuscript precursor is disclosed. The public originality rule defines prior publication in terms of refereed conference/workshop proceedings or journals; I therefore do not reject the whole-method contribution merely because v0.3 was publicly released. This does not relax the requirement to distinguish existing public algorithms. [PVLDB originality policy](https://www.vldb.org/2027/submission-guidelines.html)

## Prospective internal investment gates, assessed separately

**5-point gate: substantive and numeric components supported; final aggregate status conditional on gate 5's independent-review count.** There is an identifiable surviving contribution, real full-precision evidence on three collections, same-contract lower confidence bounds above one, and a median external whole-workflow speedup far above 1.5. I found no unresolved mathematical or measurement-invalidity defect in the inspected evidence. The collection-median external ratios on Mac have median 22.574; Linux has median 20.057. A significance objection is expressly compatible with this investment gate. I do not certify the uninspected three-review aggregate.

**6-point gate: not established.** The two-CPU and external workflow speed conditions are supported. The new sharing increment on the prospectively primary Mac panel is 1.496/1.271/1.207, with SMD's adjusted interval `[1.193, 1.221]`. Thus an at-least-1.25 effect is not supported on every primary collection; geometry-block sensitivity is 1.217, also below 1.25. Linux's 1.886/1.580/1.340 does not erase the primary SMD result. The gate wording attaches the per-collection condition explicitly to the lower confidence bound; even if the 1.25 point threshold were interpreted as pooled, the gate would still not be established here: this review retains a substantive attribution/significance objection, no comparably substantive new generalization beyond the released whole evaluator is demonstrated, and three independent reviews free of major objections were not verified. I did not change the thresholds or substitute a favorable host/width after the fact.

The surrogate **6/10 review score does not mean the prospective 6-point investment gate passed**. The former assesses the whole first-archival paper; the latter imposes a specific incremental-performance and multi-review hurdle.

## Calibration against public accepted and rejected reviews

Calibration used only the two permitted local public-calibration files. The notes are mirrored OpenReview records; current origin bytes were not verified against the mirror. They are adjacent ICLR evidence, not a PVLDB acceptance predictor or a way to translate average numeric ratings into decisions.

- **Accepted: When Foundation Models are One-Liners**, forum `H27kvyG4qf`, decision `XfBOGU95OS`, recorded ratings 4/6/6/4. Its official ICLR publication was independently verified. The analogy favors scoped claims, strong simple baselines and paired statistics. Those issues are mostly addressed here by the exact target, minimal-Klein control and explicit detector/generality limits. It does not establish that this algorithmic contribution has equal significance.
- **Accepted: Unsupervised Model Selection**, forum `gOZ_pKANaPW`, decision `HRD5hna4dy`, ratings 8/6/3/5. The calibration describes acceptance of a useful specialized combination of known ideas. Consequently I do not demand a new generic sorting or data-structure primitive. The remaining question is whether this particular combination removes enough work in an important consumer task, which is why the score is 6 rather than a rejection based solely on elementary ingredients.
- **Rejected: Subsequence Anomaly Detection via GNNs**, forum `73U_NlKaNx`, decision `GMS-BMZmsG`, ratings 5/3/6/5. The relevant objections were weak novelty, missing strong baselines and attribution to the wrong component. Including Benchopt, geometry-only sharing and minimal Klein resolves much of the omission problem. The residual compilation-matched support-cumsum attribution remains a meaningful parallel.
- **Rejected: Hypothesis Testing for Dynamical Systems**, forum `G-dM79m_EXd`, decision `GYaqYZtEQU`, ratings 6/1/5. The relevant warning is unclear contribution and a weak theory/system link. Here the support bound predicts sparse-support wins and dense-support failure, and the records substantiate both. That objection is substantially reduced, but a demanding consumer workload would better establish why this operator-level gain matters.

These comparisons support a **Revise** recommendation for a credible whole-method paper with a narrow surviving contribution. They do not justify increasing a score because an acceptance is desired, or equating an audit pass with publication merit.

## Reviewer verification receipts

The following reviewer operations ran with `/opt/anaconda3/bin/python`, into `/tmp/pvldb-blind-final-oct24/`, without new timing experiments or changes to frozen sources:

```text
audit_pvldb20261024.py: PASS; parsed result exactly equals authoritative primary v3.
audit_pvldb_supplement.py: PASS; parsed result exactly equals authoritative supplement v3.
audit_pvldb_operating_range.py: PASS; parsed result exactly equals supplied operating-range report.
audit_pvldb_klein_control.py: PASS; parsed result exactly equals supplied minimal-Klein report.
Resource raw-record median reconstruction: PASS, all 72 records.
Linux completion/report/audit hash bindings and independent ratio point estimates: PASS.
Separate direct-definition operator check: PASS, maximum candidate discrepancy 2.22e-16.
```

The temporary direct-definition check and its result are not represented as part of the original frozen experiment. Their hashes and the reviewed artifact identities follow. Recorded checks establish their stated correctness/reconstruction scope only.

## Exact reviewed SHA-256 identities

```text
0aa0c57d19dd5e18edbd96671e4d2e8540391cc7103f9711abc8347c2f522009  paper/sparse_vus_pvldb20261024.tex
b6f1ae4b6523cdf4b38eaadad53d99f0d1f83a61233615c2e42bdd6cf9ea6840  paper/sparse_vus_pvldb20261024_body.tex
cce29ae7349b2ab2dabff2c177d52b4aded0e2760304eb4ff563159cc41f206b  paper/sparse_vus_pvldb20261024_references.bib
ad65d590ce52322a7dd641c5cb8767adf3244b81b7b4469ce1f9b2cfa2ce5670  paper/sparse_vus_pvldb20261024.pdf
c8fbfab4fd4e21527cc748b233fc8f7f6bd7ccba1fd2405cb58ecf76546c4aec  paper/pvldb20261024_tables.tex
daea6973dad2c3a316a9cfb304ec733350974a03dec978f35d8ce55ea698d508  paper/figures/pvldb_operating_range.pdf
200e97634b519b6d60d2e74a1623e7e7eae63f0345d703aa86a98f3753bfc4de  docs/REPRODUCE_PVLDB_20261024.md
b25223764a5291a1144e060493d4a2217802a2a3b0469394644b35d05756289f  docs/superpowers/specs/2026-10-24-pvldb-evidence-design.md
20ac021012eaffa354a45c312f6172e4e394a5e2f8bb5d756a5ce07fed9245f2  docs/reviews/20261024/public-calibration.md
6747875eec0a7baff778094643550be3542aca6c899643788ec562c7f55852ba  artifacts/pvldb-research-20261024/public-review-calibration/verified-note-metadata.json
307e0498f441901dbe0d686064ffd8f9ff4c683e5e5f1197a2297921561a3579  artifacts/pvldb-research-20261024/full-precision/protocol.json
2b9d5dbd101d0784cec0ec2afc60ca8e20fc959a3f7457423b08209d4f0daab0  artifacts/pvldb-research-20261024/full-precision/records.jsonl
ed98f9c61208cf9036725d9c3b886473c509b28edf703cbda770afff13c13cc2  artifacts/pvldb-research-20261024/full-precision/workflows.jsonl
b657a2e185d1a0731150f579e108f1e3ecef81fe0f8e37bb831d04cb098201a9  artifacts/pvldb-research-20261024/supplement/protocol.json
d8840743f7d988b16f7d2130d3955d2b443bbb7d50e303d87e9d510c5992dd52  artifacts/pvldb-research-20261024/supplement/records.jsonl
a9585f8a70fe1707c45e519126167c0ce2769bcea0b9f4fdbd94c3a19f0e112a  artifacts/pvldb-research-20261024/supplement/workflows.jsonl
ccae7854df988dca14db843dc8dbf6f640c2c578789a8c88ca7a7f8ecc66892e  artifacts/pvldb-research-20261024/operating-range/protocol.json
a48db17c6fae7700643f40dd863d64a8793cd59da8d101b468854f50427bc180  artifacts/pvldb-research-20261024/operating-range/records.jsonl
0c2e4a637262d48268031a272a2e0855aa8820ca64ec0e9bdcca59952d8a3d22  artifacts/pvldb-research-20261024/operating-range/workflows.jsonl
0ef105ee4d2f6a80554e503ef4540e3a9b75379a6c9e61f539f5bd0c29d19ca9  artifacts/pvldb-research-20261024/klein-support-control/protocol.json
cfbf9567c4b5e34e3f7fb3ee66cc3f8b5e13638c0c9a759385983f6ac3e04dd6  artifacts/pvldb-research-20261024/klein-support-control/records.jsonl
501f21d62a6ee21f5e9415b32ed703455f116b40327670382ccc8531d5e0fd26  artifacts/pvldb-research-20261024/klein-support-control/workflows.jsonl
b5c51a22aa154e196fb219032c0c2c1391b6b096ae70fe211cccae329b8bebd1  artifacts/pvldb-research-20261024/resources/protocol.json
ea9d31c03928428f3a04f779ae532d6ebe9319d92a92e306bed6232b71bb3809  artifacts/pvldb-research-20261024/resources/records.jsonl
b6ed65bbc88f69fe6edd3e0ca2ed578881888368301899bbdff83479cf06bdcf  artifacts/pvldb-research-20261024/full-precision/independent-audit-v3.json
99396de3367f579cc55380c85c75526a7297b0157ff399e968d1779d49b2b7c2  artifacts/pvldb-research-20261024/supplement/independent-report-v3.json
aba680948a39173d157a472d2f20b53e9a42d6c859424398a83c3f03500b5314  artifacts/pvldb-research-20261024/operating-range/independent-report.json
301badd78f5df9b250655a7b1be959631d7f0123ea65ebb528f70e1b516c87be  artifacts/pvldb-research-20261024/klein-support-control/independent-report.json
e26a4238c3f2e8ba30f5b67db921201b6b445f3eadfec2523e22f51b52d73355  artifacts/pvldb-research-20261024/resources/report.json
cf5c8681954499f317e35efd4bca7b84442318a6b324732a0bac0d4e20e1899e  artifacts/pvldb-research-20261024/linux-reproduction/reproduction-complete.json
944fd9a55303ff49ccc155182f38661682804f0dd239ebcf53a0100e04410506  artifacts/pvldb-research-20261024/linux-reproduction/verification-summary.json
f7e227f3bfea58c72da8feba0c7daa36460695db8ab10106706f845d45374e2b  src/sparse_vus/core.py
d8d45d3cc15105f1771aa37cf3cac95b6138a2f1ee38ee464fc940c54a55a3f5  src/sparse_vus/radix.py
3b73ea67e23d92c00018d9a31646bac3bc03b781caca3dfa5ef9155fa47c2f32  src/sparse_vus/compiled.py
60afd9a2bc584bf670500d772552625064cdec01bb00ae76246006c163b70646  src/sparse_vus/pr_compiled.py
43bd8648a769b94e38d4310e0c7300d067764802132dbee9b55d737e11ddee14  src/sparse_vus/batch.py
61af156345f4fcc89702a24f5ec56b6f2c722295f4b6242ec7ec944fa4d50513  src/sparse_vus/dense_radix.py
4cf06015fd728405f85e6262ce5d43053d9061a4008cff2ced833185caf3a005  experiments/audit_pvldb20261024.py
0b8c45bde23da1ca774b5afcf2dacc6596d608575bb0c20d14acadccdcdda903  experiments/audit_pvldb_supplement.py
0c70f7307f95b09046d2236492208f7ca11aa0843c574c12b618296cfef6683d  experiments/audit_pvldb_operating_range.py
9ea6ae36568d54b0bdc9d830e138c94a5aea936003602a59a25a4e458a46cdf0  experiments/audit_pvldb_klein_control.py
c431080f976b6937bcba83c0ce06905745831c79936acef44f29315ae05af037  experiments/reproduce_pvldb20261024.py
313bbac796a0738d41e6a04e5c30295016aaa916cd53f56fa7a6737d989aafe3  experiments/klein_support_control.py
15b7afb94da0e1f1b1c408fe44b937d910935c19f8eb76f42ae6719f9cfcb52b  .cache/fast_vus/fast_vus.py
298c746c84a28f9296b015bd70eac984d27be5452e3ca42c853de05328c194a8  .cache/benchopt_vus/metrics.py
23c6e6e4ce235a12df2d9bc5e93753f970a151b59adb3acaaf09dafd81036e2f  /tmp/pvldb-blind-final-oct24/independent_operator_check.py
ed80531a843d58fe2e7c7a631520bb54cb8d9732781d7cba838ca4ee838e3a36  /tmp/pvldb-blind-final-oct24/independent-operator-result.json
```
