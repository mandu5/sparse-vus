# Scientific assessment of Sparse VUS, 20 October 2026

This is an adversarial internal research assessment by a separately assigned
AI agent in the same development session. It is not external peer review,
priority certification, a venue decision, or a prediction of acceptance.
Author metadata and submission administration are outside this assessment.
No numerical kernels, timing experiments, outbound contacts, or paid compute
were run for this review.

The inspected branch was `research/certified-width-20261020`, with HEAD
`67e622b45e3fca1378215cc5f3ca3e804e4b7a9b`;
the manuscript/width files had uncommitted changes. Conclusions below
concern the files inspected during this session, not an immutable release.
The follow-up review below inspected the racing implementation at source
SHA-256 `71ea48e7a212fcc861eee49f9aaa352ef793054ffb61479ade155c63add4d39b`.
The fixed-width experiment is now complete; complete selection/racing
outcomes remain pending.

## Recommendation

**Continue through one decision-latency experiment, then make a submission
decision. Do not currently advertise global SOTA or established PVLDB
readiness.** The exact evaluator has a defensible, bounded algorithmic claim
and useful published-code results. The merge-aware width method supplies a
more substantial conceptual extension, but its practical contribution was
initially unmeasured. The completed fixed-tolerance width experiment now
shows a restricted benefit: the 0.01 setting is slower at widths 30 and 100
and faster at width 300; the 0.001 setting is slower at every tested width.
This does not support a general adaptive-evaluation speedup claim.

The new incremental PR race is a coherent, disclosed post-hoc response to
fixed-tolerance overhead. Source and proof inspection found no blocking
real-arithmetic correctness defect. Its complete decision latency is still
unknown, so its existence does not upgrade the submission recommendation.

If aiming at PVLDB, **Regular Research / Foundations and Algorithms** is the
appropriate category. The present paper is substantially more coherent in
that category than EA&B. My current scientific recommendation would be
**not ready for submission to PVLDB**, with significance and experimental
utility the central unresolved issues; I do not identify a demonstrated
mathematical failure from the inspected material.

If the decisive experiment is negative, preserve the exact evaluator and the
negative result instead of enlarging the project indefinitely to rescue a
venue target. A tightly scoped TMLR paper on reliable, efficient evaluation
of anomaly detectors is a more defensible alternative to investigate.
TMLR acceptance is not established either.

## What has and has not been established

| Question | Evidence at this snapshot | Scientific interpretation |
|---|---|---|
| Is sparse exact evaluation merely a sampled metric? | The manuscript specifies the pinned all-threshold scalar target, tie semantics, inactive ROC rectangles and terminal point; numerical parity checks are recorded. | No. It computes a different resolution contract from the default 250-threshold approximation while preserving the pinned all-threshold definition. |
| Is support restriction or prefix accumulation new? | Official VUS optimization and Klein fast-VUS already use these ideas; the prior-art audit documents actual code. | No. Those cannot be counted as new contributions. |
| Is there a narrower exact contribution? | Support-event integration and off-support rank counting give the stated support-sensitive upper bound. | Yes, a credible candidate contribution under the specified metric semantics. The derivation is more informative than a speed ratio alone. |
| Does it beat an actual external optimized implementation? | Against unmodified Klein full-threshold PR: median 4.553x on Linux and 8.377x on macOS; faster in 2,100/2,100 conditions on each. | Strong scoped results on two platforms. Sparse returns ROC and PR; Klein returns PR. This is not evidence against every implementation or hardware regime. |
| Is it uniformly fastest among tested algorithms? | Against the per-case fastest of three dense methods and Klein: Linux median 1.347x, faster in 1,526/2,100; macOS median 2.043x, faster in 1,891/2,100. | No. The 574 Linux and 209 macOS slower conditions belong in the main result. Minimum ratios are 0.363 and 0.402 respectively. |
| Are merge-aware bounds conceptually sound? | The independent in-session review validates the coordinate ordering, PR p-box construction and discrete averaging invariant in real arithmetic. | A substantive method candidate, with a precise mathematical scope. This review is not a second laboratory reproduction. |
| Does the implementation provide a formal Float64 certificate? | Ordinary Float64 with an empirical guard; no directed rounding or accumulated-error proof. | No. Numerical audits support measured decisions only. |
| Is threshold approximation sensitivity explained solely by padding? | PR reversals persist under both fixed corrections: 84 original, 93 fill, 95 suffix; five per variant have both margins at least 0.01. | No. However most changes are small, and none establishes which detector is operationally better. |
| Do the adaptive bounds save useful work? | The completed 378-case macOS experiment has median ratios 0.966 at tolerance 0.01 and 0.467 at 0.001. The 0.01 setting reaches 1.313 at width 300, but loses at widths 30 and 100. Complete selection and racing outcomes remain pending. | Width omission is mathematically useful but is not yet a general practical speedup. Fewer queried widths alone is not an answer. |

