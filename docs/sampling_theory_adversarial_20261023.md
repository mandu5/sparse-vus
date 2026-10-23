# Independent adversarial review of the sampling theory

Review date: 2026-10-23. Reviewed `docs/sampling_theory_challenge_20261023.md`, its exploration script and JSON receipt, the dense implementation, and the unchanged pinned Klein source and adapter. This review changed no implementation or original receipt.

## Finding

No fatal mathematical defect was found in the scoped dynamic VUS-PR overestimation construction, the three reported same-label ranking reversals, or the real-arithmetic block enclosure. The conclusions require the original sum-and-clip square-root weights, dynamically adjusted positive mass, merged-overlap existence, complete score ties, and right-step PR integration. They do not automatically transfer to other VUS contracts.

The contribution supported by these results is a constructive failure mechanism and an exact-integration consequence. The witnesses establish possibility, rather than frequency on real detectors, practical utility, or acceptance by a venue.

## Corrections and explicit conditions

1. **The family does not overestimate for every admissible parameter.** At `L=0`, its sampled value is `1/(q+1)`, strictly below exact `1/(m+1)` because `m<q`. An additional replay with `H=2,q=5,m=1,L=6` gives exact `0.5` and sampled `0.338148421395624`. Call it a parameterized family exhibiting overestimation in the proved regimes and reported instances; do not assert universal positive error from the initial parameter conditions alone.
2. **Make competitor B's feasibility explicit.** For the implementation's last `q-1` positions to be outside every support and disjoint from its first position, sufficient conditions are `n-q+1 > floor(L/2)` and `1 <= d < n-q+1`. Together with the existing integer conditions these justify the stated ordering. All three table rows satisfy them. The first construction's weaker condition `floor(L/2)<n-m` alone does not guarantee the competitor can be formed this way.
3. **Keep zero-mass reasoning contract-specific.** Here the positive-weight support equals the union of expanded coverage intervals. Thus no additional mass implies no original admission, buffer admission, or coverage hit, so `delta=0` implies unchanged recall. This implication need not hold for a different contract with zero-weight coverage positions.
4. **Use “20,880 enclosure instances.”** The existing counter increments once per label/score fixture, width, and grid budget, rather than once per internal sampled block.
5. **“Across all widths” refers to the averaged VUS integral.** The reported reversed winners concern the mean over every integer width `0..L`; they are not a claim that each separate width reverses the ordering. At width zero the two sampled values in these constructions tie.

The current document already fixes two additional boundary issues: sampled-state indistinguishability requires `H>=3` in the construction that leaves all buffer scores in the common tail, and the unbounded asymptotic is explicitly a real-arithmetic family rather than infinitely many distinct binary64 integers.

## Proof audit

### Overestimation construction

The first `m` admissions are outside the largest support. Admission `m+1` is the only original positive, which gives `T=1`, `P=1`, existence one, and recall one. Every later exact recall increment is zero. Hence exact PR is `1/(m+1)` at each width, even though later admitted soft mass can increase precision. The second sampled threshold has exactly `q+1` admissions and includes precisely the nearest `q-m` temporal positions in addition to the original and the far negatives. This proves the stated sampled expression.

The lower bound follows by retaining only widths `2q..L` and replacing each square root with `1-d/w`. It deliberately drops nonnegative early-width contributions. Under `L=(H-1)q`, `m/q -> 0`, the first normalized term tends to `1-2/(H-1)` and the normalized harmonic term tends to `log((H-1)/2)/(2(H-1))`. Taking `m -> infinity` also makes exact PR vanish. For fixed `H>3` the support restriction is eventually satisfied. The construction requires no interchange of an infinite sum and a limit.

The finite witness is valid independently of the asymptotic. The integral comparison gives `sum_{w=2q}^L 1/w < log(L/(2q-1))`. The positive degree-seven Taylor truncation for `exp(5)` exceeds `L/(2q-1)`, proving the latter logarithm is below five. Exact Fraction arithmetic independently reproduced

```
sampled lower bound = 977516488501501/996000500000001
error lower bound   = 977498004490002500/996996500500001001 > 98/100.
```

No metric evaluation on the approximately 498-million-point instance is implied. The integer scores for that finite witness are below `2^53`.

### Block enclosure, zero cases, and refinement

