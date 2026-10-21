# Fixed-width preparation: scientific scope and citation notes

Reviewed 2026-10-21. This is a static mathematical/source review, not a timing result or external peer review. The reviewed `src/sparse_vus/radix.py` SHA-256 is `d8d45d3cc15105f1771aa37cf3cac95b6138a2f1ee38ee464fc940c54a55a3f5`. The paper-ready fragment is `paper/radix_method.tex`; the parent manuscript and bibliography were not edited by this review.

## Defensible result

The implemented preparation has time `O(n+Q+K)` and, when combined with the existing support-event kernels, exhaustive evaluation has time `O(n+(L+1)Q)`. Here `Q` counts maximum-buffer positions, `G` counts distinct support scores, and `K` counts original anomaly intervals; `G,K <= Q`. The model fixes score keys to IEEE-754 binary64, charges word operations and metric arithmetic including square root unit cost, and assumes address/count operations fit machine words. It is not a comparison-model result for arbitrary reals, an arbitrary-precision bit-complexity bound, or a formal floating-point interval guarantee.

The score-key transformation preserves order exactly for validated finite binary64 values. Signed zero must be canonicalized because `+0 == -0` in the metric although their bits differ. Input conversion precedes key construction: distinct integers above `2**53` can become one binary64 tie under the existing API. This is preservation of the API's metric, not preservation of arbitrary-precision source scores.

The global tie scan must retain both the first and past-last ranks of every group containing support. A group containing off-support and support points is one threshold transition. The preceding off-support-only groups contribute ROC rectangles; the off-support points tied to an event belong to the event trapezoid. PR has zero recall change on omitted groups. Computing ranks only among support positions would be wrong.

The geometry sweep is valid because original positive intervals are disjoint and ordered. For a fixed position, distances are nondecreasing as intervals move farther left or farther right. Two neighbors on each side therefore contain the two nearest distinct intervals. The pointer advances at most `K` times over increasing support positions. For a nonoriginal position, two active square-root ramps each contribute at least `sqrt(1/2)`, so their sum clips to one; otherwise the nearest interval determines the sole contribution. This uses the original sum-and-clip geometry, not a maximum-ramp approximation.

Peak auxiliary space is **not support-only**: keys, permutation, scratch and position map are input-sized. The paired kernel streams width averages and uses `O(n+Q)` words. The present PR-only completion interface retains `L+1` scalars and uses `O(n+Q+L)` words. A streaming PR-only variant could remove that last term, but this review describes the implemented path.

## Novelty boundary and primary evidence