The numbers above were read from
`artifacts/advancement/linux-baseline/summary.json` and
`artifacts/advancement/mac-baseline/summary.json`. Both summaries record zero
violations and maximum parity error `3.6914915568786455e-13`. Their existing
PASS labels and recorded parity are evidence from the producing workflow;
this reviewer did not independently rerun or complete the separate provenance
gate. The later `artifacts/advancement/analysis/analysis.json` now records
PASS for the post-run provenance gates on both exact-platform runs and the
fixed-width run; this reviewer read those gate summaries, not a fresh
independent rerun. The two-platform replication strengthens the scoped
exact performance finding without establishing selection utility.
The padding figures were checked against the local experimental audit.

## Novelty and coherence

The coherent central question is:

> Which contributions to a two-axis VUS integral can be integrated exactly,
> and which remaining contributions can be omitted with a bounded error?

The threshold result answers the first part using a support-sensitive
sufficient state. The width result answers the second using merge geometry,
coordinate ordering and a recall-distribution representation. Both target the
same discrete scalar integral, and the exact method supplies endpoint
evaluation and the exact fallback. This is a natural algorithmic composition,
not an unrelated appendix attached to an optimization paper.

The strongest new insight is the structural distinction between ROC and PR
inside merge-free blocks. ROC area has the required order, but PR scalar
endpoints can fail even without a merge. The PR counterexample makes the
need for a richer bound concrete. Applying an established p-box construction
to that specific structure is an intellectually coherent contribution even
though p-box extrema, monotone queues and adaptive subdivision are prior art.

The weakness is quantitative. The adaptive complexity
`O(n log(Q+1) + mQ + m log m)` is conditional on the number of queried widths
`m`; there is no guarantee that `m` is substantially below `L+1`, and curve
allocation, p-box work and endpoint recomputation cost time. It is not a
proved sublinear-in-width algorithm in the worst case. If it almost always
falls back or merely saves trivial amounts of absolute time, it remains a
correct extension but becomes a weak practical main contribution.

The exact result alone is less novel than the original framing might suggest.
Klein anticipates important ingredients. Generic curve compression also
predates this work. The defensible delta is the complete VUS-specific state
and integration identity, its treatment of negative runs and ties, and the
support-sensitive preprocessing and sweep bound. Neither support sorting nor
“dropping unimportant points” should headline the novelty claim.

The 4.553x comparison mixes algorithmic and implementation choices, including
NumPy versus compiled code. It supports a runtime claim about those executable
implementations. It does not isolate a 4.553x causal effect from event
elimination. The compiled dense controls and existing global-sort ablation
are therefore scientifically valuable even when their speed ratios are less
impressive.

The Sylligardos CPU/GPU result must remain cited and unresolved. Its unavailable
mechanism prevents a global fastest or exclusive-priority claim. It is not a
reason to demand an endless search or contact authors before any bounded
paper can be written.

## Ranked scientific blockers

### 1. The new width method has not demonstrated a useful decision-cost gain

This is the most important remaining experiment. A certificate can be valid
and still cost more than computing the answer, as the completed fixed-width
experiment now demonstrates. Fixed tolerance also need not be tight enough
to distinguish nearby detectors. Metric-only certificate measurements do not
by themselves measure a complete exact-compatible model-selection task with
all fallback work included. The fixed-tolerance selector and subsequent
incremental race must retain separate source, timing and outcome records.

