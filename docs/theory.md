# Exact scalar VUS by eliminating inactive threshold events

This note proves an algorithmic identity for the pinned dynamic-label VUS
calculation. It does not introduce a new accuracy metric. The target is
`RangeAUC_volume_opt` in TheDatumOrg/VUS at commit
`467bace0c103f5c2bdb4900306d82939bcac8ff9`, with all distinct score thresholds.
The released default grid of 250 sampled thresholds is a different numerical
approximation; equality to that grid is not claimed.

## 1. Definitions and scope

Let `y` be a binary vector of length `n`, with both classes present, and let
`s` be finite real scores. A larger score indicates a stronger anomaly.
Let `p = sum(y)` and let `L >= 0` be the maximum integer buffer width.
The scalar output averages buffer-specific ROC and PR integrals over
`w = 0,...,L`. All equal scores enter at the same threshold.

For width `w`, extend each maximal positive-label interval by `floor(w/2)`
positions at each end, clipped to the data boundaries. On an extended position
at distance `d` from that interval, add `sqrt(1 - d/w)` to its label. Add all
interval contributions and cap at one. Write the resulting weight as `a_w(i)`.
At widths zero and one there are no added positions. Original positive
positions always have weight one.

Merge expanded intervals if they overlap, retaining merely adjacent intervals
as distinct segments. Let `K_w` be the number of resulting segments. For a
threshold `t`, prediction means `s_i >= t`. Define:

\[
\begin{aligned}
C(t)&=\#\{i:s_i\ge t\},\\
T_w(t)&=\sum_{s_i\ge t}a_w(i),\\
B_w(t)&=\sum_{s_i\ge t}(1-y_i)a_w(i),\\
H_w(t)&=\#\{\text{expanded segments containing a predicted position}\},\\
P_w(t)&=p+B_w(t)/2,\qquad N_w(t)=n-P_w(t),\\
R_w(t)&=\min\{T_w(t)/P_w(t),1\}\,H_w(t)/K_w,\\
F_w(t)&=(C(t)-T_w(t))/N_w(t),\qquad
A_w(t)=T_w(t)/C(t).
\end{aligned}
\]

`R` is the range recall, `F` the false-positive coordinate, and `A` precision.
The scalar ROC calculation sums trapezoids through the initial `(0,0)`, the
threshold points, and a terminal `(1,1)`. The PR calculation sums
`(R_j-R_{j-1}) A_j` over threshold points; it does not use a trapezoidal PR
rule. These choices, including the changing denominator, are part of the
target computation. Repeated thresholds add zero increments.

All divisions are defined: `0 <= B <= n-p` implies `P >= p > 0` and
`N >= (n-p)/2 > 0`; every nonempty threshold event has `C >= 1`, and
the presence of a positive label ensures `K_w >= 1`.

Every point in an expanded segment has positive weight: merged expansions
have no gap, and the added ramps are positive on their inclusive support.
Thus `H` can be found from the maximum score in each expanded segment.

## 2. Support and event compression

Let `U` be the union of all expanded intervals at maximum width `L`, and set
`Q = |U|`. All positive weights at every width lie in `U`. Let
`v_1 > ... > v_G` be the distinct scores at positions in `U`; `G <= Q`.
Define two global counts for each such score:

\[
c_j^- = \#\{i:s_i>v_j\},\qquad c_j^+ = \#\{i:s_i\ge v_j\}.
\]

They count all data positions, including positions outside `U`. This is
essential for retaining the false-positive contribution of off-support
scores, including ties with support scores.

For a fixed width, let `T_j,B_j,H_j,R_j,N_j` be the values after all positions
with score `v_j` have entered. Use initial values
`T_0=B_0=H_0=R_0=c_0^+=0` and `N_0=n-p`.

**Lemma 1 (inactive thresholds).** Between the preceding support event and
`v_j`, `T,B,H,R,N` remain constant; only `C` changes.

*Proof.* Every entering position in this interval lies outside `U`, hence has
zero weight at every width and is outside every expanded segment. It cannot
change weighted positives, predicted ramp mass, or existence. The denominator
and recall are functions of those unchanged quantities. Only the number of
predictions increases. The same reasoning applies before the first support
event and after the last. ∎

Define

\[
f_j^-=(c_j^- - T_{j-1})/N_{j-1},\qquad
f_j^+=(c_j^+ - T_j)/N_j.
\]

**Theorem 1 (exact event elimination).** The full-threshold ROC integral equals

\[
\sum_{j=1}^G\left[
 \frac{(c_j^- - c_{j-1}^+)R_{j-1}}{N_{j-1}}
 +(f_j^+-f_j^-)\frac{R_j+R_{j-1}}2\right]
 +\frac{(n-c_G^+)R_G}{N_G}
 +\left(1-\frac{n-T_G}{N_G}\right)\frac{1+R_G}{2}.
\]

The full-threshold PR integral equals

\[
\sum_{j=1}^G (R_j-R_{j-1})\frac{T_j}{c_j^+}.
\]

