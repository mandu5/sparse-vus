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

---

# Addendum: independent reassessment after the three requested additions

Date: 24 October 2026. Five evidence gates remain directly supported; the aggregate count/independence requirement in gate 5 remains deliberately unverified by this reviewer. Next: retain the exact-operator result and adverse controls as a bounded research artifact; further investment in this PVLDB Foundations and Algorithms claim requires a new, discriminating scientific question rather than another timing round on the same panel.

**Updated recommendation: Reject for the current PVLDB Regular Research / Foundations and Algorithms submission. Internal surrogate score: 5/10. Confidence: 4/5.** The earlier **Revise, 6/10** assessment above is preserved verbatim. The same surrogate definitions and public venue criteria apply; this is not a confidential CMT score or an external decision. This change follows substantive new evidence, rather than a change in the requested experimental requirements.

The requested additions are complete. Their missing-evidence objections are closed. The new evidence makes the implementation and its limitations more credible, while reducing my assessment of the remaining algorithmic contribution and demonstrated application significance. A technically sound, useful evaluator can satisfy the prospective internal 5-point gate while falling below this reviewer's publication threshold for the chosen category.

## What was newly reviewed and verified

The reviewed manuscript is now 11 pages: PDF SHA-256 `fb81365502f290ae06ae7662019cc9a232a00dc00fd3d50140d95b3b87601633`, body SHA-256 `91e638315c79c0094bffe1c4fecbfc9436f01f4e4dbc76a762c44a7cc0fc8dc3`. I read the permitted common `post-review-additions.md`, the new manuscript passages/table, the three new evidence directories, reproduction instructions, and the relevant producer/control/auditor sources. I inspected the rendered new results and closing pages. No other internal reviews, scores or agent listings were consulted.

I reran `audit_pvldb_compiled_control.py` and `audit_pvldb_consumer.py` into new temporary outputs, using the documented statsmodels overlay for the consumer. Both passed and their parsed JSON exactly matched the supplied independent reports. I reran `analyze_pvldb_score_probe.py`; its parsed output exactly matched the archived comparison. This replay evaluates saved arrays but does not regenerate detector fits or rerun timing. I separately checked dtype, shape and raw bytes for the six input/standardization arrays, confirming actual byte equality rather than relying only on numerical equality. A further 120 small tied/untied direct-definition cases checked the new compiled control at widths 0, 1, 2, 3, 30 and 100; maximum discrepancy was `2.22e-16`.

No new timing experiment was performed in this review. All earlier numerical, dependence, memory, approximation, frozen-protocol and host-scope qualifications remain applicable.

## 1. The matched control resolves attribution uncertainty with an unfavorable result

The new control is a legitimate optimized author-created comparator. Source inspection confirms common validation, radix ranking, complete global tie counts and support enumeration, followed by direct width-specific summed/clipped ramps and component scans. Original-positive grouped mass is hoisted across widths, and scratch is support-local. It does not use the two-nearest-distance construction. The implementation and manuscript correctly identify it as a reimplementation, not unchanged upstream Klein or a literal compilation of that code.

The six balanced orders, all 73 cases, eight unchanged profiles per case and six workflow passes per collection are adequate for the stated fixed-panel comparison. Maximum recorded PR difference is `4.44e-16`. The important numbers are:

| Collection | Control / released, case geometric ratio with adjusted 95% CI | Control / stream, case geometric ratio with adjusted 95% CI | Control / stream, workflow median ratio |
| --- | --- | --- | ---: |
| NAB | 0.910 [0.905, 0.915] | 1.357 [1.291, 1.427] | 1.177 |
| SMAP | 0.960 [0.945, 0.973] | 1.201 [1.180, 1.224] | 1.126 |
| SMD | 0.978 [0.969, 0.985] | 1.166 [1.158, 1.174] | 1.152 |

The conventional control is faster than released scalar evaluation in every case; the adjusted intervals all remain below one. The smaller stream gain is also real on this panel. This contradicts a separate empirical superiority claim for nearest-distance scalar geometry at the primary width. The large unchanged-public-API ratios remain correct but are poor measures of the distinctive contribution relative to an optimized conventional implementation.

Two boundaries matter. First, the control itself reuses the candidate's support-event/global-tie machinery, and it implements only PR. It is therefore not evidence that an independent prior public algorithm already contains the entire ROC identity, or that the support-event theorem is false. Second, the control also hoists mass and changes scratch handling; this is not an isolated intervention proving that nearest-distance arithmetic is intrinsically slower. Direct ramp construction can have different costs at larger widths or more overlapping components. The supported conclusion is narrower: the primary data no longer provide a compelling independent runtime justification for this geometric construction over a well-optimized conventional support approach.

