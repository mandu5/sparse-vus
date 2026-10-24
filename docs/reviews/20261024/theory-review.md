# Independent scientific review: exact VUS evaluator

**Recommendation: Revise. Indicative internal rating: 6/10.** The central exact-arithmetic reductions survive this review, and the completed full-precision study supports useful gains on its defined workload. The largest remaining concern is the significance and reach of the contribution beyond existing support/cumulative-sum evaluators. The new collection implementation also has a concrete peak-memory qualification to correct.

Reviewed on 2026-10-24. This is one separately prompted internal scientific review, not an external review or an acceptance prediction. The 1–10 scale is an **internal surrogate**, with 6 meaning a promising contribution with material revision requirements; no current confidential PVLDB numerical review form was verified. The rating is not calculated from the project's proposed 5-point/6-point investment thresholds. Confidence: **4/5 on the inspected mathematics; 3/5 on novelty and venue significance**.

## Scope and evidence cutoff

I reviewed the entire `paper/sparse_vus.tex` candidate, its body, `saturation_method.tex`, `tie_run_method.tex`, the collection and tie-run result fragments, the 2026-10-24 evidence-design document and literature ledger, and `src/sparse_vus/batch.py` with its relevant ranking, geometry, validation and PR-kernel dependencies. This is **not** a review limited to the separate certified-sampling/TMLR manuscript.

The checked-out branch was `research/pvldb-20261024`, with HEAD `92319eafd0f937a152edf3a5c7e4355b2114acce`. New research files were untracked additions. Reviewed SHA-256 identities:

| File | SHA-256 |
| --- | --- |
| `paper/sparse_vus.tex` | `6aad5f373aa90390939e7a83262a61e2b4a4992d9db90eb1d97ef31162b4a9d2` |
| `paper/sparse_vus_body.tex` | `c551cae8bc76387735ce665e156d487e68a657469de9ae3a8e96308e32201891` |
| `paper/saturation_method.tex` | `3671bc35cc55b9238128d36db3792464c9a338244eb680f781cc9f998280ecda` |
| `paper/tie_run_method.tex` | `19caf24fbe216ed0d3e0d665aa0434d5388e302dc2cf2772a838511b6eb9befa` |
| `src/sparse_vus/batch.py` | `43bd8648a769b94e38d4310e0c7300d067764802132dbee9b55d737e11ddee14` |
| `artifacts/pvldb-research-20261024/literature.json` | `a8d043c2fc1e4c2f2c2868a76ffa571db3642e99ae0df7e481d4f68fb3ec8e04` |

I did not execute timing, detector, or numerical experiments and did not modify existing sources or artifacts. Claims about measurements below are inspections of manuscript/report evidence, not independent reruns. At the final review cutoff, the full-precision `report.json` was COMPLETE: SHA-256 `50de537a0229aa360ab3555696d7cb4800ca76b8656499866915407d209861a9`. I verified its recorded hashes against the protocol, inputs, raw timing records and workflow records. It contains 73 series (NAB 20, SMD 36, SMAP 17), eight detector families, 584 score vectors, and 62 recordings marked previously measured by name. I inspected the reported summaries but did not independently regenerate scores or recompute its bootstrap. The manuscript text itself still describes the earlier studies.

## Summary and contributions

The paper computes a pinned exhaustive dynamic VUS scalar after detector scores exist. Its useful conceptual contribution is an event representation that retains complete global score ties and analytically accounts for omitted inactive thresholds. Interval geometry and binary64 radix preparation give `O(n + (L+1)Q)` work. An offline activation schedule and component unions make subsequent traversal depend on the complete active prefix through recall saturation. A one-original-interval extension aggregates temporal runs of tied score classes and uses an integer sufficient stopping condition.

The newly added batch code shares label-only preparation across models, then interchanges the width/model loops to reuse weights and component IDs. This is a sensible engineering refinement, with unchanged `O(Mn + (L+1)MQ)` evaluation time. It should be assessed separately from the earlier whole evaluator's first archival contribution.

The completed full-precision report supplies substantially stronger evidence than the development pilot. At primary width 30, the following ratios use control time divided by stream time; the intervals are the report's simultaneous three-collection 95% paired bootstrap intervals, not independent reproduction results.

| Collection | Released / stream | Familywise 95% interval | Dense / stream | Klein / stream |
| --- | ---: | --- | ---: | ---: |
| NAB | 1.496 | [1.428, 1.566] | 3.543 | 30.513 |
| SMAP | 1.271 | [1.242, 1.302] | 3.693 | 25.772 |
| SMD | 1.207 | [1.193, 1.221] | 3.956 | 25.172 |

All 73 primary cases favor stream over released independent calls. The reported maximum scalar discrepancy is `1.1102230246251565e-15`, and the workflow winner sets agree. Direct warm-file collection median ratios against Klein are 22.16–23.03, versus 1.169–1.332 against released independent calls. These findings substantiate an exact-target numerical implementation and meaningful collection savings on one host. They do not establish the same gain for a different native VUS contract, a second host for the batch refinement, or every public implementation.

## Mathematical validity

I found **no decisive error in the principal exact-arithmetic identities or operation-count arguments**, subject to their explicit hypotheses. This is a proof inspection, not a formal verification or an all-input floating-point guarantee.

1. **Inactive events and ties.** At a fixed width, admitting an inactive position changes only global prediction count `C`. The state `T, B, P, N, H, R` remains fixed. The omitted ROC increments therefore sum to `(c_j^> - c_o)R_o/N_o`; the following complete-tie transition is a separate trapezoid. The stated predecessor FPR `(c_j^> - T_o)/N_o` is necessary. Right-step PR contributes zero on the inactive run. Retaining both global rank endpoints handles off-support positions tied with support. This establishes the claimed scalar identity, including signed FPR increments; simply joining retained ROC endpoints would be wrong (`sparse_vus_body.tex:100–123`).

2. **Two-distance geometry and preparation.** Each active half-width square-root ramp is at least `1/sqrt(2)`, so two contributions clip to one. Nearest and second-nearest distinct original intervals suffice. The linear scan and fixed eight-pass binary64 ranking justify the stated preprocessing bound in the specified model. This is not comparison-based linear sorting of arbitrary reals (`sparse_vus_body.tex:125–186`).

3. **Saturation and adaptive accounting.** `A+B/2 >= P0` with complete component coverage implies permanent recall one. Subsequent PR increments vanish, and signed ROC increments telescope to `1-F`. The reverse-deletion schedule avoids paying a full support scan before using the cutoff; union-find roots are fixed within a width. The otherwise easy-to-miss union cost is absorbed because `J_0=P0>=K`. The two-singleton separating family is consistent with the stated gap and width bounds (`saturation_method.tex:13–112`).

4. **One-interval and complete-tie results.** The distinct-active-score bound follows from at least `1/(2sqrt(2))` mass contribution per active position. The run-prefix identity is algebraically correct. The integer condition `D//3 >= P0-A` is conservative but sound, and visiting at most `3P0` active classes follows even with arbitrarily large classes. Charging all maximum-support runs of a visited class correctly prevents an unjustified universal linear-time claim (`tie_run_method.tex:16–100`).

5. **Local finite-precision bound.** The three-limb range accumulator's magnitude accounting and the local `gamma_8`/`gamma_6` rounding argument are internally consistent under the declared conversion, rounding and no-reassociation assumptions. The paper appropriately does not promote that local result into a final-scalar or winner certificate (`tie_run_method.tex:102–158`).

6. **Batch implementation.** The inspected stream kernel preserves the released PR computation's grouped masses, global tie counts and component first hits. I see no new mathematical operator in it. There is, however, a **peak-memory mismatch** in the header's unqualified working-space statement: `np.isfinite(scores).all()` at line 92 materializes an `M x n` boolean temporary, and line 88 may additionally allocate an `M x n` float64 conversion. Thus complete public-call peak auxiliary storage is `O(Mn+MQ+n+Q+K)`. `O(MQ+n+Q+K)` describes retained evaluation workspace after validation, with conversion excluded. A simple asymptotic witness is `L=0`, one original positive, hence `Q=1`, while both `M` and `n` grow: the finite-value check still allocates `Mn` entries. This does not invalidate the time bound or scalar formula.

