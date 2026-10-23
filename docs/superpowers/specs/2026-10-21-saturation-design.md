# Exact VUS saturation research

The user explicitly resumed research and authorized planning, implementation,
experiments and pursuit of a final scholarly outcome. This extension retains
the full goal: externally defensible SOTA on a stated task or actual peer-reviewed
acceptance. A new branch or favorable pilot is not the completion condition.

## Research question

Can original dynamic-label VUS be evaluated in time depending on the active
score prefix needed to saturate recall, instead of scanning maximum support at
every width? Does the resulting method improve full-call runtime, beyond radix
ranking and compiled execution, across realistic detector scores?

At a complete threshold tie, let A be admitted original-positive count, B be
admitted buffer mass, P0 original-positive count and E the expanded-component hit
fraction. Recall is min((A+B)/(P0+B/2),1) E. If A+B/2 >= P0 and E=1,
recall remains one at all later thresholds. Subsequent right-step PR area is
zero; remaining trapezoidal ROC area, including its terminal (1,1) transition,
telescopes to 1-current_FPR. This is an exact-arithmetic claim to prove and test.

## Algorithm selected for investigation

Prepare finite-binary64 score order and complete global ties with the existing
radix method. Store nearest original interval and activation radius for each
maximum-support position. Activate positions in a score-ordered linked list as
width grows. Precompute insertion neighbors by deleting in reverse activation
order. Maintain merged expanded components with union-find; stamp hits per width
instead of clearing all components. Traverse only active score groups until
recall saturation. Preserve whole global tie counts for precision and ROC gaps.

Target bound: O(n+L+alpha(K) sum_w J_w), including preparation and activations,
under the same fixed-word/unit-cost metric assumptions as v0.3. J_w counts active
support positions actually traversed; K is original interval count. This is a
hypothesis until all preprocessing, event scheduling and component operations
have been accounted for. Worst-case and numerical limitations must remain clear.

## Scientific controls and decision rules

- Exact scalar outputs must agree within 1e-11 with independent direct-ramp
  dense evaluation and the pinned official target on exhaustive small inputs,
  tied scores, signed zeros, overlapping/adjacent components and boundary widths.
- Stream-without-saturation isolates the saturation theorem. Existing v0.3
  radix PR and matched dense radix PR isolate previous engineering advantages.
- Record actual visited work, not inferred speedups. Include preparation and
  validation in whole-call times. Retain every losing case and failure.
- Development uses the existing declared 42-series partition and bounded
  synthetic mechanism cases. Previously inspected data is never called unseen.
- Freeze source/input hashes, method set and primary criterion before any new
  confirmation run. Select an independent released corpus using metadata only
  if exact raw scores/labels and lawful access can be verified.
- Reject performance promotion if parity fails or paired full-call confidence
  bounds fail. Negative results guide the next algorithm revision rather than
  being hidden. No acceptance or global firstness is inferred from internal tests.

## Implementation boundaries

Python/NumPy/Numba, existing package validation and optional acceleration rules.
New module and experiments; no modification of frozen v0.3 measured sources or
published assets. New outputs live under artifacts/saturation and carry separate
protocols. Human authorship facts, journal eligibility and actual external
decisions remain genuine external facts; their absence does not stop research.
