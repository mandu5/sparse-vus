"""Create a bounded, anonymous computational supplement; never upload it.

Run only after measurements and scientific sources have been frozen. A preview
can be built earlier, but it is not the final submission artifact. Scientific
code is copied unchanged or rejected; numeric JSON tokens are never rewritten.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import unquote, urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CODE_SUFFIXES = {".py", ".go", ".sh", ".toml"}
DATA_SUFFIXES = {".json", ".jsonl", ".csv", ".md"}
OMITTED_DIRS = {"cache", "__pycache__", "vendor", "upstream", "node_modules",
                "logs", "runtime", "raw_data", "datasets", "private", "dist", "build"}
OMITTED_FILES = {"build_vldb.py", "build_tmlr.py", "build_anonymous_supplement.py",
                 "test_anonymous_supplement.py"}
SCIENTIFIC_DOCS = {
    "theory.md", "theory_advancement_20261020.md", "incremental_pr_racing_20261020.md",
    "fast_vus_prior_art_20261020.md", "certified_independent_review_20261020.md",
    "advancement_experiment_review_20261020.md", "experimental_audit_20261020.md",
    "prior_art_update_20261021.md", "pr_engine_review_20261021.md",
}
LOCAL_PATH = re.compile(r"(?:/Users/|/home/|/root/|/private/|/var/folders/|[A-Za-z]:[\\/]Users[\\/])[^\s\"'`<>]+")
URL = re.compile(r"(?:https?://|git@)[^\s\"'`<>]+", re.IGNORECASE)
JSON_STRING = re.compile(r'"(?:[^"\\]|\\.)*"')
JSON_KEY_SUFFIX = re.compile(r"\s*:")
SHA_TOKEN = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")


@dataclass(frozen=True)
class PrivacyRules:
    # This publication tool and its privacy fixtures are deliberately excluded
    # from the archive; the scientific implementations and their tests remain.
    author_tokens: tuple[str, ...] = ("Youngmin Ko", "YoungminKo", "rhdudals0505",
                                    "mandu00005", "gosmain")
    owner_accounts: tuple[str, ...] = ("mandu5", "gosmain")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scrub_string(value: str, rules: PrivacyRules) -> tuple[str, Counter]:
    counts = Counter()

    def owner_url(match):
        url = unquote(match.group(0))
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()
        segments = parsed.path.lower().strip("/").split("/")
        identified = any(
            host == owner.lower() + ".github.io"
            or (host in {"github.com", "www.github.com", "gist.github.com",
                         "raw.githubusercontent.com", "gist.githubusercontent.com"}
                and segments[0] == owner.lower())
            or (host == "api.github.com" and len(segments) >= 2
                and segments[0] in {"repos", "users", "orgs"} and segments[1] == owner.lower())
            or re.search(r"git@github\.com:" + re.escape(owner) + r"(?:/|$)", url, re.IGNORECASE)
            for owner in rules.owner_accounts)
        if identified:
            counts["owner_project_url"] += 1
            return "[project URL omitted for anonymous review]"
        return match.group(0)

    value = URL.sub(owner_url, value)
    value, n = LOCAL_PATH.subn("[local filesystem path omitted]", value)
    counts["local_filesystem_path"] += n
    for token in rules.author_tokens:
        value, n = re.subn(re.escape(token), "[author identifier omitted]", value, flags=re.IGNORECASE)
        counts["author_identifier"] += n
    return value, +counts


def json_values(text: str, suffix: str):
    if suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def nontext_tree(value):
    if isinstance(value, str):
        return None
    if isinstance(value, list):
        return [nontext_tree(item) for item in value]
    if isinstance(value, dict):
        return {key: nontext_tree(item) for key, item in value.items()}
    return value


def anonymize(relative: Path, data: bytes, rules: PrivacyRules) -> tuple[bytes, Counter]:
    text = data.decode("utf-8")
    counts = Counter()
    if relative.suffix in {".json", ".jsonl"}:
        before = json_values(text, relative.suffix)

        def replace(match):
            decoded = json.loads(match.group(0))
            clean, changed = scrub_string(decoded, rules)
            is_key = JSON_KEY_SUFFIX.match(text, match.end()) is not None
            if is_key and changed:
                raise ValueError(f"Identifying JSON key needs explicit review: {relative}")
            prefix = text[max(0, match.start() - 100):match.start()]
            if not is_key and re.search(r'"cpu_clearance"\s*:\s*$', prefix):
                clean = "[execution-coordination note omitted]"
                changed["execution_coordination_note"] += 1
            counts.update(changed)
            return json.dumps(clean, ensure_ascii=False) if clean != decoded else match.group(0)

        clean = JSON_STRING.sub(replace, text)
        if nontext_tree(before) != nontext_tree(json_values(clean, relative.suffix)):
            raise ValueError(f"Anonymization changed numeric/structural results: {relative}")
    else:
        clean, counts = scrub_string(text, rules)
    if relative.suffix in CODE_SUFFIXES and clean != text:
        raise ValueError(f"Scientific source code requires explicit review; refusing to alter: {relative}")
    return clean.encode(), counts


def selected_files(root: Path):
    for name in ("pyproject.toml", "LICENSE", "THIRD_PARTY.md"):
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(f"Required supplement input missing: {name}")
        yield path
    for area in ("src", "tests", "experiments", "artifacts", "docs"):
        for directory, dirs, names in os.walk(root / area, followlinks=False):
            dirs[:] = sorted(name for name in dirs
                             if not name.startswith(".") and name not in OMITTED_DIRS)
            for name in dirs:
                if (Path(directory) / name).is_symlink():
                    raise ValueError(f"Symlink directory in scientific inputs: {area}/{name}")
            for name in sorted(names):
                path = Path(directory) / name
                if name.startswith(".") or name in OMITTED_FILES or "progress" in name.lower():
                    continue
                if area == "docs":
                    include = path.parent == root / "docs" and name in SCIENTIFIC_DOCS
                elif area in {"src", "tests"}:
                    include = path.suffix == ".py"
                else:
                    include = (path.suffix in CODE_SUFFIXES | DATA_SUFFIXES
                               or (area == "experiments" and name.startswith("requirements")
                                   and path.suffix == ".txt"))
                if include:
                    yield path


VERIFY_SCRIPT = '''"""Verify transported anonymous bytes; this is not a scientific acceptance check."""
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "ANONYMIZATION_MANIFEST.json").read_text())
for entry in manifest["files"]:
    path = (root / entry["path"]).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise SystemExit("Missing/unsafe manifest path: " + entry["path"])
    if hashlib.sha256(path.read_bytes()).hexdigest() != entry["anonymous_sha256"]:
        raise SystemExit("Anonymous checksum mismatch: " + entry["path"])
print("PASS: all listed anonymous file hashes match; no scientific result inferred.")
'''

WORKSPACE_SCRIPT = '''"""Create a fresh workspace for original experiments, preserving supplied records."""
import argparse
from pathlib import Path
import shutil
root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--output", type=Path, required=True)
dest = p.parse_args().output.resolve()
if dest == root or dest.is_relative_to(root):
    raise SystemExit("Choose a new directory outside the supplied artifact")
dest.mkdir(parents=True, exist_ok=False)
for name in ("src", "tests", "experiments", "docs"):
    if (root / name).exists():
        shutil.copytree(root / name, dest / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
for name in ("pyproject.toml", "README.md", "LICENSE", "THIRD_PARTY.md"):
    shutil.copyfile(root / name, dest / name)
(dest / "artifacts").mkdir()
(dest / "paper").mkdir()
for name in ("mechanism_protocol.json", "external_supplement_protocol.json"):
    if (root / "artifacts" / name).exists():
        shutil.copyfile(root / "artifacts" / name, dest / "artifacts" / name)
print("Fresh workspace created. Activate a dedicated environment there, then use run_reproduction.sh.")
'''

README = '''# Anonymous computational supplement

This archive supports the submitted manuscript's algorithms, protocols and
derived measurement records. It is not a submission receipt or external peer
review. Recorded runs retain their original scope, including negative results.
AI systems were used extensively in development, analysis, drafting and
in-session checks; those checks are not external laboratory reproduction.

## Contents and provenance

`src/` contains the current implementation, `tests/` its scientific tests,
`experiments/` the frozen protocols, adapters and measurement/analysis scripts,
`artifacts/` the derived raw measurements and receipts, and `docs/` scientific
derivations/reviews. Source data, cached upstream implementations, Git history,
private author context, CI/build logs and named manuscripts are excluded.
Third-party attribution and source/license URLs are in `THIRD_PARTY.md`.
No upstream implementation or dataset is vendored or relicensed here.

`ANONYMIZATION_MANIFEST.json` records the original and anonymous SHA-256 of
every included source file, whether bytes are identical, and transformation
counts. Computation code is copied unchanged. Necessary redactions affect
identifying metadata only; JSON numeric tokens are preserved. References to
changed metadata hashes are rebound to the anonymous copy and explicitly
recorded. Original hashes remain in the manifest: this archive is not claimed
byte-identical to a public release, nor are altered metadata hashes original
preregistration commitments. Generated README/verification/workspace helpers
have no original-file hash. The manifest cannot certify scientific correctness.

```sh
python experiments/verify_anonymous_manifest.py
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r experiments/requirements-benchmark.txt
python -m pip install -e '.[accelerate,research]'
python experiments/fetch_reference.py
python experiments/dtaianomaly_adapter.py --fetch
python experiments/fast_vus_adapter.py --fetch
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 python -m pytest -q
```

Inspect additional adapters' `--help` for their pinned-source fetch commands.
Downloading pinned references is required for tests that exercise their code;
downloaded files go to ignored local cache. Tests and benchmark downloads are
different from the supplied derived measurements. An ordinary install follows
the package's dependency ranges; the requirements file pins the original
measured environment. Machine-specific timing receipts state other versions.

## Reconstruct analyses of the supplied measurements

Fetch the source score/label members before analyses that reconcile input hashes:

```sh
python experiments/fetch_score_ranges.py
python experiments/verify_artifact.py --output /tmp/rechecked-original-artifact.json
python experiments/analyze_advancement.py \\
  --mac-baseline artifacts/advancement/mac-baseline \\
  --linux-baseline artifacts/advancement/linux-baseline \\
  --certified artifacts/advancement/mac-certified --output /tmp/width-analysis
python experiments/analyze_selection.py \\
  --selection artifacts/advancement/mac-selection \\
  --mac-racing artifacts/advancement/mac-racing \\
  --linux-racing artifacts/advancement/linux-racing --output /tmp/selection-analysis
```

The supplied records retain source hashes. A later source change can make an
older run's source gate fail; do not relabel it or bypass the check. Use the
matching source snapshot or new measurements. New follow-up protocols and
results, if included, remain separate runs; consult their protocol JSON and
script `--help` for exact arguments. No result is inferred from file presence.

## Rerun measurements without overwriting supplied records

For the original experiment series, create a separate workspace:

```sh
python experiments/create_anonymous_reproduction_workspace.py --output ../vus-original-rerun
cd ../vus-original-rerun
python3.12 -m venv .venv
source .venv/bin/activate
bash experiments/run_reproduction.sh
```

For the v0.2 follow-up, use the extracted supplement with its supplied manifests
and measurements still present, activate its environment, and run:

```sh
bash experiments/run_advancement.sh ../vus-width-rerun
```

Destination directories must be new. Timing runs are sequential, use one
compute thread, exclude separately recorded JIT/download work, and require an
otherwise idle CPU. They download approximately 451 MB for the frozen public
score/label subset; no model is retrained. Do not run timing experiments beside
tests, PDF builds or other compute jobs. Preserve every negative or slower case.

The standalone manuscript PDF/source package is supplied separately. Formatting
and submission-account tools are omitted from this computational archive.
'''


def build_supplement(root: Path, output: Path, *, rules: PrivacyRules | None = None,
                     max_bytes: int = 100_000_000) -> dict:
    root, output = Path(root).resolve(), Path(output).resolve()
    rules = rules or PrivacyRules()
    if output.exists():
        raise FileExistsError(f"Choose a new archive path: {output.name}")
    originals, base, changes = {}, {}, {}
    for path in sorted(selected_files(root)):
        relative = path.relative_to(root)
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"Symlink file in scientific inputs: {relative}")
        name = relative.as_posix()
        if scrub_string(name, rules)[1]:
            raise ValueError("Identifying archive filename requires explicit review")
        original = path.read_bytes()
        anonymous, edits = anonymize(relative, original, rules)
        originals[name], base[name], changes[name] = original, anonymous, edits

    # Rebind metadata checksum chains after redaction, without changing source
    # or pretending an anonymous metadata hash was the historic commitment.
    files = base.copy()
    rebinding_counts = Counter()
    for _ in range(len(files) + 1):
        hashes = {sha(originals[n]): sha(data) for n, data in files.items()
                  if sha(originals[n]) != sha(data)}
        next_files, next_counts = {}, Counter()
        for name, data in base.items():
            count = 0

            def rebind(match):
                nonlocal count
                replacement = hashes.get(match.group(0), match.group(0))
                count += replacement != match.group(0)
                return replacement

            text = data.decode()
            if Path(name).suffix in {".json", ".jsonl"}:
                def rebind_string(match):
                    original = json.loads(match.group(0))
                    updated_value = SHA_TOKEN.sub(rebind, original)
                    return (json.dumps(updated_value, ensure_ascii=False)
                            if updated_value != original else match.group(0))

                updated = JSON_STRING.sub(rebind_string, text).encode()
            else:
                updated = SHA_TOKEN.sub(rebind, text).encode()
            if count and Path(name).suffix in CODE_SUFFIXES:
                raise ValueError(f"Anonymous metadata changes a source-code hash binding: {name}")
            next_files[name], next_counts[name] = updated, count
        if next_files == files:
            rebinding_counts = next_counts
            break
        files = next_files
    else:
        raise ValueError("Cyclic anonymous checksum dependency requires explicit review")

    generated = {"README.md": README.encode(),
                 "experiments/verify_anonymous_manifest.py": VERIFY_SCRIPT.encode(),
                 "experiments/create_anonymous_reproduction_workspace.py": WORKSPACE_SCRIPT.encode()}
    for name, data in generated.items():
        if name in files:
            raise ValueError(f"Generated helper would overwrite a scientific source: {name}")
        files[name] = data
    entries = []
    for name, data in sorted(files.items()):
        original = originals.get(name)
        operations = dict(changes.get(name, {}))
        if rebinding_counts[name]:
            operations["anonymous_hash_reference"] = rebinding_counts[name]
        entries.append({"path": name, "origin": "generated" if original is None else "source",
                        "source_sha256": sha(original) if original is not None else None,
                        "anonymous_sha256": sha(data), "anonymous_bytes": len(data),
                        "byte_identical": original == data if original is not None else None,
                        "transformations": operations})
    manifest = {"format_version": 1, "scope": "anonymous computational supplement",
                "public_release_byte_identity_claimed": False,
                "historical_hashes": "source_sha256 values bind pre-anonymization bytes; anonymous references bind transported copies",
                "omissions": ["raw source data and cached upstream code", "Git/CI/build/runtime logs",
                              "private author/submission context", "named manuscripts and publication-only tools"],
                "files": entries}
    manifest_data = (json.dumps(manifest, indent=2) + "\n").encode()
    if scrub_string(manifest_data.decode(), rules)[1]:
        raise ValueError("Manifest contains an identifying path or author token")
    files["ANONYMIZATION_MANIFEST.json"] = manifest_data
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".zip", delete=False) as temp:
            temp_name = Path(temp.name)
        with zipfile.ZipFile(temp_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for name, data in sorted(files.items()):
                item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                item.compress_type = zipfile.ZIP_DEFLATED
                item.create_system = 3
                item.external_attr = (0o100755 if name.endswith(".sh") else 0o100644) << 16
                archive.writestr(item, data)
        size = temp_name.stat().st_size
        if size > max_bytes:
            raise ValueError(f"Compressed supplement size {size} exceeds limit {max_bytes}")
        # Detect source mutation during packaging, including a still-running run.
        for name, original in originals.items():
            if (root / name).read_bytes() != original:
                raise ValueError(f"Source changed during supplement build: {name}")
        temp_name.replace(output)
    finally:
        if temp_name is not None:
            temp_name.unlink(missing_ok=True)
    return {"archive": output.name, "bytes": output.stat().st_size,
            "sha256": sha(output.read_bytes()), "source_files": len(originals),
            "unchanged_source_files": sum(e["byte_identical"] is True for e in entries),
            "transformed_source_files": [e["path"] for e in entries if e["byte_identical"] is False],
            "generated_files": len(generated) + 1,
            "publication_status": "local preparation only; no upload or submission"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_supplement(args.root, args.output), indent=2))


if __name__ == "__main__":
    main()
