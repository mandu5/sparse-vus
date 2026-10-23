# Focused PVLDB paper assessment — 21 October 2026

**Recommendation:** develop one focused Foundations and Algorithms paper around
exact, instance-sensitive VUS evaluation. The active-prefix construction is a
more credible research contribution than another radix implementation speedup.
The newly derived single-component mass bound strengthens it further. Neither
acceptance nor broad practical superiority follows. The later outcome review
below records **failed primary criteria in both partitions**, together with
positive, prespecified high-width secondary results. A narrow theory-led paper
remains plausible; a general practical-superiority claim does not.

This review read `paper/saturation_method.tex`, the existing prior-art audits,
`docs/saturation_external_design_20261021.md`, and the frozen-runner design. It
initially performed only lightweight source/document retrieval. After the
controlled runs completed, it read their reports and summarized the existing
work profiles. A separately authorized, frozen paired-output supplement was
then executed; its findings appear at the end. There was no submission,
account action, or author contact.

## Venue fit and the strongest defensible claim

PVLDB 2027 explicitly includes time-series analytics and a Foundations and
Algorithms flavor of Regular Research papers. Its scope nevertheless requires
a substantive data-management problem, connection to database research, and
evaluation in that context. The suitable problem is scalable evaluation of
stored anomaly-score collections across complete tolerance/threshold grids.
The VLDB Journal VUS algorithms are direct predecessors, rather than decorative
database citations. This is a fit argument, not assurance of scope acceptance.
[Official call](https://www.vldb.org/2027/call-for-research-track.html)

Suggested title: **Active-Prefix Evaluation of Exact VUS**.

The strongest plausible central claim is:

> We evaluate a pinned exhaustive VUS contract by activating support positions
> across widths and scanning complete score ties only until buffer mass and
> component coverage saturate recall. The algorithm avoids width-wise
> maximum-support initialization and costs
> `O(n + L + alpha(K) * sum_w J_w)` with `O(n+Q)` auxiliary storage. A family
> separates it asymptotically from the same activation engine using a
> last-original-positive cutoff. Under a stated no-active-ties condition,
> single-component inputs also admit a uniform `O(n + L*P0)` guarantee.

The empirical continuation must name the measured workload, platform, output
contract, ratios and losses, retaining the primary failures recorded below.
Do not replace that with “SOTA,”
“optimal,” “first fast VUS,” or a claim about all range-aware ranking metrics.
`J_w` measures work on an input instance; the scalar output has fixed size,
so **instance-sensitive** is more precise here than output-sensitive.

## The stronger uniform guarantee

The theoretical follow-up communicated during this review is valid under its
stated conditions. It should be made a short theorem/corollary in the paper,
not left as an additional synthetic benchmark anecdote.

At a fixed width, each visited active original-positive position increases
`A+B/2` by one. Each active non-original position has weight at least
`1/sqrt(2)`, and therefore increases `A+B/2` by at least `1/(2*sqrt(2))`.
Consequently the mass condition is met after at most
`m = ceil(2*sqrt(2)*P0)` active positions, unless the complete active support
is exhausted earlier. For one original interval, every width has one expanded
component; its first active position already supplies the existence condition.
With distinct converted support scores,

```
J_w <= min(Q_w, ceil(2*sqrt(2)*P0)).
```

The full bound becomes `O(n + L*P0)`. For a singleton anomaly it is
`O(n+L)` for every score ordering, including an adversarially late original
positive. This is stronger than showing one favorable ranking. It still does
not prove an optimal lower bound for the scalar integration problem.

Three qualifications are essential:

- Distinctness concerns numerical scores **after Float64 conversion**. A large
  active tie can force traversal beyond `m`; off-support ties affect global
  counts but do not themselves increase active visits.
- With multiple components, let `C_w` be the first active-prefix length that
  hits every component. A valid bound uses the end of the complete active tie
  containing `max(min(Q_w,m), C_w)`. Component coverage can be the bottleneck.
- The general bound is not a uniform worst-case improvement over the existing
  `O(n+(L+1)Q)` evaluator. Full prefixes and data-structure overhead remain
  possible. The single-component result does not remove those general cases.

The algebra is simple, but it identifies a genuinely stronger parameterized
guarantee for this metric. The algorithmic work is achieving it without first
paying for a complete per-width support histogram. This is the argument to
foreground over the binary64 radix implementation.

## Closest prior art and the serious reviewer objections

Boniol et al. already introduce static/dynamic reuse and maximum-buffer support
restriction. Their displayed Algorithms 2–3 retain threshold-by-width work.
The new paper must say exactly which work remains there and which active-prefix
construction removes it. It must not rebrand support restriction as new.
[VLDB Journal paper, Section 4.3](https://www.paparrizos.org/papers/BoniolVLDBJ25.pdf)

Klein is the closest inspected exact-compatible external implementation: sorted
support scores, cumulative weighted sums and the dynamic denominator are
already present. Its per-width complete-support cumulative sums and global
threshold arrays differ from the proposed active-prefix computation.
[Pinned fast-VUS source](https://raw.githubusercontent.com/tomlouisklein/fast-VUS/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py)

Full-recall truncation is explicit in scikit-learn 1.0.2. Reversible list
deletion/restoration is established in Knuth's Dancing Links, which itself
credits earlier work. These make the matched last-positive ablation and clear
attribution indispensable; neither mechanism alone is a new invention.
[scikit-learn source](https://raw.githubusercontent.com/scikit-learn/scikit-learn/1.0.2/sklearn/metrics/_ranking.py),
[Knuth's manuscript](https://arxiv.org/pdf/cs/0011047)

The central remaining objections, and evidence that would answer them, are:

| Objection | What is needed; what would defeat the stronger claim |
|---|---|
| “This is an obvious cutoff plus standard data structures.” | Present the uniform single-component guarantee, full accounting of activation/DSU/preparation, and the strict separation from matched last-positive stopping. If practical gains disappear against that control, describe the outcome as a structural result with limited incremental utility. |
| “The new theorem hides full-support work.” | Include pseudocode that makes radius scheduling, complete ties, epoch hits and constant-time restoration visible. The existing reviewed implementation avoids a per-width `Q`/`K` reset; future revisions must preserve that property. |
| “Only a hand-built ranking benefits.” | Show `sum J_w / sum Q_w`, saturation-versus-last-positive visit ratios, whole-call costs and all losses on real score vectors. The uniform theorem already addresses all score orderings for its single-component domain. |
| “A particular implementation contract was selected to exclude fast competitors.” | State equations and semantic differences early; acknowledge genuine alternatives and their different targets. Do not call a mathematically different metric an incorrect implementation, or treat its timing as an exact-equivalence comparison. |
| “The speedup is mainly radix/JIT or self-written baselines.” | Retain identical-activation stop ablations and matched radix dense/sparse controls. Add the bounded external-source comparison below. Do not infer new-method timings from old v0.3 measurements. |
| “The dataset is small or repeatedly reused.” | Separate the previously studied 42-series development set from the 12-series external source-family set. Report actual series/family counts; score vectors and widths do not create independent datasets. |
| “Fewer visits do not make this useful.” | Use end-to-end evaluator calls, preparation included, and report absolute times as well as ratios. A failed runtime decision is a negative result, even with a valid theorem. |
| “The paper promises exact floating arithmetic.” | Keep exact-arithmetic identities separate from measured Float64 agreement and rounding limitations. The independent small-case oracle is numerical evidence, not a formal numerical certificate. |

The Sylligardos workshop paper reports CPU/GPU acceleration and is relevant
prior work. Located FF-VUS code has a different native geometry/numerical
contract, as the existing semantic witnesses document. Its presence defeats
an unrestricted “first/fastest VUS” narrative, but does not force mixing
different metric outputs in one timing leaderboard.
[Workshop paper](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/PhD/PhD25_17.pdf),
[Pinned FF-VUS Torch source](https://raw.githubusercontent.com/doanthihoaithu/aVUSi/facf4362092525671215031048a75842b9d6d632/3_metric_calculator/metrics/ffvus/vus_torch.py)

## What the current evaluation can establish

The designed development experiment has 42 previously used series, three
released model score vectors and three widths: 378 cases, including 126 at
the primary width. The external design has 12 series in nine source families,
four generated score vectors and three widths: 144 cases, including 48 at the
primary width. These are evaluator workloads, not detector-accuracy studies.
Whole-series feature fitting and simple classical controls do not invalidate
evaluator timing, but they do not reproduce the source benchmark's detector
leaderboard or demonstrate deployment-time generalization.

The mTSBench repository was inspected as a primary source. Its OpenReview PDF
returned a browser challenge in this pass; no full-paper review is claimed.
The local selection/source pins and exclusions remain the evidence for the
specific acquired workload. A new source-family name is not proof that all
underlying real-world domains are independent.
[mTSBench repository](https://github.com/PLAN-Lab/mTSBench)

Family-cluster uncertainty is appropriate for correlated score vectors, but
nine external families are limited evidence. Show the distribution and worst
losses, not just a confidence-bound PASS. Three repeated timings do not
characterize machine-population uncertainty. If Linux regenerates scores and
their hashes differ, report platform-specific ratios on the separately bound
vectors; do not label it byte-identical-input replication.

No current frozen decision should change after results arrive. The current
nine methods give eight comparators, including `active_full`, `last_positive`,
released radix/sparse variants, matched dense variants and Klein. A strong
paper should explain separately whether gains come from activation, stopping
before the last positive, or preparation. A CPU second-platform confirmation
helps assess portability but is not an external laboratory reproduction.

## Minimal additional comparison after the frozen runs

**Benchopt is the most consequential missing external baseline.** It provides
an independently authored dense cumulative-sum implementation with the pinned
exhaustive contract. Before making a broad exact-CPU superiority claim, run a
separate frozen supplement on all 48 external score vectors at `L=30`, using
unchanged source with `thre=n` and the new candidate's **paired ROC/PR API**.
This matches the native paired output instead of attributing omitted ROC work
to the new method. Include validation/preparation, randomized paired order,
three warmed repetitions, parity and every loss. This supplement should not
alter the primary decision or pool timings from the earlier v0.3 run.
[Pinned Benchopt source](https://raw.githubusercontent.com/benchopt/benchmark_tsfm/2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94/benchmark_utils/metrics.py)

DTAIAnomaly is also eligible and should not disappear from the comparison
discussion. A bounded supplement can use all 12 external series with the
prespecified `isolation_forest` vector and `L=30`, native full-threshold
configuration, one thread, and a fixed per-call timeout declared before
execution. Preserve completed numerical/timing pairs and censored cases
separately; timeouts are not measured ratios. Use matched output work and
disclose its upstream `parallel=True, fastmath=True` kernel. Broader timing
is optional if these exact scans are costly; scope the resulting claim to
the completed experiment rather than silently dropping the method.
[Pinned DTAIAnomaly source](https://raw.githubusercontent.com/ML-KULeuven/dtaianomaly/557b435790bebc57307d8e7f22047273ac923f36/dtaianomaly/evaluation/_volume_under_surface_metrics.py)

Neither addition requires changing the running experiment, implementing a new
GPU backend, or restarting a broad literature search. A GPU/native-FF-VUS
comparison is a separate research question unless the intended claim expands
to that hardware or metric contract.

## A manuscript that fits twelve pages

Regular Research papers have at most 12 pages excluding references; appendices
and acknowledgements count. Use the current official PVLDB template and
mandatory blocks, with named authors under single-blind review. Do not rely on
an overlength appendix to hold the core proofs. The abstract deadline is the
25th of the previous month and the paper deadline the 1st, at 17:00 Pacific
Time. This note makes no claim about individual submission eligibility.
[Submission instructions](https://www.vldb.org/2027/submission-guidelines.html),
[Formatting instructions](https://www.vldb.org/2027/formatting-guidelines.html)

| Content | Page budget | Essential content |
|---|---:|---|
| Abstract and introduction | 1.25 | Actual repeated evaluation bottleneck; exact target; algorithmic contribution; empirical result only when available. |
| Target and closest prior work | 1.50 | Dynamic mass/existence/integration equations; compact semantic comparison; prior support/cumsum/cutoff mechanisms. |
| Exact event representation | 1.00 | Global ties, negative-run ROC rectangles and terminal treatment; only the foundation needed for the new method. |
| Active-prefix algorithm | 2.00 | Radius activation, reversible-list schedule, DSU merges, epoch hits, complete-tie streaming; clear pseudocode and one figure. |
| Correctness and bounds | 1.50 | Saturation proof, full preparation accounting, general bound, uniform mass bound, strict separation from last-positive. |
| Evaluation protocol | 1.00 | Development/external distinction, method/output matching, total-call timing, uncertainty and numerical tolerance. |
| Results and mechanism analysis | 2.25 | Whole-call comparison with all losses; work reduction versus runtime; matched stop ablation; external supplement and platform scope. |
| Limitations, conclusion, disclosures | 0.75 | Metric/precision scope, tie and coverage degeneracy, overhead, exact AI/research-use disclosure. |
| Layout reserve | 0.75 | Captions, mandatory blocks and unavoidable page breaks. |
| **Total excluding references** | **12.00** | No claim that this outline has already been typeset to twelve pages. |

The earlier p-box width-refinement and racing developments should not dominate
this focused exact-algorithm paper. Preserve their negative evidence in the
research artifact and describe their distinct status accurately where needed.
The fixed-threshold-grid counterexample is motivation, not a second central
novelty claim. Long source audits, exhaustive test enumeration and historic
protocol chronology belong in the artifact; the target definition and central
correctness/complexity arguments belong in the paper itself.

## Decision once measurements exist

- If gains survive matched last-positive stopping and the strongest exact
  controls on both development and external workloads, lead with the
  instance-sensitive algorithm and measured practical benefit.
- If activation helps but buffer-assisted stopping adds little runtime value,
  retain the stronger theorem but describe the observed gain accurately.
- If the new engine loses overall, do not call the benchmark PASS or redesign
  its frozen success rule. The uniform theorem remains a real result, but
  practical significance for this focused PVLDB submission is then weaker.

The immediate deliverable is a coherent algorithmic argument with auditable
evidence, not another venue-status check. Whether it clears PVLDB's novelty and
significance bar remains a judgment the mathematics and measurements must
support.

## Outcome review after the two controlled Mac runs

The completed development report contains 378 cases with maximum absolute
error `1.3322676295501878e-15`; the external report contains 144 with maximum
error `3.6637359812630166e-15`. Both record `primary_decision: false`.
These are numerical agreement observations, not formal floating-point proofs.

Reviewed report SHA256 values:

- Development: `eb7f43f981f82dcf45abcab62d135b0b2c1c4e96a1588dafd8aec2f3b86f98ca`.
- External: `599ab7dc59f3e2fc1a57313740e6f01bcde088f05025f83d5200c163274b1fbf`.

The following are reference/candidate median runtime ratios. Values above one
favor the candidate. Development rows contain 126 cases each; external rows
contain 48. The widths were specified before these measurements.

| Partition | L | Versus radix | Versus last-positive | Last-positive losses | Visited / full-active work | Visited / last-positive work |
|---|---:|---:|---:|---:|---:|---:|
| Development | 30 | 1.016 | 1.011 | 54/126 | 0.934 | 0.952 |
| Development | 100 | 1.191 | 1.040 | 42/126 | 0.825 | 0.846 |
| Development | 300 | 1.660 | 1.198 | 21/126 | 0.721 | 0.738 |
| External | 30 | 1.026 | 1.012 | 22/48 | 0.760 | 0.763 |
| External | 100 | 1.151 | 1.059 | 13/48 | 0.653 | 0.658 |
| External | 300 | 1.506 | 1.136 | 6/48 | 0.575 | 0.583 |

Work ratios divide summed visited-position counts over the same cases and
widths, not medians of ratios. These values were computed directly from the
completed `measurements.jsonl` profiles, without rerunning a metric.

At `L=30`, aggregate time against radix is essentially tied: development
`1.0014`, external `0.9999`. The geometric and aggregate interval lower bounds
do not both exceed one for all comparators. The primary failure is therefore
substantive, not a reason to change the width or rerun until favorable.
Development's worst last-positive comparison has ratio `0.292`, and the
external one `0.932`; all losses must remain visible. Three repetitions do
not resolve the cause of every individual outlier.

At `L=300`, matched last-positive aggregate ratios are `1.242` (development)
and `1.655` (external); their geometric and aggregate interval lower bounds
exceed one in both partitions. Radix loses 125/126 development cases and
48/48 external cases. The candidate nevertheless loses some cases against
the identical activation engine using last-positive stopping. Thus the
secondary outcome supports an incremental saturation benefit on these
high-width workloads, with heterogeneous effects. It does not establish
uniform dominance or rescue the failed primary decision.

The width trend is consistent with the mechanism: more buffer work becomes
avoidable, and fixed preparation is amortized across more widths. This is an
interpretation, not a measured decomposition of preparation cost. The
external `L=30` workload already eliminates roughly 24% of active visits yet
shows about a 1% median gain against the matched stopping control, directly
demonstrating that work-count savings need not become equivalent end-to-end
time savings. Aggregate work ratios alone also hide differences between
series; a per-case work/runtime plot is more informative than a new headline
average. Median candidate calls range from about 0.96 to 3.27 ms across these
six partition/width groups, so absolute costs should accompany ratios.

**Paper judgment:** the uniform `O(n+L*P0)` single-component theorem,
the all-score-order singleton corollary, the strict matched-control
separation, and these prespecified secondary observations support a focused
algorithmic manuscript worth developing. The strongest claim is a structural
complexity result with width-dependent empirical benefits and an explicitly
failed default-width superiority criterion. The remaining PVLDB risk is
significance: the metric-specific proof is short, constituent data structures
are standard, and the observed default-width improvement over the strongest
existing engine is negligible. A reviewer could reasonably regard this as a
useful specialized optimization rather than a sufficiently deep contribution.
The new result should be presented clearly enough for that judgment, without
padding it with unrelated negative algorithms or unearned SOTA language.

## Smallest meaningful mechanism checks after these outcomes

Do not expand widths, tune stop thresholds, select favorable source families,
or rerun the primary experiment to obtain a pass. Three bounded actions have
distinct purposes:

1. **Analyze already recorded per-case profiles.** Plot the saturation-to-full
   and saturation-to-last-positive visit ratios against corresponding runtime
   ratios at each prescribed width, retaining every case. This tests whether
   the proposed mechanism explains observed heterogeneity. A weak association
   or many substantial work reductions without time gains limits the practical
   mechanism claim; no new metric computation is needed.
2. **A small prespecified structural falsification suite.** Use four scale
   values and constructions covering (a) distinct-score singleton with the
   original positive late, (b) the two-component separation from last-positive,
   (c) an all-active-tied singleton, and (d) delayed component coverage. Check
   actual visit counts, complete-tie boundaries, and dense numerical parity.
   The predicted outcomes are bounded singleton prefixes, strict separation,
   quadratic all-tie scans, and failure of a general `P0`-only bound,
   respectively. This tests the favorable and adverse claims together.
   It needs no broad timing sweep or repeated statistical success search;
   existing tests can supply a construction if they already record the needed
   counts. The theory agent is authoring the bounded structural runner.
3. **Close the external-source comparator gap separately.** The new
   `saturation_external_baseline_protocol_20261021.md` fixes all 48 external
   score vectors at `L=30` for paired candidate/radix/Benchopt calls and 12
   prescribed DTAI vectors with explicit timeout censoring. Its completed
   outcomes are recorded below. This answers comparator coverage, not the causal mechanism,
   and cannot retroactively alter the primary decision.

The already planned Linux run adds a platform check. No further real-data
workload expansion is justified merely by the failed primary result.

## Scope of the proposed singleton lower bound

The appended `paper/saturation_mass_bound.tex` argument is valid in its stated
deterministic adaptive score-coordinate query model. With the singleton at
position zero, `0 <= L <= n`, and `n >= 4`, there are
`n-floor(L/2)-1 >= ceil(n/2)-1 >= n/4` positions outside maximum support.
Assign the original score one and distinct lower scores elsewhere. Every
uninspected off-support coordinate could instead hold score two, preserving
the promised distinct valid input while changing every width's PR from one
to one-half. Identical adaptive observations cannot distinguish these inputs.
The finite-instance query bound is therefore sound, even if validation is
free. The explicit `-i` score construction needs representable distinct
binary64 values, which the theorem states.

This matches `O(n+L)=O(n)` for the singleton subclass with `L<=n` under the
declared fixed-key computation convention. It is a basic input-reading
optimality result, not a lower bound involving `L`, not a multi-component
optimality result, and not an arbitrary-precision comparison-sorting theorem.
Keep it as a compact corollary/caveat rather than promoting the entire
algorithm as “optimal exact VUS.”

## Completed independent-source supplement

The separate paired-output run completed once under frozen protocol SHA256
`8e9bf4a9e1d938f9b4467e46050ff5820ab04083d5cc8011cf770eb5083ae5ad`.
Its report is `artifacts/saturation/mac-external-baselines/report.json`, SHA256
`8684c5f3d41fb3f5d18b80d22a060467eedf30fc408912b8f38084b00810e1c3`.
All completed paired ROC/PR results satisfy `1e-11` absolute tolerance, with
maximum observed error `8.215650382226158e-15`. Source and protocol bindings
were unchanged through completion. These are single-threaded, warmed,
full-public-call measurements at `L=30`, with three randomized repetitions.

| Reference | Three-repeat cases / prescribed | Median reference/candidate ratio | Aggregate ratio | Candidate wins / losses |
|---|---:|---:|---:|---:|
| Released paired radix | 48/48 | 1.017 | 1.055 | 29 / 19 |
| Actual pinned Benchopt paired kernel | 48/48 | 34.918 | 60.951 | 48 / 0 |
| Actual pinned DTAI paired evaluator | 10/12 | 101.106 | 318.384 | 10 / 0 completed cases |

The DTAI `PSM_test` and `swan_sf_test` isolation-forest cases reached the
declared 30-second parent watchdog on their first timed call. Their remaining
repetitions were skipped, workers were terminated, and no ratios were inferred.
The DTAI ratios therefore describe only the ten completed cases. Warm-up and
timed deadlines were separate; worker logs confirm one Numba thread and one
thread in each reported native threadpool.

This closes the strongest independent exact-source comparator gap for the
stated paired-output workload. It does **not** attribute the full Benchopt or
DTAI speedup to the new saturation idea: the released radix evaluator remains
very close at this width. The fair incremental claim is the paired-radix row,
and the fair mechanism claim remains the matched stopping ablations in the
primary experiment. The supplement does not reverse either primary failure.
