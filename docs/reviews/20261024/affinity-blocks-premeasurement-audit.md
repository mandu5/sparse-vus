# Independent premeasurement protocol audit A

**Decision: GO for the one authorized, prospectively bounded Linux execution, after committing and freezing the exact source bytes below.** No new measurement result is implied. This is an AI-simulated independent protocol/code audit, completed on 24 October 2026 before the proposed affinity-block measurements. It does not revise the immutable scientific review A or its recommendation.

The auditor read the complete four implementation files and the prospective design, inspected their unchanged native consumer dependencies, and used fabricated durations/scalars and temporary receipt fixtures. The auditor did not run detector fitting, native metric workflows, or timed studies; did not edit paper or implementation files; and did not consult other reviewers' scientific recommendations or scores. The only new auditor-authored repository file is this receipt.

## Exact scope and identities

The current repository base commit during the audit was `062b95fe5322b224d8c2a9cda6a7dff376681a9c`. The new files had not yet been committed. That base is **not** the future experiment source commit: the execution must record the commit containing these audited bytes, and the driver's committed-source gate must succeed before acquisition or fitting.

| Audited path | SHA256 |
| --- | --- |
| `scripts/run_timeeval_affinity_blocks.py` | `91fcbb62de679f983659640fedf847a310949365a177976bdebfd6f2e5cfedeb` |
| `experiments/reproduce_affinity_blocks.py` | `5eb8ce3da05c43a9059a87abe925085e84167922d13abd17febc57d3568056be` |
| `tests/test_timeeval_affinity_blocks.py` | `4d65716c49e2cd5130dfd3342bd6bab844e18eb0e38c8655f41fc41587034248` |
| `.github/workflows/affinity-blocks-reproduce.yml` | `4e5be0cc9cc4cad77ea4736563e7d2b2eccda1690708b33d7c65263e94e13ddd` |
| `docs/superpowers/specs/2026-10-24-affinity-blocks-followup.md` | `1b3a58172af81f0ffe5092dc5f66da4ad0491a26a492e1f7a515c4bb2e61cc05` |

The existing `strengthened-independent-a-final.md` remained unchanged, SHA256 `2a33f88ac68819acdf4381d4306f2f043a56ef06ce70b7d4076564baeeff3a32`. Its manuscript snapshot and evidence judgments remain separate from this new protocol audit.

## Design and acquisition checks

The design fixes five newly started child processes on one Linux runner, all using the lowest permitted logical CPU, the same 52 profiles from 26 recordings, three compiled methods, and both query contracts. Every block includes a tiny JIT warm-up followed by six full, untimed combined workflows, then all six method permutations for each contract: 36 measured workflows per block and 180 overall. The seeded schedule is deterministic, covers every permutation once per contract, and balances method positions.

The driver generates the workload once, checks the independent input audit, and refuses a score/input mismatch before any measured block. Independently comparing the saved original and supplemental Linux references confirmed identical hashes for all **52 profile array/native-score pairs** and all **80 native input files**. The new code requires agreement with both references. It also compares the native source tree, local kernel/adapter sources, dependency versions, Python version, row identities, query plans, and inherited consumer design with the prior compiled-control protocol.

I checked the existing native runner, interval-control runner, acquisition driver, workload preparation, input auditor, and dependency file against their committed bytes; all were unchanged. The new driver invokes the existing native CSV-read, three-metric computation, and result-CSV-write/close timing boundary. Trial copying, output validation, and affinity inspection occur outside that boundary. Full warm-ups use the same method/contract workflow as the measured calls.

The workflow requires the dedicated `strength/affinity-blocks-linux-v1` tag and equality of HEAD, the tag's commit, and the event commit. It uses Python 3.11.9, pinned CPU dependencies, explicit one-thread environment variables, and a 90-minute job cap. The driver refuses an existing output directory and has no automatic replacement or retry path. The six full warm-ups are untimed; the inherited 600-second deadline applies to each measured workflow. The overall cap can end an incomplete execution, which must remain incomplete evidence.

I parsed the YAML and checked its eight artifact patterns: they retain JSON/JSONL receipts, environment metadata, logs, and `results.csv` scalar outputs, without a raw-data or score-vector archive pattern. The source protocol is frozen before measurement, and the child rechecks its protocol/source bindings and native input bindings.

## Four corrective areas inspected

