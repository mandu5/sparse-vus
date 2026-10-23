# Integer-directed certificate for threshold-sampled dynamic VUS-PR

Date: 2026-10-23. This document specifies a mathematically enclosing
integer algorithm for the **ideal real-arithmetic** target in the paper.
It does not assert a bitwise identity with a particular floating-point
implementation's accumulated result. The independent spike is
`experiments/exploration/sampling_bigint_certificate_20261023.py`.

## 1. Exact brackets for dynamic weights

Choose nonnegative weight precision b and set `D=2^b`. Original positives
have bracket `[D,D]/D`. A non-original point outside the current support
has `[0,0]/D`. If two original intervals contribute nonzero ramps, both
ramps are at least `sqrt(1/2)`, so sum-and-clip gives exact weight one.

Otherwise one interval contributes at integer distance d, with
`0<=d<=floor(w/2)` and `w>0`. Let

`z=(w-d)*D^2`, `q=isqrt(z//w)`.

Then `q^2*w<=z<(q+1)^2*w`, so `q/D<=sqrt(1-d/w)<(q+1)/D`.
If `q^2*w==z`, the exact bracket is `[q,q]/D`; otherwise it is
`[q,q+1]/D`. These claims use integer multiplication, division and square
root only. No libm square root or floating-point epsilon is involved.
Every upper numerator is at most D.

At a threshold, let A be the exact original-positive count and let
`B_lo,B_hi` be sums of the integer brackets of admitted buffer points.
Then total mass has numerators `T_lo=A*D+B_lo` and `T_hi=A*D+B_hi`.
All counts and sums in this derivation are arbitrary-precision integers.
A fixed-width implementation must prove its accumulator bounds separately;
Python integers have no overflow at these steps.

## 2. Directed recall endpoints

Choose output precision e and set `S=2^e`. H is the number of hit expanded
components, K their exact count, and P0 is the positive original count.
For a buffer numerator B define

`den(B)=2*P0*D+B`,

`num(B)=H*min(2*(A*D+B),den(B))`.

Dynamic recall at that buffer mass is `num(B)/(K*den(B))`.
For fixed A and H it is nondecreasing in B because `A<=P0`. Therefore

`R_lo = floor(S*num(B_lo)/(K*den(B_lo)))`,

`R_hi = ceil(S*num(B_hi)/(K*den(B_hi)))`

enclose the true recall in `[R_lo,R_hi]/S`. The denominator is positive
because P0>0. For nonnegative integers, implement `ceil(a/b)` as
`(a+b-1)//b`, never by conversion to float.

## 3. Uncertain endpoint masses and precision envelopes

For a retained threshold block from a to b, let C_a<C_b be exact complete
tie counts. The real mass-envelope constants can be written

`ell = T_a/(C_b-T_b+T_a)`,

`u = T_b/(C_a-T_a+T_b)`.

Both functions are nondecreasing in **both** mass arguments over valid
states `0<=T_a<=C_a`, `0<=T_b<=C_b`. For example the two partial
derivatives of ell have nonnegative numerators `C_b-T_b` and `T_a`;
those of u have numerators `T_b` and `C_a-T_a`. This is why subtracting
independently uncertain mass increments is unnecessary.

Safe rational envelopes are consequently

`ell_lo = T_a_lo / (C_b*D-T_b_lo+T_a_lo) = lnum/lden`,

`u_hi = T_b_hi / (C_a*D-T_a_hi+T_b_hi) = unum/uden`.

The upper weight bound of D guarantees that each upper total numerator is
at most its count times D, a necessary premise of the monotonicity step.
If `lden=0`, the block admits only unit-weight points and precision is one;
replace its rational bound by `1/1`. If `uden=0`, there is no admitted
positive mass and it can be set to `0/1`. Repeated complete sampled counts
describe the identical prediction set and contribute exactly zero.

Define integer recall-difference bounds

`dR_lo=max(0,R_b_lo-R_a_hi)`,

`dR_hi=max(0,R_b_hi-R_a_lo)`.

The block PR contribution is enclosed, in units of `1/S`, by

`block_lo=floor(dR_lo*lnum/lden)`,

