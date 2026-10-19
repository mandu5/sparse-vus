# Independent automated theory-review addendum

Reviewer: **automated independent agent**, separate from the implementation agent. This is not human peer review, a novelty assessment, publication readiness, or acceptance. Completed 2026-10-19T14:33:09.979022+00:00. Scope: read-only mathematical review of `docs/theory.md`, checked against `core.py`, `compiled.py` and the previously inspected pinned reference. No CPU-heavy tests or timing work were performed during this addendum; earlier numerical evidence remains in [independent_core_review.md](independent_core_review.md).

**Verdict:** no Critical, Important, or theorem-blocking objection found. The stated exact-arithmetic identity and asymptotic bounds are supported by the reviewed definitions and implementation.

- Event boundaries: `c_j^-` counts every score strictly above the event and `c_j^+` includes all ties. The inactive rectangle spans `c_j^- - c_(j-1)^+` using the old state and denominator. The following trapezoid spans the actual tied event, including off-support points tied to support points. No interpolation through omitted support transitions is introduced.
- PR discontinuities: inactive thresholds may change precision but have zero recall increment. At a retained event, the reference's right-endpoint precision is exactly `T_j/c_j^+`. Repeated equal-score thresholds duplicate both state and coordinates and add zero area. The formula correctly omits any artificial terminal PR contribution.
- Terminal ROC handling: after the last event, all remaining positions are off-support. They produce the displayed rectangle ending at `( (n-T_G)/N_G, R_G )`; the final displayed trapezoid reaches the reference's explicit `(1,1)` endpoint. The last support event alone need not have FPR equal to one.
- Existence/support: every integer point of each expanded segment has positive weight. Overlapping expansions have no uncovered gap, while adjacent intervals remain distinct exactly as required by the pinned semantics. Width-w support lies in maximum-width support U, so a point outside U cannot change existence, weighted TP or buffer mass at any width.
- Nearest-two argument: every active ramp is at least sqrt(1/2); two ramps saturate the sum-and-clip rule. Original intervals are disjoint and ordered, so distances to intervals on the left increase as their right endpoints move left, and distances on the right increase as their starts move right. Therefore the two nearest distinct intervals occur among the two candidates on each side of the insertion point. Containing original intervals need no ramp calculation because original labels stay one.
- Time bound: Q is maximum-support **position count**, G is distinct support-score count, and K<=Q. The O(Q log Q), O(n log(G+1)) and O(Q log(K+1)) preprocessing costs are absorbed by O(n log(Q+1)), since Q<=n. Each width visits O(Q+K+G)=O(Q). With L+1 widths the stated bound follows, including L=0 and G=1.
- Space bound: O(n+Q+L) is faithful to the NumPy implementation's full-length maps/histogram intermediates, support arrays and stored per-width results. The compiled scalar kernel can average without O(L) result storage. The earlier shorter O(n+Q) statement should only describe that scalar accumulation variant; the current theory document makes the distinction.

One **Minor proof-completeness suggestion was resolved during review**: the author added, and the reviewer read back, the explicit denominator-positivity argument immediately after the definitions. The argument is `0 <= B_w(t) <= n-p`, hence `P_w(t) >= p > 0` and `N_w(t) >= (n-p)/2 > 0`. The text also states `K_w>=1` and `C>=1` at each threshold event; `G>=1` follows from the positive label assumption. These facts establish that every displayed division is defined. The snapshot hash below includes this correction. No counterexample was associated with the suggestion.

Optional exposition improvement: include the monotone endpoint-distance sentence above in Lemma2's proof rather than leaving the four-candidate argument implicit. This does not require an algorithm change.

The note's distinction between real-arithmetic identity and finite-precision execution is appropriate. This review did not verify completeness of the prior-art search, the final paper, benchmark conclusions or external runtime comparisons. Those remain separate review tasks.

Reviewed snapshot hashes:

| File | SHA-256 |
|---|---|
| `docs/theory.md` | `2ec4d416f723d751af9a0ec2d5e4044e8832f511472f3f339fcaac2cf79cee04` |
| `src/sparse_vus/core.py` | `f7e227f3bfea58c72da8feba0c7daa36460695db8ab10106706f845d45374e2b` |
| `src/sparse_vus/compiled.py` | `3b73ea67e23d92c00018d9a31646bac3bc03b781caca3dfa5ef9155fa47c2f32` |
