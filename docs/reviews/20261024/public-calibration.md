# Public-review calibration for the internal PVLDB reviews

Read on 24 October 2026. These are actual OpenReview note contents obtained from
a public research-data mirror, not generated reviews. Direct OpenReview forum
and API requests returned browser verification or HTTP 403; those failures are
retained separately. The mirror is
[WENJINLIU/Paper-Review-Dataset](https://huggingface.co/datasets/WENJINLIU/Paper-Review-Dataset).
Original record hashes, note identifiers, ratings and decision identifiers are in
[`verified-note-metadata.json`](../../../artifacts/pvldb-research-20261024/public-review-calibration/verified-note-metadata.json).
Full downloaded records are cache-only. No LLM anchor scores from calibration
datasets were used. The origin service's current bytes could not be compared to
the mirrored records, so the provenance limit remains explicit.

These are **adjacent-venue TSAD reviews**, not public PVLDB reviews and not a
statistical acceptance predictor. The ICLR score scales differ by year and do
not map numerically to PVLDB decisions. A small purposive comparison illustrates
review objections; it cannot estimate an acceptance rate.

## Accepted evaluation analysis, ICLR 2026

**When Foundation Models are One-Liners**, forum
[`H27kvyG4qf`](https://openreview.net/forum?id=H27kvyG4qf), has decision
`XfBOGU95OS` (Accept, Poster), meta-review `t9hXxyBqb5`, and recorded ratings
4, 6, 6, 4. Its publication was independently corroborated in the
[official ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/cf70320e93c08b39b1b29a348097a376-Abstract-Conference.html).
Reviewers questioned overgeneralization from a pipeline to all foundation
models, limited multivariate coverage, missing strong non-foundation baselines,
and statistical rigor. The author response added normalization/horizon studies,
paired statistics and broader comparisons. The AC regarded the scoped analysis
as valuable and also identified a mistaken metric criticism in one review.
The AC's conjectures about potential revised ratings are **not actual score
updates** and are not counted as such.

**Consequence here:** numerical speedup must not become a claim about every VUS
definition, all future datasets or detection accuracy. Ablations and paired
uncertainty should answer specific objections; incorrect reviewer premises
should be checked against the actual operator.

## Accepted model selection, ICLR 2023

**Unsupervised Model Selection for Time Series Anomaly Detection**, forum
[`gOZ_pKANaPW`](https://openreview.net/forum?id=gOZ_pKANaPW), has decision
`HRD5hna4dy` (Accept: notable-top-25%) and ratings 8, 6, 3, 5. Its inclusion is
corroborated by the [official ICLR program](https://dev.iclr.cc/virtual/2023/oral/12666).
The AC credited the important problem, justified easy-to-use method, extensive
real-data experiments, and responses distinguishing existing work. One reviewer
remained concerned about missing AutoML baselines. The decision itself noted
that the method combined existing ideas and was specialized to anomaly
detection.

**Consequence here:** a useful, well-supported specialized combination can be
publishable. Merely combining known tools, or matching an accepted paper's
average score, does not establish the same value. The exact work removed from
the nearest evaluator and the measured user task must be clear.

## Rejected subsequence detection, ICLR 2023

**Time Series Subsequence Anomaly Detection via Graph Neural Networks**, forum
[`73U_NlKaNx`](https://openreview.net/forum?id=73U_NlKaNx), has decision
`GMS-BMZmsG` (Reject) and ratings 5, 3, 6, 5. The AC cited limited novelty,
insufficient experiments, presentation and dependence on initial subsequence
length. Reviews asked for missing discord-detection baselines, recent VUS and
benchmark literature, and ablations establishing which component helped. One
reviewer found that the component emphasized by the narrative was not the one
driving the ablation gain. The rejection is taken from the mirrored decision
note, not inferred from a low average rating or absence from a program.

**Consequence here:** geometry-only must remain a serious ablation because much
of the batch speedup comes from shared preparation. Benchopt cannot be omitted
merely because the Klein comparison is favorable. New loop ordering alone is
not a sufficient novelty claim.

## Rejected dynamical-system detection, ICLR 2023

**Time Series Anomaly Detection via Hypothesis Testing for Dynamical Systems**,
forum [`G-dM79m_EXd`](https://openreview.net/forum?id=G-dM79m_EXd), has decision
`GYaqYZtEQU` (Reject) and ratings 6, 1, 5. The AC acknowledged a valuable dataset
and probabilistic framing but found the new contribution unclear, the theory
and system poorly connected, and the distinction from established models
insufficiently explained.

**Consequence here:** theorem count and code volume are not evidence of research
value. The observed support/prefix regimes need to explain actual runtime and
the scope of the claimed algorithmic difference.

## Instructions to independent reviewers

Use the [PVLDB 2027 research criteria](https://www.vldb.org/2027/call-for-research-track.html)
and [submission requirements](https://www.vldb.org/2027/submission-guidelines.html)
for scope and contribution. Report summary, strengths, weaknesses, correctness,
novelty/significance, experimental support, reproducibility, and a reasoned
Accept/Revise/Reject recommendation. The current confidential CMT form was not
retrieved; this is a disclosed format based on public criteria, not a verbatim
official form. If assigning a 1–10 score, explicitly call it an internal
surrogate and define it. Do not read the other internal reviewers' scores.

Calibrate objections using the four cases above, but inspect our actual sources
and results. Record precisely which analogous objections are resolved and which
remain. Do not raise a score just because the goal is a higher score. Preserve
initial reviews and append clearly dated assessments of genuinely new evidence.
