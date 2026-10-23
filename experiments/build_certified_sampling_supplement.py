"""Build the new study's anonymous, audited transport; never modify or upload originals.

The whitelist begins with every dependency verified by the standard-library
bundle audit. Scientific source bytes remain unchanged. Only metadata strings
are anonymized; dependent metadata commitments are explicitly rebound. The
original auditor is retained and a second auditor differs only in whole SHA256
string literals, so it can check the derived transport's commitments.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
import tokenize
import zipfile

ROOT = Path(__file__).resolve().parents[1]
AUDIT_RECEIPT = "artifacts/certified-sampling-validation-20261023/bundle-audit.json"
ORIGINAL_AUDITOR = "experiments/audit_certified_sampling_bundle.py"
DERIVED_AUDITOR = "experiments/audit_certified_sampling_bundle_anonymous.py"
CORPUS = "artifacts/msad-corpus-20261023"
CODE_SUFFIXES = {".py", ".toml", ".sh", ".go"}
JSON_STRING = re.compile(r'"(?:[^"\\]|\\.)*"')
SHA = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")
IDENTITY = re.compile(r"Youngmin[ _]?Ko|rhdudals0505|mandu00005|gosmain|yun-yeseul|"
    r"(?:https?://(?:www\.)?(?:github\.com|raw\.githubusercontent\.com|gist\.github\.com)/mandu5(?:/|$))|"
    r"(?:https?://api\.github\.com/(?:repos|users)/mandu5(?:/|$))|"
    r"(?:https?://mandu5\.github\.io(?:/|$))|(?:git@github\.com:mandu5/)|"
    r"(?:/Users/|/home/|/root/|/private/|/var/folders/|[A-Za-z]:[\\/]Users[\\/])[^\s\"'`<>]+",
    re.IGNORECASE)
HOST_FIELD = re.compile(r'("(?:node|hostname)"\s*:\s*)("(?:[^"\\]|\\.)*")')

EXTRA = (
    "pyproject.toml", "LICENSE", "THIRD_PARTY.md", ORIGINAL_AUDITOR,
    "experiments/reproduce_msad_corpus.py", "experiments/fetch_reference.py",
    "experiments/msad_primary_first_20261023.py",
    "experiments/fetch_msad_score_corpus.py",
    "experiments/exploration/sampling_theory_20261023.py",
    "experiments/exploration/sampling_theory_20261023.json",
    "experiments/exploration/sampling_bigint_certificate_20261023.py",
    "experiments/exploration/sampling_bigint_certificate_20261023.json",
    "experiments/exploration/audit_sampling_certificate_20261023.py",
    "experiments/exploration/audit_sampling_certificate_20261023.json",
    "experiments/exploration/audit_msad_full_certificate_20261023.py",
    "experiments/exploration/audit_msad_saturation_20261023.py",
    "experiments/exploration/audit_msad_certificate_full_cost_20261023.py",
    "artifacts/msad-certificate-full-cost-20261023/independent-cost-ledger-audit.json",
    "artifacts/msad-sampling-20261023/completion.json",
    "artifacts/msad-sampling-20261023/primary-first-scheduler.json",
    "artifacts/msad-sampling-20261023/score-precision-summary.json",
    f"{CORPUS}/ATTRIBUTION.md",
    "tests/test_sampling.py", "tests/test_sampling_bounds.py",
    "tests/test_radix.py", "tests/test_compiled.py", "tests/test_pr_compiled.py",
    "tests/test_saturation.py", "tests/test_dense_radix.py", "tests/test_parity.py",
    "tests/test_msad_acquisition.py", "tests/test_msad_reproduction.py",
    "tests/test_audit_certified_sampling_bundle.py", "tests/test_fast_vus_adapter.py",
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_name(name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or not path.parts:
        raise ValueError("Unsafe transport path: "+name)
    return name


def read_input(root, name):
    safe_name(name)
    path = root/name
    if any(p.is_symlink() for p in (path, *path.parents) if p != root.parent):
        raise ValueError("Symlink in transport input: "+name)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Unsafe input: "+name)
    return path.read_bytes()


def select_inputs(root, extra=EXTRA, include_corpus_closure=True):
    root = Path(root).resolve()
    audited = json.loads(read_input(root, AUDIT_RECEIPT))["verified_repository_sha256"]
    files = {}
    for name, expected in audited.items():
        data = read_input(root, name)
        if sha(data) != expected:
            raise ValueError("Frozen dependency changed: "+name)
        files[name] = data
    names = set(extra)
    if include_corpus_closure:
        names.update(p.relative_to(root).as_posix() for p in (root/"src/sparse_vus").glob("*.py"))
        protocol = json.loads(read_input(root, f"{CORPUS}/protocol.json"))
        bound = dict(protocol["source_sha256"])
        bound.update({f"{CORPUS}/{p}": h for p,h in protocol["metadata_sha256"].items()})
        for name, expected in bound.items():
            data = read_input(root, name)
            if sha(data) != expected:
                raise ValueError("Frozen dependency changed: "+name)
            files[name] = data
    for name in sorted(names):
        files[name] = read_input(root, name)
    return dict(sorted(files.items()))


def nontext(value):
    if isinstance(value, str): return None
    if isinstance(value, dict): return {k:nontext(v) for k,v in value.items()}
    if isinstance(value, list): return [nontext(v) for v in value]
    return value


def assert_nontext_equal(name, before, after):
    suffix = PurePosixPath(name).suffix
    if suffix == ".jsonl":
        left, right = before.splitlines(), after.splitlines()
        if len(left) != len(right):
            raise ValueError("Changed numeric/structural JSON lines: "+name)
        pairs = zip(left, right)
    elif suffix == ".json": pairs = [(before, after)]
    else: return
    for left, right in pairs:
        if left == right: continue
        left_text, right_text = left.decode(), right.decode()
        if JSON_STRING.sub('""',left_text) != JSON_STRING.sub('""',right_text):
            raise ValueError("Changed numeric/structural JSON lexical tokens: "+name)
        integer_string = re.compile(r'"-?[0-9]+"')
        if integer_string.findall(left_text) != integer_string.findall(right_text):
            raise ValueError("Changed numeric JSON integer strings: "+name)
        if nontext(json.loads(left)) != nontext(json.loads(right)):
            raise ValueError("Changed numeric/structural JSON content: "+name)


def anonymize_metadata(name, data):
    text = data.decode("utf-8")
    changes = Counter()
    identifying = IDENTITY.search(text)
    has_host = PurePosixPath(name).suffix in {".json", ".jsonl"} and HOST_FIELD.search(text)
    if not identifying and not has_host:
        return data, changes
    if PurePosixPath(name).suffix in CODE_SUFFIXES:
        raise ValueError("Scientific source contains identifying text; refusing alteration: "+name)
    if PurePosixPath(name).suffix in {".json", ".jsonl"}:
        def host(match):
            changes["machine_hostname"] += 1
            return match.group(1)+'"[machine hostname omitted]"'
        clean = HOST_FIELD.sub(host, text)
        def scrub(match):
            decoded = json.loads(match.group())
            replacement, count = IDENTITY.subn("[identifying metadata omitted]", decoded)
            if count and re.match(r"\s*:", clean[match.end():]):
                raise ValueError("Identifying JSON key requires review: "+name)
            changes["identifying_metadata"] += count
            return json.dumps(replacement, ensure_ascii=False) if count else match.group()
        # Most ledgers have no identifiers; avoid tokenizing every JSON string.
        if identifying: clean = JSON_STRING.sub(scrub, clean)
    else:
        clean, count = IDENTITY.subn("[identifying metadata omitted]", text)
        changes["identifying_metadata"] += count
    result = clean.encode()
    assert_nontext_equal(name, data, result)
    return result, +changes


def derive_auditor(source, mapping):
    """Replace whole SHA256 Python string literals; preserve every other byte."""
    text = source.decode()
    offsets = [0]
    for line in text.splitlines(keepends=True): offsets.append(offsets[-1]+len(line))
    replacements = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type != tokenize.STRING: continue
        value = ast.literal_eval(token.string)
        if isinstance(value, str) and SHA.fullmatch(value) and value in mapping:
            replacement = mapping[value]
            if not SHA.fullmatch(replacement): raise ValueError("Invalid replacement SHA256")
            start = offsets[token.start[0]-1]+token.start[1]
            end = offsets[token.end[0]-1]+token.end[1]
            replacements.append((start,end,token.string.replace(value,replacement)))
    clean = text
    for start,end,replacement in reversed(replacements):
        clean = clean[:start]+replacement+clean[end:]
    class Substitute(ast.NodeTransformer):
        def visit_Constant(self,node):
            if isinstance(node.value,str) and SHA.fullmatch(node.value):
                node.value = mapping.get(node.value,node.value)
            return node
    if ast.dump(Substitute().visit(ast.parse(text))) != ast.dump(ast.parse(clean)):
        raise ValueError("Derived auditor changed more than SHA256 string literals")
    return clean.encode()


def transported_name(name, hashes):
    match = re.search(r"report-([0-9a-f]{16})\.json$",name)
    if not match: return name
    matches = {new[:16] for old,new in hashes.items() if old.startswith(match.group(1))}
    if len(matches) > 1: raise ValueError("Ambiguous abbreviated ledger hash")
    return name[:match.start(1)]+next(iter(matches))+name[match.end(1):] if matches else name


def make_payload(original):
    base, redactions = {}, {}
    for name,data in original.items():
        safe_name(name)
        base[name], redactions[name] = anonymize_metadata(name,data)
    current = base.copy()
    # Always apply transformations to the original scrubbed base, never rewrite
    # already-derived hashes. Acyclic metadata commitments stabilize finitely.
    for _ in range(len(original)+2):
        hashes = {sha(original[n]):sha(data) for n,data in current.items() if original[n] != data}
        names = {n:transported_name(n,hashes) for n in original}
        replacements = {**hashes, **{n:new for n,new in names.items() if n != new}}
        pattern = re.compile("|".join(re.escape(k) for k in sorted(replacements,key=len,reverse=True))) if replacements else None
        updated = {}
        for name,data in base.items():
            if PurePosixPath(name).suffix in CODE_SUFFIXES or pattern is None:
                updated[name] = data
            else:
                updated[name] = pattern.sub(lambda m:replacements[m.group()],data.decode()).encode()
        if updated == current: break
        current = updated
    else: raise ValueError("Metadata hash rebinding did not converge; cyclic commitments")
    payload, entries = {}, {}
    for name,data in current.items():
        target = names[name]
        if target in payload: raise ValueError("Transport filename collision: "+target)
        assert_nontext_equal(name,original[name],data)
        if PurePosixPath(name).suffix in CODE_SUFFIXES and data != original[name]:
            raise ValueError("Scientific source byte identity lost: "+name)
        payload[target] = data
        entries[target] = dict(source_path=name, source_sha256=sha(original[name]),
            byte_identical=data == original[name], metadata_redactions=dict(redactions[name]),
            hash_rebinding=data != base[name], renamed=target != name,
            nontext_json_equal=True if PurePosixPath(name).suffix in {".json", ".jsonl"} else None)
    if ORIGINAL_AUDITOR in original:
        payload[DERIVED_AUDITOR] = derive_auditor(original[ORIGINAL_AUDITOR],hashes)
        entries[DERIVED_AUDITOR] = dict(source_path=ORIGINAL_AUDITOR,
            source_sha256=sha(original[ORIGINAL_AUDITOR]), byte_identical=False,
            transformation="sha256_string_literals_only",
            original_auditor_preserved_at=ORIGINAL_AUDITOR)
    return payload, entries


VERIFY_SCRIPT = '''"""Verify every transported file and the SHA-only auditor derivation (stdlib)."""
import ast
import hashlib
import json
from pathlib import Path
import re
root = Path(__file__).resolve().parents[1]
m = json.loads((root/'ANONYMIZATION_MANIFEST.json').read_text())
for entry in m['files']:
    p = (root/entry['path']).resolve()
    assert p.is_relative_to(root) and p.is_file(), entry['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest() == entry['anonymous_sha256'], entry['path']
mapping = {e['source_sha256']: e['anonymous_sha256'] for e in m['files']
           if e.get('source_sha256') and e.get('transformation') != 'sha256_string_literals_only'}
old = ast.parse((root/'experiments/audit_certified_sampling_bundle.py').read_text())
new = ast.parse((root/'experiments/audit_certified_sampling_bundle_anonymous.py').read_text())
class Substitute(ast.NodeTransformer):
    def visit_Constant(self, node):
        if isinstance(node.value,str) and re.fullmatch('[0-9a-f]{64}',node.value):
            node.value = mapping.get(node.value,node.value)
        return node
assert ast.dump(Substitute().visit(old)) == ast.dump(new), 'Auditor logic changed'
print('PASS: transported checksums and SHA-only derived auditor')
'''


def readme(payload):
    manifest = payload.get(f"{CORPUS}/manifest.json")
    commitment = sha(manifest) if manifest else "[fixture has no corpus]"
    return f'''# Anonymous computational supplement: certified VUS threshold sampling

This archive contains the new threshold-sampling study's complete numerical,
integer-certificate, saturation and runtime ledgers, frozen implementations and
tests. It excludes raw datasets, upstream caches, named manuscripts, author
information, private declarations, Git history and execution logs. Earlier input
identity manifests are included only where the new acquisition protocol hashes
them. Third-party attribution and licenses are retained.

## Verify the transported evidence (Python standard library only)

```sh
python experiments/verify_anonymous_transport.py
python experiments/audit_certified_sampling_bundle_anonymous.py --output /tmp/anonymous-study-audit.json
```

Choose a fresh output filename. The second command verifies complete ledger
coverage, all eighteen sensitivity cells, exact integer decisions, saturation
witnesses, source commitments, overlap sensitivity and certificate costs. It
does not rerun metrics or acquire original input arrays.

## Anonymization and provenance

`ANONYMIZATION_MANIFEST.json` records each original and transported checksum,
metadata transformation and any renamed hash-addressed report. Machine hostnames
and other identifying metadata strings are omitted. Numeric JSON values, integer
endpoint strings and all scientific source implementations are preserved.
Dependent metadata hash references are rebound transparently. These derived
metadata bytes are not claimed to be historically identical frozen originals.

The original auditor is preserved byte for byte. Its explicitly named anonymous
copy changes only complete SHA256 string literals; the transport verifier checks
the corresponding Python AST equality. The manifest records both versions.
Existing frozen experiment scripts are historical implementations: do not append
new observations or another host's timings to supplied records.

## Install and test

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install '.[accelerate,research]'
python experiments/fetch_reference.py
python experiments/fast_vus_adapter.py --fetch
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

Without fetched external reference sources, the corresponding tests explicitly
skip; obtaining the references enables those independent controls. The included
tests concern this study and exact/certified evaluators, not older manuscript
artifact pipelines. Runtime tables describe the original single-host runs.

## Reacquire the unchanged published inputs

```sh
python experiments/reproduce_msad_corpus.py --manifest-sha256 {commitment} --cache .cache/fresh-reproduction
```

The cache must be new. Omit `--limit` to reacquire all 128 series; a supplied
`--limit` is an explicitly partial smoke test. Source member and numerical-array
hashes are checked. Upstream availability and original dataset terms apply; no
raw data are redistributed. See `artifacts/msad-corpus-20261023/ATTRIBUTION.md`.

For independent evaluations use freshly acquired NPZ arrays and these APIs:

```python
from fractions import Fraction
import numpy as np
from sparse_vus.radix import sparse_pr_radix_jit
from sparse_vus.sampling import sampled_pr_radix_jit
from sparse_vus.sampling_bounds import certified_sampled_pr
with np.load("path/to/reacquired.npz", allow_pickle=False) as data:
    labels, scores = data["labels"], data["CNN"]
    exact = sparse_pr_radix_jit(labels, scores, 30)
    sampled = sampled_pr_radix_jit(labels, scores, 30, thresholds=250)
    certificate = certified_sampled_pr(labels, scores, 30, thresholds=len(labels))
    interval = (Fraction(certificate.lower_numerator, certificate.scale),
                Fraction(certificate.upper_numerator, certificate.scale))
```

The certificate encloses the ideal real-arithmetic target. Strict ordering uses
`certificate.certifies_greater_than(other)`, not rounded displayed decimals.
Constructive witnesses and independent integer audits are in
`experiments/exploration/`. AI systems assisted derivation, implementation,
analysis and drafting; these checks do not represent external peer review.
'''.encode()


def build_supplement(root, output, inputs=None):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    original = select_inputs(root) if inputs is None else dict(inputs)
    # Freeze before transformation, and compare originals again before publishing.
    if any(read_input(root,n) != data for n,data in original.items()):
        raise ValueError("Original input changed before building")
    payload, entries = make_payload(original)
    payload["README.md"] = readme(payload)
    payload["experiments/verify_anonymous_transport.py"] = VERIFY_SCRIPT.encode()
    for name,data in payload.items():
        if IDENTITY.search(data.decode()): raise ValueError("Identifying transport text: "+name)
        entries.setdefault(name,dict(source_path=None,source_sha256=None,byte_identical=None,
                                     transformation="generated_transport_documentation"))
        entries[name].update(path=name,anonymous_sha256=sha(data),bytes=len(data))
    manifest = dict(format_version=1,scope="certified threshold sampling study only",
        scientific_source_policy="original sources byte-identical; separate SHA-literal-only derived auditor",
        numeric_json_policy="per-file nontext JSON equality; integer endpoint strings unchanged",
        original_input_files_unchanged=True, historic_metadata_byte_identity_claimed=False,
        files=[entries[name] for name in sorted(entries)])
    payload["ANONYMIZATION_MANIFEST.json"] = (json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    if any(read_input(root,n) != data for n,data in original.items()):
        raise ValueError("Original input changed during building")
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent,suffix=".zip",delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with zipfile.ZipFile(temporary,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for name,data in sorted(payload.items()):
                info = zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info,data)
        if temporary.stat().st_size > 100_000_000: raise ValueError("Transport exceeds 100MB bound")
        if output.exists(): raise FileExistsError(output)
        temporary.rename(output)
    finally:
        temporary.unlink(missing_ok=True)
    return dict(path=output.name,sha256=sha(output.read_bytes()),bytes=output.stat().st_size,
        files=len(payload),original_files=len(original),
        transformed_original_files=sum(e.get("byte_identical") is False and
            e.get("transformation") != "sha256_string_literals_only" for e in entries.values()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"paper/certified-sampling-supplement.zip")
    args = parser.parse_args()
    print(json.dumps(build_supplement(ROOT,args.output),indent=2))


if __name__ == "__main__": main()
