# Scientific review resolution, 2026-10-23

This follow-up checks the final source revisions requested in
`certified_sampling_final_scientific_review_20261023.md`. The original review,
frozen experiments and measurement ledgers were not edited or rerun.

| Request | Final source finding | Resolution |
| --- | --- | --- |
| R1: official default and target provenance | `sampling_theory.tex` cites `officialvuscode` alongside Klein for the 250-rank default. The new bibliography entry pins official revision `467bace0c103f5c2bdb4900306d82939bcac8ff9`, covering `get_metrics` and `RangeAUC_volume_opt`. This is the source previously checked directly. | Fulfilled. |
| R2: PAULA comparison | The introduction and related work cite Sabharwal and Sedghi (UAI 2017). The text correctly distinguishes their precision-monotonicity assumptions and unknown-label acquisition setting from this available-label, dynamic-integral enclosure. It makes no annotation-efficiency or runtime superiority claim. | Fulfilled. |
| R3: stable new evidence entry point | The PDF source links the reproduction guide at immutable code snapshot `60e68af3cb2534aa7a889b5a3e177633ce7d12b8`. Following publication, independent public HTTP retrieval returned 200 and the complete guide bytes matched the local Git object. The latest guide and PDF source explicitly specify checkout of that snapshot. | Fulfilled, including public readback. |
| R4: retain negative and limiting evidence | The final empirical text retains all overlap/quantization results, the partial intervals' failure to identify an erroneous sampled set as suboptimal, the full-grid same-guarantee baseline, and all cost ratios. It recommends numerical exact evaluation ordinarily and full-grid certificates for rigorous ordering. | Fulfilled. |

The optional clarity edits are also correct: best-case regret is explicitly
defined using the maximum exhaustive value among all tolerance-tied sampled
winners; the information-limit construction puts the halo in a common tail;
and the abstract calls the large finite bound worst-case. No new mathematical
or empirical defect was introduced by these edits.

The latest guide and PDF source now explicitly instruct checkout of the cited
code snapshot after cloning. This resolves the earlier moving-branch ambiguity
without changing the frozen experiment sources or requiring further metric
experiments.

The root reports 3,517 passing tests, an isolated standard-library bundle
audit, and a modern NumPy/Numba installed-wheel check. This revision review
does not independently rerun those checks or convert them into additional
experimental replications. The previously completed independent 5,400-record
cost audit remains unchanged.

## Reviewed final source hashes

| File | SHA-256 |
| --- | --- |
| `paper/certified_sampling.tex` | `142d42831a4417142f26e4d277bbcceb34f3b734445051689c89c5728a1901d7` |
| `paper/sampling_theory.tex` | `10bc17accaabb4204e9c2f02f07e668ef823870df8bf8be551297181ab4b0573` |
| `paper/sampling_empirical.tex` | `a434b6fe42e383e677b3e64c53f2d75fc518e4cd18bae4459ff00f93590dd963` |
| `paper/sampling_references.bib` | `ae402129f7dd7db30ee8a3c1882623bf41d73f248c2a4f8b989b837440b47c2d` |
| `paper/certified_sampling.pdf` | `643b0f13c813a8e179052bc7dc22c127199a1bf2fd2cab0281e6c68ab03c8016` |
| `docs/certified_sampling_reproduction_20261023.md` | `8790315034b8277c7de9be7915c2fdafc632c23d6b522f7f8c5b3097b19d11b7` |

These final files were read at local and remote branch HEAD
`eb98c59e1ea462507bcaf14f14f191d377181beb`.

## Publication-resolution receipt

The initial HTTP 404 was observed before the cited commit was published. After
the push, a fresh independent request to each of the following public raw
objects returned HTTP 200; every response was byte-for-byte identical to
`git show <commit>:<path>`, including the final PDF. `git ls-remote` independently
confirmed the branch HEAD above. No authentication or local cache was used for
these HTTP reads.

| Public object | Commit | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Immutable reproduction guide | `60e68af3cb2534aa7a889b5a3e177633ce7d12b8` | 8516 | `ee063b729ca8007440431357a2667475427f4577368781b91c167e6c86fb3800` |
| Updated reproduction guide | `eb98c59e1ea462507bcaf14f14f191d377181beb` | 8570 | `8790315034b8277c7de9be7915c2fdafc632c23d6b522f7f8c5b3097b19d11b7` |
| Final manuscript source | `eb98c59e1ea462507bcaf14f14f191d377181beb` | 13283 | `142d42831a4417142f26e4d277bbcceb34f3b734445051689c89c5728a1901d7` |
| Final manuscript PDF | `eb98c59e1ea462507bcaf14f14f191d377181beb` | 141514 | `643b0f13c813a8e179052bc7dc22c127199a1bf2fd2cab0281e6c68ab03c8016` |

Public URLs use `https://raw.githubusercontent.com/mandu5/sparse-vus/`, the
complete commit above, and respectively
`docs/certified_sampling_reproduction_20261023.md`,
`paper/certified_sampling.tex`, or `paper/certified_sampling.pdf`.

All R1–R4 review requests are resolved, including publication/readback. The
venue judgment remains a scoped TMLR evaluation-reliability submission,
without an assertion of global SOTA, a superior model selector, or an external
acceptance outcome.
