# Sparse VUS manuscript packet

Status on 20 October 2026: **working manuscript, unsubmitted**. This packet
prepares an official-format counterpart; it is not an acceptance, venue
endorsement, external scientific review, or confirmation of novelty.
The confirmed author metadata is **Youngmin Ko — Independent Researcher,
Republic of Korea — rhdudals0505@naver.com**. The author has graduated, and
this work was conducted as an independent personal project. Penn State is
not listed as the research affiliation. No city or ORCID was supplied.
TMLR is the current primary venue candidate from the in-session scope review;
the PVLDB file is a formatting counterpart, not a claim of venue fit or
submission readiness. The scientific manuscript remains venue-neutral.
The manuscript explicitly discloses AI assistance in software development,
mathematical derivation, experiment analysis, manuscript drafting, and
in-session review. Separate test implementations from this session are
distinguished from external laboratory reproduction. Author review and
responsibility for the complete manuscript remain required before submission.

## Scientific scope

The manuscript is **Exact and Error-Bounded VUS Evaluation through Sparse Events
and Width Geometry**. Its claims are:

1. Exact elimination of inactive threshold events, including the ROC rectangle
   before each tied support transition, with support-sensitive complexity.
2. Merge-free width partitions with ordered ROC coordinates and p-box PR
   enclosures, allowing error-bounded refinement of the discrete width average.
3. Incremental PR model selection that retains preparations and refines until
   interval separation or exact tie resolution; explicitly a post-hoc follow-up.
4. Audited numerical equivalence, measured runtime tradeoffs, and
   approximation-induced ranking changes on fixed released scores.

Support restriction, support-score sorting, and weighted cumulative sums are
credited to earlier VUS work and Klein's fast-VUS. General p-box expectation
bounds are credited to Utkin and Destercke (2009) and Troffaes and Destercke
(2011). The Sylligardos CPU/GPU algorithm remains an unresolved comparator.
No global SOTA, detector improvement, or universal speedup is claimed.
The proofs concern real arithmetic; float64 guards are empirical numerical
allowances, not directed-rounding certificates.

The exact evaluator beats the released PR-only fast-VUS baseline in all 2,100
cases on each of two CPU systems, with median ratios 8.38 and 4.55. Against the
fastest tested comparator including dense methods, 209 and 574 cases are slower
or equal. Width refinement is often slower, and racing's width-300 median
speedups of 1.177 and 1.376 do not imply a net saving: summing task medians gives
10.615 versus 6.249 seconds on macOS and 10.522 versus 7.051 seconds on Linux.
Both extensions remain optional; full-width exact evaluation is the default.

The 350-series padding sensitivity retains all 23 families. Of 84 original
PR reversals, 75 survive first-score filling and 74 survive a common
64-position crop. Only five per variant have both order gaps at least 0.01.
The manuscript separates these numerical effects from model-quality claims.

## Documents and shared sources

| File | Role |
|---|---|
| [`paper/main.tex`](../paper/main.tex) | Editable generic manuscript; scientific narrative and bibliography |
| [`paper/width_method.tex`](../paper/width_method.tex) | Shared width-bound derivation |
| [`paper/racing_method.tex`](../paper/racing_method.tex) | Shared incremental selection rule, finite-resolution proof, and work accounting |
| [`paper/advancement_results.tex`](../paper/advancement_results.tex) | Current baseline and adaptive-width results derived from verified analysis |
| [`paper/selection_results.tex`](../paper/selection_results.tex) | Generated fixed-tolerance and incremental decision results on both machines |
| [`paper/vldb.tex`](../paper/vldb.tex) | Official-format entry point with confirmed author metadata |
| [`paper/vldb-references.bib`](../paper/vldb-references.bib) | Primary-source metadata, formatted with the official bibliography style |
| `paper/vldb-{title,abstract,macros,body}.tex` | Generated fragments from the same manuscript and inputs |
| [`experiments/build_vldb.py`](../experiments/build_vldb.py) | Pinned-style verification, shared-source generation, optional PDF build |
| [`paper/main.pdf`](../paper/main.pdf), [`paper/vldb.pdf`](../paper/vldb.pdf) | Verified 14-page generic and 11-page official-format outputs |

The official counterpart changes wide tables and paired-panel figures to
ordinary two-column spanning floats. It does not modify font sizes, margins,
line spacing, or upstream template styles. Numerical tables are supplied by
their recorded experiment outputs, not inferred from partial progress.
The generated precision macro is namespaced to avoid the ACM class's
Unicode-math `\Prec` collision. Inline comma-separated mathematics and the long
reference function name permit line breaks. A `2em` emergency line-breaking
stretch resolves narrow-column paragraphs without altering font or margin
settings. All three figures have descriptions in the official counterpart.

## Official template provenance

