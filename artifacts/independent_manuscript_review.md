# Independent automated manuscript and artifact review

Author: independently assigned automated review agent in the same development session. This is not human peer review, external reproduction, or a publication-acceptance decision.

Scope: read-only review of the mathematical definition, event identity, theorem and complexity, fixed-grid PR proposition, main result generation/statistical code, validation gate, and revised external supplement harness. The external supplement was still running; its final numeric results and the rendered manuscript were not yet reviewed. No CPU-heavy validation was run during timed experiments.

## Findings and responses

No unresolved Critical or Important mathematical or main-result counting defect was found in this snapshot.

- The event identity correctly integrates the negative-only rectangle before the entire tied support event, uses strict/non-strict prediction counts, initializes (TP,N,recall,count)=(0,n-P0,0,0), and includes the final negative tail and terminal ROC point. Dynamic positive mass and expanded-interval existence are preserved. The two-nearest-interval argument applies to this sum-and-clip ramp because two active contributions exceed one. The real-arithmetic upper bound and streamed compiled-kernel memory bound are appropriately qualified.
- The fixed-grid PR proposition is valid: at full support TP=A_w, B=A_w-m, P=(m+A_w)/2, so TP/P>=1 and clipped recall equals one. Exact PR is 1-(H_(m+1)-1)/m and sampled PR is mean(A_w)/k_n. Fixed geometry, distinct scores, and a uniform-rank grid are explicit.
- Minor clarity request at paper/main.tex around line 125: explicitly define T=TP, R=TPR, and F=FPR when introducing event state notation.
- Minor prior-art precision request at paper/main.tex around lines 202–204: explicitly credit prior maximum-buffer support restriction in addition to static/dynamic label splitting. The contribution should remain event elimination and support-only score counting; support restriction, rank sweeps, and compilation are prior techniques. Earlier primary-source review covered Boniol et al. Section 4.3 and Sylligardos Section 4; absence of a located implementation is not proof of nonexistence.
- Minor grammar request: result_body.tex final scaling sentence should say “an 8.92-fold speedup.”
- Analysis originally checked only gate status PASS, allowing stale validation on future regeneration. The builder reports adding verification of every recorded input hash and the gate source hash before consuming data. Current main-record bytes independently matched the PASS receipt before this change; no current numerical discrepancy was found.
- Revised gate/supplement review found no blocker: numeric values must be finite actual numbers; supplementary input/source hashes are bound at startup and rechecked; each worker verifies data identity and thread count; queue transport is excluded from measured call duration; late completion is censored; worker/parity failures are persisted before raising; speed ratios use completed paired cases only. An all-timeout/no-completed-call corner fails closed on an empty maximum, rather than fabricating a successful comparison.

## Independent main-results recomputation

A separate stdlib-only Python script parsed all 2,100 main records, recomputed each ratio as the minimum median of dense_numpy/dense_numba/dense_direct_numba divided by sparse_numba, and enumerated all unordered model pairs per series/width. It used strict differences above 1e-10 and separately computed unique top sets. It did not call the analysis implementation. This small check took under one second and did not repeat benchmark kernels.

Confirmed values:

- 2,100 records; median speed ratio 2.06066191185162; geometric mean 2.023415502573515; 1,916 ratios above one; range 0.27175240087058855–7.497219474338777.
- ROC: 2,100 pairs, 5 reversals, 2 affected series and 2 families, 2 unique-top changes, 96 exact ties and 95 sampled ties; maximum absolute sampling error 0.11684217217512993.
- PR: 2,100 pairs, 84 reversals, 55 affected series and 13 families, 50 unique-top changes, 96 exact ties and 95 sampled ties; maximum absolute sampling error 0.5827309171331194.
- Main JSONL SHA256 matches the gate: 29fc773db307d20730c3b32d1b1daa4de06517e802194a08a07dc1ffc260cf96.
- Bootstrap code review confirms whole-series resampling retains all model/width rows, and whole-family resampling retains source-family clusters. Reported intervals are descriptive fixed-corpus summaries, not population-generalization evidence. The bootstrap numerical draws were not independently rerun during timing.

The scientific contribution is a focused exact algorithm and evaluation result. The measured advantage over strong in-repository dense baselines is approximately twofold. Larger external ratios must retain their measured family/input and approximation-vs-exact scope. The mechanism ablation and actual external support-scan comparator distinguish algorithmic improvement from compilation and weak-baseline effects. No acceptance or broad “breakthrough” verdict is inferred from this review.

