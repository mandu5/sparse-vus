# Sparse VUS: evidence required for the PVLDB research route

Date: 2026-10-24. User-authorized continuation of this session's research.
Baseline source: `92319eafd0f937a152edf3a5c7e4355b2114acce`.

## Research question and venue

Can a complete, same-contract VUS evaluation workload over stored full-precision
detector outputs be made substantially cheaper without changing model decisions?
The proposed archival contribution is the complete support-event evaluator,
including its disclosed public software precursor; its new refinements are
reported separately. This is not a new anomaly detector or a claim that every
ingredient was invented here. Sampling failures motivate exhaustive evaluation.

Primary target: PVLDB volume 20, Regular Research, Foundations and Algorithms.
EA&B is appropriate only if a comprehensive comparative study, rather than a new
algorithm, becomes the main result. TMLR remains a distinct candidate for the
narrow sampling-reliability manuscript, not a simultaneous submission.

Official checks, 2026-10-24:
- https://www.vldb.org/2027/call-for-research-track.html
- https://www.vldb.org/2027/submission-guidelines.html
- https://www.vldb.org/2027/important-dates.html
- https://jmlr.org/tmlr/acceptance-criteria.html

Target cycle: abstract 2026-11-25 17:00 America/Los_Angeles, paper 2026-12-01
17:00 America/Los_Angeles. This is a research target, not a reserved submission.
Use the later cycle rather than rush the current October 25 abstract deadline.

## Fixed interpretation of the user's six gates

1. Compare at least ten genuinely related 2024-2026 primary papers, plus older
   indispensable algorithms. Identify what each already solves and one precise
   surviving distinction. Software is additional baseline evidence, not padding
   the ten-paper requirement.
2. Beat the strongest eligible public same-contract baseline on at least three
   public dataset collections, with paired uncertainty and meaningful ablations.
   Report the author's released evaluator as a separate strongest internal
   control. No floating-point/exact-integer or PR-only/ROC+PR apples-to-oranges
   comparison may establish a win. Compare sampled evaluation separately on an
   accuracy-cost frontier.
3. Use unrounded detector outputs, complete real series, at least eight different
   detector families, and explicit failures. Reused raw recordings must be
   identified; regenerated scores do not make the underlying recordings unseen.
4. One command reconstructs the principal table from fixed inputs/source hashes.
   Fresh execution must be distinguished from a ledger audit.
5. Three independent internal reviews using the target's verified criteria;
   calibrate interest/novelty objections against public accepted and rejected
   related reviews where available. If a current form or PVLDB reviews are not
   public, record that fact and use explicitly labelled adjacent-venue evidence,
   never fabricate the form or external review. No self-score is an acceptance.
6. Record venue, category, scope argument, deadline, and the exact contribution
   whose evidence is submitted. The research track of VLDB is the intended route.

## Research score gates, fixed before new outcome inspection

These are internal investment judgments, not a venue scale or acceptance odds.

**5-point candidate:** all six evidence gates addressed; an identifiable surviving
algorithmic or experimental contribution; real full-precision results on three
collections; lower 95% paired confidence bound for same-contract speedup >1 on
each collection; median whole-workflow speedup >=1.5 over the strongest external
eligible baseline; no unresolved mathematical or measurement-invalidity defect.
Reviews may still identify significance/generality as the chief weakness.

**6-point candidate:** 5-point evidence plus a new useful mechanism beyond the
released implementation: >=1.25 geometric speedup over the released Sparse VUS
evaluator with a lower 95% paired bound >1 on each collection, or an independently
supported comparably substantive generalization. Median full-workflow speedup
over the strongest external baseline >=2; two CPU environments; no unresolved
major scope, novelty, baseline, or validity objection in three internal reviews.
Adverse tails and memory costs remain visible. These numerical gates are this
study's prospective operational definition, not PVLDB's requirements.

## Three distinct remedies for the current weakest scientific gate

A. Full-precision, broader-detector evaluation: test whether the quantized-score
   limitation and simple full-distinct remedy dominate the broader workload.
B. Collection-level reuse: share label geometry and width-dependent quantities
   across detector scores. Compare independent calls, geometry-only reuse, and
   width-major streaming; account for preparation, allocation and output costs.
C. Certified model selection: measure partial-certificate plus exact fallback
   against direct exhaustive selection. Stop promoting it if the entire policy
   costs more; a certificate count alone cannot establish practical benefit.

If A-C do not support an important contribution, next explore native-contract
generalization with the correct trapezoidal predecessor term. Do not merely add
more repetitions to the failed algorithm or replace its primary test post hoc.

## Data and experimentation decisions

Development uses identified existing full-precision TSB-AD released outputs. The
new evaluation selects complete NAB, SMAP and SMD collections by a frozen rule,
without consulting new metric outcomes, and generates eight fixed CPU detector
families. It explicitly reports any reused recordings and preprocessing.
No anomaly-centred cropping, jitter to manufacture distinct scores, label-based
training/tuning, or post-result exclusions. Record genuine ties and constant
outputs. Detector training is separately timed; stored-score query evaluation
excludes training and is named accordingly.

Use balanced method orders, single numerical threads, warm compilation for all,
full public-call validation/preparation, and paired bootstrap by independent
series (with family/block sensitivity where appropriate). Do not run timing jobs
concurrently on the same host. Freeze source, input and run specifications before
the confirmatory measurements. All prior frozen files stay unchanged.

## Execution boundaries

The user has authorized research, implementation, testing and continued work.
Use the existing isolated worktree. Do not change TCPR or launch paid resources
merely because resources were described as plentiful. Keep the user's confirmed
authorship; do not ask for contribution again. Do not fabricate submission fields.

The existing thread goal is unfinished and was returned as `blocked` by the goal
tool. Creating a replacement was rejected on 2026-10-24; the tool has no resume
operation. This document resumes authorized work, but does not claim that the
goal service's status changed or that the old goal has been achieved.