This outcome weakens the strongest performance-based argument for algorithmic significance. What survives is the exact dynamic scalar representation, correct ROC predecessor bookkeeping, a support-sensitive bound, and modest work-sharing gains. These remain useful. In my assessment the conceptual advance over support cumsums, ordinary rank-event compression and standard reuse is too limited to carry the present Foundations and Algorithms paper by itself.

## 2. The public consumer establishes a small benefit and an explicit bottleneck

The source-level consumer is appropriate: pinned TSB-AD `get_metrics`, all nine outputs, an unchanged public width estimator, and an injection only at the scalar ROC+PR callback. Both timed backends are exact and return both VUS outputs. This is not a comparison to TSB-AD's original sampled default or a claim to replay its detector-training script. The largest primary recording was selected by length, with a fixed tie break, before consumer outcomes; it has 28,696 points and the public estimator chooses width 125.

The full trace contains four ABBA passes, eight profiles per pass and all 32 nine-metric calls. The independent audit validates the selected case, width, order, input/source binding, complete metric keys, nested timings and output agreement (`3.44e-15`). The initial statsmodels 0.14.2/pandas import failure precedes measurement and is retained; the separate 0.14.6 overlay is documented. I found no measurement-invalidity defect in this experiment.

The outcome is adverse to broad application-impact claims:

- Median VUS time: `0.928865 s -> 0.014060 s`, ratio **66.067**.
- Median complete consumer time: `34.260309 s -> 33.233999 s`, ratio **1.030881**.
- VUS is only **2.70-2.72%** of baseline time.

At the baseline median, setting VUS cost to zero while holding other work fixed yields an Amdahl ceiling of about **1.027868**. Substituting the measured faster VUS cost gives **1.027434**. The slightly larger observed whole-workflow ratio includes approximately **0.1115 seconds** less non-VUS/other work; with two observations per backend, that difference should not be assigned causally to the evaluator. The manuscript's descriptive interpretation is appropriate.

This is one fixed consumer, not proof that VUS is unimportant in every application. VUS-only profile selection and the previously reported long-recording workloads still have valid absolute savings. Nevertheless, the concrete public consumer requested in the initial review supplies no strong positive application-impact evidence: most of its runtime lies elsewhere. Seeking a different workload solely because this one is unfavorable would not improve the scientific case. A new workload would need an independent, documented usage reason.

## 3. The two-host diagnosis resolves the evaluator-versus-score ambiguity

The archived arrays make the previously opaque discrepancy inspectable. Observations, labels, standardized matrices, fit indices, feature means and feature standard deviations have identical dtype, shape and bytes. SVM fitted states differ: 104 versus 105 support vectors, both fit status 0 and 133 iterations; maximum SVM score difference is about `0.000119587`.

Both score sets, evaluated on the same reviewer host, reproduce SVM VUS-PR values **0.3092648648** and **0.3329318469**, and agree with unchanged exact Klein to at most `5.56e-17`. The difference is localized after standardization to model fitting/score generation, rather than a disagreement between these VUS implementations on identical input arrays. The receipts preserve differing loaded backend configurations, but there is no causal intervention establishing which library, compiler or instruction caused the fitted-state difference.

The Mac complete score bytes match the original experiment. The new Linux complete eight-model score bytes do not match its earlier runner, and other original-versus-repeat metric differences reach `0.000582135`. The new diagnostic reproduces the SVM metric discrepancy and the 250-threshold winner switch but is not recovery of the missing original Linux arrays. Non-SVM scores also differ between hosts. This qualification is correctly preserved. I consider the requested diagnostic issue resolved to a scientifically useful, bounded extent; recovering the unavailable original arrays is not an outstanding revision request.

## Why the recommendation changes

The previous Revise recommendation asked for three specific additions to discriminate between a substantial method and a primarily implementation-driven improvement. They have now been supplied, including the negative outcomes. The new control shows that the conventional compiled scalar method is already faster on the complete primary panel, and the actual public consumer shows a small total benefit despite a very large VUS-kernel speedup. The host analysis closes a reproducibility concern without adding algorithmic novelty.

The resulting paper is more reliable and more useful as an exact-operator reference, but the evidence does not establish enough remaining algorithmic novelty or practical significance for my acceptance recommendation at PVLDB Foundations and Algorithms. This is a substantive threshold judgment, not a correctness rejection, a complaint about the number of tests, or a penalty for reporting negative results. The disclosed public unrefereed precursor remains eligible to be part of the first archival contribution; the whole-method rather than batch-only framing was used throughout.

The same public calibration supports this distinction. The accepted specialized-combination example prevents an automatic rejection merely for using known components, but usefulness and contribution must still be demonstrated in the particular paper. The rejected component-attribution examples are relevant because the new measurements substantially narrow which mechanism is responsible for speed. The rejected theory/system example does not imply the theorem here is wrong: its algebra and sparse-support trend remain supported. Negative findings can themselves be valuable research, but a single Amdahl-limited consumer plus this fixed-panel attribution result is not yet a broad EA&B contribution either. I do not infer that changing the category name would produce acceptance.