## Novelty relative to the closest primary sources

**Boniol et al.** already partition static and maximum-buffer regions and reuse predictions; their Algorithms 2/3 retain a threshold loop inside the width loop. The candidate's remaining distinction is complete-event compression with correct scalar integration and the resulting support-sensitive bound, not support restriction or reuse itself. This comparison is supported by direct inspection of §4.3 and Algorithms 2/3 of [the VLDB Journal paper](https://www.paparrizos.org/papers/BoniolVLDBJ25.pdf).

**Klein fast-VUS** already sorts support scores, forms weighted support cumulative sums, and uses segment maxima for existence. Its pinned source still constructs threshold-length arrays and a full-series coverage mask within every width; `thre=n` supplies the exhaustive comparator. Those operations distinguish it from event elimination and the active-prefix schedule. They also show why “sorted support plus cumsum” would be an invalid novelty claim. I inspected [the primary source at revision 1bae859f](https://raw.githubusercontent.com/tomlouisklein/fast-VUS/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py).

The pinned official implementation confirms the manuscript's dynamic denominator, clipped square-root ramps, `>=` ties, right-step PR, integer-width mean and explicit ROC terminal point. Its semantics should remain the referent of “exact” throughout the revised paper. [Official VUS source, revision 467bace0](https://raw.githubusercontent.com/TheDatumOrg/VUS/467bace0c103f5c2bdb4900306d82939bcac8ff9/vus/utils/metrics.py).

Sylligardos's 2025 workshop paper already describes preliminary CPU/GPU VUS acceleration. Therefore neither accelerated VUS generally nor large speedups over the original implementation establish priority. That short paper does not disclose enough algorithmic or semantic detail to infer the present event representation or to declare same-target runtime superiority. [Primary workshop paper, §4](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/PhD/PhD25_17.pdf).

The 2026-10-24 ledger has twelve paper entries, but several concern alternative metrics or detector/model-selection benchmarks. They are useful context, not twelve equally close competing evaluator algorithms. I independently checked the closest sources above and the [TAB paper](https://arxiv.org/html/2506.18046) and [TSB-AutoAD paper](https://www.vldb.org/pvldb/vol18/p4364-liu.pdf); I did not independently verify every ledger entry or establish exhaustive priority.

The public v0.3.0 release explicitly contains the support-event evaluator and a working manuscript. I verified [that release page](https://github.com/mandu5/sparse-vus/releases/tag/v0.3.0). Public software does not by itself establish an earlier refereed publication. PVLDB's originality policy defines prior publication by refereed acceptance, so I would assess the disclosed complete evaluator as a possible first archival contribution, while separately assessing the incremental batch refinement. Refereed publication of that precursor remains unverified. [PVLDB submission guidelines, originality policy](https://www.vldb.org/2027/submission-guidelines.html).

**One-sentence surviving distinction:** the candidate gives a complete-tie support-event representation and input-sensitive implementation of the pinned dynamic VUS scalar, then avoids per-width full-support preparation when a saturated active prefix suffices; batch reuse is an additional implementation refinement.

## Scope, strengths and major weaknesses

The work has a plausible **Regular Research / Foundations and Algorithms** fit: its core is formal operator evaluation, it builds substantively on a VLDB Journal algorithm, and it evaluates a repeated time-series analytics operation. The official call values formal algorithms and encourages prototypes; its scope still requires an actual data-management contribution. I would not require an unrelated database-engine integration merely to create a scope argument. [PVLDB 2027 research call](https://www.vldb.org/2027/call-for-research-track.html).

The strengths are precise semantics, explicit global ties and dynamic denominators, charged setup costs, disclosed precursor history, and retention of negative incremental findings. In particular, the manuscript does not quietly replace the failed default-width saturation criterion with its favorable larger-width results.

The major weaknesses are:

- **Significance is narrower than the volume of theory may suggest.** The elementary area identity, standard radix sorting and standard offline data structures form a useful combination, but the general value of that combination needs a concise argument. The new batch mechanism is routine loop interchange and reuse; it cannot independently carry a major algorithmic novelty claim. At width 30, its marginal geometric gain over geometry-only reuse is 1.094 on NAB and only 1.024/1.025 on SMAP/SMD, with 3/17 and 2/36 case losses respectively. Most of the batch gain on those latter collections comes from shared preparation, not width-loop interchange.
- **The strongest extensions are conditional and their default-width benefit is weak.** The paper reports saturation ratios of 1.016, 1.026 and 1.013 against released radix at width 30, with its primary runtime criterion failing in all three runs. The run method loses to active prefix on 16/21 development and 14/16 external cases at width 300. These do not invalidate theorems, but they favor presenting those methods as regime-specific extensions. The whole support-event evaluator, not a generally superior prefix/run method, should carry the main claim.
- **The new evidence is useful but bounded, and not integrated into the paper.** The full-precision report addresses the old score-resolution concern and demonstrates gains across three collections, so lack of full-precision evidence is no longer a fair objection. However, 62/73 recordings have documented prior reuse, eight CPU procedures share preprocessing, and the completed batch run uses one host. Named series may also share a physical machine/channel source; per-series bootstrap intervals should not be represented as uncertainty over unrelated domains. A contemporaneous strongest-public-comparator check beyond Klein is still pending at this review's cutoff. The new gains must be presented as a defined repeated-evaluation workload, not universal detector-evaluation SOTA.
- **The batch workspace claim must distinguish retained state from public-call peak memory.** Sparse support is precisely where the hidden `Mn` validation temporary matters asymptotically. The current implementation's time savings may still be worthwhile, but the unqualified smaller space bound is not valid for its full public call.

## Specific falsifiable revision conditions

1. **Make the archival claim inspectable in one comparison.** Preserve the present semantic contract and provide precise pseudocode/cost accounting showing which per-width operations disappear relative to Boniol and Klein, which are standard tools, and which existed in v0.3.0. Keep the remaining novelty sentence narrow. This condition fails if the main claimed innovation reduces to already-public support cumsums or standard caching.
2. **Integrate and audit the completed frozen full-precision study.** The report now provides the requested collection-level estimates; incorporate them into the manuscript with complete-call versus workflow distinctions, paired uncertainty, all losses, genuine tie cardinalities, recording reuse and winner parity. Preserve the released evaluator and geometry-only ablation. Finish the pending strongest-public-comparator audit with matched exhaustive output contracts. Show machine/recording-block sensitivity where channels share a source, or explicitly limit the interpretation of the per-series interval. A second host for the new batch implementation is needed for a cross-platform batch claim, not for the already demonstrated one-host claim. Do not change the original prespecified criterion to conceal the SMD ratio being below the project's optional 1.25 investment threshold.
3. **Tie the conditional theorems to observed regimes.** Report distributions of `Q/n`, `J_w/Q_w`, component counts and class fragmentation, linking slowdown tails to those quantities. The revision should state explicitly whether the practical contribution is sparse-support evaluation, saturation, or compressible ties on each tested workload. No requirement for universal speedup is implied.
4. **Correct or enforce batch peak-memory accounting.** Either document the `O(Mn+MQ+n+Q+K)` public-call bound plus the smaller retained workspace, or after the frozen run produce a separately identified implementation whose validation/conversion is streamed. If the latter is claimed, verify memory scaling with variable `M` under sparse `Q`; existing timings must retain their original source identity.
5. **Separate numerical fidelity from decision certification.** Retain the present exact-arithmetic theorem versus tolerance-based implementation boundary. Winner equality may be claimed for measured cases under the declared tie convention. A universal winner or correctly rounded scalar guarantee would require a new proof; it is not a prerequisite for the narrower operator paper.

Minor revisions: integrate the recent literature comparison into the actual manuscript rather than only an external ledger; define “collection” versus source family consistently; ensure the final expanded text retains the 12-page non-reference limit. The inspected PDF has 13 pages with references starting on page 12, so its total length alone is not evidence of a current formatting violation.

## Public-review calibration and decision

**No actual accepted/rejected public review text was used to calibrate this score.** The inspected `public-review-calibration/ordinary-public-api-attempts.json` records HTTP 403 for OpenReview forums `UiNhIyGi1MT`, `iMmsCI0JsS`, and `8LfB8HD1WU`. Those access receipts are not review evidence. The official PVLDB criteria and primary published papers informed this review, but accepted papers are not substitutes for their reviews and no rejected-paper review was verified. Thus this review contributes one independent internal assessment; it does not complete the user's separate public-review calibration requirement.

I favor **Revise** because there is a coherent, apparently correct first-archival algorithmic contribution and a completed full-precision study demonstrating useful collection savings. The new evidence supports the 6/10 assessment; the score is not evidence that every project investment threshold passes. I do not currently favor unconditional acceptance because the main contribution needs sharper significance framing, the new result is not yet in the manuscript, the strongest-public-comparator check remains incomplete, and the batch peak-space wording is too strong. The required revision is principally attribution, comparative completeness, scope and evidence integration. Merely adding more internal checks, more citation entries, or more runs of already unfavorable variants would not resolve these points.

---

## Dated reassessment — 2026-10-24, 01:39 UTC evidence cutoff

**Reassessed recommendation: Accept (weak), with the minor numerical correction below. Internal surrogate: 6/10; confidence 3/5 overall, 4/5 for the core mathematics.** This is my independent scientific recommendation for the narrowly scoped whole exact-evaluator paper. It is not a venue decision, a calibrated acceptance probability, or a finding that every project investment gate passes. I have not read the other internal reviewers' scores. The initial review above is preserved.

The recommendation changes because the requested major revisions now have concrete evidence: a coherent whole-method manuscript, a matched-output Benchopt comparison, full-precision approximation consequences, dependence sensitivity, and explicit memory accounting. The same coarse score remains appropriate because the algorithmic idea is useful but specialized and technically modest. I would not support a paper whose primary novelty claim were merely the new batch loop.

### Materials and verification boundary

The reviewed revision is `paper/sparse_vus_pvldb20261024.tex`, titled *Exact VUS Evaluation by Support Events and Shared Interval Geometry*, together with its body, bibliography, generated tables and eight-page PDF. SHA-256 identities at this cutoff are:

| Material | SHA-256 |
| --- | --- |
| New manuscript entrypoint | `0dc8cf80da51f2fa20f0b8f3508faf113c8bb9cbf8b378b63c4b5863ff966836` |
| New manuscript body | `c3152127af8b50d20069b6ce7123051267d44ad0f592c7ad4e51318aa3fcc5b3` |
| `paper/pvldb20261024_tables.tex` | `7fcd5ed10547160582169134117420ec86719c07dd2c45263e03ac5b820c6f08` |
| New manuscript PDF | `6c953fd87dbdfe5e5af2fa2ce7f31e902df79af4ded2e2d71add4a424c0a941a` |
| `full-precision/independent-audit-v3.json` | `b6ed65bbc88f69fe6edd3e0ca2ed578881888368301899bbdff83479cf06bdcf` |
| `supplement/independent-report-v3.json` | `99396de3367f579cc55380c85c75526a7297b0157ff399e968d1779d49b2b7c2` |
| `resources/report.json` | `e26a4238c3f2e8ba30f5b67db921201b6b445f3eadfec2523e22f51b52d73355` |

The last three paths are relative to `artifacts/pvldb-research-20261024/`. I read both v3 PASS reports, inspected their relevant reconstructed summaries, and checked the available protocol, input, report, record and workflow hash bindings. The primary report is still the previously inspected report `50de537a…`, with unchanged measured outcomes. These are stronger evidence-integrity and reconstruction checks; I did not rerun their numerical producers, execute new benchmarks, or independently reimplement the auditors.

**The fresh Linux one-command run `40049786600` is pending at this review cutoff and receives no completion credit.** A provided entrypoint, a PASS record audit and a fresh acquisition-to-execution reproduction remain different states. I assess the new batch result as a one-host result. The manuscript does not need a fabricated second-host claim to support that bounded result; the project's outstanding fresh-reproduction gate nevertheless remains outstanding here.

### Correctness, novelty and integration

The central event formulas and complexity proofs are unchanged in substance and remain valid on inspection. The dynamic denominator is retained. The negative-run rectangle is integrated before each active complete tie, and off-support members of that tie remain in the global prediction count. The two-distance reduction is justified by the specified half-width square-root, sum-and-clip geometry. The binary64 and unit-cost metric-arithmetic assumptions are explicit. I found no new critical mathematical validity defect.

The new shared-evaluation proposition now correctly separates retained workspace `O(MQ+n+Q+K)` from full public-call peak auxiliary storage `O(Mn+MQ+n+Q+K)` (`body:276–299`). This resolves my concrete memory-bound objection without changing the frozen implementation. The real and synthetic process-RSS study supplies useful complementary evidence: for dense synthetic support, stream's approximately 225.0 MiB peak exceeds released's 175.2 MiB. The text correctly avoids equating process RSS or differences of high-water marks with auxiliary-space measurements.

The contribution framing is substantially better. The introduction and algorithm comparison engage directly with Boniol's static/support reuse and Klein's support cumsums, credit the standard tools, and identify the surviving distinction as **complete scalar event elimination with correct dynamic integration and support-sensitive evaluation**. The broad recent-paper discussion is now in the manuscript. I continue to give greater evidentiary weight to the nearest algorithm/source comparisons than to the number twelve itself. The disclosed software precursor remains eligible to be part of a possible first archival contribution; I have no verified evidence of prior refereed publication that changes that assessment.

Prefix saturation and tie-run aggregation are now conditional alternatives, with their earlier negative runtime findings retained. This prevents theorem count or constructed asymptotic separations from obscuring which implementation supplies the practical gain. For the present Foundations and Algorithms submission, I no longer regard lack of a universally beneficial prefix/run method as an unresolved major objection.

### What the new evidence supports

- **Whole exact method:** the matched ROC+PR comparison now measures the same returned outputs and shows Benchopt/radix workflow ratios 25.315, 32.065 and 40.924. The paired-trial intervals exclude one on every collection. The maximum recorded ROC discrepancy is approximately `4.852e-14`, below the stated `1e-11` tolerance. This resolves the omitted Benchopt/mismatched-output objection for the measured panel. It does not establish a comparison to an unmeasured GPU implementation or a different native VUS definition.
- **Incremental shared evaluation:** released/stream case geometric ratios remain 1.496, 1.271 and 1.207; directly timed workflow median ratios remain 1.332, 1.226 and 1.169. Geometry-only sharing explains most of the SMAP/SMD increment. The additional width-major loop gives only approximately 1.024/1.025 there and retains individual losses. These are useful savings, but no new asymptotic result or major standalone algorithmic breakthrough follows.
- **Separation from compilation and batching:** the matched dense/stream ratios 3.543–3.956 include sharing as well as the earlier sparse method. Dividing the same-panel case geometric ratios by released/stream gives dense/released approximately **2.368, 2.905 and 3.279**. This is an arithmetic inference from the paired summaries, not a separately timed workflow. It confirms that the precursor's support-event method contributes substantial benefit before the new sharing refinement. A sentence stating this explicitly would improve attribution further.
- **Why exhaustive evaluation is useful:** in the separately frozen supplement, 250-threshold Klein changes 14/73 numerical winner sets; four cases have both minimum and maximum selected-model regret at least 0.01. At 1,000 thresholds only three sets change, with no such practical-loss case. Exact stream still beats the measured 250-threshold workflow by 7.27–11.25. Thus the stated operator workload has a concrete accuracy-cost reason to use exhaustive evaluation; this is neither a general condemnation of approximation nor a detector-accuracy improvement.
- **Scope and dependence:** sparse-support fractions and component counts now connect the complexity result to the observed workload. The nine-block SMD sensitivity and exclusion of 18 development-matching geometries retain the gain's direction. They do not establish independence of physical recordings, and the manuscript says so. Together with declared recording reuse, transductive score generation and fixed-panel interval interpretation, these are adequate qualifications for the present operator experiment.

The small absolute workflow latencies, sparse supports, shared preprocessing, short-to-moderate real series and one-host batch result limit significance. They remain reasons for a weak rather than strong recommendation. They are not hidden contradictions of the now narrower claim.

### Calibration against actual public review contents

I read `docs/reviews/20261024/public-calibration.md` and then directly parsed the four matching cached `*-original-record.json` files with `ast.literal_eval` where needed. All four original-record hashes match `verified-note-metadata.json`. I read their decision/meta-review notes and relevant reviewer weaknesses, rather than using average ratings or inferred score updates.

These are original review-note contents **retrieved through the public [Paper-Review-Dataset mirror](https://huggingface.co/datasets/WENJINLIU/Paper-Review-Dataset)**. Current origin-service bytes could not be compared because direct OpenReview access remained unavailable. I independently corroborated the one-liners paper's publication in the [official ICLR 2026 proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/cf70320e93c08b39b1b29a348097a376-Abstract-Conference.html). The other decision labels here are read from their mirrored decision notes; I do not turn an inaccessible program page into fresh corroboration. These are adjacent-venue examples, not PVLDB review forms or an acceptance-rate sample.

| Actual note evidence | Implication for this revised manuscript |
| --- | --- |
| Accepted model-selection paper, [decision `HRD5hna4dy`](https://openreview.net/forum?id=gOZ_pKANaPW&noteId=HRD5hna4dy), plus reviewer `NuKBOZgVkj`: a specialized combination was valued for a justified useful problem, while missing strong baselines remained a serious objection. | Standard building blocks alone are not grounds to reject this paper. The concrete removed evaluator work and matched dense/Klein/Benchopt evidence now justify the combination. The example does not prove this paper has the same significance. |
| Accepted one-liners analysis, reviewers [`GNaYZoHZub`](https://openreview.net/forum?id=H27kvyG4qf&noteId=GNaYZoHZub) and [`3ebbNTymw6`](https://openreview.net/forum?id=H27kvyG4qf&noteId=3ebbNTymw6): objections targeted scope inflation, univariate coverage and missing paired statistical support. | Pinned dynamic VUS semantics, the fixed univariate panel, numerical rather than detector-quality claims, paired intervals and dependence qualifications answer the analogous scope objection. Multivariate or universal pipeline claims would reopen it. |
| Rejected GraphSAD paper, [decision `GMS-BMZmsG`](https://openreview.net/forum?id=73U_NlKaNx&noteId=GMS-BMZmsG) and reviewer [`EfHxtysAGTA`](https://openreview.net/forum?id=73U_NlKaNx&noteId=EfHxtysAGTA): missing comparisons and an ablation attributing improvement to a different component weakened the narrative. | The revised manuscript retains geometry-only and explicitly assigns most batch gain to preparation reuse. It includes the previously missing matched Benchopt comparison. I would still reject attributing the 25–41x whole-method ratios to the new width-major loop. |
| Rejected DyAD paper, [decision `GYaqYZtEQU`](https://openreview.net/forum?id=G-dM79m_EXd&noteId=GYaqYZtEQU) and reviewer `zzPoK1Z88ei`: useful application results did not resolve an unclear novelty boundary and a theory-to-system disconnect. | The present support-event theorem, pseudocode, support-density observations and matched dense control now form a traceable explanation of the speed benefit. The new manuscript no longer relies primarily on a list of conditional theorems. |

This calibration changes which objections I regard as fatal; it does **not** map ICLR numbers to a PVLDB score or mimic the accepted papers' ratings. My initial statement that no public review contents had been used remains historically accurate for that initial review and is superseded for this reassessment only.

### Remaining correction and final assessment

There is one minor reproducible numerical transcription issue in the reviewed body. At `body:445–446`, the SMD identical-label-block Klein/stream interval is printed as `[20.63,26.54]`. The v3 audited unadjusted `ci95` is `[20.6820201593,26.5856005213]`; it should round to **[20.68,26.59]**. The geometric ratio 23.76 and the positive conclusion are unaffected. The released/stream interval and geometry-disjoint interval in that paragraph match the v3 evidence. This should be corrected before submission and regenerated in the PDF.

I find **no remaining critical scientific-validity issue in the scoped whole-method claim** on the inspected materials. I would support acceptance as a useful, technically sound specialized exact-operator contribution, with the above minor numerical correction and the current limitations retained. The remaining uncertainty concerns broader interest and reach, not an identified false central theorem or invalid primary comparison. Fresh Linux completion is still unverified here; its eventual receipt must be assessed separately before calling the new one-command procedure successfully reproduced across hosts.

---

## Dated reassessment — 2026-10-24, 01:59 UTC evidence cutoff

**Recommendation: Accept (weak); internal surrogate rating 6/10, unchanged.** Confidence remains 4/5 in the central mathematical argument and 3/5 in the overall venue/significance judgment. The completed fresh-host reproduction strengthens empirical confidence; it does not create additional algorithmic novelty. The original review and the first reassessment above are preserved, including their then-accurate pending statuses. I have not read the other internal reviews or their ratings.

### Evidence checked and what is now resolved

The [public GitHub run 40049786600](https://github.com/mandu5/sparse-vus/actions/runs/40049786600) reports **Success**, commit `e1d504aba90dfd5bf7eaf1e6eb64e5765f859a3f`, and the expected Linux artifact. I inspected the downloaded start/completion receipts, input/protocol bindings, primary report, independent primary audit, supplementary independent report and verification summary. This is evidence of an actual fresh execution, beyond reconstructing statistics from the original Mac records. I did not execute any experiment, test, compilation or bootstrap during this reassessment.

The completion receipt records 01:53:14 UTC, Python 3.12.4, NumPy 1.26.4, Numba 0.59.1, Linux x86_64 and an AMD EPYC 7763 hosted runner with four exposed logical CPUs. The raw archive and public comparator sources were downloaded and the detector scores generated anew. The primary and supplementary audits both report PASS, respectively covering 10,512 and 5,256 timing records plus 216 collection-workflow records each. Their maximum exact PR discrepancies are `8.881784197001252e-16`; the supplementary matched-workflow ROC discrepancy is `4.884981308350689e-15`. These are numerical parity checks, not real-arithmetic certificates. An independent reconstruction code path and a project CI run are also not an independent external group's replication.

The evidence bindings inspected include:

| Item | SHA-256 |
| --- | --- |
| `linux-reproduction/reproduction-complete.json` | `cf5c8681954499f317e35efd4bca7b84442318a6b324732a0bac0d4e20e1899e` |
| `linux-reproduction/verification-summary.json` | `944fd9a55303ff49ccc155182f38661682804f0dd239ebcf53a0100e04410506` |
| Linux primary report | `b76b2ebd26eb5d03caecf3a1831547395185d290dcf88cd4a562dfaa79c41691` |
| Linux primary independent audit | `8ff422267f2ba03bc6e0f2a2e57371149d3ed3119ca147d917cafad546a1c41f` |
| Linux supplementary independent report | `06e349b6a94260f3ea2bbf882051169977c70742656c37d4e9660c037bb93f3d` |
| Revised manuscript body | `c058b634453c3e3d71e7b418f03dd056acc6343984bf87affa7c363054e2f8bc` |

The completion receipt's report/audit hashes match the inspected files. The primary audit's protocol, run-start and input hashes match those files too. The GitHub artifact lists digest `460d7a312d9ec3862a3aa2e52621ce0e0c30c59257a674ae0d00ba531344910c`. I have corroborated the public run status and inspected the extracted records/metadata; I do not claim a separate redownload and byte-level verification of the archive itself. The generated Linux score arrays were not retained in the downloaded artifact, so their record-level identities and the completed runner audit are available, while a new local input-array audit would require regeneration.

### Replicated effect and its boundary

The Linux primary width-30 evidence is:

| Collection | Released/stream case geometric ratio, adjusted 95% CI | Exact Klein/stream measured collection-workflow ratio | Matched ROC+PR Benchopt/sparse-radix workflow ratio |
| --- | --- | --- | --- |
| NAB | 1.886 [1.732, 2.043] | 20.06 | 22.38 |
| SMAP | 1.580 [1.526, 1.644] | 20.28 | 30.40 |
| SMD | 1.340 [1.322, 1.359] | 16.17 | 42.55 |

All 73 case medians favor stream over released independent calls. The case intervals adjust over the three collections for this comparator; the workflow ratios are measured fixed-collection operations, not the same estimand as case geometric means. The results preserve the direction of the claim across two CPU architectures and fresh score generation. They do not justify pooling Mac and Linux repetitions or assigning a portable universal speed factor. Shared hosted-runner load is uncontrolled. The manuscript retains the unfavorable NAB stream workflow of 0.111 seconds against its 0.061-second median, rather than censoring it.

The attribution boundary remains essential. The large Klein and Benchopt ratios concern the **whole support-event method**. The smaller released/stream ratios measure the **incremental sharing implementation**. On the original Mac panel, the added pure independent-call dense/released decomposition is 2.368, 2.905 and 3.279, with all 73 cases favoring support compression. This answers the previous request to isolate the whole-method mechanism from batch sharing. Geometry-only sharing still explains much of the batch increment; none of these results makes loop interchange itself a novel algorithmic principle.

Approximation results are correctly host-specific. Linux's 250-threshold evaluation changes 13/73 winner sets, with three losses at least 0.01, versus Mac's 14/73 and four. At 1,000 thresholds, both hosts have three changed sets and no loss at least 0.01. The manuscript explains that newly generated detector scores differ, including an observed SVM VUS-PR change in the affected SMAP case; it appropriately leaves the precise numerical cause unassigned without the runner arrays. This does not contradict same-input parity of the exact evaluators. It does rule out treating the cross-host selection counts as an exact fixed-input replication or claiming identical detector outputs from a seed alone.

### Theory, novelty and manuscript integration

I reread the current target definition, inactive-event lemma, ROC predecessor correction, two-distance lemma, comparison-model theorem, fixed-binary64 proposition and shared-evaluation bound. I identify no new critical validity defect. Complete global ties, the dynamic denominator, signed ROC increments, word-size assumptions and accepted-input conversion costs remain explicit. The support-event result still concerns exact scalar evaluation of the pinned operator in the stated arithmetic model; numerical agreement is a separate implementation check. No inference of exact real-arithmetic certification is warranted.

The novelty assessment from the preceding reassessment survives. Boniol's support reuse and Klein's support cumulative sums substantially precede this work. The narrower first-archival contribution is a complete scalar event reduction with global counts, the necessary dynamic ROC correction and width-dependent support geometry, supported by a compiled dense control. Public release of the precursor remains disclosed. No additional foundational novelty arises from the fresh CI run, memory measurements, conventional work sharing or the count of recent citations. Whether this specialized contribution has sufficient breadth for PVLDB remains the main reviewer-dependent uncertainty.

The revised body now actually integrates the Linux results and limitations. It also corrects the SMD block interval to `[20.68,26.59]`, identifies the unsuccessful default-width prefix experiment as a separate earlier study, and states that the one-command contract regenerates numerical tables as JSON while TeX rendering and compilation are separate. These resolve the specific presentation/correctness issues raised above. The public-call peak bound still includes `Mn`; the reported RSS tradeoff is retained. I inspected the revised source, not a newly compiled PDF, so final PDF/source synchronization remains a production check rather than a verified result of this reassessment.

### Residual limits and falsifiable conditions

The operating-range follow-up on nine MITDB/SWaT series and sixteen controlled regimes is **running and receives no evidential credit here**. Completed fresh execution does not by itself broaden the present real-data result beyond short-to-moderate, predominantly sparse, partly reused univariate recordings. Nor do two hosts establish all-platform performance, multivariate generality, a GPU advantage, low peak memory, superior anomaly detectors, or application-valid model selection.

My weak acceptance applies to the current, bounded whole-method claim. I would revise it downward if a pinned same-target competitor already implemented the complete claimed reduction; if a complete-tie/dynamic-denominator counterexample invalidated the central identity; if a same-output compiled comparison eliminated the claimed support-compression effect; or if the paper assigned whole-method gains to the incremental batch loop. The current evidence does not exhibit those failures. An adverse result in the running dense/long-series study must be reported and used to delimit an operating range; it would invalidate a universal speed claim, which this recommendation does not endorse.

The major surviving weakness is specialized significance and empirical reach, not an identified false theorem or invalid primary timing comparison. Successful reproduction closes the previously pending fresh-host execution item and justifies more confidence in the reported scoped result. I retain **weak Accept / 6 out of 10 on the explicitly internal surrogate scale**, rather than raising scientific merit merely because additional verification work completed.

---

## Final dated review — 2026-10-24, integrated evidence cutoff 02:42 UTC

**Five of the six evidence gates can be marked PASS from this review's evidence; aggregate completion of gate 5 requires the coordinator to verify all three independent reviews. My final venue recommendation is Accept (weak), internal referee surrogate 6/10. The separate prospective project 6-point research criterion FAILS.** The appropriate next action is to close the three-review process and submit a carefully scoped whole-method paper, without relabeling the failed incremental target as achieved. Earlier reviews and their scores remain unchanged above. I have read no other internal review or its score.

### Final materials and scientific summary

I inspected the completed operating-range study and minimal-Klein control, their independent reports, frozen protocols and completion receipts, the final manuscript body/tables, and extracted text from the newly compiled 10-page PDF. The PDF contains the new long-recording, dense-support and minimal-patch results. This was a static scientific review and record inspection; I did not execute the metrics, benchmark producers, tests, bootstrap or compilation.

The work's defensible contribution is a complete, support-sensitive evaluator for one precisely specified dynamic VUS operator: global complete-tie counts, PR event contraction, the correct ROC predecessor/rectangle contribution, and interval geometry that avoids full-series setup at every width. It combines known techniques and elementary identities into a useful implementation. The disclosed released evaluator already embodies the main algorithmic contribution; the new batch loop adds ordinary preparation sharing and loop interchange. I would not recommend acceptance of the batch increment as a standalone algorithm paper.

The new evidence is bound to the following inspected artifacts:

| Artifact | SHA-256 |
| --- | --- |
| Operating-range independent report | `aba680948a39173d157a472d2f20b53e9a42d6c859424398a83c3f03500b5314` |
| Operating-range completion receipt | `a344b09627216fc2cbabde33f777ae13dc1e449094be36ad3abf573b4c496937` |
| Minimal-Klein independent report | `301badd78f5df9b250655a7b1be959631d7f0123ea65ebb528f70e1b516c87be` |
| Minimal-Klein completion receipt | `4d697591186197f160d5d8784c2455357d881581ab24891335a494b0aac9b94c` |
| Final manuscript body | `c86fcda95b6afb8f963d7f607b74bd4149ee61ed72678478e85bb1980f9418ab` |
| Final tables | `c8fbfab4fd4e21527cc748b233fc8f7f6bd7ccba1fd2405cb58ecf76546c4aec` |
| Inspected 10-page PDF | `4a05a41264b20749b3884883f4cdad1db5e0a3fabd7a1f141f698ba7c5be3148` |

The operating-range protocol and input hashes agree between the completion receipt, independent report and actual files. For the minimal-Klein study, I additionally hashed the raw record/workflow files and both control source files: they match the frozen protocol and audit bindings. Audit PASS means the stated independent reconstruction passed; it is not proof of every possible input or a separate outside group's replication.

### Does the novelty reduce to an obvious patch?

**The PR threshold restriction alone does reduce to a simple patch.** The inspected [pinned Klein source](https://raw.githubusercontent.com/tomlouisklein/fast-VUS/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py) already has support-score cumulative sums and global prediction counts. Selecting only the distinct maximum-support scores preserves every PR recall change, including complete ties. No sophisticated new primitive is needed for that observation. The author-created control replaces exactly one threshold-list expression, retaining all other operations. Its measured result must therefore narrow the novelty narrative, and the final manuscript does so.

| Collection | Unchanged Klein / minimally patched Klein | Patched Klein / released evaluator, adjusted 95% CI |
| --- | --- | --- |
| NAB | 1.654 | 12.052 [10.325, 13.812] |
| SMAP | 2.274 | 9.067 [8.179, 10.052] |
| SMD | 2.968 | 6.969 [6.586, 7.270] |

All 73 case medians favor the released evaluator over the patch; exact numerical winner sets agree and maximum PR discrepancy is `1.11e-15`. The audited SMD label-block comparison is 6.772 [5.835, 7.253]. Direct patched/stream workflow median ratios are 11.96, 10.14 and 7.46, with only three not-fully-balanced workflow orders. These are new author-created ablation results, not a newly discovered unchanged upstream baseline.

The remaining 7–12x case ratios **do not quantify algorithmic novelty**: they include NumPy-versus-compiled implementation effects. The patch also duplicates maximum-support discovery once and is deliberately a minimal change, not an optimized reimplementation of every Klein operation. The separate compiled dense/released experiment, with 2.368/2.905/3.279 case ratios on the primary panel, is the cleaner evidence for support compression beyond compiler choice.

What survives the patch is narrower: the full width kernel avoids the retained per-width full-length coverage/segment-max operations, the two-distance construction avoids repeated ramp assembly, and the ROC scalar requires the predecessor correction absent from a PR-only patch. The stated `O(n+(L+1)Q)` construction is not obtained merely by changing that one expression. Nevertheless, these are accessible specialized optimizations, not a deep general algorithmic framework. A skeptical reviewer could reasonably find the conceptual depth modest. I do not dismiss that objection because the artifact is extensive or the external speed ratios are large.

### Generality, negative results and validity

The operating-range study genuinely expands the measured lengths: all eight MITDB and one SWaT archive recordings, 419,919–650,000 points and 2–199 original components, plus sixteen controlled conditions reaching one million points. The independent report covers 697 timing records, 42 workflows and the separate prefix diagnostics. Maximum reference PR and ROC discrepancies on the checked real inputs are `2.5535e-15` and `8.6153e-14`. The controlled inputs' untimed reference arrays were not retained: their recorded PR error is bounded and ROC is finite-checked, while real-case discrepancies are reconstructed. This is a narrower audit guarantee than independently recomputing every synthetic scalar reference.

MITDB's measured Klein/stream workflow improves from 53.14 to 2.30 seconds; SWaT improves from 4.34 to 0.245 seconds. Their ratios are 23.10 and 17.70, with matched ROC+PR Benchopt/radix ratios 29.50 and 25.66. These absolute savings strengthen the practical case compared with the primary subsecond collections. They do not make the nine recordings independent new populations: eight names were used previously, MITDB has seven distinct label sequences, and SWaT contributes one series.

The new batch effect remains weaker. Released/stream workflow median ratios are 1.220 and 1.086, but the paired-geometric timing intervals [0.925, 1.340] and [0.955, 1.165] include one. One MITDB case favors geometry-only sharing. Those observations support the whole evaluator much more convincingly than an added robust batch speedup on long recordings.

The controlled regimes expose the predicted failure. At support fraction about 0.9003, dense/released is 0.980 [0.962, 0.9994]; support compression provides no advantage and can cost time. At width zero its ratio is 1.065 with interval [0.932, 1.184], whereas width 300 gives 16.36. With one score vector, released/stream is only 1.023. These are conditional four-order timing intervals, not general crossover thresholds. Changing component count also changes expanded support, so it does not identify a pure component-count effect. The separate prefix algorithm visits 99.94% of active positions in the million-point random-score condition; this diagnoses that algorithm, not stream's internal work.

No critical mathematical invalidity emerged on rereading the final theorem and proof sections. The exact-arithmetic identity, fixed-word preparation assumptions, public `Mn` validation/conversion peak, numerical tolerance and lack of a universal rounding certificate remain distinct. Dense-support failure, the memory penalty, failed saturation timings and uncertain additional batch gains are now results rather than hidden exclusions. The original Mac and fresh Linux scores and timing intervals remain separate.

### Venue fit and weakest point

The official [PVLDB 2027 research call](https://www.vldb.org/2027/call-for-research-track.html) allows a Foundations and Algorithms paper centered on a precise algorithm with implementation evidence. The [scope policy](https://www.vldb.org/2027/submission-guidelines.html) requires a substantive data-management problem, engagement with database research and an appropriate application context. This paper directly builds on the PVLDB/VLDB Journal VUS operator and reduces recurring stored-profile evaluation cost; it is more than a syntactic database citation. I regard that as a plausible Regular Research fit. It is not a demonstrated general database execution engine, and calling it one would weaken the submission.

**The weakest point is limited conceptual breadth and depth:** PR event restriction is elementary, full-recall stopping and the data structures are prior tools, batching is standard work sharing, and the geometry depends on the pinned ramp/overlap semantics. The long-workflow and compiled-control results make the combination useful enough for my borderline positive judgment. They do not turn it into a broadly applicable foundational breakthrough. I retain weak Accept rather than a stronger score; a significance-based rejection by another competent reviewer would remain plausible. An EA&B label would not automatically solve this concern because that category has its own broad-interest and comprehensive-insight expectations.

The accepted/rejected public-note calibration remains exactly the actual mirrored evidence documented in the first reassessment: two accepted and two rejected adjacent ICLR papers, including their substantive novelty, baseline, scope and theory-to-evidence objections. I used no average-score mapping. Direct OpenReview origin bytes remain unverified; this is not calibration against an obtained confidential PVLDB form or public PVLDB decisions.

### The user's six evidence gates

| Gate | Independent assessment at final cutoff |
| --- | --- |
| 1. Novelty against at least ten recent primary papers | **PASS, narrowly.** `literature.json` compares twelve 2024–2026 primary papers and the body states the surviving distinction: a complete support-event evaluator of the existing dynamic operator, rather than a new metric, detector or selection policy. Software is additional evidence, not counted among the twelve papers. Most are application/metric context; the decisive algorithmic challenge remains Boniol plus Klein and the minimal patch. Citation count is not proof of depth. |
| 2. Strong same-output baseline on three public collections, uncertainty and ablation | **PASS for the whole method.** Primary NAB/SMAP/SMD gains have paired lower bounds above one, large directly measured external workflow gains, matched compiled dense controls and sharing ablations. Matched ROC+PR and sampled APIs are separated; the new minimal patch remains a strong improvement over unmodified Klein yet trails the released evaluator. |
| 3. Real generality and explicit failures | **PASS at the declared operating scope.** Complete unrounded outputs from eight fixed detector procedures, real primary and long recordings, declared reuse/dependence, dense-support loss, memory tradeoff and failed/uncertain incremental regimes. This does not validate tuned detector accuracy or broad multivariate/deployment generality. |
| 4. Reproduction | **PASS for the principal primary/supplement tables.** Fresh one-command Linux execution is complete, separately audited and recorded. Follow-up, resource and minimal-patch studies have separate frozen commands; the new operating-range wrapper itself has not received a second fresh execution. The final body explicitly states this boundary. |
| 5. Three independent calibrated mock reviews | **This review's component is complete; aggregate status not independently certified here.** I used verified public venue criteria, labelled the numeric scale internal, inspected actual mirrored accepted/rejected notes and recorded the main weakness. The coordinator must verify three completed independent reviews; I deliberately did not read the other reviews or their scores. Their mere filenames would not establish independent final review completion. |
| 6. Venue, track and deadline | **PASS.** Target is PVLDB volume 20, Regular Research / Foundations and Algorithms, for the whole exact-evaluator contribution. The chosen abstract deadline is 2026-11-25 17:00 America/Los_Angeles and paper deadline 2026-12-01 17:00, consistent with the [official monthly schedule](https://www.vldb.org/2027/important-dates.html). This is a target, not a submitted paper or external decision. |

### Prospective project 5-point versus 6-point rules

These are the operational investment thresholds in `docs/superpowers/specs/2026-10-24-pvldb-evidence-design.md`, **not** my referee surrogate or a PVLDB scoring scale.

- **5-point scientific conditions are met.** An identifiable whole-method contribution remains, real full-precision results cover three collections with positive paired lower bounds, external whole-workflow ratios comfortably exceed 1.5, and I identify no unresolved mathematical or measurement-invalidity defect. Final administrative completion of the aggregate three-review gate is the coordinator's check, as above.
- **6-point criterion is not met.** The prospectively fixed new-increment test requires at least 1.25 geometric released/stream speedup on every collection with a positive lower confidence bound. Mac SMD is **1.207**, adjusted interval approximately **[1.193, 1.221]**. The new patch-control run again gives SMD released/stream **1.205 [1.193, 1.216]**. A positive improvement is not a pass at 1.25. Linux's larger value cannot replace the primary host after seeing the result, and neither pooling hosts nor switching to a favorable workflow statistic is a valid rescue.
- **The alternate generalization clause is not established.** Longer real inputs and synthetic stress tests strengthen validation of the already released method; they are not a new comparably substantive mechanism or mathematical generalization beyond that release. The already released ROC result cannot be relabeled as a new batch contribution. Two CPU environments and large external workflow gains satisfy other 6-point components but do not repair this failed component. I also cannot certify absence of major objections across reviews I have not read.

Thus the defensible operational classification is **5-point evidence, conditional only on aggregate review-process closure; not 6-point achievement**. My independent **6/10 weak-Accept referee assessment** remains a separate judgment about the complete archival paper.

### Final recommendation and revision conditions

**Accept (weak), internal 6/10; confidence 4/5 on the central mathematics and 3/5 on overall significance/venue fit.** No further experiment is necessary to justify the present bounded claim in my assessment. Preserve the minimal-patch result, the compiler-attribution qualification, dense-support loss, uncertain long-recording batch increment, source/host distinctions and the failed prospective 1.25 criterion in the submission and research report.

The recommendation would change if a same-target prior algorithm already supplied the complete claimed reduction, if a complete-tie/dynamic-denominator counterexample invalidated the theorem, if the disclosed precursor were found to be prior refereed publication relevant to the venue's originality rules, or if the final paper reassigned whole-method speedups to the new batch increment. None is established in the reviewed evidence. The strongest remaining reason to reject is a judgment that the useful specialized construction is too incremental for this venue, not a discovered false theorem, unmatched primary baseline or missing execution receipt.

---

## Dated reassessment — 2026-10-24, 11-page revision checked at 03:34 UTC

**Five bounded evidence gates remain directly supported; aggregate completion of the three-review gate remains the coordinator's check. My recommendation changes to Revise, internal referee surrogate 5/10, from the preceding weak Accept / 6/10.** The new compiled control and public-consumer result materially weaken the argument for a sufficiently distinctive and consequential PVLDB contribution. Mathematical validity and implementation credibility remain strong. The prospective project 5-point conditions remain supportable within their original external-baseline scope, subject to aggregate review completion; the project 6-point criterion remains unmet.

I assessed the complete first-archival evaluator paper, including its disclosed unrefereed precursor. This is not a rating of batch engineering alone. I read the permitted common additions note, current source/PDF, the three new evidence packages and the compiled control's implementation. I did not read another internal review, another reviewer's score or the agent listing. All earlier text and scores above are preserved.

### Evidence actually checked

The inspected body SHA-256 is `91e638315c79c0094bffe1c4fecbfc9436f01f4e4dbc76a762c44a7cc0fc8dc3`; the 11-page PDF SHA-256 is `fb81365502f290ae06ae7662019cc9a232a00dc00fd3d50140d95b3b87601633`. The extracted PDF text contains the new control, consumer and host-diagnostic findings. Both the abstract and body state the negative attribution and application results. Thus this reassessment is not requesting disclosure of evidence already disclosed.

I independently hashed the new control/consumer protocols and raw records against their completion receipts and audit reports, checked all 13 compiled-control and 29 consumer source bindings, and found no mismatch. I also verified both host-probe receipt/NPZ hashes and directly compared the saved input arrays. No metrics, fits, timings, bootstrap or compilation were rerun. The principal new report hashes are:

| Evidence | SHA-256 |
| --- | --- |
| `compiled-support-control/independent-report.json` | `ba8ea76283d68aa0d888673006c7a10743704137ceb4f700d6f9724ddc339330` |
| `public-consumer/independent-report.json` | `ad2cb5ee149283e1ebb37e3d4cbfc8b0ba733f4be3a23e8852e8e1b1d15d5612` |
| `score-host-probe/comparison.json` | `ee0870d5dae4ab331fa1565785a16b4718e5be8ceb4fbd9d6fe365a90abc10df` |

The first two audits report PASS. The compiled study covers 1,314 complete case calls and 54 workflows; maximum reference PR discrepancy is `4.44e-16`. The consumer trace covers 32 nine-metric calls and four complete workflows; maximum paired output discrepancy is `3.44e-15`. These are scoped record/trace audits, not an independent reimplementation of the seven non-VUS metrics or all-input floating-point certification.

### What the compiled control changes

The optimized authored control uses the candidate's validation, fixed-word ranking and complete global tie counts. It replaces nearest-distance geometry with direct sum-and-clip ramps and component support scans, uses support-local scratch, and caches original-positive group mass across widths. It is neither an unchanged historical baseline nor a literal JIT compilation of Klein. Its balanced six-order evidence is substantially more informative about attribution than the earlier NumPy-only patch.

| Collection | Control / released case ratio, adjusted 95% CI | Control / stream case ratio, adjusted 95% CI | Complete-workflow control / stream |
| --- | --- | --- | --- |
| NAB | 0.910 [0.905, 0.915] | 1.357 [1.291, 1.427] | 1.177 |
| SMAP | 0.960 [0.945, 0.973] | 1.201 [1.180, 1.224] | 1.126 |
| SMD | 0.978 [0.969, 0.985] | 1.166 [1.158, 1.174] | 1.152 |

The control beats the released scalar evaluator on all 73 case medians. Stream still beats this control, including positive timing intervals in the six balanced workflow passes. However, the remaining complete-workflow gain is approximately 13–18%, and includes standard sharing across eight score vectors. The large previous public-library factors remain accurate comparisons to those public APIs; they do not establish a similarly large benefit of the distinctive geometry or batch mechanism over conventional optimized support evaluation.

This is not a controlled substitution of geometry alone: caching and data-flow choices also differ. It therefore does not prove the geometric lemma intrinsically slower. It does establish that the current primary panel supplies no separate runtime superiority of the proposed scalar implementation over a straightforward compiled alternative without that geometry. A similarly shared direct-ramp implementation is not measured, so the remaining stream advantage is not uniquely attributed to nearest-distance geometry either.

My earlier borderline acceptance gave substantial weight to elimination of repeated width work as a practical distinction beyond the elementary PR patch. The stronger control now removes full-series clearing by ordinary support-local storage and obtains all the primary scalar outputs more cheaply. That is a material change to the significance assessment, not merely another small qualification to the same positive conclusion.

### The theorem still has a real, narrower distinction

I do not find a counterexample to the support-event identity, dynamic ROC correction or stated bound. The control itself uses the paper's support grouping and global-rank machinery; it is not evidence that the whole construction was previously published. The public software precursor remains distinct from a verified prior refereed publication.

There is also a genuine worst-case distinction from the direct-ramp control. Let `D_w` count individual original-interval ramp visits made by that control at width `w`, including visits that later clip. Inspection of its loops gives work bounded by `O(n + (L+1)Q + sum_w D_w)`, with `D_w <= K w`. When many ramps overlap, the summed visit term can grow as `Theta(K L^2)` for an appropriate interval family. The two-distance construction removes that multiplicity and retains `O(n+(L+1)Q)`. For sparse nonoverlapping ramps, the direct visits can already fit within the support-linear width work, consistent with the new empirical result.

This theoretical distinction should not be erased because one implementation loses at width 30. Equally, it should not be credited as a demonstrated practical improvement where the measured conventional control wins. The existing wide-width synthetic comparison uses the matched dense evaluator, not this new direct-ramp control; it does not isolate the repeated-ramp term against the strongest newly measured support alternative. The ROC predecessor correction also remains necessary for that scalar target, but is a short specialized integral identity rather than, by itself, evidence of a broad new algorithmic framework.

The narrow novelty survives: a complete exact representation and complexity account for the pinned dynamic operator. Its conceptual depth is modest. PR support-threshold restriction, complete ties, caching, radix ranking, local scans and loop interchange remain standard or elementary ingredients. The new control makes that limitation more consequential for a Foundations and Algorithms submission.

### Application significance and the host diagnostic

I inspected the pinned [TSB-AD `get_metrics` source](https://raw.githubusercontent.com/TheDatumOrg/TSB-AD/303dffbfc11612995b17b06633f8c9d0ea0e38e5/TSB_AD/evaluation/metrics.py). The experiment retains its nine outputs and seven non-VUS computations, replacing only the VUS callback with two exact ROC+PR backends. Its largest-primary-recording selection, public width estimator, ABBA order, output checks and import-failure disclosure make this a useful application probe.

The result is unfavorable to a broad application-speed claim: VUS median time falls from 0.9289 to 0.01406 seconds, **66.07x**, while total median workflow time falls from 34.2603 to 33.2340 seconds, **1.03088x**. VUS occupies only 2.70–2.72% of the baseline trace. Two fixed-input repetitions per backend provide descriptive evidence, not a significance test or population interval. Other metrics and training are not accelerated by this method. One consumer does not prove that VUS is never a bottleneck; it does mean that the supplied public-consumer evidence does not substantiate a large end-to-end payoff.

The earlier VUS-only MITDB saving from 53.14 to 2.30 seconds remains useful operator evidence. It is not an observed consumer bottleneck, and that long-recording study has not compared the new optimized compiled support control. A convincing practical novelty case can no longer rely mainly on the large unchanged-public-library ratios and that operator-only latency.

The host diagnostic resolves a narrower issue successfully. I directly verified byte identity of observations, labels, standardized matrices, fit indices, feature means and standard deviations in the saved Mac/Linux arrays. The saved SVM support-vector shapes are `(104,16)` and `(105,16)`, and maximum SVM score difference is `0.0001195869`. The report evaluates both saved score sets on one evaluator host, reproduces SVM PR values 0.3092648648 and 0.3329318469, and agrees with unchanged Klein within `5.56e-17`. The [public diagnostic run](https://github.com/mandu5/sparse-vus/actions/runs/40057467287) also reports Success.

This localizes the observed SVM discrepancy to fitted-state/score generation after standardization; it does not establish a specific BLAS, compiler or instruction as its cause. The new Linux eight-model bytes differ from the original Linux run, while the Mac bytes match their original run. Original Linux arrays have therefore not been recovered. The manuscript states these limits accurately. This addition strengthens provenance and implementation validity but does not supply new algorithmic or application significance.

### Six evidence gates and the prospective research thresholds

| User gate | Current assessment |
| --- | --- |
| 1. Recent primary-literature comparison and surviving distinction | **PASS as a bounded evidence requirement; major venue-significance reservation remains.** Twelve primary comparisons and an identifiable complete-operator distinction survive. They do not establish sufficient conceptual depth, and the new control materially narrows the practical distinction from conventional support evaluation. |
| 2. Strong eligible public baseline, three collections, uncertainty and ablation | **PASS within the frozen operator scope.** Same-output public comparisons remain valid and positive; a stronger authored compiled control is now included. The much smaller gain over that control must accompany any interpretation of the public-library factors. There is no large application-wide speedup in the measured public consumer. |
| 3. Real generality and failures | **PASS at the declared scope.** Complete real inputs, eight procedures, long recordings and explicit failures remain. The new consumer failure further limits the application claim. These data do not establish deployment-wide or multivariate benefit. |
| 4. Reproduction | **PASS for principal primary/supplement results.** The earlier fresh Linux execution remains complete. New studies have separate frozen producers, receipts, raw records and audits; they are not silently included in the older one-command receipt. Saved diagnostic arrays now support the localized host-difference analysis. |
| 5. Three independent calibrated reviews | **This independent review is complete; aggregate status requires coordinator verification.** No other review or score was inspected. The actual adjacent accepted/rejected mirrored notes documented earlier remain the calibration evidence; direct OpenReview origin bytes and the confidential current PVLDB form remain unavailable. |
| 6. Venue and deadline | **PASS as specification, with a substantive merit concern.** PVLDB volume 20 Regular Research / Foundations and Algorithms, abstract 2026-11-25 and paper 2026-12-01 at 17:00 America/Los_Angeles. The whole first-archival evaluator is the submission unit; an official acceptance is not implied. |

The prospective investment definitions must remain separate from this reviewer score. The original **5-point rule** uses the strongest eligible external baseline and asks for a surviving contribution, real three-collection results, positive lower bounds, at least 1.5x whole-VUS-workflow speedup and no unresolved validity defect. Those scoped scientific conditions still hold, with aggregate review completion to be checked by the coordinator. The author-created compiled control does not retroactively become an unchanged external release, and the new nine-metric consumer does not retroactively replace the frozen VUS-specific workflow. However, **a 5-point operational pass is now visibly insufficient to establish a convincing PVLDB significance case**.

The **6-point rule still fails**: the primary Mac SMD released/stream ratio is 1.207 rather than at least 1.25, and no substantive new generalization beyond the released method has been demonstrated. The stronger compiled comparison further reduces the remaining incremental advantage. The host diagnosis is a reproducibility explanation, and the consumer is an application-boundary result; neither qualifies as a new generalization that repairs the failed target. This review now also records an unresolved major significance/novelty objection for the intended venue. No favorable host, rerun, different denominator or expanded definition should replace the prospective condition after inspection.

### Recommendation, confidence and falsifiable revision conditions

**Revise; internal surrogate 5/10. Confidence: 4/5 in the central mathematics and inspected numerical evidence, 3/5 in the overall venue judgment.** The biggest weakness is the absence of a demonstrated consequential advantage specific to the nontrivial part of the construction over conventional optimized support evaluation. The controlled experiments are valuable precisely because they reveal this limitation. Honest disclosure improves the paper's credibility; it does not by itself restore the missing significance.

The official [Foundations and Algorithms category](https://www.vldb.org/2027/call-for-research-track.html) makes the conceptual/algorithmic contribution central. The full paper remains plausibly in scope through its direct engagement with database VUS research and stored-profile analytics, but scope eligibility and research merit are different judgments. The present evidence supports useful specialized software and a correct formal account more strongly than a compelling regular research contribution.

A revision capable of changing my recommendation needs substantive evidence along at least one of the following routes, with claims restricted to what it establishes:

1. **Establish the remaining geometric distinction where it matters.** Compare nearest-distance and optimized direct-ramp methods with the same compilation, ranking, cached positive masses and sharing policy across a prospectively chosen overlap/width regime. Report individual ramp-visit multiplicity alongside timing. A credible positive result must connect the theoretically removed work to a material measured benefit and explain the relevance of that regime; the existing dense-control comparison cannot substitute for this attribution. If there is no such benefit on relevant inputs, retain the negative result and reduce the algorithmic claim accordingly.
2. **Demonstrate meaningful use of the operator result.** Use an independently motivated stored-profile consumer where VUS is actually a measured bottleneck; compare the best eligible compiled alternatives under matched outputs and sharing, and report complete-workflow paired uncertainty. A reproducible lower bound above one on representative cases is necessary, but a small isolated percentage alone would still need an application-specific reason to matter. Merely repeating the current nine-metric input or selecting a consumer because it gives a favorable fraction would not address the objection.
3. **Provide a substantive conceptual generalization.** A rigorously specified operator class or independently defined additional metric for which the complete-tie/dynamic-integral reduction yields a nontrivial result could broaden significance. Repackaging standard weighted PR, the already released ROC identity or additional implementations of the same operator would not meet this condition.

These are evidence routes, not a guarantee of acceptance or instructions to keep collecting repetitions until a desired score appears. If they are unsupported, the next defensible move is to present the work as a narrower exact-evaluation/optimization contribution and choose a publication format aligned with that scope. The current identified problems are significance and attribution, not a false central theorem or a defective experimental receipt.
