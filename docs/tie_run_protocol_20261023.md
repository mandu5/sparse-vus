# Tie-run evaluation protocol — 23 October 2026

Freeze source and every input before timing. This study evaluates a newly
derived one-interval run-sensitive algorithm. Previously studied real inputs
are reused evaluation, not unseen confirmation. No original primary criterion
is replaced. Timings are descriptive; work-count predictions and numerical
parity are the falsifiable tests.

Structural matrix: L=32,128,512,2048; n=4L+3; one original singleton in the
center, except interval8 which has eight consecutive original positives.
Five score families: all equal; monotone distinct with original last; eight
contiguous equal-score blocks; alternating two score classes (fragmented negative
control); and interval8 with all scores equal. Every case is retained.

Real inputs: every K=1 case from the frozen Mac development and external
active-prefix input manifests, at all their widths 30,100,300. Select using
labels alone, before any new candidate timing. Keep original scores unchanged;
record current array hashes and their source manifest hashes. Store real data
only in ignored local cache, respecting original source redistribution terms.

Four PR-only full-call methods: new tie-run evaluator, frozen active-prefix
evaluator, released radix evaluator, pinned actual Klein fast-VUS with n
thresholds. All validation, preparation and square-root prefix construction
are timed. JIT/import/input I/O and diagnostic profiles are outside timing.
One compute thread; one untimed per-case warm call per method; five seeded
randomized serial repetitions (seed 202610234). No cross-case preparation reuse.

Parity: every measured result within absolute 1e-11 of released radix. Tests
also compare independently built dense geometry; that is distinct evidence.
Work: every width visits at most 3P0 complete score events; all-tied singleton
visits exactly one temporal run per width, versus the frozen position scan's
1+2 floor(w/2) visits. No conversion from operation counts to timing is assumed.

Report every case, median ratio, aggregate times and loss counts. Separate
structural families from reused real data and widths. Do not infer population
confidence or a deployable selector from this selected single-interval subset.
Interrupted runs retain raw records and never receive a COMPLETE receipt.
