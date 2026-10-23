# Independent production certificate review, 2026-10-23

Reviewed implementation: `src/sparse_vus/sampling.py` SHA-256
`6ea098351b40d9155db1fc64262c91537c425842138c1fc5aeafe3a6fa10b101`;
`src/sparse_vus/sampling_bounds.py` SHA-256
`ec1511ff448373096bc3e6d253e3e748a8182bc04c4d20e2d5ca5391a8adb790`.

Disposition after repair: **PASS within the stated real-arithmetic target
and supported input limits**. This is an internal adversarial code/math
review, not external peer review or a performance finding.

## Blocking defect discovered and repaired

The initial public certificate accepted NumPy integer `max_buffer` values
through the shared validator, but retained that scalar type into final
aggregation. `lower//np.int64(widths)` could become NumPy int64 or float64;
`_ceildiv` could overflow before division. Reproduced examples include
`(2**63-1+np.int64(301)-1)//301` becoming negative and
`2**63//np.int64(301)` returning float64. Even small NumPy widths yielded
NumPy scalar certificate numerators, allowing overflow in later cross-scale
winner comparisons. An unsigned NumPy width also failed through floating
scalar promotion. These defects broke the claimed integer-directed guarantee
for accepted inputs.

The root implementer normalized validated widths to Python integers before
geometry/call use and final aggregation, and added `PRCertificate` field
normalization plus endpoint/range validation. This reviewer reran signed
and unsigned scalar cases after the repair and verified Python integer
endpoint types and exact comparison behavior.

## Arithmetic and structural review

- Every buffer weight is bounded by `2**32`; the input guard `n<2**31`
  bounds each compiled sum by `n*2**32<2**63`. Maximum-support positions
  are disjoint and each contributes to exactly one threshold bin, so
  cumulative bin sums obey the same bound. Original and hit counts are
  smaller still. Nonlinear products and total accumulation explicitly
  use Python integers after converting Numba/NumPy outputs.
- Root tables use `isqrt(((w-d)<<64)//w)` and exact squared equality for
  perfect roots. Inactive positions contribute zero, originals one, and
  two overlapping ramps clip to one. Float64 distance arrays contain only
  exact integer distances below `2**31` or infinity, so those arrays do
  not introduce numerical uncertainty in the supported length regime.
- Global radix keys merge signed zeros and operate on the shared binary64
  score conversion. The sampled grid intentionally follows the upstream
  `linspace` rule. Support events map to the next retained complete global
  score tie; the final sampled tie includes every position. Global
  distinct-score ordinals correctly identify blocks without omitted
  thresholds, including a single huge score tie.
- Recall bounds use monotonicity in buffer mass before and after clipping.
  Fixed component counts and exact coverage are retained at every width.
  The interval arithmetic handles saturated recall, zero recall, repeated
  sampled states and no-omission blocks.
- Both precision-envelope rational functions are monotone in their two
  endpoint masses. The piecewise strengthened lower integral follows the
  exact rational breakpoint; all floor/ceil directions are preserved.
  Averaging retains dyadic lower/upper numerators. Final clipping to
  `[0,1]` is valid for the target PR scalar.
- Outward float displays are checked against the exact ratio of the
  returned float and adjusted when necessary. Scientific decisions use
  the integer endpoints, not display values. Different scales are compared
  through Python integer cross products.

## Independent verification executed

`experiments/exploration/audit_sampling_certificate_20261023.py` completed
with a source-bound receipt at the adjacent `.json` path:

| Check | Completed |
|---|---:|
| Production block formula versus exact Fraction oracle | 14,400 |
| Full public API versus independently constructed Decimal120 real-root oracle | 360 |
| Integer endpoint states versus independent temporal reconstruction | 4,627 |
| Complete-tie counts and global ordinals versus direct score sorting | 360 |
| Python/NumPy signed/unsigned width regressions | 10 |
| Outward display comparisons using exact Fraction conversion | 5,000 |
| Length guard before compiled accumulation | passed |

The block oracle deliberately uses coarse weight precision 3 and output
precision 12 to stress rounding directions. It evaluates lower, midpoint
and upper admissible rational weights with Fraction arithmetic. The full
API checks use unrelated seeded fixtures, actual Decimal square roots,
boundary anomalies, multiple intervals, ties, overlaps and complete grids.
No metric source changed during the recorded audit.

While connecting that independent oracle to NumPy inputs, the reviewer
also found and repaired a reference-only empty-sum coercion: an empty
buffer sum started as integer zero, and dividing it by two introduced a
float into what was intended to be an exact Fraction expression. Explicit
`Fraction(0)` starts and `Fraction(1)` clipping now preserve rational
arithmetic throughout. The corrected spike and production audit were
rerun. This correction concerns the independent exploratory oracle, not
the final production certificate.

## Scope

The certificate encloses ideal real-arithmetic dynamic VUS-PR with exact
square-root weights. It does not promise to enclose the final bit pattern
of every independently rounded NumPy/Numba implementation. Decimal and
Fraction checks support the implementation audit; the mathematical
guarantee follows from integer weight enclosures and directed formulas.
The implementation still evaluates all widths and may return wide
intervals. Useful certification rates and overhead require separate
experiments. An adaptive interface should intersect successive sound
intervals if it promises nesting after per-block directed rounding.

## Subsequent frozen accuracy experiment

After the corrected implementation passed the independent audit, a separate
accuracy-only protocol was frozen at
`artifacts/msad-certificate-20261023/protocol.json`, SHA-256
`4b73c88d7f129f5d5fdfeb7b36e1efb71d753bc8351c55ea5815c3bb84897e04`.
It binds all 128 newly acquired series and twelve original stored score
vectors per series, width 30, primary H=250 and secondary H=1000. All
3,072 declared certificate calls completed without failures, with every
input NPZ, label array and score array hash verified. No timing claim is
made by this study.

| Threshold budget | Complete series | Certified unique exhaustive winner | Certified suboptimal sampled winner set | Median scalar interval width |
|---:|---:|---:|---:|---:|
| 250 | 128 | 63 (49.21875%) | 0 | 0.0062365738967743445 |
| 1000 | 128 | 94 (73.4375%) | 0 | 0.00038996400964232125 |

These are deterministic conditional rates on the selected finite corpus,
not confidence levels or estimates of universal effectiveness. A certified
winner must have its exact dyadic lower endpoint strictly greater than
every competitor's upper endpoint. Overlapping intervals are retained as
uncertified; they are not silently assigned a winner. The widest intervals
remain above 0.98, so useful certification is not universal.

The H=1000 record for YAHOO/Yahoo_A2synthetic_44_data.out, CNN, illustrates
why the target distinction matters. Its binary64 exhaustive reference is
`0.988888888888888`, falling approximately `7.63e-16` below the certified
lower endpoint. A separate exact rational argument establishes the ideal
value **89/90 at every width 0..30**: three original components remain
separate, the first eight predictions are original positives covering all
three components, and the final positive joins one off-support negative
in a complete score tie. Thus PR is `8/9+(1/9)*(9/10)=89/90`; all later
buffer events have zero recall increment. The certificate contains this
exact rational value. No epsilon or widened endpoint was introduced.

The bound input checks and rational derivation are retained in
`float-reference-discrepancy-audit.json`. This is an accumulation discrepancy
in the informational floating evaluator, not a failed real-target
certificate. The immutable record ledger has SHA-256
`4e557a2696ab92d35b2c433bdf98918de41afeb7e1a92172da62adfa52e185ab`.
