# Exact radix release integration — 21 October 2026

This review records the additive v0.3.0 integration. Both frozen holdouts have
completed and passed independent audits. The earlier v0.2.0 tag/assets and all
16 measured implementation sources remain unchanged. Final release and
transport receipts are recorded separately; this document is not an acceptance
or global speed-record claim.

## API and installation

The existing public submodule API is suitable for an additive release:
`sparse_vus.radix.sparse_pr_radix_jit(y, scores, max_buffer)` returns PR only;
`sparse_vus_radix_jit` returns `(ROC, PR)`. Both validate/convert inputs and
prepare ranks on each call. Keep these functions in the optional submodule:
top-level `sparse_vus` currently imports only NumPy-based core APIs, preserving
installation without Numba. No top-level re-export or default algorithm switch
is needed for publication.

`.[accelerate]` supplies Numba; `.[accelerate,research]` adds the experiment
tools. No GPU framework is needed. The package declares Python >=3.10;
the current numerical CI matrix covers 3.11/3.12. Do not present that matrix as
verification of every interpreter/dependency combination admitted by metadata.
The benchmark pin file and each platform's environment receipt remain the
authority for reproducing its numerical/runtime environment.

README now gives self-contained radix examples, outputs, tie/conversion rules,
JIT/preparation costs, and scope of the asymptotic bound. It explicitly separates
the branch APIs from v0.2.0 timing results and corrects the obsolete statement
that Sylligardos-attributed FF-VUS code is unavailable. Both complete 924-task reports and all negative cases are now included;
no global speed claim is added.

## Integration fixes verified in CI

- Fresh-workspace creation previously omitted the historical auditor required
  by a current test. Public and anonymous helpers now copy every inventoried
  `source-v2` file, preserving all original release anchors, original benchmark
  records, own source, and license under its separate root. Hashes and byte
  lengths are checked before copying; cache links and unlisted files are omitted.
  Root-level rerun outputs remain empty. This is not a substitute for the final
  independent historical audit with fetched input/reference caches.
- Both legacy reproduction runners now fetch the pinned Benchopt reference
  before the expanded suite. The v0.2 runner stages downloader sources so new
  download receipts do not overwrite release bindings in the checkout.
- The existing wheel job checks only the NumPy-only install. A second isolated
  environment and `check_installed_accelerated_package.py` now exercise both
  radix APIs, signed-zero ties, negative/tied scores, and float64-converted large
  integers; compare with the installed base evaluator; and verify every packaged
  Python module's bytes and the distribution version against source. The first
  environment still checks absence of Numba. These are packaging/parity checks,
  not timings.

CI run 39533404287 passed 3,206 tests on each of Python 3.11 and 3.12
(two optional Torch probes skipped per environment), both isolated wheel
checks, and real historical-v2 and Linux-v3 report reconstruction. The release
adds the completed Mac report reconstruction to the same workflow.

Before edits, both the v2 development and v3 holdout `source_sha256` maps were
inspected. The changed workspace helpers, shell runners, CI configuration,
README and new smoke helper are outside those measured-source maps. No frozen
kernel, benchmark producer, adapter, data gate, or historical snapshot was edited.

## Final integration sequence

1. Require both complete 924-case v3 audits; preserve original run directories,
   input/source hashes and negative cases. Keep the v2 development snapshot and
   timings separate. Generate reports, oracle figure and `pr_engine_results.tex`
   from those bound reports. The generator's PASS is a derivation check, not a
   replacement for either raw-record audit.
2. Run the updated CI, isolated NumPy-only and accelerated wheel checks, and a
   clean extracted-artifact full suite. Fetch sources/data separately and rerun
   both the unchanged v2 auditor and current v3 auditor in that extraction.
   No success is claimed for the new checks until their receipts exist.
3. Regenerate `paper/main.pdf` from `main.tex` plus final fragments. Regenerate
   the anonymous variant through `build_tmlr.py --build --source-zip`; inspect
   its page count/layout and anonymity again. Manuscript sources and the separate
   computational supplement have different contents and validation gates.
   The PVLDB counterpart remains an optional formatting artifact, not evidence
   of submission or venue suitability.
4. Use a new additive release, preferably **v0.3.0**, after the evidence is frozen.
   At that point update `pyproject.toml` and `CITATION.cff` together, including
   the actual release date and paper title. Both now identify v0.3.0 and 21 October 2026. Build a
   new wheel, sdist, named manuscript/research artifact and checksums; do not
   overwrite v0.2.0 assets. Record source-byte identity separately from anonymous
   metadata transformations. Publish only the actual audited scope and CPU
   descriptions supported by the new environment receipts.

The release can expose a reproducible exact evaluator without asserting a
publication, acceptance, universal speed record, or a favorable racing result.
Venue/account/human declarations remain a separate submission gate.
