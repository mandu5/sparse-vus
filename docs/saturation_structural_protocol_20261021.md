# Structural active-prefix VUS study

Protocol date: 2026-10-21. This study tests constructed mathematical witnesses
and an explicit negative control. It is separate from the development and
external corpus experiments. Family selection and visit-count hypotheses are
fixed before this script computes outcomes. Previous small witness checks are
development history; these are not previously unseen structural hypotheses.
No runtime result is required to be a win.

## Inputs and prior hypotheses

The Cartesian product of the following four families and maximum widths
`L in {32,128,512,2048}` contains exactly 16 cases. Every case has `n=4L+3`,
binary `uint8` labels, finite `float64` scores, and all integer widths `0..L`.
Positions below are zero-based. No case is removed after evaluation.

| Family | Construction | Required visit-count property |
| --- | --- | --- |
| `singleton_original_last` | One positive at `2L+1`. Initially `score[i]=i+1`; replace the positive score with `-1`. Every score is distinct. | Saturation `J_w<=min(Q_w,3)` and total visits `<=3(L+1)`. Both active controls visit `Q_w=1+2 floor(w/2)`. |
| `two_positive_separation` | Positives `a=L+1`, `b=3L+1`. Background scores zero; scores at `a,a-1,a+1,b-1,b` are respectively `10,9,8,7,-10`. | `J_0=J_1=2`; every `w>=2` has `J_w=4`, so total visits `4L`. Last-positive and full active scans visit `Q_w=2+4 floor(w/2)`. |
| `interval8_original_last` | Eight consecutive positives from `2L+1` through `2L+8`. Initially `score[i]=i+1`; positive scores become `-1,-2,...,-8`. Scores remain distinct. | Saturation `J_w<=min(Q_w,ceil(2 sqrt(2)*8))=min(Q_w,23)`. Both active controls visit `Q_w=8+2 floor(w/2)`. |
| `tied_singleton` | One positive at `2L+1`; every score zero. | Every active-list mode must finish the sole active tie, so `J_w=Q_w=1+2 floor(w/2)`. This violates an unrestricted-tie constant-prefix claim for this evaluator. |

For the two-positive family, the expanded components remain separated at all
tested widths. At `w>=2` the four highest-score active positions contain one
original and three buffer points, each with weight at least `1/sqrt(2)`.
They hit both components and give `A+B/2 >= 1+3/(2 sqrt(2)) > 2`.
The other original is last, so the last-positive control must visit every
active position. At widths zero and one, only the two originals are active.
The tied background is intentional and does not lie in the terminating four
singleton score events. For even `L=2m`, the last-positive total is
`4m^2+4m+2`, whereas the saturation total is `8m`.

These assertions check finite examples of the proofs. Scaling observations
are not proofs, and all-tied work is a limitation of the present evaluator,
not a lower bound on every possible exact VUS algorithm.

## Methods and measurement

Measure four complete scalar PR public calls, including input validation,
radix order, geometry, allocation, and all-width integration:

1. `sparse_pr_saturation_jit(..., stop=True)` (`saturation`).
2. The same API with `stop='last_positive'` (`last_positive`).
3. The same API with `stop=False` (`active_full`).
4. Unchanged v0.3 `sparse_pr_radix_jit` (`radix`).

Use one compute thread, fixed seed `2026102127`, and three timed repetitions
per method per case. Warm the public APIs and diagnostic mode before the run;
also make one untimed call to each method on each actual case. Shuffle the
per-case warm order and each repetition's four-method order with one seeded
Python random generator. Cases use increasing `L`, then the family order in
the table. Record all orders, all individual durations and outputs, and the
median duration per method/case. Timing uses `perf_counter_ns`; input I/O,
hashing, profiles, assertions, and reporting occur outside each timed call.

After timing each case, obtain full `profile_saturation` dictionaries for all
three stop modes. Preserve their ROC/PR values, all `L+1` visited and active
counts, `Q`, and `K`. Check PR values against every radix and active-list timed
output at absolute tolerance `1e-11`; also check ROC parity between the three
profile modes. Enforce the table's counts and bounds, expected geometry, and
`0 < visited <= active <= Q`. Verify input arrays were not mutated.

This study's parity reference is the production radix evaluator, not an
independent dense oracle. Its two-component family intentionally has early
coverage; these 16 cases do not assess delayed multi-component coverage.
Independent dense-oracle checks and adversarial coverage tests belong to
separate validation records. Before freezing the measured run, a lightweight
runner preflight may check input recipes, receipt rejection, and structural
counts/parity on the four smallest-width cases. It records no timing outcome
and does not change the fixed cases or hypotheses.

Runtime ratios are baseline median divided by saturation median, so values
above one favor saturation. Report every case, including regressions and the
negative control. There is no runtime pass/fail threshold or population
confidence interval for four deliberately constructed families. A reported
radix `(L+1)*Q` position budget is analytic, not an instrumented radix count.

## Freeze, run, and receipts

`experiments/benchmark_saturation_structural.py` offers three actions. Do not
run it while another controlled CPU study is active. Use a new output directory
for every attempt; interrupted or failed runs must remain available as evidence.

```sh
/opt/anaconda3/bin/python experiments/benchmark_saturation_structural.py freeze artifacts/saturation/structural-mac-20261021
/opt/anaconda3/bin/python experiments/benchmark_saturation_structural.py run artifacts/saturation/structural-mac-20261021 --protocol-sha256 HASH_FROM_FREEZE
/opt/anaconda3/bin/python experiments/benchmark_saturation_structural.py report artifacts/saturation/structural-mac-20261021
```

Freeze creates all 16 NPZ inputs and an input manifest with NPZ hashes and
array hashes. An array hash binds the canonical JSON dtype/shape header,
a newline, and contiguous C-order bytes. Freeze imports no VUS module and
computes no metric. It records the source commit and SHA-256 hashes of this
script, this protocol, the saturation and radix modules, and their package,
validation and compiled-kernel dependencies. The protocol hash printed by
freeze is mandatory for `run`. Input bytes, recipes, identities, and sources
must match at execution; source hashes must still match at completion/report.

Run writes start/end environment receipts with Python, NumPy, Numba, CPU,
thread settings, threadpool inspection and process snapshots. A local-host
snapshot does not establish continuous machine isolation. The JSONL log keeps
all raw per-case values, durations, profiles, and identities; it is flushed
before assertions so failures retain the measured record. Completion binds
the protocol, source state, environment receipts, raw log hash, and case count.
Report validates these bindings, input recipes, full method/case coverage,
parity and structural assertions. A repeated report may reproduce identical
content, but never overwrite different results. Run refuses to reuse any
directory where execution has already started.

This is evidence for exactness and algorithmic work on specified synthetic
families. It does not establish unseen-domain performance, global SOTA,
independent peer review, publication acceptance, or firstness.