## Snapshot

Recorded UTC: 2026-10-19T15:00:13.489187+00:00

```json
{
  "paper/main.tex": "fdb959f5d7b532e04ff3d9690487033aceff15f31e7d77a85363f074cfecf6bc",
  "paper/result_body.tex": "d6b5c14d29160c8f20aab6524b5da6167c1849a16d25e7881a6bc70a7f6d2001",
  "paper/results.tex": "2fb29250c2ca2a3d066f3d511e11943234952221a8f4413f3a4403777db7c998",
  "experiments/analyze_results.py": "9de223cc437cb01b05409c4aa075cdffe962f5226fdd1ef4ff0156e6a62dd75d",
  "experiments/verify_artifact.py": "906d8504c7a52f42415395f949744ff20bbdec7433666a43fc5312dff019b373",
  "experiments/external_supplement.py": "0ae26f6b17864ecfdfec3175c91fb2dfff5a02604ce34693378f43d45b26f36f",
  "artifacts/analysis_summary.json": "eb201fa844b6664c91e2cfc634add0169c3914e8c31964a4880987fa77e6b19f",
  "artifacts/public_benchmark.jsonl": "29fc773db307d20730c3b32d1b1daa4de06517e802194a08a07dc1ffc260cf96",
  "artifacts/final_artifact_gate.json": "b56099b20dca3b18fe3b93d752837b820ac4c0fcbac50e0b9b879c8c8cb80edd"
}
```

## Supplemental results audit

Completed after the supplement ended. `independent_supplement_review.json` records an independent stdlib-only reconstruction from raw per-call receipts; `independent_supplement_check.py` reproduces it. All 42 selected external rows, their deterministic family/length selection, bound hashes and worker data identity agree. Full-threshold dtaianomaly completes 35 cases and times out on 7, with a 143.8498105-fold median ratio on completed pairs; the 250-threshold comparator completes all 42, median ratio 8.1665116. No timeout enters a numerical speed ratio. Maximum output discrepancy is 9.547918e-15. All 112 feasible mechanism cases and 1,680 raw calls agree with reported medians, ratios, coverage and hashes; maximum output discrepancy is 6.805667e-14. Randomized raw order and sorted aggregate order contain identical rows by case ID. No benchmark kernel was rerun.

## Rendered manuscript review

All eight pages of the PDF built at 2026-10-19 15:07:10 UTC were rasterized with Poppler at 110 DPI and visually inspected individually, alongside full text extraction. Reviewed PDF SHA256: `e17ee031636e86041c8d7af14dee85b565c9e3dbceffe9b3490765e5f8619ff5`. Equations, theorem statements, all three figures, both tables, references and appendix were readable; no clipping, overlaps or missing glyphs were observed. Prior notation, prior-support credit and grammar requests were resolved.

Remaining minor request communicated to the builder: Table 2's heading “Complete families” should say “Families with completions” or equivalent. The reported 19 counts families represented among completed cases; only 18 have all selected cases complete, because SVDB has one complete and one timed-out case. Numeric 19 is correct with the clarified meaning. Optional layout polish: keep Table 2 in its results subsection rather than floating past the limitations heading. Supplementary numbers otherwise match the audited raw receipts.

## Final review closure

Final PDF SHA256: `d362f667d4eb37e47c00653f0bb61bf343f48d80a71dbbee5998a463696e5a90` (865502 bytes). Recorded UTC: 2026-10-19T15:11:34.971197+00:00.

Final pages 5 and 7 were rasterized at 110 DPI and visually re-inspected. Figure 2 now has clear explicit speed-ratio ticks. Table 2 now says “Families represented” and its caption explicitly requires at least one completed pair in each counted family. Bibliography wrapping is clean. The remaining six rendered pages (1, 2, 3, 4, 6, 8) were independently confirmed byte-identical to the previously visually reviewed rasterizations.

All substantive and minor review requests are resolved. The standard float placement of Table 2 is acceptable and is not an outstanding defect. No outstanding Critical, Important, or Minor finding remains within this review's code/math/record/visual scope. The automated-review and scientific-scope qualifications above continue to apply.