| Ingredient | Primary prior evidence | Appropriate claim |
|---|---|---|
| Stable least-significant-digit counting radix | [MIT 6.006 lecture 7, Fall 2011, pp. 3–4](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/bf7d79105762bf79bbc0925438e1468a_MIT6_006F11_lec07.pdf), instructor [Erik Demaine](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/lecture-7-counting-sort-radix-sort-lower-bounds-for-sorting/) | Established algorithm. Eight fixed byte passes imply `O(8(n+256))`, not a new sorting theorem. |
| Order-preserving floating-point bit transform | [Michael Herf, *Radix Tricks*, December 2001](https://stereopsis.com/radix.html), floating-point support section; Herf also credits Pierre Terdiman | Established sign-bit/complement technique. This implementation uses its 64-bit form, reverses order, and canonicalizes numerical zero ties. No invention or firstness claim. |
| Sparse support and weighted cumulative sums in VUS | [Klein fast-VUS `1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00`](https://github.com/tomlouisklein/fast-VUS/blob/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py), 2026-10-16 | Prior support restriction/cumsums. Its global threshold sort and width-dependent dense coverage/search work remain in the inspected code. Do not claim first sparse or first cumulative-sum VUS. |
| Full-rank cumulative VUS, same original target | [Benchopt `2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94`](https://github.com/benchopt/benchmark_tsfm/blob/2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94/benchmark_utils/metrics.py#L325), 2026-09-29 | Independent same-task paired baseline at `thre=n`; include it in measured comparisons. |
| Global support events, exact negative rectangles/ties and linear two-distance geometry composed with fixed-width ranking | The proof in `paper/radix_method.tex`, building on the preceding sparse-event theorem | A specific exact VUS construction and computational bound. Generic sorting and one-dimensional sweep techniques remain prior art. No optimality or universal SOTA follows from this upper bound. |

Searches for `"VUS" "radix" "anomaly"` and `"volume under the surface" "radix"` did not locate a relevant earlier composition. This is a limited search result, not evidence of firstness. The existing prior-art audit and publicly available Sylligardos-attributed FF-VUS remain material: see `docs/prior_art_update_20261021.md`. Its semantic differences prevent treating its native PR output as an exact original-target comparator without qualification.

The useful research delta is the exact VUS composition plus reproducible performance on a declared workload against actual same-task implementations. Radix alone is standard engineering. Whether the composition is scientifically sufficient or fastest on the held-out scope cannot be decided from the proof or exploratory large-series probe. No acceptance, optimality, or global speed claim is made here.

## Why a NumPy stable-sort claim would be unsound

In NumPy 1.26.4, the general `sort` documentation is insufficient to establish the dispatch for indirect `uint64` sorting. The pinned [dtype table](https://github.com/numpy/numpy/blob/9815c16f449e12915ef35a8255329ba26dacd5c0/numpy/core/src/multiarray/arraytypes.c.src#L4348) uses `rsort = 1*5, 0*16`: only the first five listed types (Bool, Byte, UByte, Short, UShort) select radix. The `ULongLong`/64-bit unsigned path selects `atimsort`. [`PyArray_ArgSort`](https://github.com/numpy/numpy/blob/9815c16f449e12915ef35a8255329ba26dacd5c0/numpy/core/src/multiarray/item_selection.c#L1663) consumes that per-dtype function table. The existence of [`radixsort.cpp`](https://github.com/numpy/numpy/blob/9815c16f449e12915ef35a8255329ba26dacd5c0/numpy/core/src/npysort/radixsort.cpp) does not establish that a particular dtype uses it. The inspected NumPy 2.3.0 dtype table retains the same selection pattern.

The implemented evaluator instead performs eight explicit stable counting passes, making the bound independent of NumPy's sort dispatch. Raw-source receipts for NumPy 1.26.4, revision `9815c16f449e12915ef35a8255329ba26dacd5c0`:

| File | SHA-256 |
|---|---|
| `arraytypes.c.src` | `677a6e42086722dcb9dda139f8e58e5868e72f20e414f517be2013966f933953` |
| `item_selection.c` | `7d9701996f734ddb7677be395b2a6500a49d986a64faf9d6dbb4a066c389b1ff` |
| `radixsort.cpp` | `6e623ab6328740e5f70dc52480ce1205d0d38063211ec2a54dcf7f56df8565a8` |

## Bibliography additions for integration

The method fragment cites only the following two keys. Both URLs were opened and their contents checked on 2026-10-21. Herf's original page discusses 32-bit floats; the manuscript explicitly applies the same bit-order argument to finite binary64 rather than attributing this VUS algorithm to that article. The lecture page identifies Demaine as the instructor; the course also lists Srini Devadas, who is not assigned authorship of this individual lecture here.

```bibtex
@misc{herf2001radix,
  author = {Michael Herf},
  title = {Radix Tricks},
  year = {2001},
  month = dec,
  url = {https://stereopsis.com/radix.html},
  note = {Accessed 2026-10-21}
}

@misc{demaine2011radix,
  author = {Erik Demaine},
  title = {Lecture 7: Linear-Time Sorting},
  year = {2011},
  howpublished = {MIT OpenCourseWare, 6.006 Introduction to Algorithms, Fall 2011},
  url = {https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/bf7d79105762bf79bbc0925438e1468a_MIT6_006F11_lec07.pdf},
  note = {Accessed 2026-10-21}
}
```

For the generic manuscript's manual bibliography:

```tex
\bibitem{herf2001radix}
M. Herf. \emph{Radix Tricks}. December 2001.
\url{https://stereopsis.com/radix.html}. Accessed 2026-10-21.

\bibitem{demaine2011radix}
E. Demaine. \emph{Lecture 7: Linear-Time Sorting}.
MIT OpenCourseWare, 6.006 Introduction to Algorithms, Fall 2011.
\url{https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/bf7d79105762bf79bbc0925438e1468a_MIT6_006F11_lec07.pdf}.
Accessed 2026-10-21.
```

No typesetting, benchmark or computational correctness run was performed for this drafting task while the formal development timing process was active.
