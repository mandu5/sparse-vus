# Anonymous computational supplement builder

`experiments/build_anonymous_supplement.py` prepares a local ZIP; it does not upload, submit, create an account, or make author declarations. Build the final file only after the scientific sources and all measurement records are frozen. The current preview is explicitly not that final artifact.

## Build and inspect

Run outside controlled CPU timing:

```sh
python experiments/build_anonymous_supplement.py \
  --output dist/anonymous-computational-supplement.zip
```

The destination must be new. The builder prints the ZIP byte count, SHA-256, file counts, and transformed relative paths. It enforces a conservative 100,000,000-byte compressed limit, uses deterministic ZIP metadata, rejects symlinks/identifying archive names, and checks that selected files did not change during packaging. A later rerun after new experiments needs a new filename and a fresh receipt.

Extract the ZIP into a new directory and run its `experiments/verify_anonymous_manifest.py` before downloads. This verifies transported bytes, not scientific correctness. The extracted README gives environment setup, upstream fetches, numerical tests, analysis reconstruction, and separate-workspace rerun instructions. A generated workspace helper avoids the named-manuscript/CI dependencies of the original public-release helper while retaining the original helper's bytes for provenance.

## Included and excluded scope

Included: current Python implementation, scientific tests, original experiment code, pinned data/source manifests, protocols, derived per-case measurements, structured environment/analysis/audit receipts, original license, third-party attribution, and an explicit selection of scientific derivation/review documents. New source/test files and future structured results under these roots are discovered without requiring a Git commit. Additional scientific documents require review of the small `SCIENTIFIC_DOCS` allowlist.

Excluded: `.git`, raw input datasets, downloaded upstream source, caches, hidden folders, bytecode, vendored directories, logs/progress streams, binary plots/PDFs, named manuscripts, citation metadata, publication-only builders, their privacy-specific packaging test, submission/identity documents, private context and career information. Binary plots are derivable from included measurements and remain in the separately prepared anonymous manuscript package. The computational ZIP does not nest that package.

Only source-data download instructions and hashes are supplied. No upstream code or raw benchmark data is redistributed. Third-party people, software URLs, license notices and citations are preserved; the builder does not broadly remove names or email addresses. Original repository attribution is represented by the existing non-personal contributor license. The MIT license does not supersede upstream/data licenses.

## What may change in the anonymous copy

Scientific code (`.py`, `.go`, `.sh`, `.toml`) is either copied byte-for-byte or causes the build to fail for explicit review. Identifying literals are never silently rewritten inside measured implementations. Source and result files in the working tree are not changed.

In included textual metadata, the builder can remove known author identifiers, owner GitHub/API/Pages/raw links, personal absolute paths, and private execution-coordination notes. JSON strings are decoded before checking, so escaped identifiers are also caught. JSON numeric tokens and non-string structure remain unchanged. Numeric records without identifying metadata remain byte-identical.

Changing metadata can invalidate another receipt's checksum. The builder follows those checksum dependencies and rebinds them to the anonymous copies. It rejects a cycle or any dependency that would require altering executable source. This is an explicitly transformed provenance chain, **not** a claim that its new hashes were the original preregistration commitments. The original hashes remain available in the manifest.

`ANONYMIZATION_MANIFEST.json` lists each included source path, original SHA-256, anonymous SHA-256, byte-identity status, archived size, and transformation categories/counts. It records generated README/verification/workspace helpers separately. It does not contain original sensitive strings or a personal source-root path. Existing historical scientific claims are not strengthened by this transport manifest.

## Verification so far

Twelve tests passed after observed failing tests. They exercise private/cache/log exclusion; preservation of scientific and third-party bytes; numeric-token preservation under metadata redaction; original/anonymous provenance; refusal to edit source code; symlink rejection; deterministic ZIPs; the size cap; escaped JSON identities; binary input exclusion; extracted verification detecting tampering; a fresh reproduction workspace preserving supplied results; checksum rebinding; and owner links across GitHub hosts.

An initial live-worktree preview contained 170 source files: 148 byte-identical and 22 transformed metadata/review files, plus four generated archive files. It compressed to 3,827,562 bytes. These are preview facts, not final freeze statistics. All scientific code passed the unchanged-source requirement. No benchmark was run by the builder. Root owns the full-suite run and the isolated final-artifact suite after controlled timing; these are not yet claimed passed here.

Before final upload, rebuild after the last scientific change, verify its extracted hashes, fetch the pinned references, and run the scientific suite from that isolated extraction. Recheck the archive inventory and declarations against the final paper. Submission and acceptance each require separate external receipts.