Let `delta=t_b-t_a`. Since each admitted weight is in `[0,1]`, `0<=delta<=c_b-c_a`; both optimizer counts `c_b-delta` and `c_a+delta` lie within the block. Dividing the lower mass envelope by `c` gives a decreasing piece `t_a/c` followed by an increasing piece `1-(c_b-t_b)/c`. Their junction yields `ell=t_a/(c_b-delta)`. The upper envelope has the reverse monotonicity and yields `u=t_b/(c_a+delta)`.

If `c_b-delta=0`, necessarily `c_a=t_a=0` and every admitted weight is one; setting `ell=1` is valid. The upper denominator can vanish only when `c_a=delta=0`; the block then has zero recall increment and is discarded. Complete ties and integer counts restrict the admissible thresholds, so optimizing over the continuous count interval remains conservative.

For `P0>0`, `(A+B)/(P0+B/2)` is nondecreasing in both admitted original mass and buffer mass; its buffer derivative has numerator at least `P0/2>0`. Clipping and the nondecreasing, nonnegative existence factor preserve monotonicity. Also `R<=T/P<=T/P0`, hence `T>=P0 R`. With `C<=c_b`, event precision is at least `P0 R/c_b`. The right-endpoint integration of a nondecreasing lower envelope bounds the continuous integral below, proving the stronger lower bound without assuming precision itself is monotone.

Refinement is sound. Write the false-positive mass as `f=c-t`, which is nondecreasing. For an intermediate state `(c_i,t_i)`, each child's lower mass ratio is at least the parent's and each child's upper ratio is at most the parent's. The left child's coefficient `P0/c_i` is at least `P0/c_b`; the right child's is unchanged. Integrating over the two recall intervals proves nesting. These bounds can remain wide even with every tie retained; when no distinct threshold is omitted, substituting its observed exact right-step contribution is the correct way to collapse that block.

These are real-arithmetic statements. The existing floating implementation uses no directed rounding. Its numerical tolerance is not a machine certificate and should not authorize a formally certified winner claim.

### Sampled-state indistinguishability

For `H>=3` and sufficiently large `q` relative to `m,L`, the original interval and all of its halo fit away from the boundaries, and at least `q+1-m` off-support positions exist. Both orders admit the same off-support first point and exactly the same set by rank `q+1`; the tail is identical. All sampled sufficient states therefore match at every width. Buffer mass remains zero while the originals are admitted, giving the two displayed ordinary-AP expressions. The lower bound applies to methods restricted to this sampled transcript, even if labels and the common score multiset are known. It does not apply to algorithms inspecting omitted score positions or choosing adaptive thresholds.

## Independent executable checks

The following checks were run during this review, without editing source or original receipts:

- Verified all five SHA-256 values in the existing JSON receipt against current files: exploration script, core, saturation evaluator, adapter, and cached Klein source. All match.
- Replayed the original 20,880 enclosure instances using `/opt/anaconda3/bin/python`. Largest apparent floating endpoint violation was again `1.1102230246251565e-16`.
- Replayed the complete `L=30` same-label witness, including independent dense values, the compiled evaluator, sampled dense evaluation, and unmodified Klein at both 250 and exhaustive thresholds.
- Independently recomputed all three table rows using direct scalar closed forms and `math.fsum`, without importing repository metric functions. Maximum difference from the receipt was `5.551115123125783e-16`. The three exact regrets were `0.5071423069553272`, `0.7005796694237083`, and `0.8463917538280048`.
- Independently checked **84,415 block enclosures and 135,370 nested refinements with exact rational arithmetic**, with zero violations. Enumeration used all streams of lengths two through six over original weight one, soft weight one, soft weight one-half, and inactive weight zero, retaining streams with at least one original. At each admission the state was `(C,A+B,min((A+B)/(P0+B/2),1))`. Every subinterval and every internal split was checked. This tests the algebra over a broader admissible weight space, with one coverage component; it is not a new temporal detector corpus. Multiple-component coverage, temporal overlaps, and complete ties are covered by the original fixture replay and the proof.
- Independently rechecked the finite large witness using `fractions.Fraction`; the strict error lower bound above is exact.

This review supports incorporating the scoped theorem and constructive consequences. It supplies no performance evidence for the proposed enclosure implementation, no prevalence estimate, and no priority claim beyond the separately documented bounded literature review.
