# Active-prefix VUS: venue and significance audit

Assessment date: 23 October 2026. Inspected checkout: `78974a3387b1600c31d5efaf56341a769d9618cb`. This is an internal critical assessment, not external peer review, an editorial decision, or an acceptance prediction. No experiments, submission, account changes, or external correspondence were performed.

## Decision

**PVLDB Regular Research, Foundations and Algorithms is a defensible category for this work, but category fit does not establish that the current paper clears its scope and contribution thresholds.** There is a substantive algorithmic result: preparation is charged once, the traversal depends on the actual saturated prefix, and a single-interval bound holds for every score ordering under the stated tie condition. The clearest vulnerability is the narrow incremental contribution and its limited demonstrated practical importance. The elementary singleton input-inspection lower bound does not resolve that concern.

For the current focused paper, **an experimental-algorithmics framing is the most natural scientific identity**. ACM JEA is a serious candidate for that identity, subject to verifying its current author requirements; this audit could retrieve only an older publisher call. TMLR has a more compatible stated standard for a modest, sound finding, but actual eligibility depends on its author-level submission budget, which includes desk rejections. JMLR is not an easier fallback: its reviewer guidance explicitly asks for a significant contribution and its scope favors a broader ML audience.

The strongest framing to investigate is a **first archival paper about the complete Sparse VUS evaluator**, with active-prefix traversal as its final refinement, provided the actual publication and submission history permits this. That can be scientifically stronger than restricting the entire contribution to the last increment over the author's public software. The strongest immediate improvement within either framing is to make the algorithmic delta and the useful workload regime unmistakable. Another round of favorable timing alone would not establish significance or repair the failed primary decisions.

## What the current paper actually establishes

The inspected sources are [the manuscript body](../paper/active_prefix_body.tex), [the algorithm proof](../paper/saturation_method.tex), [the mass and singleton results](../paper/saturation_mass_bound.tex), [the results](../paper/active_prefix_results.tex), [the complete control table](../paper/active_prefix_results_table.tex), and [the structural study](../paper/active_prefix_structural_results.tex). The [submission packet](active_prefix_submission_packet_20261021.md) and [earlier internal manuscript review](active_prefix_manuscript_review_20261021.md) provide context; they are not independent acceptance evidence.

| Evidence | Defensible significance | Limit |
|---|---|---|
| Exact-arithmetic `O(n + L + alpha(K) sum_w J_w)` evaluation with complete ties and dynamic denominators | Avoids a hidden width-by-support preparation charge; combines omission of inactive events, early saturation, activation, and component bookkeeping correctly at the stated abstraction level | An instance-sensitive upper bound; `J_w` can be the full support, and no uniform runtime dominance follows |
| `O(n + L P_0)` for one original interval and distinct support scores | Uniform over score ordering, so it is stronger than one favorable-score witness | No comparable general bound follows for multiple components; ties and delayed component coverage matter |
| Singleton `Theta(n)` for `L <= n` in the stated model | Establishes matching deterministic score-coordinate inspection order on a restricted class | The lower bound is basic input sensitivity; it is not general VUS optimality or a difficult new lower-bound technique |
| All three predeclared `L=30` runtime decisions fail | Useful negative evidence about overhead and the limits of traversal reduction | Cannot support a default-width speedup-success claim |
| External `L=300` medians over released radix: `1.506x` Mac and `1.627x` Linux, with `48/48` wins in each | Positive secondary/stress evidence for the new evaluator | Against matched last-positive stopping, the medians are only `1.136x` and `1.152x`; against the fastest measured control, losses remain `9/48` and `10/48` |
| External paired `L=30` supplement: `34.918x` over Benchopt, but `1.017x` over released paired radix with `19/48` losses | The complete implementation is useful relative to those external implementations | Most of this large library gap cannot be attributed to the active-prefix addition |
| Frozen protocols, oracle comparisons, negative controls, two environments | Stronger traceability and numerical evidence than a favorable benchmark alone | Internal agent checks are not independent laboratory replication; numerical parity does not certify exact floating-point stopping on all inputs |

For practical scale, the main paper already reports sums of 48 separately timed `L=300` calls: candidate/released-radix totals are `0.584/0.914` seconds on Mac and `0.738/1.388` seconds on Linux. Those absolute savings are useful context. They are not measured application runtimes and do not yet show that metric evaluation dominates an actual analyst workflow.

