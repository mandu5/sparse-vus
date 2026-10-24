# Independent reviewer A: exact v3 delta acknowledgment

**Recommendation: Accept. Internal research-quality rating: 7/10. No must-fix scientific blocker.** The correction below does not change my scientific judgment. This is an **AI-simulated review**, not an official PVLDB score, external peer review, acceptance probability, or venue decision. On the scale defined in my [immutable v2 review](strengthened-independent-a-final-v2.md), 7 means solid publishable specialized work.

24 October 2026. This acknowledgment applies to:

- Review commit: `c7eff9be3340c8fbab7afaabc54dc284ac4ac1cc`.
- PDF: `paper/exact_metrics_strengthened20261024.pdf`, **201,275 bytes**.
- PDF SHA256: `48e9c8f5f78b6b3168b67b5b1040cd06da43e74304d0f5e13184c41d0f70f75b`.
- Manifest: `artifacts/pvldb-research-20261024/strengthening/manuscript-review-snapshot-v3.json`.
- Manifest SHA256: `ee5ff107c508d93841da83e4df2bc5f22874a2ae6135e28e30f94e167f987450`.
- Unchanged evidence commit: `448ad1b714a5daa13feeba617b10e02efef674fe`.

I independently verified the PDF, manifest, all nine source files and three style files against their recorded hashes and committed bytes, and checked evidence ancestry. Relative to v2 commit `8036526f9bea0d4a03617477b290df3302e80bb2`, the sole manuscript-source change is Table 7's Apple O / All observed / Raster cell, **2.9461 → 2.9460 seconds**. Its source, `paper/strengthened_native_control_table.tex`, now has SHA256 `cd10f45f98a3b54b0e06b0b83da9b9f4808107cfd8c8bcf85e4d0203a9d57f81`. This is the correct four-decimal rounding of the independently reconstructed raw median **2.946046354 seconds**.

Full extracted PDF text differs only in that number. I independently rendered all 13 v3 pages and compared them with my v2 renders using identical settings. The only changed pixels occur on page 11, inside the corrected digit's bounding box `(512, 782, 520, 793)` in the 1237-by-1600 render. I visually inspected that page. The layout remains unchanged: references start on page 12 and only references continue onto page 13. Runtime scripts, experiment scripts and workflows have no v2-to-v3 changes. No experiment was run for this acknowledgment.

The [full v2 scientific review](strengthened-independent-a-final-v2.md), SHA256 `3446c427e16c3d8cdc72cf51766324c2aea30bc87c4ab0cb5d42d0eb3d965bd8`, is preserved. Its novelty, correctness, experimental-scope, venue-fit and public-calibration assessments apply unchanged. The correction resolves its one minor numerical-display observation; it changes no ratio, interval, claim, protocol or measurement. The largest remaining uncertainty is still the significance of the modest metric-specific increment over established component-tree and offline-processing machinery. No further finite measurement is required for my recommendation on this exact v3 PDF.
