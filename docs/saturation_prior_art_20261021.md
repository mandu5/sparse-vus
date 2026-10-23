# Bounded prior-art assessment: active-prefix VUS

Checked 2026-10-21. This note concerns the proposed exact scalar evaluator in
`src/sparse_vus/saturation.py`; it is not a systematic literature review or a
firstness determination. Only web retrieval and light source reading were used
while the controlled development timing ran. No timed sources were modified.

The closest inspected external algorithm is Klein's fast-VUS, because it already
sorts maximum-support scores, answers threshold sums by cumulative sums, and uses
the same dynamic positive denominator. The closest prior cutoff is the full-
recall truncation in scikit-learn 1.0.2. The proposed contribution should be the
VUS-specific composition that avoids width-by-maximum-support preparation and
permits buffer-assisted stopping before the last original positive, together
with its adaptive bound and stated separating family. It should not be presented
as inventing linked-list restoration, union-find, sorted threshold sweeps,
complete-tie treatment, prefix sums, or recall-one tail elimination.

## Data structures that require attribution

**Reversible list deletion: Knuth, with his earlier attribution.** Knuth's
*Dancing Links*, arXiv:cs/0011047, pp. 1–2, equations (1)–(2), explains deleting a
node by linking its neighbors and restoring it through the retained neighbor
links. He explicitly credits Hitotumatu and Noshita (1979), reference [22]. Our
reverse-deletion preparation and forward reinsertion apply this established
principle to a known activation schedule. Retaining only next pointers during
forward traversal does not make the underlying reversible-list trick new.
[Knuth's primary manuscript](https://arxiv.org/pdf/cs/0011047)

Recommended citation: Donald E. Knuth, “Dancing Links,” 2000,
arXiv:cs/0011047. Historical attribution: Hirosi Hitotumatu and Kohei Noshita,
“A Technique for Implementing Backtrack Algorithms and its Application,”
*Information Processing Letters* 8(4), 174–175, 1979. The earlier paper was not
successfully fetched in this pass; attribute its priority as Knuth's statement,
not an independent reading of the 1979 text.

**Union-find: Tarjan and Tarjan–van Leeuwen.** Tarjan's 1974 technical report,
published in JACM in 1975, analyzes weighted union with path compression and its
inverse-Ackermann behavior. This is the origin to cite for the standard
amortized machinery, not a new analysis of union-find.
[Author's Berkeley report](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1974/Archive/ERL-m-434.pdf),
[JACM DOI](https://doi.org/10.1145/321879.321884)

Our `_root` specifically performs **path halving**, not a full two-pass
compression. Tarjan and van Leeuwen's 1984 Theorem 3 explicitly covers linking by
size or rank combined with compression, splitting, or halving, with bound
`O(n + m alpha(m+n,n))`. This is the more precise supporting citation for the
implemented combination. The full text inspected was uploaded by coauthor
Jan van Leeuwen; its theorem appears on printed pp. 258–259.
[Author-uploaded paper](https://www.researchgate.net/publication/220430653_Worst-case_Analysis_of_Set_Union_Algorithms),
[Princeton publication record](https://collaborate.princeton.edu/en/publications/worst-case-analysis-of-set-union-algorithms/)

Recommended citation: Robert E. Tarjan and Jan van Leeuwen, “Worst-Case Analysis
of Set Union Algorithms,” *JACM* 31(2), 245–281, 1984,
DOI `10.1145/62.2160`. The new proof must account for its own number of union/find
operations; citing the generic bound does not establish the VUS bound by itself.

## Closest VUS algorithms inspected

**Boniol et al., VLDB Journal 2025.** Section 4.3, Algorithms 2–3 on printed page
12, distinguishes maximum-buffer dynamic support from static regions. The
algorithms retain a threshold loop inside the width loop; the memory variant
caches threshold predictions. Those displayed algorithms do not describe the
combination of radius-activated score lists, incremental component unions, and
a mass-plus-existence stopping condition. This is a statement about the
inspected algorithms, not everything ever implemented by their authors.
[Primary paper](https://www.paparrizos.org/papers/BoniolVLDBJ25.pdf)

The official `RangeAUC_volume_opt` source at revision `467bace`, lines 359–440,
independently confirms all-width/all-selected-threshold loops, dynamic
`P_new`, capped recall, component existence, and an explicit terminal ROC point.
The inspected method does not exit after recall saturation. Its default
threshold count is 250; passing the input length obtains every ranked threshold
with repeated equal-score thresholds allowed.
[Official pinned source](https://raw.githubusercontent.com/thedatumorg/VUS/467bace/vus/utils/metrics.py)

**Klein, fast-VUS, revision
`1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00`.** In `fast_vus.py`, lines 63–83 sort
global and support scores and define `above` through a cumulative sum over the
sorted maximum support. Lines 85–102 build a fresh support-sized soft-label
vector per width, evaluate the cumulative sums and all selected threshold
coordinates, and calculate component hits from segment maxima. The source
therefore already supplies the prefix-sum and support-ranking ingredients. It
does not maintain a radius-activated list or incremental DSU, nor stop the
per-width computation at mass/existence saturation. Its default is 250 sampled
thresholds; the experiment's `thre=len(scores)` call compares the exhaustive
threshold target. It returns PR only.
[Primary pinned source](https://raw.githubusercontent.com/tomlouisklein/fast-VUS/1bae859f/fast_vus.py),
[Repository](https://github.com/tomlouisklein/fast-VUS)

The local adapter records source SHA256
`15b7afb94da0e1f1b1c408fe44b937d910935c19f8eb76f42ae6719f9cfcb52b`.
This pass read the cached file and the corresponding primary raw source; it did
not rerun the adapter or establish new performance evidence.

**Our own v0.3 is also a necessary baseline.** Its maximum-support event kernel
already removes negative-only threshold runs, preserves global ties, and uses
two-distance geometry plus radix preparation. The new work must be compared
against this released construction. Repackaging those earlier components is
not itself a new result. The proposed change is to make the work depend on an
active prefix rather than all maximum-support positions at each width.

## Standard curve evaluation and cutoff precedents

**Sorted sweeps and complete ties.** Fawcett's 2006 paper, Section 5 and
Algorithm 1, gives the decreasing-score linear scan following sorting and
explains why all equal-score observations must be processed before emitting a
ROC point. Algorithm 2 accumulates trapezoidal area during that scan. Those
techniques predate this work and should be treated as standard foundations.
[Fawcett's paper](https://people.inf.elte.hu/kiss/13dwhdm/roc.pdf)

**Direct full-recall cutoff precedent.** scikit-learn 1.0.2
`precision_recall_curve`, lines 781–793, computes `_binary_clf_curve`, then uses
`tps.searchsorted(tps[-1])` to truncate the returned curve at the first point
with all true positives. This is explicit prior software evidence for a
last-positive/full-recall cutoff. It follows construction of all cumulative
counts, so that snapshot does not establish our claimed output-sensitive
computation bound. It does establish why the `last_positive` ablation is
necessary and why recall-one stopping must not be claimed as newly invented.
[Official versioned source](https://raw.githubusercontent.com/scikit-learn/scikit-learn/1.0.2/sklearn/metrics/_ranking.py)

**Current curve pruning and partial AUC.** The stable documentation source,
revision `afe5bcd80ce17fd8ca88c33beb17534bd36423bc`, still constructs complete
tie thresholds and cumulative confusion counts. It can drop intermediate PR
points with unchanged true positives and collinear ROC points. Its partial-AUC
path first obtains the ROC curve, truncates/interpolates at `max_fpr`, then
standardizes that partial integral. A fixed-FPR partial AUC changes the target;
our suffix formula retains the entire original VUS integral. Neither current
function operates over VUS buffer-width activation or dynamic `P0+B/2`.
[Official source snapshot](https://raw.githubusercontent.com/scikit-learn/scikit-learn/afe5bcd80ce17fd8ca88c33beb17534bd36423bc/sklearn/metrics/_ranking.py),
[ROC API documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html)

## Defensible contribution wording and limits

Suggested wording for review, subject to the final correctness and experiment
results:

> We combine standard reversible-list scheduling and union-find with the exact
> VUS event representation. Across increasing widths, the evaluator activates
> only nonzero-support positions and traverses complete score ties until buffer
> mass and component coverage permanently saturate recall. This removes
> width-wise maximum-support setup, giving an adaptive
> `O(n+L+alpha(K) sum_w J_w)` bound under the stated fixed-word arithmetic model.
> A VUS-specific family separates this mass cutoff from a last-original-positive
> cutoff, while matched ablations measure whether it improves full-call runtime.

The mathematical distinction from last-positive stopping is
`A+B/2 >= P0` together with `H=K_w`, potentially with `A<P0`.
That condition is algebraically simple; its strength as a research contribution
rests on avoiding hidden full-support work, the exact all-width integral, the
strict separating family, and convincing measurements against the closest
implementations. A proof alone does not imply practical superiority, and a
single crafted family does not establish broad empirical usefulness.

No identical complete composition was identified in the inspected source
snapshots above. That bounded finding does **not** establish global firstness.
This note does not newly audit every aeon, dtaianomaly, FF-VUS/aVUSi, unpublished,
or proprietary implementation, nor later revisions of the pinned software.
It makes no SOTA or peer-review acceptance claim.
