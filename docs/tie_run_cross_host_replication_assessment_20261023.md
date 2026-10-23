# Complete-tie procedural replication assessment — 2026-10-23

The portable workflow completed on both Mac and Linux and passed the frozen numerical and work checks. This closes the need for the original Mac observational NPZ files for this **68-case subset**. It does not establish general runtime superiority: against the existing saturation evaluator, the candidate loses on 14 of 16 regenerated cases at width 300 on each host.

The Linux evidence comes from [GitHub Actions run 39900063718](https://github.com/mandu5/sparse-vus/actions/runs/39900063718), commit `ac7f5f4f4314340c5204ffc3504243d1ad001148`. The downloaded archive was checked against GitHub's SHA-256 digest before extraction into its original repository-relative path. The [download receipt](../artifacts/tie-runs/linux-39900063718/download-verification.json), [independent Linux audit](../artifacts/tie-runs/linux-39900063718/independent-verification.json), [Linux report](../artifacts/tie-runs/linux-39900063718/report.json), and [Mac audit](../artifacts/tie-runs/mac-regenerated-20261023-retry1/post-run-verification.json) preserve the evidence. Frozen reports were not edited.

## Coverage and input identity

Each host evaluates 20 source-bound synthetic cases and 48 regenerated external cases: four one-interval series, four score models, and widths 30, 100, and 300. Each case has five repetitions of four complete evaluator calls, giving **1,360 timed calls per host**. The four series are two GHL and two GutenTAG series. The 63 historical development cases are excluded; this subset must remain distinct from the original 131-case study.

Preparation regenerates all 48 score vectors from the same 12 fixed source series across nine families, then selects the same one-interval vectors. Selection metadata matches the historical selection except for the explicitly permitted environment and timestamp fields. All 12 raw-data and label identity receipts, preprocessing settings, and realized generation parameters match.

Mac regeneration matches all 48 historical score hashes. Linux matches **9/48**, all from `robust_marginal_z`; no Isolation Forest, PCA, or kNN score vector is byte-identical to the historical Mac vector. Among the 16 vectors actually timed, only **2/16** match across hosts, accounting for 6/48 width-specific cases. These are independently regenerated inputs from previously studied data, not an identical-input external hardware comparison or new-domain validation. Hash inequality alone does not quantify numerical score differences or establish their cause.

## Numerical and work results

Both hosts report `PASS_PARITY_AND_WORK`. Maximum error against the first radix scalar for each case is **2.220446049250313e-16**. Independent comparison of every method pair gives the slightly larger maximum **2.7755575615628914e-16** on both hosts. Both are below the frozen `1e-11` tolerance; these empirical results do not constitute a general end-to-end error certificate.

All **20,548 recorded width-level work checks per host** pass. All fields in both recorded work profiles agree across hosts for all 68 cases. Tie-runs, saturation, and radix also produce identical scalar values across all 340 matched repetition outputs per method; Klein differs by at most `1.1102230246251565e-16`. Score-byte differences therefore produce no observed difference in these work profiles or in the three in-repository evaluator outputs.

## Runtime results and negative cases

Ratios below are comparator median time divided by tie-run median time; a ratio below one is a tie-run loss. Aggregate ratios divide the sum of comparator case medians by the sum of tie-run case medians. Each external row contains 16 cases.

| Host | Width | Saturation median / aggregate ratio | Losses | Radix median / aggregate ratio | Losses |
|---|---:|---:|---:|---:|---:|
| Mac | 30 | 1.023761 / 1.024624 | 1/16 | 1.018133 / 1.019832 | 4/16 |
| Linux | 30 | 1.023166 / 1.011364 | 2/16 | 1.011185 / 0.991645 | 6/16 |
| Mac | 100 | 0.965025 / 0.996305 | 9/16 | 0.989575 / 1.005563 | 10/16 |
| Linux | 100 | 0.936222 / 0.972028 | 10/16 | 1.013892 / 1.006656 | 4/16 |
| Mac | 300 | 0.855122 / 0.929037 | 14/16 | 1.085992 / 1.088496 | 0/16 |
| Linux | 300 | 0.765759 / 0.879358 | 14/16 | 1.156640 / 1.124006 | 2/16 |

Across all 68 cases, losses against saturation/radix/Klein are **28/16/0 on Mac** and **31/16/0 on Linux**. Every slower case and its ratio is retained in the corresponding independent audit. The all-tied synthetic case at width 2048 has a saturation-to-tie-run ratio of **8.884307 on Mac** and **19.673543 on Linux**. This supports a useful favorable structure, alongside substantial losses on the reused observational subset. Klein is slower on all cases on both hosts; that comparison does not erase losses against the stronger in-repository controls.

## Audit coverage and limits

The Linux audit rechecked all 23 source bindings and eight manifest bindings; 22 tracked sources also match the exact Git commit used by the workflow. The remaining source is the cached, pinned Klein reference, whose bytes match its recorded digest. The unchanged reporting command and a separate reconstruction both reproduce all 68 case records and summaries, with complete repetitions and seeded method order.

All 20 published NPZ files are synthetic and were independently opened and rehashed after download. Linux observational arrays deliberately remain outside the public artifact. Their hashes were checked by the frozen remote runner before timing; this download audit verifies their recorded provenance and measurement associations, but cannot rehash the absent Linux observational arrays. The included [ATTRIBUTION.md](../artifacts/tie-runs/linux-39900063718/ATTRIBUTION.md) matches the repository's data attribution document.

Mac uses an Apple M1 Pro with Python 3.12.4; Linux reports an AMD EPYC 9V74 CPU model, four available CPUs, and Python 3.12.15. Both use NumPy 1.26.4 and Numba 0.59.1. Reported Numba and library thread counts are one. Neither host is established as dedicated isolated benchmark hardware; process snapshots are not continuous load traces. Cross-host timing differences cannot be attributed solely to processor architecture, and the small width-30 advantages have no inferential confidence claim.

The strongest remaining research limitation is practical scope: the new run demonstrates portable regeneration and consistent evaluation on a small, previously studied one-interval subset. It strengthens artifact reproducibility, while the repeated losses against saturation preserve the need for a narrowly stated, structure-dependent contribution. It adds no new primary runtime success or independent dataset population.

## Principal hashes

| Evidence | SHA-256 |
|---|---|
| Downloaded Linux archive | `6453a77c3a5823190d601c7594f700df6f5a7955ce4bf733426b8bb7bdbe19c6` |
| Linux protocol | `978dc5e452e32729be51250a5dd03d39a7392038a8e66223a6333f840fcb0889` |
| Linux measurements | `1194286fee19b413df282970c6c81467da8037982a53cd47102f3d9049c11956` |
| Linux report | `0b6de759ca82cfbd2558b8ce3ecac722ea282492fe78f8811fad06f7d7937984` |
| Linux independent audit | `cb4a7582e71d81f4ebf377f0d06952d9ffbd7c8103c5c314c2e8f6cb29a5c455` |
| Mac protocol | `13aa05f3d88e4e6ed86d89363b268655e5c6d9c8475b1e1d97e9cff1cc2fa795` |
| Mac report | `31dc104f24f853f286a5aeaf5aa10980245bafbb6ae8a400ee6ae63a92651e4c` |
