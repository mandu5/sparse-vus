# Saturation diagnostic and updated empirical manuscript review

This internal review independently checks the diagnostic algebra, its complete retained ledger, raw integer stopping evidence, and the updated empirical manuscript against its source receipts. It changes no frozen producer source, production code, or manuscript text.

## Diagnostic algebra

Let `s` be the first complete threshold where recall is one, `b` the first sampled threshold at or after it, and `r_prev` recall at the preceding sampled threshold. Write `T_s=A_s+B_s`, and let `C_s,C_b` be their global predicted counts. Inserting `s` into the sampled grid changes only this recall increment: every subsequent increment is zero. Consequently,

`sampled - inserted = (1-r_prev) * (T_b/C_b - T_s/C_s)`.

Expanding `T_b=T_s+delta_A+delta_B` gives the reported three terms:

- Buffer mass: `(1-r_prev) delta_B / C_b`.
- Original mass: `(1-r_prev) delta_A / C_b`.
- Count dilution: `-(1-r_prev) T_s (C_b-C_s)/(C_b C_s)`.

This identity also covers a saturation threshold already retained by the sampled grid, when the change is zero. The producer's complete-tie counts and mapping to the most recent support event are consistent with it. The diagnostic does not claim that this intervention removes all omitted-threshold effects.

## Independent integer evidence

Saturation is equivalent to full component coverage and `B >= 2(P0-A)`. Using a lower bracket for the current buffer mass proves saturation; using an upper bracket and a strict reverse inequality proves that the predecessor is unsaturated. A predecessor with incomplete coverage is also unsaturated. Monotonicity then proves that this is the first saturation threshold.

The independent replay imports no production metric code. It reconstructs original temporal intervals directly from labels, sums their clipped square-root ramp brackets, reconstructs expanded components, and enumerates all global score classes with `numpy.unique`. Python integer square roots and `Fraction` comparisons prove the stopping condition for all 96 score vectors and all 31 widths: **2,976/2,976 proofs pass**.

Each raw witness retains current and previous global counts, admitted original count, lower/upper integer buffer mass, component hits and total components, the exact stopping threshold, signed integer margins, and rational recall bounds. Every current lower recall equals one; every predecessor upper recall is strictly below one. Global predecessors can differ from the producer's previous support event, providing a separate enumeration of the same stopping boundary. All recorded saturation global counts agree.

The replay protocol was frozen before these independent outcomes. The timing owner granted a slot before its exclusive timing window, and the audit completed before that window. The original diagnostic and its protocol remain unchanged.

## Ledger and mechanism interpretation

A separate standard-library ledger audit confirms all eight selected primary harmful cases, all twelve models, all 2,976 width records, frozen hashes, means, decomposition identities, and winner sets. Its largest binary64 identity residual is `1.67e-16`; the largest mean-recomputation residual is `5.56e-16`. Those residual checks audit numerical bookkeeping; the algebra above establishes the exact identity.

For the KDD21/005 CNN/LOF pair:

| Model | Sampled minus exhaustive | Buffer term | Original term | Count dilution | Remaining inserted-grid error |
|---|---:|---:|---:|---:|---:|
| CNN | -0.4445838844 | +0.0260043509 | 0 | -0.4705882353 | 0 |
| LOF | +0.1616922812 | +0.1818905508 | 0 | -0.0527973551 | +0.0325990855 |

LOF exhibits the claimed soft-mass inflation. CNN exhibits substantial negative count dilution. The insertion restores the exhaustive winner on exactly three cases: KDD21/005, Yahoo_A1real_33, and Yahoo_A2synthetic_44. Five remain wrong. Thus the three restorations must be described as outcomes of inserting the saturation boundary, not three proofs that soft-buffer inflation alone caused the original selection errors. The updated manuscript makes this distinction through the signed decomposition and its stated limits.

## Updated empirical text and tables

Reviewed `paper/sampling_empirical.tex` SHA-256: `0f3bcdaa934b33c7414ff045dc8bc7faed75a09df29d30eb4c721bccc47fb74c`.

All sixteen family table entries match the primary JSON: sample counts, practical-error counts, and maximum regret rounded to four decimals. The twelve zero maximum-regret entries are actually zero in the primary report, not missing values or erroneous rounding. Counts total 128 and practical errors total eight across four families.

The source-overlap sensitivity is correctly represented: twenty bounded joint matches remain in the frozen primary panel; the 108 nonmatching cases contain four practical errors across two families, with maximum `0.2362084785`. This descriptive subgroup does not pass the original five-percent/three-family gate. The text appropriately avoids calling all recordings new or independent, and distinguishes newly evaluated score vectors from unseen source recordings.

The full-grid integer evidence supports more than eight lower-bound witnesses. Exact endpoint comparisons also prove every other primary best-case regret is below 0.01: **eight at or above 0.01 and 120 below 0.01**. At H=1,000, all 128 best-case regrets are provably below 0.01. The maximum rigorous regret intervals, expressed as display decimals, are:

- H=250: `[0.39857503016651635, 0.39857503027554464]`.
- H=1,000: `[0.0018926253154655515, 0.0018926255809339765]`.

The receipt retains exact rational upper endpoints; these decimal displays are not used to decide the cutoff. This validates the manuscript's eight-case ideal-target statement and the secondary statement that none reaches 0.01. All 128 unique exhaustive winners are certified.

No substantive numerical or interpretation defect was found in this updated empirical snapshot. Sensitivity and timing findings remain separate collections; this review does not infer their outcomes or attach an acceptance grade.

## Receipts

- `artifacts/msad-saturation-diagnostic-20261023/independent-ledger-review.json`: source algebra and standard-library ledger replay.
- `experiments/exploration/audit_msad_saturation_20261023.py`: that ledger audit.
- `experiments/exploration/replay_msad_saturation_integers_20261023.py`: independent direct-ramp integer implementation.
- `artifacts/msad-saturation-diagnostic-20261023/integer-replay-protocol.json`: protocol SHA-256 `76b9ba48540cf13b960342058357726d9a29a34442d1def38e131904e202f2c4`.
- `artifacts/msad-saturation-diagnostic-20261023/integer-replay-witnesses.jsonl`: all 2,976 raw proofs; SHA-256 `cdd636a7ed855dee9effbdd2d0739baae344893e70be272c8afdf7a989db21ca`.
- `artifacts/msad-saturation-diagnostic-20261023/integer-replay-receipt.json`: replay PASS.
- `artifacts/msad-full-certificate-20261023/updated-empirical-manuscript-review.json`: family-table, overlap-subgroup, and exact cutoff audit.

The earlier ledger-only receipt explicitly says that integer states had not then been independently recomputed. The later replay receipt above supplies that computation without modifying the earlier record.
