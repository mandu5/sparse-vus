# Aborted initial weighted Mac run

This directory is a partial pilot, not a complete study or a primary result.
It began on 24 October 2026 at 07:55:11 UTC. It retains 5,400 records and 75
curve archives: all scheduled contracts for the 12 WSD recordings and the
grid100 contract for the first Stock recording. No MSL trial is present.

The run was stopped to distinguish conditional paired-order timing uncertainty
from recording-reweighting sensitivity and bind the independent auditor before
a complete v2 rerun. The original protocol had described recording resampling
as its uncertainty analysis. Version2 retains that calculation as workload
sensitivity and adds a separately defined paired-order calculation, explicit
bootstrap seed/resample fields, and the auditor source hash.

A direct protocol comparison finds no changes to the input hash, model order,
cases, positional/cardinality choices, alpha, precision weighting, query sets,
method orders, timing scope, tolerances, comparators, hypotheses, failure policy
or data note. Changed fields are `utc`, `sources`, `uncertainty`, and the added
`bootstrap_seed`/`bootstrap_resamples`. The metric runtime source is unchanged.

The complete `weighted-mac-v2` run began at 07:58:50 UTC with a new destination.
Its 11,232 records and 156 curve archives supply the reported complete study.
The partial measurements here are not pooled into those estimates. The
version2 analysis plan was fixed after this partial pilot, so it must not be
described as preceding every observed result in the research process.

Both protocols, sources in Git history and all partial observations are retained.
There is deliberately no fabricated completion receipt for this directory.
