# Threshold-sampling challenge: constructive overestimation and enclosures

Date: 2026-10-23. Status: exploratory mathematics with executable witnesses;
not a new measured corpus result, timing benchmark, or external peer review.

## Target and distinction from the existing appendix

The target is the manuscript's pinned dynamic VUS-PR, averaged over every
integer width `0..L`. A threshold admits the complete numerical score tie.
At a fixed width, `T=A+B`, `P=P0+B/2`,
`R=min(T/P,1) H/K`, and precision is `T/C`. PR integrates right steps.
All counterexamples below use distinct, finite integer-valued scores.

The unchanged Klein source at revision `1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00`
uses the descending scores at zero-based indices
`np.linspace(0,n-1,H).astype(int)`, with complete ties through `searchsorted`.
For `n=1+(H-1)q`, its sampled one-based counts are exactly
`1,1+q,...,n`. The source SHA-256 is
`15b7afb94da0e1f1b1c408fe44b937d910935c19f8eb76f42ae6719f9cfcb52b`.
[Pinned source](https://github.com/tomlouisklein/fast-VUS/blob/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py)

`paper/main.tex`, Appendix “A fixed uniform-rank grid can lose almost all
PR area,” already proves near-unit **underestimation** at any fixed `L,H`.
That old proof is not a newly discovered result. The distinct candidate
result here is large **overestimation caused by post-saturation buffer
mass**, together with same-label high-regret ranking witnesses at
`H=250`, `L=30,100,300`, and an elementary threshold-wise enclosure.

## Proposition 1: a finite, exactly specified sampling family

Choose integers `H>=2`, `1<=m<q`, `n=1+(H-1)q`, and
`floor(L/2)<n-m`. Put the only original positive at temporal position 0.
Order scores descending as follows:

1. The last `m` temporal positions `n-m,...,n-1`.
2. The original positive at position 0.
3. Positions `1,...,n-m-1` in increasing temporal order.

Assign distinct scores `n,n-1,...,1` in that order. The first `m` positions
are outside the support of every width `0..L`. Until the original is
admitted, both true-positive mass and recall are zero. At its rank `m+1`,
true-positive mass, existence and recall become one. All later recall
increments vanish. Therefore **every width** has exact PR `1/(m+1)`,
and the same equality holds for VUS-PR.

The first sampled threshold contains one inactive point and has recall
zero. The second contains the original and the nearest `q-m` buffer
positions, besides the `m` inactive points. The original alone guarantees
recall one at that threshold, for every width. Define

`B_w = sum_{d=1}^{min(q-m,floor(w/2))} sqrt(1-d/w)`, with `B_0=0`.

The sampled scalar is exactly

`S = [1 + (L+1)^(-1) sum_{w=0}^L B_w] / (q+1)`.

The family does not overestimate for every parameter choice: at `L=0`,
for example, `S=1/(q+1)<1/(m+1)`. The executed regimes below and the
proved large-width regime specifically establish overestimation.

Thus the post-saturation buffer mass increases the precision assigned by
the sampled integral to the entire recall jump, while it contributes zero
PR area to the exact integral. This mechanism specifically uses dynamic
soft labels and clipped recall; it is not the width-zero AP loss example.

For `L>=2q`, the bound `sqrt(1-x)>=1-x` gives the finite inequality

`S >= { (L-2q+1)(q-m+1)
        - [(q-m)(q-m+1)/2] sum_{w=2q}^L 1/w }
       / [(L+1)(q+1)]`.

Only widths `2q..L` were retained in that lower bound; all omitted terms
are nonnegative. Take fixed `H>3`, `L=(H-1)q=n-1`, `q->infinity`,
`m->infinity`, and `m/q->0`. The exact scalar tends to zero, while

`liminf S >= 1 - 2/(H-1) - log((H-1)/2)/(2(H-1))`.

At `H=250` this bound is approximately `0.9822805106`. The regime here
has `L=n-1`; do not describe it as a usual small-width workload.
The asymptotic statement is about the real-arithmetic mathematical family,
not an unbounded collection of distinct binary64 scores. All executed
instances and the finite witness below have `n<2^53`, so their consecutive
integer scores and integer-spaced sampled ranks are exactly representable.

There is also a wholly finite, rational check: `H=250`, `q=2,000,000`,
`m=1000`, `n=498,000,001`, `L=498,000,000`. Since
`sum_{w=2q}^L 1/w < log(L/(2q-1)) < 5`, the sampled scalar exceeds
`977516488501501/996000500000001`. Subtracting exact value `1/1001`
is strictly greater than `98/100`, verified using `fractions.Fraction`.
The inequality `log(L/(2q-1))<5` follows from the degree-7 positive Taylor
lower bound for `exp(5)`. **No huge array was allocated and this finite
instance was not executed through an evaluator.** It is an exact symbolic
lower-bound check, separate from the smaller executed witnesses below.

## Same-label reversal at standard fixed widths

For a second score vector, place one nearby buffer position `d` first and
the original at position 0 second. Fill the remaining `q-1` positions of
the first sampling gap with far outside-support negatives. Rank every
other point later. For the script's choice of the last `q-1` temporal
positions, sufficient feasibility conditions are
`n-q+1>floor(L/2)` and `1<=d<n-q+1`; every table row satisfies them.
At width `w<2d`, its exact PR is `1/2` and its sampled
PR is `1/(q+1)`. At width `w>=2d`, write

`a=sqrt(1-d/w)` and `r=a/(1+a/2)`.

The exact and sampled per-width values are respectively

`E_B(w) = r*a + (1-r)*(1+a)/2`,

`S_B(w) = r*a + (1-r)*(1+a)/(q+1)`.

The original saturates recall at the second actual score threshold, so
all later thresholds contribute zero exact PR. The sampled method delays
the remainder of this recall mass until its next retained threshold.

The following constructive cases were executed, each over **all** widths
`0..L`, with `H=250`. A is the overestimation construction above.

| L | n | q,m,d | Exact A | Sampled A | Exact B | Sampled B | Exact regret of sampled winner |
|---|---:|---|---:|---:|---:|---:|---:|
| 30 | 2,491 | 10,3,5 | 0.250000000 | 0.506412087 | 0.757142307 | 0.418181118 | 0.507142307 |
| 100 | 4,981 | 20,4,5 | 0.200000000 | 0.624742871 | 0.900579669 | 0.569008459 | 0.700579669 |
| 300 | 9,961 | 40,6,1 | 0.142857143 | 0.706288889 | 0.989248897 | 0.668766840 | 0.846391754 |

For every row the exact winner is B, the sampled winner is A, and both
ordering margins are positive. These are same-label, distinct-score
witnesses; there is no rounding, tie splitting, change of ramp semantics,
or substitution of an alternative VUS definition.
The pinned library correctly executes its configured sampled target;
the disagreement concerns the sampling approximation to the exhaustive
integral and is not a claim of an implementation bug in that library.

The script verifies both vectors against: the closed forms above; the
independent dense implementation; the compiled saturation evaluator; and
the **unmodified** pinned fast-VUS module with `H=250` and `H=n`.
These examples establish possibility and mechanism, not prevalence among
real detectors or superiority under an operational anomaly utility.
Parameters were chosen during exploration rather than preregistered as a
statistical study. Other exploratory choices were considered; these are
not an estimated distribution of ranking errors.

## Proposition 2: a bidirectional threshold enclosure

Fix any width and take two adjacent retained complete threshold states
`(c_a,t_a,r_a)` and `(c_b,t_b,r_b)`, where `c` is predicted count, `t` is
true-positive mass and `r` is dynamic recall. Include the initial zero
state. Repeated sampled states contribute zero and may be discarded.
For `c_b>c_a`, let `delta=t_b-t_a`. All temporal weights lie in `[0,1]`.
For every intermediate complete threshold with count `c` and mass `t`,

`max(t_a, t_b-(c_b-c)) <= t <= min(t_b,t_a+c-c_a)`.

Optimizing these envelopes divided by `c` gives

`ell = t_a/(c_b-delta) <= precision <= t_b/(c_a+delta) = u`.

For the lower bound, if `c<=c_b-delta`, use `t_a/c`; otherwise use
`1-(c_b-t_b)/c`. Both are minimized at `c_b-delta`. For the upper
bound, use the analogous increasing and decreasing pieces meeting at
`c_a+delta`. The continuous optimizer is valid for integer counts and
complete ties because it optimizes over a superset of their possible
counts. If `c_b-delta=0`, all admitted weights are one and precision is
identically one; set `ell=1`. If `delta=0`, recall cannot change and the
block contributes zero, so no `0/0` evaluation is needed.

Dynamic recall is nondecreasing in descending score order. Indeed,
`(A+B)/(P0+B/2)` increases in each of `A,B`: the derivative in B has
numerator `P0-A/2>0`; original count `A<=P0`. Clipping and multiplication
by the nondecreasing nonnegative existence factor preserve monotonicity.
Thus every recall increment in a block is nonnegative, and its exact PR
contribution lies between `(r_b-r_a)ell` and `(r_b-r_a)u`.

The dynamic target additionally satisfies `T>=P0 R`. Since `C<=c_b`,
precision is at least `P0 R/c_b` at each contributing event. The stronger
lower bound is therefore

`integral_{r_a}^{r_b} max(ell, P0*r/c_b) dr`.

This follows because the exact PR uses right endpoints and the integrand
is nondecreasing. It is not an assumption that precision is monotone.
With `alpha=P0/c_b` and `v=clamp(ell/alpha,r_a,r_b)`, the integral is

`ell*(v-r_a) + alpha*(r_b^2-v^2)/2`.

Sum the block bounds, then average them over widths, to obtain `[lower,
upper]` containing exact VUS-PR. Consequently the sampled-to-exact error
lies in `[lower-sampled,upper-sampled]`; it can have either sign. For two
models, `lower_A>upper_B` certifies that A has larger exact VUS-PR. The
usual all-competitor inequality certifies a unique winner.

Refining a block by retaining an intermediate threshold can only increase
its lower bound and decrease its upper bound. To see this, note that
`c-t` is nondecreasing. The two mass-envelope constants on either subblock
are at least the parent's `ell` and at most the parent's `u`. The extra
linear lower envelope `P0*r/c_b` also grows when the subblock's right count
decreases. Thus blockwise integration and summation preserve nesting.
These bounds can still be loose; they do not necessarily become point
values when a retained complete tie admits several positions. If it is
known that a block has no omitted distinct threshold, its contribution
can instead be replaced by the exact observed right-step term.

This is an **exact real-arithmetic theorem**. The exploratory NumPy code
does not use directed rounding and does not issue machine-certified
Float64 intervals. In 20,880 checked enclosure instances the largest apparent
endpoint violation was `1.1102230246251565e-16`, consistent with arithmetic
rounding; allowing a tolerance in those checks is not a proof of a global
Float64 error bound. The count includes all binary labels/scores for
lengths 2 through 5 (both label classes), four widths, three grid budgets,
and 500 seeded random tied-score fixtures. It includes zero width,
boundary intervals, overlap, adjacent components, complete global ties,
all-score ties and repeated sampled thresholds.

## Sampled-state indistinguishability

For completeness, there is a direct limitation of any certificate that
only sees sampled sufficient states. Fix `H>=3` and L, put a contiguous
original interval of length m away from boundaries, and choose q much
larger than m and L. In ordering A, put one off-support negative first,
then all originals, then off-support negatives up through rank q+1. In
ordering B, put the same number of off-support negatives first, then all
originals at ranks q-m+2 through q+1. Keep all buffer scores and the entire
tail identical between orderings. At every sampled threshold and every
width, `(C,A,B,H)` is identical; so both sampled PR and ROC surfaces are
identical. Nevertheless their exact PR values are

`E_A=(1/m) sum_{j=1}^m j/(j+1)`,

`E_B=(1/m) sum_{j=1}^m j/(q+1-m+j)`.

As m grows and q/m grows, `E_A->1` and `E_B->0`. Therefore any interval
guaranteed to contain the exact PR for all score vectors consistent with
these sampled states must have width approaching one. This does not apply
to methods that inspect omitted support scores or adapt their thresholds.
It also explains why a sound endpoint-only enclosure may remain wide.
This argument is closely related to ordinary AP information loss and
should not be presented as an independently deep new theorem.

## Novelty assessment and integration recommendation

The generic statement that coarse PR curves lose information is old, and
the existing manuscript already proves arbitrary underestimation. The
stronger specific finding here is the dynamic-buffer **overestimation**
mechanism and its exact high-regret witnesses at the ordinary widths used
in the artifact. That creates a concrete consequence for using exact
evaluation: it can change the numerical model-selection decision by a
large margin even with distinct scores and identical labels.

The mass-envelope enclosure is mathematically elementary. Its VUS
instantiation and the `T>=P0 R` refinement are useful, but a literature
search of quadrature, weighted AP approximation and certified ranking is
needed before any priority claim. A bounded primary-source search of
VUS/threshold/overestimation on 2026-10-23 did not establish priority or
universal absence of this result. The inspected
[VUS paper](https://arxiv.org/html/2502.13318v1) studies metric robustness
and efficient implementations; its discussion of threshold independence
must not be confused with a theorem that its finite integration grid
equals exhaustive integration.

Recommended integration: a compact theorem and the three same-label
ranking witnesses can strengthen motivation and scientific consequence.
Retain the enclosure as a clearly scoped auxiliary result unless a useful
implementation and real-workload certification rate are independently
measured. Do not call these exploratory witnesses a fresh held-out corpus,
a new detector, or evidence of operational detector quality.

## Reproduction

`PYTHONPATH=src python experiments/exploration/sampling_theory_20261023.py`

requires the already pinned fast-VUS cache and the project's NumPy/Numba
dependencies. It prints a source-bound JSON receipt and never alters
production modules or frozen experiment results. The actual receipt from
this run is in `experiments/exploration/sampling_theory_20261023.json`.
