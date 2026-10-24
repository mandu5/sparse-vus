# Historical PVLDB form and revision calibration

Checked directly on 24 October 2026. This supplements the adjacent-field
[OpenReview calibration](public-calibration.md); it does not replace its
accepted and rejected cases or provide an acceptance predictor.

## A published venue form

The authors of *Data-Parallel Query Processing on Non-Uniform Data* publish
their [initial PVLDB reviews](https://dbis.cs.tu-dortmund.de/publikationen/2020/data-parallel-query-processing-on-non-uniform-data/vldb-2020-reviews/).
The form asks for a recommendation, venue fit, whether revisions could alter
the judgment, synopsis, at least three strengths and weaknesses, originality,
importance, technical merit, experimental support, readability, numbered
analysis and concrete revision requirements.

Final internal reviews should use those fields, augmented with correctness,
artifact evidence and the [current 2027 scope criteria](https://www.vldb.org/2027/submission-guidelines.html).
This is an adaptation of a **historical actual PVLDB form**. The current private
2027 CMT review form has not been retrieved. Any 1–10 score remains a defined
internal surrogate, not an official PVLDB score.

## What changed in the published case

The [authors' publication log](https://dbis.cs.tu-dortmund.de/publikationen/2020/data-parallel-query-processing-on-non-uniform-data/)
records initial recommendations Weak Accept / Weak Reject / Weak Accept and
a revision decision. The [revised reviews](https://dbis.cs.tu-dortmund.de/publikationen/2020/data-parallel-query-processing-on-non-uniform-data/vldb-2020-revision-reviews/)
give three Accept recommendations. The final paper is independently present
in [PVLDB 13(6), pages 884–897](https://www.vldb.org/pvldb/vol13/p884-funke.pdf).

Initial concerns included limited whole-query benefits and adaptation of
existing techniques. The revision added a complete-system competitor and
explained an unfavorable parameter regime. One accepting reviewer still
questioned whether memory-access improvements, rather than the proposed
balancing mechanism, explained an important result.

## Application to this manuscript — our inference

This case makes three objections particularly relevant: whether the baseline
already removes most of the work; whether the novel recurrence contributes
beyond implementation changes; and whether a complete consumer benefits.
The direct-ramp VUS control, weighted interval control, faster raster control
and native TimeEval execution address different parts of that chain. Their
negative results must remain in the abstract, experiments and judgment.

The analogy has a substantial limit: DogQC evaluates multiple database
operators inside a query compiler, whereas this manuscript optimizes two
specialized analytics operators. The latter still needs an independent
significance judgment. Similar objections, numerical ratios or improved
internal scores do not imply the same editorial decision.

Use this source to calibrate the **questions and evidence**, not to target the
published paper's recommendation. Each internal reviewer should state the
largest remaining objection and whether a specific achievable revision could
materially alter it. Preserve disagreement across reviewers.