## Official PVLDB criteria and the manuscript's fit

The current call describes Foundations and Algorithms within Regular Research, with the principal contribution in formal foundations or algorithms. A prototype and experiments are encouraged; an implemented DBMS is not prescribed for this flavor. Time-series analytics is explicitly listed. [PVLDB 2027 research call](https://www.vldb.org/2027/call-for-research-track.html).

The current submission page assesses scope through three substantive tests: a data-management advance, engagement with database research, and evaluation grounded in motivating data-management applications. It explicitly says that related prior PVLDB papers and topic labels do not establish scope. [PVLDB volume-20 scope policy](https://vldb.org/2027/submission-guidelines.html).

| PVLDB test | Current evidence | Assessment |
|---|---|---|
| Foundations/algorithmic contribution | Formal target, exact event identities, incremental preparation, prefix bound, uniform restricted bound, pseudocode | A credible match to the category; the novelty and significance judgment remains open |
| Core data-management advance | Reducing exhaustive evaluation cost over stored score/label collections | Plausible analytics-operator optimization; the manuscript should make the workload and scaling benefit concrete |
| Substantive DB-literature connection | It preserves and analyzes the VUS operator from PVLDB and its optimized VLDB Journal treatment | Stronger than a decorative citation; a concise algorithm/cost comparison would make this directly inspectable |
| Evaluation in motivating data-management contexts | Real-source score arrays, full metric-call timings, controlled ablations | The weakest scope element: no measured collection-level evaluation workflow, operational bottleneck, or realistic width-selection rationale is established |

I did not locate a public volume-20 reviewer scoring form or a separate current acceptance rubric. The verified criteria above come from the current official call and scope policy. The predicted objections below are this audit's judgments, not quotations from an unseen review form. Historical PVLDB reviewer examples were not treated as current rules.

**EA&B is not a shortcut.** Its intended contribution is extensive evaluation yielding new insights about existing methods or workloads. The present paper's center is a new evaluator and theorem; reclassifying it would require a different research question and a much more comprehensive comparative study. SDS's deployed-system emphasis is also a poorer match. [Official category definitions](https://www.vldb.org/2027/call-for-research-track.html).

## Strongest plausible rejection case

An adversarial reviewer could reasonably conclude:

> The implementation and analysis appear careful, but the incremental idea is specialized early termination combined with established bookkeeping. The simple mass inequality and restricted input-reading lower bound do not establish a sufficiently broad algorithmic advance. The primary workload shows negligible gains against the author's existing implementation, and the strongest new practical results use secondary widths whose relevance is not demonstrated. Large external-library speedups mainly reflect earlier components. The paper therefore leaves the practical importance and broader data-management contribution underdeveloped.

This is a constructed review argument, not a quotation from an actual reviewer. It does not assert a false theorem. Its force comes from the contribution/evidence gap, especially when the abstract's largest asymptotic statement and the implementation's largest empirical ratios concern different comparisons.

The strongest response already present is that a stopping rule alone cannot avoid the preparation cost: the joint schedule provides an actual asymptotic separation, and the single-interval guarantee is uniform in score order. That deserves prominence. Still, reproducibility, honest negative findings, and mathematical correctness do not by themselves answer why this particular incremental result warrants PVLDB publication.

There is also a scope-dependent distinction: an earlier public software release or preprint is not automatically a previous refereed publication. If this is the first archival account of a broader exact-evaluation method, a disclosed synthesis may legitimately explain earlier ingredients as part of the overall research contribution. That would require reassessing the manuscript's complete claim set and overlap history; it would not justify attributing the entire external-library speedup to saturation. PVLDB explicitly distinguishes technical reports and website postings from disqualifying prior refereed publication. [Publication policy, originality](https://vldb.org/pvldb/general-information/publication-policies).

## Could the complete Sparse VUS method make a stronger first paper?

**Yes, conditionally.** The focused manuscript may be making its research contribution artificially small by treating the author's own unrefereed software as if it exhausted the publishable contribution. Publicly disclosed precursor work must be credited, but its mere public availability does not force the first archival article to report only the next software increment. Publication chronology and contribution scope are different questions.

A coherent paper can follow one question: how can the exhaustive scalar dynamic VUS operator be evaluated while avoiding work that cannot change its answer? The method has a natural sequence:

| Layer | Research content to explain | Correct evidence role |
|---|---|---|
| Exact event representation | Omitted inactive thresholds contribute ROC rectangles and zero PR area; global tied counts preserve the target | Establish mathematical equivalence to the specified exhaustive operator; show the counterexample to simply reconnecting retained ROC endpoints |
| Support-sensitive preparation and sweep | Count all scores against support events; use interval geometry and established fixed-key ranking to avoid repeated dense work | Compare with actual external exact-target implementations and matched dense/sorting controls; cite the earlier software version |
| Active-prefix refinement | Avoid width-wise full-support preparation and terminate after mass plus coverage saturation | State the adaptive bound and restricted uniform guarantee; compare against the released support sweep and matched stopping ablations |
| Practical complete evaluator | Return both ROC and PR, or PR alone, for the same semantic contract | Keep paired and PR-only protocols separate, show absolute times and losses, and explain which speedups belong to the whole method versus the final refinement |

The aggregate bounds form a comprehensible progression: comparison-based support evaluation `O(n log(Q+1) + (L+1)Q)`, fixed-key support evaluation `O(n + (L+1)Q)`, and active-prefix evaluation `O(n + L + alpha(K) sum_w J_w)`. This is a composition of metric-specific reductions with established sorting/data-structure techniques, not a claim that radix sorting, cumulative sums, or support restriction are newly invented.

Under that framing, the `34.918x` Benchopt paired median and the `101.106x` DTAI completed-subset median are relevant whole-implementation comparisons. DTAI still has only ten completed series and two censored cases; no twelve-case median is justified. The primary `L=30` failure belongs to the **incremental active-prefix hypothesis against its eight controls**. It must remain visible, but it does not establish that the preceding support-sensitive method failed every separate hypothesis. Conversely, an external-library ratio alone does not isolate the algorithm from compilation, memory layout, and other implementation differences. Matched controls remain essential.

There is a broader predecessor manuscript in [paper/main.tex](../paper/main.tex), labeled “Working manuscript; unsubmitted” and titled *Support-Sensitive Exact VUS Evaluation*. Its abstract reports 308 series from 17 families, two CPU runs, and successful separate five-control primary criteria for the radix support evaluator. Those claims were **read but not independently re-audited in this venue assessment**. They should enter a combined article only after their exact protocols, source versions, controls, and receipts are reconciled with the active-prefix study. Do not pool overlapping datasets or quietly present development inputs as a new external confirmation.

TMLR author-level eligibility must be verified privately against the current annual submission budget; no eligibility is inferred from the paper's scientific fit.

My judgment is that this integrated framing is **more promising for PVLDB Foundations and Algorithms than the incremental-only paper**, provided the earlier components remain scientifically original relative to external literature and the actual publication history permits it. It also fits JEA's algorithm-engineering identity. It does not automatically satisfy PVLDB scope or significance: operator-level workload importance, prior-art distinctions, and clear attribution still matter. Keep unrelated width-enclosure/model-selection branches out of the central story unless they are necessary to answer the same research question; adding every previous experiment would reduce coherence.

## Selected alternatives

| Venue | Scientific fit | Main obstacle | Appropriate positioning |
|---|---|---|---|
| **PVLDB Regular Research / Foundations and Algorithms** | Defensible for an exact time-series analytics operator with a formal adaptive algorithm | Narrow incremental significance; insufficiently demonstrated workload importance; scope remains editorial | Lead with preparation-free prefix evaluation and an explicit useful workload regime; retain all primary failures |
| **ACM Journal of Experimental Algorithmics** | Natural fit for algorithm design, implementation, controlled evaluation, and reusable code | A specialist venue still needs algorithmic insight beyond a local optimization; current submission requirements were not retrievable here | Center on the mechanism, parameter-dependent crossover, complete ablations, and interpretable negative results |
| **TMLR** | Sound evaluation-method findings can fit | Author-level eligibility requires a private check; limited contribution breadth | Focus on supported insights rather than a required SOTA claim |
| **JMLR** | Evaluation methods can fall within scope | Its broader-audience and significance expectations make this narrow kernel optimization a difficult fit | Consider only after a materially broader ML evaluation contribution; changing the template is insufficient |

TMLR's criteria prioritize evidential support and clear findings of interest to part of its audience; they explicitly reject state-of-the-art performance and novelty as necessary acceptance tests. That makes a modest result more compatible with its stated standard, not automatically acceptable. [TMLR acceptance criteria](https://jmlr.org/tmlr/acceptance-criteria.html).

TMLR author-level eligibility must be verified privately against the current annual submission budget; no eligibility is inferred from the paper's scientific fit.

JMLR seeks principled ML methods and insight and may reject work whose audience is too narrow. Its reviewer guide asks whether the contribution is significant and sufficiently different from prior work. Those requirements do not make it a natural lower-risk substitute for PVLDB. [JMLR scope](https://www.jmlr.org/author-info.html), [reviewer guide](https://www.jmlr.org/reviewer-guide.html).

For JEA, the accessible publisher call describes empirical study of discrete algorithms/data structures through design, implementation, performance evaluation, and classical analysis, including ML applications. This is a **historical 2020 call**, not verified 2026 instructions. Both the JEA site and ACM Digital Library pages returned access errors/403 in this audit, including a direct HTTP check. Consequently, current submission format, charges, AI policy, and administrative eligibility are **UNKNOWN** here. [Publisher call hosted by ACM BCB](https://acm-bcb.org/2021/documents/jea-cfp-08-2020.pdf), [current journal entry](https://dl.acm.org/journal/jea).

## Content that would materially improve the case

1. **Add one compact contribution/cost table.** Compare the pinned original/optimized VUS, Klein, released sparse radix, active full scan, last-positive stopping, and the candidate. State the exact output contract, per-width preparation, traversed events, tie handling, and what is inherited versus new. Use proven or source-supported costs only. This makes the conceptual contribution reviewable without enlarging the claims.

2. **Connect the bound to the observed input regimes.** From existing frozen profiles, report `P_0`, `K`, support fraction, active tie sizes, and coverage-prefix behavior alongside work and runtime. Explicitly count which real cases meet the single-interval distinctness hypothesis. Explain why delayed coverage or pointer/preparation overhead defeats savings. Such analysis must be labeled descriptive, not newly preregistered confirmation.

3. **Establish a motivating workload before making practical-impact claims.** A bounded, reproducible batch evaluation over stored detector outputs can measure metric share of runtime, throughput, absolute saved time, and memory. Choose width ranges from the evaluation task or published practice before measuring outcomes. Preserve `L=30` as the failed original primary test and label any new protocol separately. A DBMS integration is not inherently required; merely renaming the scalar call an analytics system is insufficient.

4. **Separate the three kinds of contribution on the first page.** State the adaptive algorithmic advance, the restricted uniform theorem, and the empirical result with different scopes. Keep elementary input-inspection optimality subordinate to the main algorithm. Keep secondary-width gains and earlier-baseline advantages separate.

5. **Make the practical lesson portable.** Identify conditions under which a user should expect little gain and those under which the evaluator is worthwhile. A runtime selector would require its own prospective evaluation; the fastest-of-eight comparison is an analysis device. Do not propose selection guarantees based on choosing the best method after timing.

6. **Retain the numeric contract and failures.** The present distinction between exact mathematical integrals and finite-precision execution is necessary. Oracle tests do not establish all-input rounding guarantees. Keep all slower cases, timeout censoring, the small external corpus, and cross-platform score differences visible.

Items 1, 2, and 4 primarily improve explanation or analyze existing evidence. Item 3 is additional research if the paper seeks a stronger practical/data-management claim. These are recommendations based on the identified weaknesses, not invented venue-mandated experiments. None should be used to erase or repeatedly retest the existing primary failures.

## Submission integrity

Authorship, current affiliation, account counters, conflicts, concurrent review and author approval are checked in the private submission workflow. AI assistance is disclosed in the manuscript. Scientific fit does not establish these facts.

**Recommendation:** first verify whether a complete-method first archival article is permitted by the actual publication/submission history. If it is, develop that coherent framing for PVLDB Foundations and Algorithms while keeping the active-prefix failures and precursor chronology explicit; it presents a stronger scientific case than the incremental-only draft. If the contribution must remain focused on active-prefix evaluation, improve the explanatory delta and workload relevance before treating it as a strong PVLDB submission. Investigate JEA as the closest disciplinary alternative, and consider TMLR only after eligibility is verified. No venue choice supplies the missing human/account facts or guarantees acceptance.
