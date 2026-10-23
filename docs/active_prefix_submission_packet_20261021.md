# Active-Prefix Evaluation of Dynamic VUS — submission packet

Prepared 21 October 2026. This packet records manuscript fields and factual
dependencies; it is not a submitted paper or an editorial decision.

## Concrete manuscript and target

- Manuscript: [`paper/active_prefix.pdf`](../paper/active_prefix.pdf), official
  unmodified PVLDB template, 9 pages including references in the checked build.
- Title: **Active-Prefix Evaluation of Dynamic VUS**.
- Proposed venue: **PVLDB volume 20, Regular Research**, Foundations and
  Algorithms flavor. This is a fit assessment, not an editorial determination.
- Author metadata supplied by the human: **Youngmin Ko**;
  **rhdudals0505@naver.com**. Affiliation: **Independent Researcher, Republic of
  Korea**, reflecting graduation rather than claiming a current university role.
- Portal: https://cmt3.research.microsoft.com/PVLDBv20_2027/
- Upcoming cycle: abstract by **25 October 2026**, full manuscript by
  **1 November 2026, 17:00 America/Los_Angeles** (2 November, 10:00 Korea).
- Public artifact branch:
  https://github.com/mandu5/sparse-vus/tree/research/saturation-20261021

The present research question concerns an exact data-analytics operator and
its complexity. The theoretical contributions and matched-control evidence
support a focused algorithms paper. The earlier generic manuscript and
software releases are distinct artifacts and are not editorial decisions.

## Abstract field

Volume Under the Surface (VUS) evaluates time-series anomaly scores over
thresholds and tolerance widths. Existing support sweeps can still inspect
every maximum-support position at every width, even after the integral can
no longer change. We give an instance-sensitive evaluator for the original
dynamic-denominator, sum-and-clip VUS definition. A complete score threshold
permanently saturates recall when admitted original positives plus half the
admitted buffer mass reach the original positive count and every expanded
component has been hit. Its remaining PR contribution vanishes; its ROC
suffix telescopes analytically. Combining this condition with reversible
support activation and incremental component unions eliminates width-wise
full-support preparation. Under fixed-binary64 ranking and unit-cost metric
arithmetic, the full call takes O(n + L + alpha(K) sum_w J_w) time and O(n+Q)
auxiliary words, where J_w includes the complete terminating active score tie.
With one original interval and distinct support scores, the bound is
O(n + L P_0) for every score ordering. For a singleton and L <= n, it matches
a deterministic score-query lower bound, giving optimal linear time under
the stated model. We evaluate 378 development cases on macOS and 144 external
cases on each of macOS and Linux. The predeclared width-30 runtime criterion
fails in all three runs. At width 300, external median speedups over the
preceding sparse radix evaluator are 1.51x and 1.63x, with all 48 cases faster
on each platform. Maximum observed PR discrepancy in these three runs is
below 3.67e-15. Exactness refers to the mathematical all-threshold, all-width
target; floating-point parity and runtime are evaluated separately.

## Self-assessment of relevance field

The paper addresses the computational cost of exhaustive range-aware
evaluation over stored time-series labels and anomaly-score collections.
This analytics operation is repeated across detector outputs and tolerance
widths. Sections 2–3 build directly on the VUS operator introduced in PVLDB
and optimized in the VLDB Journal, preserving its original dynamic mass,
component coverage, and complete-threshold integrals. The contribution is
an instance-sensitive evaluation algorithm that eliminates unnecessary
threshold events and per-width full-support preparation, with a uniform
single-interval guarantee and a restricted matching input-query lower bound.
Sections 5–6 evaluate complete metric calls against source-pinned external
implementations and matched ablations on stored real-source series and
constructed witnesses. The experiments do not claim a DBMS integration,
detector-quality improvement, or measured end-to-end model-selection system.

## Human and account facts required for actual submission

The user has authorized continued research and pursuit of submission. That
authorization is recorded separately from the following factual declarations:

| Field | Evidence/status |
|---|---|
| Actual intellectual contribution and meaningful drafting/revision | Asked against the completed focused PDF; human response required. Do not invent a contribution statement. |
| Author's review and accountability | Asked against the completed focused PDF; human response required. |
| Other contributors/coauthors and research support | Human clarification requested; no negative declaration assumed. |
| CMT identity, account counter and reviewer nomination | Existing CMT email requested. The actual portal was opened in local Chrome and redirected to `/User/Login?ReturnUrl=%2FPVLDBv20_2027%2F`; no authenticated author dashboard or counter is available in that session. Nominate the actual best-qualified author if no author meets the publication criterion. |
| Concurrent/similar submissions and PVLDB history | Human clarification requested; no eligibility attestation made. |
| Domain and individual conflicts | Known Penn State/Hanwha history is context, not a complete verified conflict list. Apply the volume-20 five-year rule to actual affiliations/collaborations; campus-specific and individual conflicts require accurate facts. |
| AI assistance | Disclosed explicitly in the manuscript, including code, proofs, experiments, draft and internal agent reviews. |
| Editorial receipt or decision | No submission receipt or acceptance recorded by this packet. |

PVLDB requires substantial human intellectual participation, meaningful
drafting/revision, awareness of submission and accountability. Those are
authorship facts, not an extra agent-imposed authorization round. The
automated workflow cannot certify them for the human. The existing user
instruction already authorizes performing the remaining submission actions
once truthful required facts and account access are available.

## Verified policy sources

- [Submission guidelines](https://www.vldb.org/2027/submission-guidelines.html):
  volume 20, current cycle, single-blind identity, 12-page regular-paper limit,
  submission counters, five-year conflicts, reviewer nomination and artifacts.
- [Formatting guidelines](https://www.vldb.org/2027/formatting-guidelines.html):
  official template and mandatory blocks.
- [Publication policy](https://vldb.org/pvldb/general-information/publication-policies):
  authorship, AI disclosure, originality and concurrent review.

The year-specific five-year conflict rule takes precedence over the older
two-year wording on the generic policy page. No account state, peer-review
outcome, badge, DOI or claim of global firstness is inferred from these pages.