*Proof.* By Lemma 1, every ROC segment between support events has the same
recall `R_{j-1}`. Its trapezoidal integral is a rectangle. Summing those
rectangles telescopes to the first summand. The support event itself enters
all tied scores simultaneously and is exactly the displayed trapezoid from
`(f_j^-,R_{j-1})` to `(f_j^+,R_j)`. After the final support event, the
remaining off-support points give the final rectangle. The prescribed
terminal point gives the final trapezoid. This is an algebraic identity for
the reference's ordered trapezoidal sum; it does not require an additional
monotonicity assumption about the false-positive coordinate.

For PR, every inactive step has zero recall increment, regardless of its
precision. Its contribution vanishes. Only support-event recall increments
remain, and their precision uses the full tied prediction count `c_j^+`. ∎

The theorem preserves the scalar integrals, not every plotted point of the
full ROC or PR surfaces. An interface that emits every surface point has a
different output-size requirement.

## 3. Computing the support states

**Lemma 2 (two nearest intervals suffice).** For a non-positive position,
its extended weight is zero if no original interval is within
`floor(w/2)`, equals the nearest interval's ramp if precisely one is within
that radius, and equals one if at least two are within that radius.

*Proof.* Each active ramp is at least `sqrt(1/2)`. Two active contributions
already exceed one, so clipping makes further contributions irrelevant.
The original intervals are disjoint and ordered. The two nearest intervals
can be found among the two neighboring intervals on either side of a
position's insertion point in the ordered start coordinates. ∎

Precompute the two nearest interval distances for each position in `U`.
For each width, the weights then require constant work per support position.
Aggregate weighted positives and weighted ramp mass by support-score group,
then take prefix sums in descending score order to obtain `T_j` and `B_j`.
Merge intervals for that width. For each merged segment, find its first
support-score group; histogramming these first groups and taking a prefix
sum gives `H_j`. A sweep over position-ordered support points and interval
endpoints implements this in linear support size.

## 4. Complexity

**Theorem 2.** The scalar ROC and PR values for all `L+1` widths can be
computed in

\[
O(n\log(Q+1)+(L+1)Q)
\]

time and `O(n+Q+L)` auxiliary space in the present array implementation.
The compiled scalar kernel can accumulate width averages without storing
the `O(L)` per-width output.

*Proof.* Extracting original intervals and the maximum support takes
`O(n+Q)` work. Sorting support scores takes `O(Q log(Q+1))`. For every one
of the `n` scores, binary search in the sorted distinct support values
identifies its interval or equality class. Histograms yield all `c^-` and
`c^+` counts in `O(n log(G+1)+G)` work without sorting off-support scores.
The two nearest interval distances take `O(Q log(K+1))`, where the number
of original intervals satisfies `K <= Q`. For each width, expansion merging,
weight calculation, support-state accumulation, and integration take
`O(K+Q+G)=O(Q)` work. Since `Q <= n` and `G <= Q`, the stated bound follows.

Current preprocessing uses several length-`n` arrays and length-`Q` support
arrays, while per-width accumulation needs `O(Q)` space. Optional per-width
return values need `O(L)` space. No threshold-by-position or
threshold-by-width matrix is materialized. ∎

This improves the width-dependent work of a dense exact rank sweep from
`O((L+1)n)` to `O((L+1)Q)`, and replaces its full-score sorting stage by
support sorting plus rank counting. It does not guarantee a runtime
improvement when `Q` approaches `n`; that regime is retained in the
benchmark. Floating-point executions are compared with explicit absolute
tolerances. The algebraic identity is exact over real arithmetic and does
not imply bitwise equality under different summation orders.

## 5. Prior-art boundary

- The original VUS metric and its static/dynamic-region optimization belong
  to Paparrizos et al. (2022) and Boniol et al. (2025). Support restriction
  alone is not the contribution here.
- The proposed contribution is the exact inactive-event integration identity
  together with counting all off-support scores against support events,
  without globally sorting those scores. The two-nearest-interval observation
  supplies a compatible linear-per-width weight calculation.
- The actual `dtaianomaly` implementation dated 2026-10-13 is included as an
  external compiled comparator. Its support-only loops evaluate a supplied
  threshold grid, whereas this algorithm eliminates inactive events while
  preserving the full-grid scalar.
- The 2025 VLDB Ph.D. workshop report by Sylligardos describes accelerated
  CPU/GPU VUS work. Its published speed claims are prior art, not a measured
  competitor result in this artifact. A claim of being the first accelerated
  VUS implementation would be incorrect.

Sources: [VUS paper](https://arxiv.org/abs/2502.13318),
[pinned VUS code](https://github.com/TheDatumOrg/VUS/tree/467bace0c103f5c2bdb4900306d82939bcac8ff9),
[pinned dtaianomaly code](https://github.com/ML-KULeuven/dtaianomaly/blob/557b435790bebc57307d8e7f22047273ac923f36/dtaianomaly/evaluation/_volume_under_surface_metrics.py),
[Sylligardos workshop paper](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/PhD/PhD25_17.pdf).
