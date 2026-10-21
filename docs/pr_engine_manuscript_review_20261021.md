# Final manuscript scientific review — 21 October 2026

**Result: no unresolved substantive blocker found in the reviewed scope.** This is an internal AI review, not peer review, external reproduction, a proof-assistant verification, or an acceptance/SOTA determination. The reviewing AI agent also participated in implementation, prior-art research, and manuscript preparation; the review is not independent of authorship.

## Sources and checks

Reviewed the final [generic manuscript source](../paper/main.tex) and its 20-page [PDF](../paper/main.pdf), including the exact-event theorem, [radix proposition](../paper/radix_method.tex), prior-art discussion, protocol, limitations and conclusion. Checked the [current results fragment](../paper/pr_engine_results.tex), [earlier paired-output results](../paper/advancement_results.tex), width/racing appendices, and the [radix](radix_prior_art_20261021.md) and [dated exact-VUS source audits](exact_vus_sota_search_20261021.md). All PDF pages were inspected in contact sheets; the event formulas, fixed-word proposition, primary/secondary/oracle tables and ECDF were also inspected at larger scale. No clipping or unresolved reference was found in those checks.

The two final reports were checked against their bound raw timing records:

- [Mac v3 holdout report](../artifacts/pr-engine/mac-holdout/report.json).
- [Linux v3 holdout report](../artifacts/reproductions/linux-pr-engine-39523992616/report.json).

Recomputed all 39 radix/reference point-statistic comparisons per platform, their faster/slower/tied counts, and all 924 oracle choices per platform using existing records. Report, raw-record, audit, protocol, generated-table and figure hashes match their receipts. In-memory table regeneration is byte-identical. No metric evaluation, timing experiment, or bootstrap resampling was rerun for this review.

## Scientific scope

The central proof preserves the pinned scalar target: complete global numerical ties, dynamic mass, sum-and-clip ramps, expanded-interval existence reward, horizontal negative-only ROC contributions, the terminal ROC point, and right-endpoint PR integration. The two-distance argument uses the fact that each active ramp is at least `sqrt(1/2)`. The preparation and width costs yield `O(n log(Q+1) + (L+1)Q)` with comparison-based ranking and `O(n + (L+1)Q)` with eight explicit fixed-byte radix passes and linear interval geometry.

The fixed-word proposition explicitly requires finite binary64 keys, fitting address/count/index arithmetic, and unit-cost metric arithmetic including square roots. `Q` is support size, not the number of score groups. Auxiliary memory includes input-sized arrays; the current PR-only implementation additionally retains `L+1` scalars. These are upper bounds, not optimality or arbitrary-precision bit-complexity results. Exact-arithmetic identities are distinguished from numerical floating-point agreement.

The paper attributes support restriction/cumulative sums to earlier VUS implementations and generic radix/bit-order techniques to prior sources. Its defensible contribution is the specific exact event representation and its computational composition. FF-VUS is described as located public code with different native semantics, not missing code or a defeated GPU comparator. No global firstness or universal runtime claim follows from the bounded source search.

Both v3 reports contain 924 tasks, 308 series, 17 families and all 14 required methods. Both exact-radix primary decisions pass against all five frozen controls; both racing decisions fail. Primary median ratios round to 20.92/14.54 against Klein and 2.60/4.79 against the matched nearest dense radix PR control. The explicitly defined five-control retrospective oracle gives 1.71/1.99, with 40/6 slower cases retained. Maximum recorded exhaustive PR discrepancy is `1.5543122344752192e-15`, consistent with the abstract's “below 1.56e-15.”

The empirical claim is appropriately restricted to the declared full-threshold/full-width, three-model CPU workload. Paired-output methods are labelled; matching PR-only radix and geometry controls address those implementation confounds. Family-cluster intervals describe family/case variation, not three-repeat timing uncertainty. Summed case medians are not batch wall times. The previously studied corpus, Mac background activity, hosted Linux limitations, negative racing outcomes, and separation from earlier experiments remain explicit.

## Anonymous source cross-check

The generated TMLR title and abstract match the reviewed generic source exactly. Independently expanding shared inputs confirmed that body content changes only through citation-command conversion, caption placement and bibliography placement. Captions are unchanged; the generated bibliography matches the shared bibliography byte-for-byte, and all 15 cited keys resolve. No explicit author, email, owner-repository identifier, local user path or affiliation was found in the generated manuscript sources. The full AI disclosure remains present. PDF metadata, source-archive compilation and submission-format checks are handled by the separate build review; this source check is not an anonymity guarantee against public-paper matching.

No manuscript modification is required by this review. Actual external scholarly assessment remains outstanding.

## Reviewed snapshot

| File | SHA-256 |
|---|---|
| `paper/main.tex` | `170ab6596e9e07148ba874782088d322c0bb4c14847042fafab00c43bb07282b` |
| `paper/main.pdf` | `35b586bf80944fbf0a147fc8f6451bf45e7134e256c63f886a74ed68f39b8bd9` |
| `paper/radix_method.tex` | `c028a0f164c6da4f2b3a363adab662c220df0dc1c7506b56a4243b1432495d1d` |
| `paper/pr_engine_results.tex` | `e03f24e19114a05d3928f1f870bf5aa4072388676feabcfe7506d03313166ee9` |
| Mac report | `c72f2df666c49e58c7deb7fec72dc10d9d3bddcdcb05602fb787ac09c62af2aa` |
| Linux report | `46c6fba361e4e9f021781a08dd72050b43df8ded160883e35ed6a3594355f837` |
| `paper/tmlr-body.tex` | `d96582821a74836e7c9e1ec605cdde0b2e32a2d412055062b1856c8cdae17863` |
