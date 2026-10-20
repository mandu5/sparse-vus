# Fast VUS prior-art audit, 20 October 2026

This audit concerns the algorithmic and empirical claims of Sparse VUS at
`7565b6657ba510e79db13e79b809b58e77feacc0`. It uses primary papers, author
repositories, package records, and direct source inspection. Repository
revisions were checked against the 2026-10-20 cutoff. This is a bounded
literature/code audit, not a proof that no other implementation exists.

**Assessment:** a global SOTA claim is not established. A previously omitted,
public, closely related baseline, Tom Louis Klein's **fast-VUS**, predates this
release and must be evaluated. The support restriction, support-score sorting,
and support cumulative sums are already implemented there. The remaining
candidate contribution is eliminating inactive threshold events exactly,
including ROC rectangles, and obtaining off-support ranks without globally
sorting all scores. The unavailable Sylligardos CPU/GPU implementation remains
an unresolved comparison and novelty risk.

## 1. New direct comparator: fast-VUS

[The public README](https://github.com/tomlouisklein/fast-VUS/blob/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/README.md)
describes a NumPy implementation of PR only and explicitly targets the
official **250-threshold** calculation by default. Its reported 84–939× ratios
are author measurements against the reference, not measurements against
Sparse VUS. Its Apache-2.0 license is present.

Git history independently retrieved during this audit:

| Revision | Commit date, UTC | Meaning |
|---|---|---|
| [`189de211f8821c3027110af2d00593e603c11cfc`](https://github.com/tomlouisklein/fast-VUS/commit/189de211f8821c3027110af2d00593e603c11cfc) | 2026-10-12 11:03:32 | Initial commit |
| [`1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00`](https://github.com/tomlouisklein/fast-VUS/commit/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00) | 2026-10-16 10:36:48 | Audited revision; documentation update |

The [implementation](https://github.com/tomlouisklein/fast-VUS/blob/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py)
accepts `thre=n`, enabling direct full-threshold comparison without modifying
upstream code. It preserves dynamic positive mass, clipped summed ramps,
expanded-segment existence, and right-endpoint PR integration. It sorts all
scores for thresholds/counts, additionally sorts maximum-support scores, and
uses cumulative sums of support weights. It still creates threshold-length
arrays and full-length masks per width. Thus support cumulative sums are
prior art; inactive-event elimination and removal of global sorting are
concrete differences. This source inspection is not an independent proof of
all-input equivalence.

An unchanged-module adapter is in
[`experiments/fast_vus_adapter.py`](../experiments/fast_vus_adapter.py).
Only source and license are downloaded into ignored `.cache/fast_vus/`.

- Source SHA-256: `15b7afb94da0e1f1b1c408fe44b937d910935c19f8eb76f42ae6719f9cfcb52b`.
- License SHA-256: `3b19b00e8d74e9e8f3db69d8407da5b5dd2078f3bf9c57ff47ff0fb9551db282`.
- Use `fast_vus_pr(y, scores, L, max_samples=len(scores))` for full thresholds.
- The result is **PR only**. A comparison against Sparse VUS's ROC/PR pair
  must disclose the extra work performed by Sparse VUS.

Fresh adapter verification used Python 3.12, NumPy 1.26.4 and
[`tests/test_fast_vus_adapter.py`](../tests/test_fast_vus_adapter.py).
All **31 tests passed**: 24 randomized cases comparing full and sampled grids,
five structured edge/tie/overlap cases, a grid-resolution counterexample,
and rejection of changed source bytes. Across the 24 full-threshold cases,
maximum absolute PR disagreement was `5.551115123125783e-17`.
The six-point example in the README produced PR `0.6834092121537311`
in both implementations. These small checks establish comparator suitability,
not large-corpus performance or universal numerical identity.

The default-grid test uses 1,001 descending scores and one positive at rank
two, with width zero. The upstream default returns `0.2`; `thre=1001`
returns `0.5`. Its default claim of exactness therefore means equality to
the sampled reference, not equality to all-threshold integration.

## 2. Sylligardos CPU/GPU VUS: real prior art, unresolved mechanism

The primary [VLDB Ph.D. Workshop 2025 paper, §4 and Fig. 3](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/PhD/PhD25_17.pdf)
presents preliminary CPU/GPU VUS work under future work. It reports up to two
orders of CPU speedup and three of GPU speedup over the then-current
implementation, on nearly 1,900 TSB-UAD series up to 600,000 points. Detailed
implementation analysis and an evaluation toolkit are promised subsequently.
The paper supplies no pseudocode, source revision, threshold-resolution
contract, or sufficient detail to establish equivalence to Sparse VUS's
pinned semantics. Billion-point scalability is an aim, not a demonstrated
result in the presented experiment.

Therefore **first accelerated VUS**, **first 100× VUS**, and **faster than
Sylligardos** are unsupported claims. Conversely, lack of located code does
not establish a novel mechanism. There is no evidence from this audit that
Klein's repository is the promised Sylligardos implementation.

The implementation search followed the
[author's GitHub profile](https://github.com/sylligardos) and six returned
public repositories, the supervisor's
[publication list](https://boniolp.github.io/publi), the
[Inria VALDA 2025 report](https://prod-rex-app.inria.fr/report/2025/valda/index.html),
and the subsequent
[MSAD paper](https://arxiv.org/abs/2510.26643).
The MSAD paper concerns model selection, not a disclosed fast-VUS algorithm.
None of these inspected materials resolved the missing implementation.

Two concrete follow-up trails were checked:

- [`sylligardos/MSADv2`, `87aa06897e13131659e154013bbf3860db9cee4f`](https://github.com/sylligardos/MSADv2/tree/87aa06897e13131659e154013bbf3860db9cee4f)
  (2025-12-02) imports `tsb_kit.vus.metrics.get_metrics` in
  `src/utils/utils.py`; requirements pin `tsb_kit==1.0.1`. The
  [PyPI release](https://pypi.org/project/tsb-kit/1.0.1/) dates to
  2024-06-14. Its verified wheel contains the earlier nested-threshold
  `RangeAUC_volume_opt`/`_mem` implementations, not a GPU kernel or
  support-event elimination.
- [`sylligardos/tsad-template`, `50960962c2b9ccdc26402e134eb31dc47ea5dbc8`](https://github.com/sylligardos/tsad-template/tree/50960962c2b9ccdc26402e134eb31dc47ea5dbc8)
  (2026-06-19) contains data-loading and execution scaffolding. Its inspected
  tree has no evaluator implementation. A linked `tsb-ad-parser` repository
  was not among the six public repositories returned by the API; its
  contents and relevance remain unknown.

The tutorial repository's commit API request returned HTTP 403 during this
audit; its full contents were not inspected. Web indexing, public-repository
visibility, and that access failure limit any negative search conclusion.

## 3. Official VUS, TSB, and dtaianomaly

The [2025 VUS paper, §4.3](https://arxiv.org/html/2502.13318v1#S4.SS3)
(arXiv v1 submitted 2025-02-18) already partitions maximum-buffer support
from unaffected regions and offers static/dynamic reuse and stored-prediction
tradeoffs. Algorithms 2 and 3 retain a threshold loop inside the width loop.
Support restriction is consequently not a new contribution.

Current code revisions were obtained using GitHub's public commit API with
an explicit cutoff, followed by raw-file retrieval:

| Repository and pinned source | Commit date, UTC | Direct finding |
|---|---|---|
| [VUS `467bace0c103f5c2bdb4900306d82939bcac8ff9`](https://github.com/TheDatumOrg/VUS/blob/467bace0c103f5c2bdb4900306d82939bcac8ff9/vus/utils/metrics.py) | 2026-08-12 08:41:59 | Current target remains unchanged; repeated threshold scans |
| [TSB-AD `303dffbfc11612995b17b06633f8c9d0ea0e38e5`](https://github.com/TheDatumOrg/TSB-AD/blob/303dffbfc11612995b17b06633f8c9d0ea0e38e5/TSB_AD/evaluation/basic_metrics.py) | 2026-10-20 02:57:28 | Relevant evaluator methods match VUS |
| [TSB-UAD `313f0fdeba14292b9db4e1aa94c74a983a25de31`](https://github.com/TheDatumOrg/TSB-UAD/blob/313f0fdeba14292b9db4e1aa94c74a983a25de31/TSB_UAD/vus/utils/metrics.py) | 2024-12-03 22:06:27 | Relevant evaluator methods match VUS |
| [dtaianomaly `557b435790bebc57307d8e7f22047273ac923f36`](https://github.com/ML-KULeuven/dtaianomaly/blob/557b435790bebc57307d8e7f22047273ac923f36/dtaianomaly/evaluation/_volume_under_surface_metrics.py) | 2026-10-13 14:42:21 | Compiled support scans retained per supplied threshold |

For the first three sources, `RangeAUC_volume_opt`,
`RangeAUC_volume_opt_mem`, `sequencing`, and `new_sequence` were compared
using `ast.dump(..., include_attributes=False)` and matched exactly.
Today's TSB-AD HEAD change therefore does not supply a distinct algorithm
for those routines.

dtaianomaly's `_range_curves` uses Numba `parallel=True, fastmath=True`;
each threshold scans relevant scores/weights and tests expanded-segment
maxima. It globally sorts scores to choose thresholds and count predictions.
This is a useful compiled comparator already in Sparse VUS, but it does not
make Klein's vectorized support-prefix comparator redundant.

## 4. Algorithm comparison and novelty boundary

Here `n` is input length, `Q` maximum expanded-support size, `L` maximum width,
and `T` the requested number of thresholds. These are structural code
observations, not cross-machine speed conclusions.

| Method | Sorting and support treatment | Threshold work per width | Exactness/output contract |
|---|---|---|---|
| Official VUS/TSB optimized | Global sorting; support-region scans, optionally stored predictions | Repeated scans for `T` thresholds | Selected grid; ROC and PR, plus surface arrays |
| dtaianomaly | Global sorting; support arrays and segment maxima | Compiled scan of support at every threshold | Selected grid; shared ROC/PR curves |
| Klein fast-VUS | Global and support sorting; support cumulative sums | Vectorized lookup and integration over `T` entries; full-length mask work | Selected grid, including `T=n`; PR scalar |
| Sylligardos CPU/GPU | Not disclosed sufficiently | Unknown | Detailed semantic and resolution contract unknown |
| Sparse VUS | Support sorting; all-score rank counting | Only support events, with integrated inactive runs | Full-threshold ROC/PR scalars; `O(n log(Q+1)+(L+1)Q)` claimed/proved locally |

The first three external implementations do not implement the specific
negative-run ROC rectangle plus tied support-transition identity in
`docs/theory.md`. Klein's algorithm nonetheless anticipates a substantial
part of the computation that might otherwise be mistaken for novelty.

Generic curve compression is also older than this project:
[scikit-learn's pinned ranking source](https://github.com/scikit-learn/scikit-learn/blob/1.5.2/sklearn/metrics/_ranking.py)
sorts scores, accumulates weighted positives, and can remove redundant
curve points. Its
[ROC documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html)
explicitly describes collinear-point dropping without changing ROC AUC.
Thus “remove irrelevant ROC points” by itself is not a defensible novelty
claim. The narrower question is the support-sensitive implementation and
proof under VUS's threshold-dependent mass, existence reward, and tie rules.
This is a novelty candidate, not an independent priority certification.

Searches for sparse/event-elimination VUS, fastCPU/fastGPU VUS, exact VUS-PR,
and VUS cumulative sums did not locate another matching disclosed algorithm.
GitHub repository search, which did locate Klein's code despite its absence
from earlier web results, used `"VUS-PR"`, `"VUS" "anomaly"`, and `"fastVUS"`.
This was not an exhaustive authenticated global code search. Unpublished,
unindexed, private, and differently named implementations remain unknown.

## 5. Go/no-go

**No-go for a present global SOTA or “conference-worthy result established”
claim.** Existing release correctness checks do not fill the omitted
fast-VUS comparison or resolve Sylligardos. The relevant baseline set has
changed; prior ratios retain only their originally stated comparison scope.

**Go for a bounded research continuation** with a falsifiable claim:

1. Run unmodified Klein full-threshold PR on the same frozen corpus, widths,
   hardware, thread budget, and timing protocol. Verify parity before
   reporting runtime ratios. Report PR-only versus paired-output scope.
2. Separate `T=250` approximation comparisons from `T=n` exact comparisons.
   An implementation can be exact for its sampled grid while differing from
   full-threshold integration.
3. Attribute support restriction, cumulative sums, and ordinary curve
   compression explicitly. Frame the potential contribution around the
   support-sensitive complexity reduction and exact VUS state/integration
   identity.
4. Preserve dense-support losses and test regimes where `Q≈n`. A universal
   speed advantage is neither promised by the bound nor established by a
   selective sparse-case speedup.
5. Keep Sylligardos labeled **mechanism/performance comparison unknown**.
   A direct implementation or detailed subsequent disclosure could change
   the novelty assessment. No author was contacted in this audit.

Conference acceptance, independent peer review, and global fastest status
remain unestablished. No paid compute or external message was used.
