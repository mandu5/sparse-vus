# Independent active-prefix review — 21 October 2026

**Finding:** no correctness or complexity defect was found in the reviewed
active-prefix implementation and theorem. This is a bounded, independently
written in-session audit, not external reproduction, a floating-point
certificate, or a publication/priority judgment.

## Bound source and executable evidence

The audit checks source bytes both before and after execution and fails its
status if they change. The saved run reported unchanged sources.

| File | SHA-256 |
|---|---|
| `src/sparse_vus/saturation.py` | `319271b40a5f029e71088eedc2830d98665f55f5f7dbbbe3b1d03b5fdc7a1914` |
| `src/sparse_vus/radix.py` | `d8d45d3cc15105f1771aa37cf3cac95b6138a2f1ee38ee464fc940c54a55a3f5` |
| `src/sparse_vus/core.py` | `f7e227f3bfea58c72da8feba0c7daa36460695db8ab10106706f845d45374e2b` |
| `paper/saturation_method.tex` | `3671bc35cc55b9238128d36db3792464c9a338244eb680f781cc9f998280ecda` |
| `experiments/audit_saturation_oracle.py` | `b4ba42db3d1b7c8374647a778478dd9e3f976431e54168439c521dc10e993f55` |
| `artifacts/saturation/independent-oracle-20261021.json` | `69c32f3057ac28d6344697617c3a0c0116d374665b0914fac75fc6d2d38c9db8` |

Reproduce from the repository root, writing a new receipt if the audited
sources have since changed:

```sh
python experiments/audit_saturation_oracle.py --output /tmp/saturation-oracle-replay.json
```

The saved run is **PASS**. It enumerated every both-class binary label vector
of lengths 2 through 5 and every score assignment from `{-1, 0, 1}`. Each case
evaluated all integer widths from zero through `2*n+1`. This gives 8,604
exhaustive cases. Two further cases use reversed and non-contiguous views.
All three stop modes are checked through both public output APIs: 25,818
case/mode pairs and 51,636 public calls. Maximum absolute discrepancies were
`3.3306690738754696e-16` for paired ROC/PR and `2.220446049250313e-16` for
PR-only, against the declared `2e-12` absolute tolerance and zero relative
tolerance. No failures occurred. The 6.28-second execution duration includes
imports/compilation and is not a performance comparison.

The oracle imports no production interval, geometry, ranking, or integration
helper. It directly enumerates original intervals, constructs every ramp,
merges expanded closed intervals on overlap only, visits every distinct global
score threshold, and integrates the dense coordinates. Only the candidate
APIs are imported from `sparse_vus.saturation`.

## Static algorithm and theorem review

- Complete terminating ties are processed before the cutoff. Global
  before/after counts include inactive and off-support positions in a tie.
- Reverse deletion and forward insertion use corresponding orders, including
  positions sharing an activation radius. Traversal preserves score order
  and excludes inactive positions without scanning the maximum support.
- An active point lies in its nearest original interval's expansion. Any
  other expansion containing that point overlaps it and has the same DSU
  component. The stored nearest owner is therefore sufficient.
- Merge radii implement overlap, not adjacency. Unions occur before each
  width's threshold sweep; roots remain fixed during that sweep. Width stamps
  count each component once without a full component-array reset.
- The width loop contains no hidden `Q`- or `K`-sized initialization. Activation
  and merge schedules are capped at `min(L//2, n-1)`; their storage is `O(n)`.
  Every position activates once, and each neighboring interval pair merges
  at most once. The cost of at most `K-1` unions is absorbed because
  `J_0 = P0 >= K`.
- At a complete tie, `A+B/2 >= P0` and `H=K_w` imply permanent recall one.
  Subsequent PR increments vanish; the complete remaining ROC area telescopes
  to `1-current_FPR`, despite the changing negative denominator.
- `J_w` must count visited active positions, including every active position
  in the terminating tie. It is not merely the number of score events.
- The two-positive separating family is valid against the stronger
  last-original-positive cutoff: three early immediate-neighbor buffer
  positions supply at least `3/sqrt(2)` mass, both components are hit, and
  full saturation uses four active positions for every width at least two.
  The last-positive control still traverses `Theta(L^2)` positions in total.

`tests/test_saturation.py` was also inspected for complete ties, component
coverage, merge boundaries, binary64 score conversion, stop ablations and
the separating family. Its test-suite execution belongs to the integration
owner; this receipt does not substitute for the full repository suite.

## Numerical and evidence limits

The exact-arithmetic theorem does not make a machine-level exactness promise.
Floating sums, the saturation inequality and the telescoped ROC suffix can
differ from a full accumulation near rounding boundaries. The bounded oracle
results quantify tested numerical agreement; they do not certify all finite
binary64 inputs. No symbolic or directed-rounding validation was performed.
Linked-list and DSU overhead can also outweigh a reduced visit count. The
review establishes neither measured speedup nor global SOTA.

## Benchmark protocol review communicated before freeze

`experiments/benchmark_saturation.py` was under active revision during this
review. The following were sent to its owner; this document is not approval
of a later, uninspected frozen revision.

1. **Historical outcomes in new input records:** copying whole original
   benchmark rows carried old `exact`, timing and support-size values into
   cases with changed widths. The owner replaced this with an identity-field
   whitelist during review. The summary had used new `methods` results, but
   removing old fields prevents misleading artifacts.
2. **Report reconstruction binding:** the standalone report path should check
   the frozen input digest, expected protocol/analysis identity and successful
   completion/source-check receipt. Merely writing newly computed hashes does
   not validate the original execution. The immediate run path already
   checked primary source hashes before and after measurements.
3. **Work-profile validation:** require all three mode keys, both vector
   lengths, finite integer counts, `full.visited == full.active` and
   `saturation.visited <= last_positive.visited <= full.visited`. The owner
   added the missing active-vector length check during review.
4. **Protocol constants:** repetitions, primary width, parity tolerance and
   bootstrap seed/confidence were hardcoded in summarization. They matched
   the current protocol; passing them explicitly or checking equality avoids
   silent inconsistency in later protocol revisions.
5. **Environment evidence:** record the actual CPU model and BLAS threadpool
   configuration, and enforce `threadpool_limits(1)`. Environment variables
   and `cpu_count` alone are weaker evidence for the stated hardware/thread
   conditions. Background-load snapshots are not continuous isolation proof.

Whole-call PR output matching, explicit last-positive/full-active controls,
seeded randomized method order and honest development-data labeling are
appropriate. Family-cluster intervals describe observed corpus variation,
not uncertainty from three timing repeats or hardware populations. Report
aggregate ratios as sums of per-case median runtimes, not measured batch
wall times. Do not relabel the already studied development corpus as an
unseen holdout for this new algorithm.

**Integration-owner update before freeze:** the owner subsequently reported
implementing all five requested safeguards: identity-only input records and
a regression test; start/completion receipts binding protocol, source and raw
measurements; strict profile checks; fixed protocol-contract validation; and
CPU/threadpool recording with explicit thread limits. The owner also added a
separately identified external-data phase. These are owner-reported resolutions;
this reviewer did not rerun CPU experiments or certify a later frozen runner
after the bound oracle audit above. No unresolved candidate-kernel correctness
finding was identified.
