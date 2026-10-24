# New weighted range method: integration note

The new, standalone section is `paper/weighted_range_method.tex`. It is intended for the separately named strengthened manuscript. The frozen range method and manuscript were not edited. It uses the existing theorem environment and `\ind` macro and the existing bibliography keys `tatbul2018`, `timeseadclassic`, `wagner2023timesead`, `najman2006`, and `menotti2007`.

One new bibliography entry is required in the strengthened manuscript's bibliography. The primary source was inspected at this exact revision in the preceding proof audit:

```bibtex
@misc{timeevalrangecurve2026,
  author = {{TimeEval contributors}},
  title = {{TimeEval}: Range Precision--Recall Curve Implementation},
  year = {2026},
  note = {Software, audited revision 7c3622757b1a3afa9a84cbc97ce132d9e379f715;
          accessed 24 October 2026; range\_metrics.py, lines 195--296},
  url = {https://github.com/TimeEval/TimeEval/blob/7c3622757b1a3afa9a84cbc97ce132d9e379f715/timeeval/metrics/range_metrics.py}
}
```

The source provides an existing weighted range PR curve and explicitly sorts outputs by recall/precision. It establishes that neither weighted curve construction nor that consumer is new. The associated current implementation computes one mask and calls the underlying range metric per threshold. This citation is for software inspected in 2026; it is not a claim that TimeEval or range PR-AUC was introduced in 2026.

The theorem is generic, while the implementation supports four biases, three shared cardinality choices, and two precision aggregations. The section explicitly separates these scopes. It gives the stronger `qdn+H` arithmetic bound, the requested `qd(n+H)` consequence, and the finite-grid alternative. A consumer's recall sorting is charged separately when input queries are already ordered.

The section is approximately 850 prose words. Text inspection found matching theorem/proof/align environments and display-math delimiters, and no trailing whitespace. This is not a compilation check.

This edit is text-only. No TeX compilation, numerical probe, test suite, or benchmark was run during the Mac timing window. Integration must add the new bibliography entry and include this section only in the separately named strengthened manuscript.