The abstract remains numerically accurate about public API speedups. A future version should also foreground the compiled-control and consumer boundaries, because they now materially affect interpretation of those headline ratios. Editorial clarification alone would not change this recommendation.

## Updated six-gate assessment

| Gate | Reassessment | Consequence of the additions |
| --- | --- | --- |
| 1. Recent primary literature and a surviving distinction | **Pass for the scoped evidence requirement; significance objection remains** | The earlier twelve-plus-paper comparison and exact dynamic ROC distinction still stand. The new control shares candidate event machinery, so it is not a proof of independent prior anticipation. The size/depth of the surviving advance is now less persuasive. |
| 2. Strong same-contract baselines, three collections and ablations | **Pass for the declared CPU operator comparison** | Unchanged public comparisons remain valid. The stronger author-created internal control is included with all unfavorable scalar results, and stream still improves all three collection workflows modestly. Its smaller ratios must accompany the much larger public-library ratios. |
| 3. Real-data scope and failures | **Pass within the limited claim** | Existing real inputs and failure cases remain; the public consumer adds a measured application limitation rather than proving broad end-to-end benefit. No new population-independence claim is justified. |
| 4. Reproduction/reconstruction | **Pass for the stated primary/supplement numerical scope** | New independent audit replays agree exactly; the host diagnostic is now inspectable. Follow-ups retain separate commands, and original missing Linux arrays remain missing. This is not one command reproducing every later figure/experiment. |
| 5. At least three independent calibrated reviews | **Aggregate unverified by this reviewer** | This addendum is a reassessment by the same reviewer, not an additional independent review. Other reviews remain unread. The coordinator must verify their count and independence. |
| 6. Venue, category, scope and deadline | **Pass as a target declaration** | PVLDB Vol. 20 Regular Research / Foundations and Algorithms and the 25 November/1 December cycle remain explicit. Naming the venue and having an in-scope operator do not settle the contribution threshold. |

Thus five gates are directly supported here, with gate 5's aggregate intentionally unverified. Passing these operational evidence requirements is not identical to a positive referee recommendation.

## Prospective project 5-point versus 6-point gates

**5-point candidate: substantive/numeric conditions still supported, conditional on the coordinator's three-independent-review check.** The frozen gate compares whole-workflow speed to the strongest eligible *external* same-contract baseline and separately requires internal controls. Those external ratios still far exceed 1.5 with lower paired bounds above one on all three collections. An identifiable exact-operator result survives; no unresolved mathematical or measurement-invalidity defect was found. Replacing that prospective external-baseline rule after seeing the new internal control would change the gate, so I do not do so. The new internal ratios nevertheless matter greatly to scientific significance.

**6-point candidate: not established.** The original primary SMD sharing increment remains 1.207, with its adjusted upper confidence bound 1.221. The new control study also gives only 1.193 released/stream on SMD; neither result supports a uniform 1.25 primary-collection increment. Against the new internal control, SMAP/SMD case gains are 1.201/1.166 and workflow gains are 1.126/1.152. These new comparisons are supporting context, not substituted prospective thresholds. The same earlier wording qualification about pooled versus per-collection interpretation remains, and the gate fails to be established even under a pooled reading because a major substantive-novelty objection persists and a qualifying new generalization has not been demonstrated. The fresh host diagnostic and public consumer are valuable validation, not such a generalization. Two CPU environments and the external-workflow condition remain satisfied.

## Is further scientific work justified?

The current three requested investigations are complete; repeating them more often is not the next useful step. The evidence justifies retaining and sharing a careful exact VUS implementation, its derivation, strong public-API gains, and its negative controls. It does not justify open-ended additional optimization or reviewer rounds solely to obtain a higher score for this same claim.

A **bounded new investigation** could be scientifically worthwhile if it is explicitly a different, falsifiable question: for example, whether the two-distance construction has a predictable advantage over direct ramps in high-overlap/high-width real workloads, using the current conventional control and a workload rule fixed independently of outcomes; or whether a documented real consumer is actually dominated by repeated exact VUS queries. Such a study should start from the mechanism or usage evidence and retain failures. It is not required to complete the current review, and synthetic favorable cases alone would not establish application importance.

My present investment recommendation is to close this evidence cycle at the supported 5-point level, preserve the full artifact and consider a narrower software/technical contribution. Reopen the PVLDB main-track investment only when a distinct mechanism or independently motivated bottleneck can be stated before further measurement. Neither broad rejection of the research topic nor a promise that another venue would accept follows from this assessment.

## Addendum verification and exact identities

