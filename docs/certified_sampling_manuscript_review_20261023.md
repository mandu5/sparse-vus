# Independent scientific review of the certified-sampling manuscript

Date: 2026-10-23. Role: internal adversarial review, not an external review or an acceptance prediction. This review owns no manuscript or production-code changes. The review reads the theory, empirical text, prior exact-arithmetic audits, and the two primary PR papers below. It performs no timed or heavy numerical computation.

## Scope and verdict

The manuscript has a mathematically specific contribution: post-saturation soft mass can inflate the original dynamic VUS-PR right-step integral under threshold sampling, and retained-state inequalities can certify the ideal real-arithmetic ordering of models. I found no fatal error in the stated construction, its finite bound, or the enclosure derivation under the implementation's input domain. This is narrower than a new general PR interpolation theory, a new generic interval algorithm, or a demonstrated efficient replacement for exhaustive evaluation.

The certificate experiments establish 63/128 and 94/128 uniquely certified winners under the two fixed budgets. They demonstrate mathematical confirmation of those selections. They do not demonstrate correction of a wrong sampled winner: every certified winner agrees with the unique sampled winner, and no sampled winner set is certified suboptimal. The full numerical prevalence and cost sections were still absent at the reviewed snapshot. A favorable assessment of practical significance must depend on those results, including the frozen primary decision rule; it cannot be inferred from the proof or from an internal review grade.

Reviewed snapshot SHA-256 values:

| File | SHA-256 |
|---|---|
| `paper/certified_sampling.tex` | `f13cd863f5513c1e6b6a2e4b53dc74c9b795504c192443e28f4f2cf5f8dfc9fc` |
| `paper/sampling_theory.tex` | `3a627bf57db65711ccb838a9600e8ea31b7915eac8becc916f38a79981287aff` |
| `paper/sampling_empirical.tex` | `4f9e53e4f8ca76a2283339326eec4c084d90df8495a4009719632d36482f7cca` |

## Primary-literature novelty boundary