1. **Successful process completion and bound evidence are prerequisites for inference.** Initially, complete-looking trial rows could have supplied intervals even if a child subsequently failed its final verification. Eligibility now requires a successful child exit and a hash-bound final block receipt with the expected block/protocol/count, final input verification, evidence-file hashes, and final thread/affinity checks. The final audit also caught and resolved the remaining specification mismatch: any `INVALID_OUTPUT` in the hash-bound trial trace invalidates the whole block for all four contrasts. A timeout remains a retained incomplete pair and suppresses the affected contrast only. Tests cover both cases, as well as a child that leaves all timing rows but fails its final gate.

2. **Output parity extends across blocks and includes full warm-ups.** Within each block the runtime compares every completed output with every previous output under the same contract, rather than only one anchor. The supervisor independently rereads hash-bound scalar CSVs, validates the frozen 52-row identity/order and finite three-metric outputs, and compares matching contracts across all five blocks. A shared scalar shift in one block is rejected. A complete execution contains 210 saved outputs including warm-ups; an independent synthetic fixture produced the expected **8,820 cross-block same-contract comparisons**. Its deliberately shifted fifth block failed parity. This is compiled-method scalar parity, not new public-implementation parity evidence.

3. **Malformed child traces do not silently stop the remaining planned attempts.** JSONL parsing retains the raw file, identifies malformed lines, and permits the supervisor to attempt all five children. The continuation regression leaves all 36 rows plus a truncated extra line in the first failed child, confirms all five children were attempted, preserves the malformed bytes, and prevents all four five-block intervals. No failed block or observation is replaced.

4. **Affinity covers live threads and reported numerical pools.** Pinning occurs before numerical/native imports in each fresh child. The implementation checks every live `/proc/self/task` thread's affinity before each measured call and at block completion, and requires every reported numerical pool to have one thread. Synthetic regressions reject an auxiliary thread with an expanded CPU set and a two-thread pool. This addresses Linux's per-thread affinity semantics; checking only the main thread would have been insufficient. See the [Linux `sched_setaffinity` documentation](https://man7.org/linux/man-pages/man2/sched_setaffinity.2.html). These are runtime snapshots, not exclusive-core reservation or continuous CPU-frequency/load control.

## Independent statistical reconstruction and validation

On the final runner hash above, I constructed irregular synthetic durations with block, method, round, position, and contract effects. Independently of the production ordered-sequence loop, I enumerated the **126 multinomial count configurations** for drawing five blocks with replacement, weighting each by `5! / product(count!)`. Their multiplicities sum to **3,125**, agreeing with the complete empirical bootstrap distribution.

For all four contrasts, the independently reconstructed equal-block geometric mean and interpolated bootstrap endpoints at probabilities **0.00625 and 0.99375** agreed with the implementation to a maximum absolute difference of **4.440892098500626e-16**. These endpoints implement the stated Bonferroni tail adjustment over four contrasts. Pairing uses the same block, round, and contract; the six log ratios are averaged within the block before resampling. The sampling unit is five process blocks, not 30 orders or 180 workflows. An ineligible fifth block suppressed every corresponding interval while retaining its six observed paired ratios in the diagnostic output.

Fresh validation command:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -B -m pytest -q tests/test_timeeval_affinity_blocks.py
18 passed
```

These tests execute fabricated protocol, statistics, receipt, and process-supervisor cases. They do not execute the native metric producer or measure its performance. I also independently checked the two saved Linux input identities and YAML/archive scope as described above.

## Limits and required result audit

No remaining source/design defect found in this audit blocks the single frozen execution. The prospective specification and final code now agree on failed-child, invalid-scalar, timeout, and incomplete-coverage handling. No further premeasurement experiment is needed for this protocol decision.

The largest remaining uncertainty is the actual size and variability of the advantage on the chosen shared runner. Five process blocks are a small descriptive sample sharing one host, logical CPU, workload, and environment. Their bootstrap does not establish guaranteed coverage, independent-machine reproducibility, a workload-population effect, the cause of the earlier Linux difference, or greater conceptual novelty. Linux affinity and native execution were inspected in source and exercised only with synthetic receipts here; the real Linux gates must pass during the authorized execution.

After the run, the saved-output audit must reconstruct the result from the frozen protocol, source commit, input identities, distinct child-process receipts, per-thread affinity/pool receipts, all 180 planned trial identities and statuses, all available scalar CSVs including 30 full warm-ups, final evidence bindings, and the five block estimates. It must independently recompute parity and the four bootstrap summaries. A timeout, invalid output, preparation failure, or job interruption remains visible and cannot be relabeled as a complete five-block study. Negative or uncertain results must remain visible; this finite follow-up supplies no justification for repeated runs seeking a favorable ratio.