**Closure:** run the single frozen selection experiment below. It should be
allowed to fail. Report absolute milliseconds, totals, width-specific gains,
fallback fractions, and all losses.

### 2. Significance is not established by corpus size or relative speed alone

The existing public study is a valuable correctness and performance corpus,
but it contains three fixed detector score vectors per series and short
original width budgets. It is not 2,100 independent applications. The earlier
audit's sum of metric medians shows that absolute savings can be small;
this cannot be translated into end-to-end inference or operational savings.
Most observed ranking reversals also have small margins.

**Closure:** state one actual computational task and measure its full cost.
The proposed selection task is enough for this continuation; training new
models, adding a GPU system, or gathering user adoption are not prerequisites.
If gains arise only at width 300, call that a stress regime unless its scale
is justified for the inspected data. The original VUS paper permits widths
based on period, anomaly length or user choice; that general permission does
not establish width 300 as appropriate for every dataset.
[VUS definition and buffer discussion](https://arxiv.org/html/2502.13318v1#S4)

### 3. Novelty must survive the strongest disclosed prior art

The manuscript now appropriately credits Klein and the official optimized
VUS paper. Retain that treatment, the real external baseline, and the dense
negative cases. A claim such as “first fast VUS” would contradict known prior
art. A claim about all disclosed implementations requires a broader
comparison than has been completed.

**Closure:** make the narrow algorithmic delta explicit in the introduction,
comparison table and conclusion. No new baseline hunt is required for this
bounded decision; the unresolved Sylligardos mechanism remains a limitation.
[Klein source at the audited revision](https://github.com/tomlouisklein/fast-VUS/blob/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py)

### 4. “Certified” can overstate what the executable artifact guarantees

The theoretical bound is deterministic in real arithmetic. The current
Float64 guard is empirical, and finite tests do not convert it into a proved
rounding enclosure. Requiring a larger decision gap reduces sensitivity in
the measured audit but cannot establish an all-input guarantee.

**Closure:** continue using “error-bounded in real arithmetic” and
“numerically audited bound-separation decisions.” Make this distinction in
the abstract, API description, result tables and decision experiment.
Formal interval arithmetic would be a different additional project; it is
not required if the present claims remain accurately scoped.

### 5. PVLDB scope and audience benefit require a concrete argument

PVLDB 2027 requires a core data-management contribution, a substantive
connection to database research and evaluation in an appropriate
data-management context. An earlier VUS paper in PVLDB is relevant ancestry,
but the current policy explicitly says ancestry or topic labels alone do
not settle scope. The concrete opportunity here is scalable, reproducible
evaluation over labeled time-series collections and candidate models.
[PVLDB 2027 scope policy](https://www.vldb.org/2027/submission-guidelines.html)

**Closure:** connect the algorithm and measured selection workload to that
evaluation problem without inventing a deployment. It is a plausible scope
case, not a confirmed editorial judgment. More rhetoric cannot compensate
for an unhelpful experiment.

## Decisive workload: time to an audited exact-compatible PR selection

The root agent proposed the following bounded protocol after the initial
recommendation and before inspecting its pipeline outcomes. This reviewer
endorses it with the qualifications below. It reuses the frozen 42-series
metadata-only selection; it does not select favorable score patterns.

**Task.** For each of 42 series and maximum widths 30, 100 and 300, select the
highest-PR detector among the same three released score vectors. There are
126 selection tasks, not 378 independent tasks. Preserve all cases,
including ties and cases where exact computation is already cheap.

**Proposed algorithm.**

1. Starting from the same raw arrays, compute `certified_vus(atol=0.01)` for
   all three detectors, including preparation cost.
2. Return a unique winner only if its lower PR bound exceeds every other
   upper PR bound by more than `3e-10`.
3. Otherwise remove only candidates whose upper bound is below the largest
   lower bound by more than `3e-10`, then compute exact PR for all retained
   candidates. Return every retained candidate within `1e-10` of the
   resulting maximum.
4. Audit the complete returned winner set against all-three exact PR values.
   Report any mismatch as failure; do not mask it with aggregate accuracy.

The `3e-10` gap is conservative relative to the experiment's two `1e-10`
per-model containment allowances plus its `1e-10` tie convention. It is an
empirical-audit convention, not a forward-error proof. The current API
refines both ROC and PR even though this task needs PR; report that design
choice rather than silently treating the pipeline as PR-optimized.

**Comparators.** Time complete all-three evaluation using sparse exact,
unmodified Klein exact PR, and the compiled dense exact implementation(s).
Include the actual 250-threshold method as an approximate speed-versus-error
comparator. It has a different output contract and cannot be counted as an
incorrect implementation of the all-threshold target.

Each fixed comparator is executable. A per-case minimum over comparator
times is an oracle reference; label it as such rather than claiming a
deployable “fastest baseline.” Audit numerical parity at all three width
budgets, because old width-10/30 receipts do not validate width 100/300.

**One useful ablation, if the pipeline is implemented.** On unresolved
cases, disable candidate pruning and compute all three exact results after
the same initial bounds. This distinguishes savings from early winner
resolution and savings from eliminating candidates. Do not add a tolerance
sweep or further detector families to this decisive experiment.

**Timing.** Measure the full pipeline call, including bounds, preparation,
candidate handling and fallback, with the same single-thread, serial,
randomized three-repetition protocol. Do not reconstruct pipeline latency by
summing separately timed components. Exclude source loading and JIT warmup
equally and state that this is an evaluator/selector workload, not detector
inference latency.

**Required output.**

- Exact-compatible winner-set agreement and separately counted approximate
  winner-set disagreements; show ties explicitly.
- Whole-task median and sum of measured task medians, saved milliseconds,
  wins/losses, worst slowdowns, and width-specific results.
- Fraction resolved without fallback, number of candidates pruned, and number
  of exact evaluations after bounding.
- Actual curve evaluations as well as distinct queried widths, merge-block
  count and support fraction for explaining observed break-even behavior.
- Whole-series aggregation; the three width budgets and three models are
  repeated measurements on a series. Family-stratified descriptive results
  should retain families with no observed gain.

**Falsifiable interpretation.** A wrong bound-separation decision fails the
measured reliability claim. Correct decisions accompanied by no total
runtime gain over sparse exact fail the practical selector-acceleration
claim for this workload. Gains confined to large widths support only that
regime. Gains over Klein alone, while losing to the strong exact local
baseline, do not establish a useful reason to choose adaptive evaluation.
Broad gains over the strongest exact implementations, meaningful absolute
savings and low fallback rates would materially strengthen the PVLDB case.
There is no numerical speedup threshold that guarantees acceptance.

If this experiment is negative, the next action should be to narrow the
paper's practical claim or choose a different venue, not automatically to
invent a larger benchmark.

## Completed fixed-width result and bounded racing follow-up

The 378-case fixed-width experiment ran on an Apple M1 Pro, macOS arm64,
Python 3.12.4. Ratios below are sparse-exact time divided by bounded-method
time, so a ratio below one favors the exact baseline. Every width/tolerance
row contains 126 model evaluations over the same 42 series.

| Tolerance | Maximum width | Median speed ratio | Faster evaluations | Unique winners resolved from intervals / 42 |
|---|---:|---:|---:|---:|
| 0.01 | 30 | 0.835 | 27 / 126 | 21 |
| 0.01 | 100 | 0.905 | 46 / 126 | 17 |
| 0.01 | 300 | 1.313 | 100 / 126 | 15 |
| 0.001 | 30 | 0.615 | 4 / 126 | 33 |
| 0.001 | 100 | 0.426 | 11 / 126 | 32 |
| 0.001 | 300 | 0.391 | 25 / 126 | 34 |

Across all 378 evaluations, tolerance 0.01 has median ratio 0.966 and wins
173 cases; tolerance 0.001 has median ratio 0.467 and wins 40. The analysis
records zero incorrect interval-separated pairs or winners and zero
containment/tolerance violations under its numerical audit. Its ranking
margin is `2e-10`, whereas the later selection/racing margin is `3e-10`;
the tables therefore do not predict the later pipeline's exact early-stop
counts.

The method can query few widths and still lose: at width 30/tolerance 0.01
the median queried fraction is about 16%, yet the median runtime ratio is
0.835. Tighter intervals improve decision coverage but substantially increase
cost. The width-300 gain coincides with only 15/42 interval-resolved unique
winners at tolerance 0.01. This is direct evidence that scalar approximation
cost and complete decision cost are different objectives.

These figures were read from `artifacts/advancement/analysis/analysis.json`,
`mac-certified/summary.json` and `mac-certified/environment.json`. The
analysis binds certified measurements to
`32000ea30f876f47c4b421912c6f77b0902b5f0e396acc78d482ec3a544f11d4`.
The complete fixed-tolerance selection experiment is still necessary to
measure fallback cost; the table above is not that result.

The follow-up `race_pr_models` addresses three specific costs: it keeps each
model's preparation, refines according to PR uncertainty rather than a joint
ROC/PR tolerance, and obtains exact values from accumulated widths instead
of restarting an exact evaluator. It still computes ROC coordinates in the
shared endpoint oracle. “PR-directed refinement” is accurate; “computes only
PR operations” is not.

This is a **post-hoc algorithm-design iteration on the same inspected
workload**, not a preregistered independent confirmation. Fresh timings can
honestly compare the final algorithm to its baselines on that workload, but
they do not remove the dependence of the design on earlier outcomes.
Preserve the fixed-width and fixed-tolerance selector results, freeze the
race before measuring it, and retain the same 126 selection tasks. No new
dataset, tolerance search or favorable subset is needed for this follow-up.

### Racing proof and source findings

No blocking defect was identified in the inspected real-arithmetic
algorithm/proof:

1. **Separation checks every model.** A candidate lower bound above all
   other upper bounds by `3e-10` implies a unique maximum outside the
   `1e-10` tie set.
2. **Screening preserves the complete tie set.** An upper bound below the
   greatest lower bound minus `3e-10` implies that model is more than
   `3e-10` below some feasible competitor and therefore below the global
   maximum. It cannot be an exact-tolerance tie.
3. **Refinement preserves the partition.** Each heap item represents only
   its unevaluated interior; the midpoint replaces one unknown width with
   its scalar value and leaves disjoint child interiors. A refinement
   adds exactly one previously unseen width.
4. **Exact resolution terminates.** When all current candidates are fully
   evaluated, their existing per-width values determine the tie set.
   Otherwise each step adds a width. At most `M(L+1)` unique model-width
   evaluations are possible, and valid intervals cannot screen out every
   model.
5. **Reported work is consistent.** With the default eight-curve cache,
   one refinement computes its new midpoint and at most two evicted
   endpoints. Actual curve evaluations, unique widths and preparation
   counts remain separate quantities.

One source-level nuance is worth preserving: candidates are recomputed
from all models at each iteration. The implementation does not store a
permanently shrinking active set. Thus “screened at this iteration” or
“excluded from the final candidate set” is more precise than claiming
permanent deletion. Correctness and finite termination do not require
candidate-set monotonicity.

The Float64 implementation updates running sums by additions and
subtractions; repeated two-term `math.fsum` calls do not establish a global
outward-rounding bound. The existing empirical guard and explicit numerical
scope remain essential. The exact tie-resolution path can also differ by
roundoff from another implementation near the tie boundary, so the fresh
all-model exact comparisons are necessary.

The source audit is not an additional formal verification or independent
numerical reproduction. GitHub run `39426662776` was read live and reports
successful Linux Python 3.11/3.12 jobs at commit
`cb2b60d633c4b7ee3be50644864bde20fd022296`. That CI status supports its
executed checks; it does not establish new runtime results.

**Current gate:** finish and analyze the already authorized fixed-selector
and racing runs, including separate executable exact baselines. Racing
latency, its winner-set agreement on all 126 tasks, absolute savings and
worst losses remain unknown in this review. A favorable result would
strengthen a narrow practical contribution; it would not by itself establish
global SOTA, external reproduction or venue acceptance. A negative result
should narrow the main practical claim rather than trigger an open-ended
series of further method variants.

## Venue comparison

| Venue or category | Fit judgment | Qualification |
|---|---|---|
| PVLDB 2027 Regular / Foundations and Algorithms | Correct PVLDB category and a credible stretch target if the decision experiment demonstrates useful gains. | Its core contribution can be algorithmic and formal, but scope, novelty and benefit remain review questions. |
| PVLDB EA&B | Poor fallback for the present paper. | The main scientific result is a proposed algorithm. The current three-model corpus is not a comprehensive evaluation paper yielding broad new conclusions about existing methods. |
| TMLR | Most defensible alternative to investigate now for the bounded paper. | Frame the work as reliable numerical evaluation of anomaly detectors and explain the actionable lesson for ML evaluation. Its official criteria prioritize evidence and audience interest, explicitly not SOTA or novelty alone. This is not a promise of acceptance or of a conference presentation. |
| ALENEX | Particularly good thematic fit for the algorithm-engineering version. | Official scope emphasizes implementation and extensive experimental analysis of nontrivial algorithms. ALENEX27's July 20, 2026 deadline has passed; a future cycle requires a new live deadline check. |
| JOSS | Not an automatic immediate route. | The current policy asks for demonstrated research impact and substantive research software, and excludes minor/single-function utilities. A clean release and many tests alone do not establish this fit. |

PVLDB's category descriptions distinguish algorithmic/formal work from
extensive studies of existing methods.
[PVLDB 2027 research categories](https://www.vldb.org/2027/call-for-research-track.html)
TMLR uses rolling submission and its published acceptance criteria require
supported claims and clear interest for its audience.
[TMLR overview](https://www.jmlr.org/tmlr/),
[TMLR acceptance criteria](https://www.jmlr.org/tmlr/acceptance-criteria.html)

TMLR's criteria also say that a fully AI-generated paper with little or no
human involvement is unlikely to meet the audience-interest criterion.
This is not a categorical ban on AI assistance, nor does it mean correctness
alone suffices. Its policy allows LLMs as assistive tools while requiring
human authors to make a substantial intellectual contribution, draft or
revise the work, and take responsibility for its complete content; LLMs
cannot be authors. This agent review and automated tests do not establish
that a human has met those conditions. Human authorship and substantive
engagement remain unverified here, so TMLR is an alternative to assess,
not a ready submission channel.
[TMLR acceptance criteria](https://www.jmlr.org/tmlr/acceptance-criteria.html),
[TMLR LLM and authorship policies](https://www.jmlr.org/tmlr/editorial-policies.html)

ALENEX's subject fit and closed 2027 deadline are explicit in its official
pages.
[ALENEX27 scope](https://www.siam.org/conferences-events/siam-conferences/alenex27/),
[ALENEX27 submissions](https://www.siam.org/conferences-events/siam-conferences/alenex27/submissions/)
JOSS's current scope is more demanding than merely publishing a tested
package.
[JOSS scope and requirements](https://joss.theoj.org/about)

The ordering above is a scientific fit assessment. It is not a claim that
any venue has endorsed this work, that one venue is easy, or that a journal
acceptance would satisfy a conference objective.

## Review scope and evidence

The main local evidence inspected was:

- `docs/fast_vus_prior_art_20261020.md`
- `docs/theory_advancement_20261020.md`
- `docs/certified_independent_review_20261020.md`
- `docs/advancement_experiment_review_20261020.md`
- `docs/experimental_audit_20261020.md`
- `paper/main.tex` and `paper/width_method.tex`
- `experiments/benchmark_advancement.py`, relevant analysis functions and the
  certificate interface
- `artifacts/advancement/linux-baseline/summary.json` and
  `artifacts/advancement/mac-baseline/summary.json`
- `artifacts/advancement/analysis/analysis.json` and the fixed-width summary
  and environment
- `src/sparse_vus/racing.py`, its selection/width dependencies,
  `tests/test_racing.py` and `docs/incremental_pr_racing_20261020.md`

The existing review supports the real-arithmetic mathematics; this review
evaluates the resulting scientific story and experiment sufficiency, and
the follow-up directly inspects the racing invariant and implementation.
Fixed-width timings are now available; complete fixed-selector and racing
outcomes remain pending. Future successful measurements can change the readiness judgment;
they cannot retroactively make this review external peer review.