The [VLDB 2027 formatting page](https://www.vldb.org/2027/formatting-guidelines.html)
links the [official template repository](https://github.com/vldbproceedings/VLDB-Template).
This packet pins commit
[`39c95f5c6fcbe652a83be24e4eff8f2134cd3fbc`](https://github.com/vldbproceedings/VLDB-Template/tree/39c95f5c6fcbe652a83be24e4eff8f2134cd3fbc),
dated 13 July 2026. The bundled ACM class identifies itself as v2.19,
27 June 2026; `pvldb.sty` identifies the VLDB 2027 / PVLDB volume 20 overrides.
These three files are preserved byte-for-byte:

| File | SHA-256 |
|---|---|
| `paper/acmart.cls` | `2f949e6e3f2a79f2cdc218b9dcdbaa7dd451adb4ee0be1af6dc7ebe00b318ea7` |
| `paper/pvldb.sty` | `52ad3948f3231b31d2ac90f470c1759e7f96add7b577ec4e267dfbdc87fc4eb2` |
| `paper/ACM-Reference-Format.bst` | `0590db3b8d255a3af91982ab710f3ace5fcaa52434020c9af8a4f141b00b68f3` |

The class's original source and license accompany it in
[`paper/template-source`](../paper/template-source/README.md), pinned to
upstream acmart v2.19 commit `062edc8119be9067a346ce874281eab48b2c29a4`.
That directory records source hashes and a link to the complete unmodified
upstream distribution. Upstream license and copyright notices are retained.

The `\usepackage{pvldb}` and `\vldbtopmatter` blocks remain in `vldb.tex`.
The style renders the reference-format and license footer unchanged.
DOI/page values remain the official placeholders; these are not assigned
publication identifiers. The artifact-availability URL points to the
[v0.2.0 release](https://github.com/mandu5/sparse-vus/releases/tag/v0.2.0);
release publication is a separate operation from this document build. The counterpart
retains the generic manuscript's citation keys and uses the official
`ACM-Reference-Format.bst` with `vldb-references.bib`. The generator checks that
the two bibliographies have exactly the same key set.

## Build and verification

From the repository root:

```sh
# Verify the pinned styles and regenerate the common text; no typesetting.
python experiments/build_vldb.py
python experiments/build_vldb.py --check

# Fetch a missing original style only after verifying its expected hash.
python experiments/build_vldb.py --fetch-styles

# Run after controlled CPU measurements have finished.
python experiments/build_vldb.py --build
```

The script refuses modified template bytes and stale generated fragments in
`--check` mode. `--build` requires the measured advancement-results fragment
and compiles both entry points with Tectonic. It does not generate author
identity, submit a paper, or publish files.

The exact two-machine baseline, 378-case width-refinement results, 126-task
fixed-tolerance selection slowdown, and 126-task incremental race on each
machine are included. All timing work finished before final typesetting.

Final verification on 20 October 2026, after the confirmed author metadata
was incorporated, used Tectonic 0.17.0, `pdfinfo`,
`pdftotext -layout`, and `pdftoppm`. The generic PDF has **14 US Letter pages**;
the official counterpart has **11 US Letter pages total**, including references
and appendices. References begin on pages 14 and 11 respectively. Since even
the total official page count is below 12, it satisfies the current regular
paper's 12 non-reference-page limit without excluding any appendix or float.

Every page was rendered and visually inspected: generic pages 1–14 at a
1,400-pixel long edge, official pages 1–11 at 1,600 pixels. Final renders are
locally retained under the ignored `paper/rendered/final-main/` and
`paper/rendered/final-vldb/` directories. Figure 1 was enlarged to a spanning
float after inspection. The final pages have legible figures and tables,
no clipping or overlap, and intact precision notation.
Both PDFs display the confirmed name, independent affiliation, country, and
personal email; no author-information placeholder remains.

Both final TeX logs contain **zero overfull boxes, missing glyphs, undefined
citations/references, or fatal errors**. Text extraction contains no replacement
characters or unresolved `??` markers. Underfull-box warnings remain and were
visually inspected; the official class also warns about the omitted affiliation
city and its own top-matter spacing. These are recorded rather than hidden.
The generated-fragment check and all six pinned style/source hash checks pass.
Bibliography intermediates (`.blg`, `.bbl`) and build logs/renders are ignored.

| PDF | SHA-256 of verified build |
|---|---|
| `paper/main.pdf` | `a966f3495cca9fc20233ac9b1ba6156fef94faf2b1965081cf50a2d59a95f1ea` |
| `paper/vldb.pdf` | `5811041cd6d8be76e615818c7baf5f5601a71111d7e289759c6f5910a8a58736` |

PDF build timestamps can change file hashes on a later rebuild; the source and
template hashes identify the content inputs. This verification establishes the
working documents' rendering, not scientific acceptance or external review.

## Remaining submission decisions

The [PVLDB volume 20 submission rules](https://www.vldb.org/2027/submission-guidelines.html)
require real author names and affiliations for single-blind review.
A regular research paper allows 12 non-reference pages, including appendices.
The current method-and-proof narrative is prepared as a regular research
manuscript; this is a proposed category, not a venue determination.
The official-format PDF must be checked against the current rules again at
submission time.

Before external submission, the author must approve the complete manuscript
and authorship, select the venue and submission cycle, verify the archival
artifact URL, and complete the venue's author declarations.
No abstract, manuscript, or email has been sent to a venue or researcher.

Evidence and boundaries:

- [`docs/fast_vus_prior_art_20261020.md`](fast_vus_prior_art_20261020.md):
  current primary-source and source-code audit.
- [`docs/certified_independent_review_20261020.md`](certified_independent_review_20261020.md):
  separate in-session mathematical review and limitations.
- [`docs/experimental_audit_20261020.md`](experimental_audit_20261020.md):
  complete padding protocol, negative cases, and effect sizes.
- [`docs/advancement_experiment_review_20261020.md`](advancement_experiment_review_20261020.md):
  independent reconstruction and coverage review of new measurements.
- `artifacts/robustness/summary.json` and `artifacts/advancement/`:
  underlying measured summaries and retained records.
