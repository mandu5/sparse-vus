# Published MSAD score corpus: acquisition and reproduction

The completed input corpus contains **128 series, 16 source families, and 1,536 published stored-score vectors**. It has 15,793,514 temporal positions and 189,522,168 score scalars. Compressed NPZ files occupy 112,262,040 bytes in ignored cache. The fixed candidate prefix examined 148 cases: 128 were retained, 19 matched previously retained label/observation identities, and one had a single label class. There were no failed acquisition attempts. No exact identity matched the earlier 362-series reference index; differently cropped or transformed source overlap remains possible.

The manifest is `artifacts/msad-corpus-20261023/manifest.json`, SHA256:

```
5617e4fdc0bb082ac910144212546e05cc009622e45b07b672e562a999e6bc59
```

The protocol, frozen before bulk acquisition or any new metric outcomes, is `artifacts/msad-corpus-20261023/protocol.json`, SHA256:

```
9bf1a79b50d4070eff761c6c66e6de6644f33d9b71d8a4d928ba24b50f7c15e7
```

## Reacquire all selected inputs

From the repository root, with Python and NumPy installed:

```sh
python experiments/reproduce_msad_corpus.py \
  --manifest-sha256 5617e4fdc0bb082ac910144212546e05cc009622e45b07b672e562a999e6bc59 \
  --cache .cache/msad-reproduction/fresh-check
```

The output cache path must be new and inside ignored `.cache`; a worktree cache symlink is supported with containment checks. The wrapper verifies the public manifest, protocol, acquisition source, design, prior manifests, and frozen archive/queue metadata before downloading. It then validates every selected compressed member's CRC, original decoded member SHA256, and all fourteen numerical array identities per case. The original cache and previous raw-data acquisitions are not prerequisites. Members are retrieved with exact HTTP byte ranges from the linked public MSAD source archive. Source servers must honor Range requests and retain the frozen bytes.

The generated `reproduction.json` records coverage, raw/score/array identity matches, and whether all 128 selected cases were reproduced. NPZ-container byte equality is recorded separately from exact numerical-array equality. A bounded smoke check is available by appending `--limit 3`; its receipt explicitly marks `full_selected_corpus_reproduced: false`.

A fresh-cache three-case smoke run was executed successfully on 2026-10-23: 36 score vectors and 42 arrays matched, with 2,442,792 expected HTTP response bytes. Its public receipt is `artifacts/msad-corpus-20261023/reproduction-smoke.json`, SHA256 `1ea61521b6ee90b85bb9c9e2cf1adfce3fa7ad2a51234ab3fc16199d89751fe9`. This is a functional acquisition-path check on three cases, separate from the full independent audit below.

## Complete independent input audit

`artifacts/msad-corpus-20261023/independent_input_audit.py` imports neither the acquisition module nor any metric. It independently parses source observations/labels with Python `csv.reader` and every scalar score with Python `float`, then checks the original NPZ arrays. Its completed receipt, `independent-input-audit.json`, reports:

- 128 raw members and 1,536 score members: byte length, CRC, and SHA256 verified.
- 1,792 arrays, including 189,522,168 score scalars: independently parsed values and canonical hashes identical.
- All 350 prior TSB-AD source-member hashes match the original measurement provenance; all 362 prior identity-index rows remain bound.
- The fixed 148-candidate prefix, all exclusions, selected records, source files, and manifest/log hashes are consistent.

Audit receipt SHA256: `cf9219a90121e188108bcfe6b6ca970d5b5de89c5680401fe8baff0badd0ef06`.

The acquired numerical files are headerless published text scores converted directly to binary64, with no inference, normalization, repair, rounding, smoothing, or padding. The supplied observations are retained only for identity checks and potential independently specified metadata; no new detector was trained. Array keys are `labels` (int8), `observations` (float64), and these twelve float64 vectors in fixed order: `AE`, `CNN`, `HBOS`, `IFOREST`, `IFOREST1`, `LOF`, `LSTM`, `MP`, `NORMA`, `OCSVM`, `PCA`, `POLY`.

Each manifest row exposes `series`, `family`, `source_filename`, `candidate_index`, `n`, `positive_points`, `npz_path`, `npz_sha256`, `array_sha256`, and original raw/score member receipts. `IFOREST1` is preserved as a named configuration; the twelve names are not a claim of twelve distinct architectural families.

The acquisition counter `downloaded_response_bytes_this_invocation` is 110,556,947. It sums expected bounded-range response lengths; transport overhead and any transient retried traffic are not an end-to-end network measurement. A pre-freeze local-path failure and its correction are preserved separately in `artifacts/msad-corpus-20261023-prefreeze-failure/`; no metric had been evaluated and no protocol had been frozen at that point.

## Outcome-independent timing subset

`artifacts/msad-corpus-20261023/timing-subset-proposal.json` selects the first two retained cases per family in the same precommitted hash order. The result is 30 cases, covering all sixteen families and 3,541,423 positions. This is a proposed input subset; the experiment runner must separately freeze its actual methods, semantics, timing repetitions, resolution grid, and scientific decision rules before outcomes. The full numerical study can use every acquired case.

All acquisition and reproduction tests pass: 15 tests cover ZIP CRC/path integrity, complete score coverage, no-repair parsing, source identity, metadata-deterministic selection, cache isolation, and explicit subset coverage. Full package/integration testing belongs to the final combined study validation.

Dataset/source attribution and licensing scope are documented in `artifacts/msad-corpus-20261023/ATTRIBUTION.md`. Raw data and scores remain in ignored cache. This work does not establish unseen domains or entirely independent physical recordings; the new evidence is a prospectively selected, previously unmeasured published twelve-model score workload with explicitly audited identities.
