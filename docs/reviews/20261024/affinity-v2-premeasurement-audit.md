# Independent premeasurement audit C: affinity v2

AI-simulated independent code/protocol audit, 24 October 2026. This is not a paper-acceptance review, a result audit, or an official PVLDB decision. I did not implement this orchestration, consult other scientific reviewers' scores, or execute detector generation, metric evaluation, warm-ups, or measured workflows. Only this audit file was added by this review; the pre-existing C final review remains unchanged.

**Disposition: no material premeasurement blocker found in the reviewed bytes.** The implementation supports the separately scoped, one-new-realization design. Source commit and tag freeze are still required before the single authorized execution. This disposition does not establish that the future execution will complete or pass its data/output gates.

## Reviewed identity and scope

At inspection, repository HEAD was `ee3031aafb5cc30c7928d36e965d2156cf3ac2ca`; the six new files below were untracked working files. Therefore this audit binds their SHA-256 values, not an already-existing v2 commit or tag.

| Reviewed file | SHA-256 |
|---|---|
| `scripts/run_timeeval_affinity_blocks_v2.py` | `db3aefe52324840d1c05c66e41bec0394197469e097cbeaa8fe5a04bf3b556fd` |
| `experiments/reproduce_affinity_blocks_v2.py` | `2a520c4cf217f5fe1c322663e540065b4f8615d1e5c6b799da67874295ae27b8` |
| `tests/test_timeeval_affinity_blocks_v2.py` | `145d11ba84f8732dc36a55b326600363b01d572aebced922db7e69fa94a2bf99` |
| `tests/test_timeeval_affinity_realization.py` | `b7d3fbda9ade54aed2b70899e5108adea364cb30e70c48abd2829c59917d83a2` |
| `.github/workflows/affinity-blocks-v2-reproduce.yml` | `f89ac8981b5a61c88786b87facf03ad37556b3a449c6cb71574f0e07f4d0f8b3` |
| `docs/superpowers/specs/2026-10-24-affinity-realization-v2.md` | `f7ea1638e841cf73105da813abaf1730dafe01b10881b588632b42c512e5051e` |

I independently compared the original v1 runner, driver, test file, workflow and specification with `git show ee3031a...:<path>`: all five were byte-identical. AST comparison of the two runners found changes only to `design()` and `freeze()`, the added `reference_diagnostics()`, and the expected module metadata/source-file list. All other function ASTs, including timing, process orchestration, eligibility, saved-output parity and statistics, were identical. The v2 block-test file differs from v1 only in the runner path it loads.

## Gate and execution findings

1. **The prior-input relaxation is restricted.** `reference_diagnostics()` requires both historical Linux references, complete 26-case/52-profile coverage, successful fits, matching selection and model declarations, ordered case/label metadata, ordered profile identity/dtype/shape, native templates and row identities. The complete native file-key sets must match. A changed file is diagnostic only when it is already present in both maps and ends in `/anomaly_scores.ts`. The two actual prior maps contain exactly 52 such paths; an added or removed score path fails the hard gate. Dataset, index and result-template changes remain fatal. This is not a blanket waiver of `input_sha256`.

2. **Raw and typed input checks remain substantive.** The unchanged preparation code checks the pinned archive, raw members, typed observations and labels against the fixed selection before fitting. The unchanged independent input auditor rereads the archive and raw/combined arrays, verifies exact observation and label bits, the explicitly source-bound decoding rule, native serialization, all 52 worker receipts, and equality among current per-model, combined and native score representations. V2 additionally requires the selection and non-score native bytes to match both prior executions. These are checks the future execution must pass; this premeasurement review has not verified nonexistent v2 inputs.