`block_hi=ceil(dR_hi*unum/uden)`.

If global distinct-score ordinals establish that the block contains **no
omitted complete threshold**, use its exact right-step structure instead:

`block_lo=floor(dR_lo*T_b_lo/(C_b*D))`,

`block_hi=ceil(dR_hi*T_b_hi/(C_b*D))`.

This includes a first retained state whose global ordinal is zero and
adjacent retained global ordinals. A large complete tie can admit many
positions, yet still have no internal valid threshold. Count difference
alone does not encode that information.

## 4. Stronger lower integral, also entirely integer

The original dynamic target obeys `T>=P0*R`. Therefore the earlier
real-arithmetic lower integral uses `max(ell,P0*r/C_b)`. Use the smaller
recall integration domain `[R_a_hi,R_b_lo]/S` and the smaller constant
`ell_lo`. If `x=R_a_hi>=y=R_b_lo`, return zero for this refinement.

Otherwise set `N=lnum`, `M=lden`, `C=C_b*S`, and `P=P0`. In integer
recall coordinates, the breakpoint is `N*C/(M*P)`.

- If `N*C>=M*P*y`, the lower numerator is
  `floor((y-x)*N/M)`.
- If `N*C<=M*P*x`, it is `floor(P*(y^2-x^2)/(2*C))`.
- Otherwise it is
  `floor(((P*y*M)^2-2*N*x*C*M*P+(N*C)^2)/(2*C*M^2*P))`.

The mixed expression follows by analytically integrating the constant
piece and the linear piece at their exact rational breakpoint. The
numerator is nonnegative in the mixed case. Take the larger of this lower
numerator and `block_lo`. No Fraction denominator accumulation is needed.

## 5. Width aggregation and comparisons

Sum lower and upper block numerators at each width. For W evaluated widths,
sum again, and return

`VUS_lo=floor(sum_lower/W)`, `VUS_hi=ceil(sum_upper/W)`

with common denominator S. The sums enclose the exact width-averaged
scalar because every rounding direction is preserved. Clipping outward
to `[0,S]` is valid since this PR scalar lies in `[0,1]`.

For models with the same e, compare the integer endpoints directly:
`lo_A>max(hi_other)` certifies a unique exhaustive-target winner. Different
dyadic scales can be aligned by exact bit shifts. Persist the integer
endpoints and scale; any decimal or float display is presentation only.
Do not silently use an inward-rounded float display for the certificate
decision. Threshold-grid uncertainty remains even when the weight and
output grids are very fine. Refinement or exact fallback is required when
the score intervals overlap.
The exact real-arithmetic nesting theorem does not by itself promise
nesting after separate outward rounding of a larger number of blocks.
If an adaptive interface promises nested intervals, intersect each newly
computed sound interval with its previous sound interval.

## 6. Independent arithmetic checks

The stdlib-only spike directly reconstructs interval geometry, complete
ties and component hits on tiny examples. It uses exact Fraction arithmetic
as an independent oracle, assigning each uncertain buffer point the lower,
midpoint or upper rational admissible weight. Certificate calculations use
integers only, including all roots and divisions.

The completed run checked **14,400** enclosures with weight precision
`b=3` and output precision `e=12`, deliberately coarse enough to expose
rounding-direction mistakes. Inputs cover all nonconstant binary labels
and binary scores at lengths 2 through 4, plus 120 seeded random tied-score
fixtures, widths 0/2/5/16, all three rational weight choices, and threshold
budgets 2/3/5. It also checked **12,500** square-root brackets across
precisions 0/1/3/32/63, using exact squared-integer inequalities.

Result: `PASS_EXACT_RATIONAL_ORACLE`, with zero enclosure violations.
These finite tests verify the independent arithmetic implementation;
the universal guarantee comes from the bracket and enclosure arguments,
not from replacing an error tolerance with a larger number of examples.
The spike does not measure speed, implement adaptive scheduling, or prove
that a compiled fixed-width implementation cannot overflow.

Reproduce using only Python's standard library:

`python experiments/exploration/sampling_bigint_certificate_20261023.py`

The producing receipt is stored alongside the script as
`sampling_bigint_certificate_20261023.json`.