[Davis and Goadrich, ICML 2006](https://ftp.cs.wisc.edu/machine-learning/shavlik-group/davis.icml06.pdf) derive the relationship between ROC and PR geometry for fixed positive/negative totals. Section 4 explains why linear PR interpolation can be optimistic and interpolates confusion-matrix counts with a constant local skew. This already rules out novelty for saying PR interpolation is nonlinear or that coarse PR integration can mislead. Its interpolated path is not an enclosure over every omitted score ordering. The present target additionally has a threshold-dependent positive denominator, clipping, and component coverage; the manuscript preserves its existing right-step definition rather than proposing a replacement interpolation.

[Keilwagen, Grosse and Grau, PLOS ONE 2014](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0092209) define nonnegative class weights and continuously interpolate accumulated confusion-matrix entries with fixed total foreground mass. Their Theorem 1 characterizes maximizing/minimizing score orderings for their weighted AUC-PR. Their results also show interpolation differences of either sign and changed model rankings when weights are used. Those broad ideas are therefore prior. Their extrema concern all score orderings for a weighted dataset, rather than conditioning on a retained threshold transcript. Their fixed-total recall cannot have the particular early saturation with remaining positive mass used in this manuscript's construction.

The defensible distinction is consequently the joint treatment of this pinned dynamic denominator, clipped recall, coverage, complete global ties, and rigorous directed arithmetic. The mass envelope itself follows elementary per-point mass constraints and should remain described as elementary. These two sources do not establish worldwide priority for the narrower result; the manuscript appropriately avoids that claim. Other referenced VUS and numerical-integration work remains relevant to the overall literature audit.

## Mathematical review

1. **Parameterized inflation family:** the support-separation condition makes the top `m` points zero-weight at every evaluated width. The original point at rank `m+1` makes recall one, so later soft mass adds no exact area. The second sampled state has the claimed precision. The separate sign qualification is necessary and present: width zero gives underestimation, not overestimation.
2. **Finite bound:** the retained-width lower bound, harmonic-tail estimate, and exact rational subtraction support the finite `>0.98` statement. The manuscript correctly discloses the extreme `L/n` regime and that the enormous instance was evaluated symbolically, not executed. The ordinary-width table supports a different, narrower claim: three constructed same-label selection reversals.
3. **Competing score vector:** the explicit feasibility inequalities allow the far negatives to fill the first sampling gap without adding buffer mass. The first soft prediction, second original prediction, and later saturated states give the stated formulas. These are possibilities, not population frequency estimates.
4. **Enclosure:** each intermediate mass lies between the intersection of endpoint and per-point-cap constraints. Optimizing those feasible precision envelopes yields the stated lower and upper constants. Dynamic recall is nondecreasing because `A<=P0` and the derivative with respect to buffer mass is positive. `T>=P0 R` strengthens the lower integral. These arguments survive complete ties because the continuous feasible envelope is an enlargement of the actual threshold set.
5. **Refinement and information limit:** real-arithmetic nesting is justified by the subblock inequalities; rounding needs interval intersection to preserve nesting, as stated. The indistinguishable-transcript construction is an endpoint-information limit only. It does not constrain the current implementation's ability to inspect already loaded omitted scores, nor adaptive support-event methods. The manuscript makes that restriction explicit.
6. **Integer guarantee:** the audited root brackets, int64 accumulator bound, Python integer nonlinear arithmetic, exact cross-product decisions, and outward float presentation support the implemented guarantee. Existing independent exact-rational and high-precision checks exercise implementation errors; they do not replace the derivation. The resolved NumPy scalar defect is recorded separately in the code-review audit.

## Required wording repairs

These are local precision defects, not requests to alter the proven mechanism.

1. At the start of `sampling_theory.tex`, declare binary labels with both classes, `0<P0<n`, finite score inputs, and nonnegative integer `L`. The public validator enforces this domain. Without it, the all-negative case leaves both the positive denominator and component fraction undefined, so the theorem's stated domain is incomplete.
2. Lines 235–237 of the reviewed theory file call `[R_a^+,R_b^-]` a subset of the actual recall interval unconditionally. Endpoint uncertainty can make the lower limit exceed the upper limit. State: integrate only when `R_a^+<R_b^-`; otherwise this refinement contributes zero. The production implementation already has the appropriate guard.
3. Empirical lines 44–47 report a median and then say “an average narrow interval.” Replace the latter with “a small median interval width.” Maximum widths near one are scientifically important and must remain reported.
4. Abstract line 36 promises that all costs are reported. This becomes true only after the frozen cost collection and complete results are inserted. Keep the statement contingent on that completion, including all timeouts and uncompleted cases if any.

## What the certificate is useful for

A floating-point exhaustive evaluation produces an accurate numerical answer after traversing every relevant score event. It does not by itself return a proof that one model's ideal real-arithmetic value exceeds every competitor. The certificate answers that latter question when its intervals separate. It can also report that the retained information is insufficient instead of turning an approximation into a confident ranking. This is a valid output contract even if it costs more.

That difference should not be sold as a general practical advantage. The full score vectors and support geometry are already available to the current implementation; it has no demonstrated information-access advantage. At the primary budget, 65 of 128 series remain uncertified. Even the improved secondary rate is a conditional success rate on this score bank. For routine comparisons with comfortably separated numerical values, the existing fast exhaustive evaluator may be the preferable practical method. For an application requiring mathematical assurance of a real-valued ordering, the integer certificate offers an explicit stronger guarantee.

The `89/90` case is a useful audit of that contract: it explains why a mathematically valid interval need not contain a particular rounded sum. Its approximately `7.63e-16` discrepancy is not evidence of a meaningful detector-ranking error or of improved operational utility. The actual ordering decisions must continue to use integer endpoints, not an epsilon around the float reference.

A same-output-contract cost comparison would use exhaustive/support-event integer enclosures or another rigorous exhaustive evaluator. Comparing only against float exhaustive evaluation measures the price of the stronger guarantee; it cannot establish certificate efficiency over equally rigorous alternatives. No superiority claim is necessary for the current contribution. If the paper later claims that certification is an efficient way to obtain rigorous decisions, it needs this additional baseline and a complete fallback policy/cost accounting.

Suggested practical-positioning sentence:

> The certificate converts a sampled metric into a sufficient test for the ideal exhaustive ordering. On this panel it confirms a subset of sampled selections; it does not improve those selections, and its extra arithmetic may cost more than ordinary exhaustive numerical evaluation.

## Remaining scientific decision after the frozen runs

The critical empirical question is whether the fixed, published detector panel exhibits meaningful threshold-induced regret under the default setting. Report the primary rule exactly, including a negative result. Sensitivity settings, constructed failures, and the stronger arithmetic contract cannot substitute for that primary prevalence result. Cost findings must be reported separately from correctness and mathematical soundness.

A strong final paper can be an evaluation-fidelity study with a precise failure mechanism and a verifiable remedy; it need not be advertised as a faster algorithm. However, this internal review supplies no basis to promise acceptance or to promote the unfinished practical evaluation to a positive result. The substantive theoretical claims survived this review with the local domain/empty-interval wording repairs above.