3. **Exactly one generation path is present.** The driver contains one call site for `prepare_strengthening_workload.py`, outside any retry loop. The producer makes one subprocess call for each fixed case/model pair, retains errors/timeouts and does not replace profiles. It may finish attempting the remaining fixed profiles after a failure, but the subsequent input auditor rejects any incomplete generation and prevents freeze/measurement. Interpreter import probing before fitting is not detector-fit regeneration. The protocol is frozen before the first fit; the actual new score realization is frozen before the first metric or warm-up. There is no score, cardinality or timing acceptance threshold.

4. **Source and copy bindings are retained.** The driver requires every `NEW_SOURCES` file to match its committed HEAD blob before acquisition. It copies the new specification/workflow as well as source files and checks the copied hashes. The native source tree is checked against the historical manifest. `freeze()` requires the original native/kernel/compiler/dependency contract to match the interval-control reference, binds the new orchestration and reference metadata, and embeds the fresh generation/input-audit receipts and current native input hashes. The dedicated workflow checks that HEAD, event commit and the v2 tag coincide before setup; it has one driver invocation, a 90-minute job cap and retained-artifact upload. No v1 artifact is substituted or overwritten.

5. **Every child uses the current frozen realization.** `run_block()` retains the frozen-protocol digest check, same-runner identity checks, singleton affinity before numerical imports, source/environment/file binding checks, and exact native row order. `manifest()` derives each current contract's threshold count and binary64 threshold hash from the current native score files. Before/after-block verification binds those score bytes and unchanged query-producing source; it does not separately recompute the query-plan dictionary inside every child. Consequently the shared deterministic query plan is enforced through the frozen inputs/code, with saved scalar parity across warm-ups, methods, orders and blocks. No new fitting occurs within a block.

6. **The finite analysis is unchanged.** There are five fresh processes, 36 measured workflows and six full untimed warm-ups per process. Every contract has all six method permutations. The four contrasts average six paired log ratios inside each block and then five block means equally; all 3,125 empirical bootstrap sequences use tails `.025/4` and `1-.025/4`. Invalid scalar output invalidates a whole block; a timeout suppresses the incomplete comparison rather than inventing a duration. Missing/malformed completion evidence cannot stand in for a successful block. All attempts remain recorded without replacements.

## Independent verification performed

I reran the three relevant test files, with automatic third-party pytest plugins and bytecode/cache writing disabled:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -p no:cacheprovider tests/test_timeeval_affinity_blocks.py tests/test_timeeval_affinity_blocks_v2.py tests/test_timeeval_affinity_realization.py -q
```

Result: **46 passed**. These are fabricated-duration, metadata and failure-path checks; they are not numerical kernel execution or performance evidence.

Separate in-memory probes against both real prior metadata maps confirmed acceptance of changes to all 52 existing score-file contents, retention of changed threshold hashes, and rejection of altered dataset/index/template bytes, extra or missing score paths, missing or failed fits, and reordered cases/profiles. I also verified the single producer call site and the unchanged function ASTs independently of those tests.

## Interpretation that must survive into the paper

The amended study follows v1's preparation failure, not a completed unfavorable timing result. The retained v1 archive reports 52 successful fits, 25 changed COPOD score identities against each prior, one changed distinct-score count, and zero measured blocks. No score-distance or harmless-roundoff conclusion follows from those hashes.

V2 can provide descriptive process-session robustness for one newly generated, then fixed, 52-profile realization on one logical CPU of one shared runner. It cannot complete v1's exact-score replication, explain the earlier 1.932/2.756 timing difference, demonstrate detector-output reproducibility, provide new public-reference parity, or increase conceptual novelty. Five-block empirical bootstrap tails have no guaranteed finite-sample familywise coverage; singleton affinity is not exclusive physical-core isolation. These limits are explicit in the reviewed specification and do not require another premeasurement code change.

The remaining necessary checks are operational: freeze these reviewed bytes in the new source/tag, retain the single execution regardless of outcome, independently reconstruct its input/receipt/output/statistical evidence, and assess the resulting immutable manuscript. No additional timing experiment is requested by this audit.