The original review prefix before this addendum has SHA-256 `2253faa873bdad3297722c2e6c635a925584275cd671c8ef753d95e55def174d` and was preserved byte-for-byte. New reviewer audit outputs are in `/tmp/pvldb-blind-final-oct24/`; their parsed contents exactly match the supplied three reports. The following full digests identify the revised manuscript and new evidence actually assessed.

```text
fb81365502f290ae06ae7662019cc9a232a00dc00fd3d50140d95b3b87601633  paper/sparse_vus_pvldb20261024.pdf
91e638315c79c0094bffe1c4fecbfc9436f01f4e4dbc76a762c44a7cc0fc8dc3  paper/sparse_vus_pvldb20261024_body.tex
207009804ae15ae6e3efd3cac83bab79f215528b239a3146e919d15c1532cce3  paper/sparse_vus_pvldb20261024.tex
6e41e18f56568848453e91d53599799a2f93ebd73f2fb0ea14b8427585d24b84  paper/pvldb20261024_tables.tex
6e0c54f33a7ab0b2c74c040ce463bbdf863526bdbdf2f3cadc192340a9d4850d  docs/REPRODUCE_PVLDB_20261024.md
518b837cd6f3855d334b4d0a13abb82010fa1a767dabdd84ccdd25d453718f5c  docs/reviews/20261024/post-review-additions.md
c2a985dd93c97aed7899e75d8ae3657ee806f5c29bcaa54b72c519efb928ea7d  experiments/support_cumsum_control.py
9276086f38021b236a26dc17548872da707e574de82918380068818456397d03  experiments/pvldb_compiled_control.py
5ddbb19e4c76a5768a6a966da22dbce1c6c7c8c8d694473805ffb45b318ef5c8  experiments/audit_pvldb_compiled_control.py
287eb7c3a1f94144a0894e700ae61926059b48bfd0910a690d7c0d7926df71cf  experiments/pvldb_consumer.py
13ddbb522cd709d856bee2a8888a8f41952da0b101d59004a1a35cc647c3e350  experiments/audit_pvldb_consumer.py
0b7ab5216989fa03e336dc82718797003fe2bc398e2a49badcb83162df34821b  experiments/pvldb_score_probe.py
a2d034bbc4c080580d7ad8aeb3ca5ef177f6cf1aed9b207d1560545503951668  experiments/analyze_pvldb_score_probe.py
13dd166e907be1756c07d9f2216e86bf61016409901408aa94cc4068adb828b5  artifacts/pvldb-research-20261024/compiled-support-control/protocol.json
ba8ea76283d68aa0d888673006c7a10743704137ceb4f700d6f9724ddc339330  artifacts/pvldb-research-20261024/compiled-support-control/independent-report.json
846e9147300a3d49c5cb756b5ebce18d2c6a6c7580ac98243d3bfdf552f5d950  artifacts/pvldb-research-20261024/compiled-support-control/records.jsonl
bd082af600f885de1e833e5312328e319b88bd27ff32bd9812429dfa4681c4d6  artifacts/pvldb-research-20261024/compiled-support-control/workflows.jsonl
4811c90e71adf7681834818237fd2fa9587e3806b60ff05d4aac68a4c7f73354  artifacts/pvldb-research-20261024/public-consumer/protocol.json
ad2cb5ee149283e1ebb37e3d4cbfc8b0ba733f4be3a23e8852e8e1b1d15d5612  artifacts/pvldb-research-20261024/public-consumer/independent-report.json
c71985a9b3564007b3c1760be353ec8ba7cbb07fb6cbe0449e9d311c8c551633  artifacts/pvldb-research-20261024/public-consumer/profiles.jsonl
f767ca0dd210c3c6b6ad502075551b20514975be2e98bb1f7e71bd19ddf7def8  artifacts/pvldb-research-20261024/public-consumer/workflows.jsonl
ee0870d5dae4ab331fa1565785a16b4718e5be8ceb4fbd9d6fe365a90abc10df  artifacts/pvldb-research-20261024/score-host-probe/comparison.json
31d74c80c82d03529a9822e67da88e1469e9901d306d8aa326f791d6b6c2094e  artifacts/pvldb-research-20261024/score-host-probe/mac/receipt.json
2fef454c4712615b5711143fa4af4beb9a442d20abace73349ad8553c2393ae5  artifacts/pvldb-research-20261024/score-host-probe/mac/arrays.npz
9d140e3fce5186f69a80e875a36ee6b3bcff0f7db4caff4016ee13f395172967  artifacts/pvldb-research-20261024/score-host-probe/linux/receipt.json
0f602e4889d22e5a878cb7c24bc5c4f2911cc2f359073a27e9b30ca6c3dc1f01  artifacts/pvldb-research-20261024/score-host-probe/linux/arrays.npz
```
