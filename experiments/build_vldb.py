"""Generate the PVLDB counterpart from the generic manuscript.

Default: verify the pinned template files and regenerate shared TeX fragments.
--fetch-styles downloads missing files, never silently replaces changed bytes.
--build additionally compiles both PDFs with Tectonic. This is an explicit
step so document builds cannot accidentally overlap controlled CPU timings.
No submission, author metadata, or experimental results are generated here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
TEMPLATE_REPOSITORY = "https://github.com/vldbproceedings/VLDB-Template"
TEMPLATE_COMMIT = "39c95f5c6fcbe652a83be24e4eff8f2134cd3fbc"
ACM_SOURCE_COMMIT = "062edc8119be9067a346ce874281eab48b2c29a4"
STYLE_HASHES = {
    "acmart.cls": "2f949e6e3f2a79f2cdc218b9dcdbaa7dd451adb4ee0be1af6dc7ebe00b318ea7",
    "pvldb.sty": "52ad3948f3231b31d2ac90f470c1759e7f96add7b577ec4e267dfbdc87fc4eb2",
    "ACM-Reference-Format.bst": "0590db3b8d255a3af91982ab710f3ace5fcaa52434020c9af8a4f141b00b68f3",
}
SOURCE_HASHES = {
    "acmart.dtx": "4e2fd29fc8a45c3d02facb616ed29954d7932891883185460bf374303036f3e1",
    "acmart.ins": "fa7daaa9375775ce699f33f909667bdb83c0408fd8d67606926df86c346c4044",
    "LICENSE": "ca3227f672053cb608959d7e1d476c7a13efea11be3f6e53758a68b650c918e8",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_styles(fetch: bool) -> dict[str, str]:
    receipts = {}
    files = [
        (name, expected, PAPER / name,
         "https://raw.githubusercontent.com/vldbproceedings/"
         f"VLDB-Template/{TEMPLATE_COMMIT}/{name}")
        for name, expected in STYLE_HASHES.items()
    ] + [
        (f"template-source/{name}", expected, PAPER / "template-source" / name,
         "https://raw.githubusercontent.com/borisveytsman/"
         f"acmart/{ACM_SOURCE_COMMIT}/{name}")
        for name, expected in SOURCE_HASHES.items()
    ]
    for name, expected, destination, url in files:
        if not destination.exists() and fetch:
            with tempfile.TemporaryDirectory(prefix="sparse-vus-template-") as tmp:
                downloaded = Path(tmp) / destination.name
                subprocess.run(
                    ["curl", "--fail", "--location", "--silent", "--show-error",
                     "--output", str(downloaded), url],
                    check=True,
                )
                data = downloaded.read_bytes()
            if sha256(data) != expected:
                raise ValueError(f"Downloaded template hash mismatch: {name}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        if not destination.exists():
            raise FileNotFoundError(f"Missing {name}; use --fetch-styles")
        digest = sha256(destination.read_bytes())
        if digest != expected:
            raise ValueError(f"Template changed; preserve upstream bytes: {name}")
        receipts[name] = digest
    return receipts


def section(text: str, start: str, end: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"Expected exactly one pair of markers: {start}, {end}")
    return text.split(start, 1)[1].split(end, 1)[0].strip()


def shared_fragments() -> dict[str, str]:
    main = (PAPER / "main.tex").read_text()
    title_match = re.search(r"^\\title\{(.+)\}$", main, re.MULTILINE)
    if title_match is None:
        raise ValueError("Expected a single-line title command in main.tex")
    title = title_match.group(1).replace("\\\\", " ")
    abstract = section(main, r"\begin{abstract}", r"\end{abstract}")
    body = section(main, "% BEGIN SHARED BODY", "% END SHARED BODY")
    inputs: dict[str, str] = {"main.tex": sha256(main.encode())}

    def expand(match: re.Match[str]) -> str:
        name = match.group(1)
        path = (PAPER / name).resolve()
        if path.parent != PAPER.resolve() or path.suffix != ".tex":
            raise ValueError(f"Unexpected shared input: {name}")
        if not path.exists():
            # Results must be supplied by the measurement owner, never fabricated.
            return match.group(0)
        content = path.read_text()
        inputs[name] = sha256(content.encode())
        return f"% Shared source: {name}\n{content.rstrip()}\n"

    body = re.sub(r"\\input\{([^}]+)\}", expand, body)
    references = PAPER / "vldb-references.bib"
    bib = references.read_text()
    inputs[references.name] = sha256(bib.encode())
    expected_keys = set(re.findall(r"\\bibitem\{([^}]+)\}", body))
    actual_keys = set(re.findall(r"@\w+\{([^,]+),", bib))
    if expected_keys != actual_keys:
        raise ValueError("Generic/PVLDB bibliography citation keys differ")
    body, bibliography_count = re.subn(
        r"\\begin\{thebibliography\}\{[^}]+\}.*?\\end\{thebibliography\}",
        lambda _: "\\bibliographystyle{ACM-Reference-Format}\n"
                  "\\bibliography{vldb-references}",
        body, flags=re.DOTALL,
    )
    if bibliography_count != 1:
        raise ValueError("Expected exactly one bibliography in shared manuscript")
    # The single-column manuscript has wide tables and paired-panel figures.
    # In the official two-column class these use standard spanning floats.
    # No font, margin, line-spacing, or template style is modified.
    body = re.sub(r"\\begin\{table\}(?:\[[^]]*\])?", r"\\begin{table*}[t]", body)
    body = body.replace(r"\end{table}", r"\end{table*}")
    descriptions = {
        "figures/event-elimination.png": (
            "Score positions and a ROC curve illustrate that negative-only "
            "events contribute rectangles before tied support transitions."
        ),
        "public-results.png": (
            "Paired plots show exact-evaluation speed ratios by support fraction "
            "and cumulative threshold-sampling errors for ROC and PR."
        ),
        "figures/mechanism.readable.png": (
            "Four panels show the score-counting ablation and dense-comparator "
            "speed ratios across support fractions, widths, and two lengths."
        ),
    }
    for image, description in descriptions.items():
        pattern = r"\\begin\{figure\}\[t\](?:(?!\\end\{figure\}).)*?" + re.escape(image)
        match = re.search(pattern, body, flags=re.DOTALL)
        if match:
            start = match.start()
            end = body.index(r"\end{figure}", match.end()) + len(r"\end{figure}")
            block = body[start:end].replace(r"\begin{figure}", r"\begin{figure*}")
            block = block.replace(r"\end{figure}", r"\end{figure*}")
            block = block.replace(
                r"\caption{", r"\Description{" + description + "}\n" + r"\caption{",
                1,
            )
            body = body[:start] + block + body[end:]

    banner = "% Generated by experiments/build_vldb.py; edit main.tex/shared inputs.\n"
    provenance = "\n".join(f"% SHA-256 {name}: {digest}" for name, digest in inputs.items())
    macros = "\n".join(
        line for line in main.splitlines()
        if line.startswith((r"\newtheorem", r"\newcommand", r"\input{results.tex}"))
    )
    # unicode-math in the ACM class reserves \Prec for U+2ABB at begin-document.
    # Namespace the manuscript's precision notation instead of changing styles.
    body = re.sub(r"\\Prec(?![A-Za-z])", lambda _: r"\VusPrecision", body)
    macros = re.sub(r"\\Prec(?![A-Za-z])", lambda _: r"\VusPrecision", macros)
    # Permit inline comma-separated examples to wrap at their punctuation.
    # This only changes legal breakpoints, not mathematical content or sizing.
    body = re.sub(
        r"(?<!\\)\$([^$]+)\$",
        lambda match: "$" + match.group(1).replace(",", r",\allowbreak ") + "$",
        body,
    )
    body = body.replace(
        r"\texttt{RangeAUC\_volume\_opt}",
        r"\texttt{RangeAUC\_\allowbreak volume\_\allowbreak opt}",
    )
    return {
        "vldb-title.tex": banner + r"\title{" + title + "}\n",
        "vldb-abstract.tex": banner + abstract + "\n",
        "vldb-macros.tex": banner + macros + "\n",
        "vldb-body.tex": banner + provenance + "\n" + body + "\n",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-styles", action="store_true")
    parser.add_argument("--check", action="store_true",
                        help="Verify generated files without rewriting them.")
    parser.add_argument("--build", action="store_true",
                        help="Compile both PDFs; run only outside controlled timings.")
    args = parser.parse_args()
    if args.check and args.build:
        parser.error("--check and --build are mutually exclusive")
    styles = verify_styles(args.fetch_styles)
    generated = shared_fragments()
    for name, content in generated.items():
        path = PAPER / name
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise ValueError(f"Stale generated fragment: {name}")
        else:
            path.write_text(content)
    if args.build:
        if not (PAPER / "advancement_results.tex").exists():
            raise FileNotFoundError("Verified advancement_results.tex is required")
        for source in ("main.tex", "vldb.tex"):
            subprocess.run(
                ["tectonic", "--keep-intermediates", "--keep-logs", source],
                cwd=PAPER, check=True,
            )
    print(json.dumps({
        "template_repository": TEMPLATE_REPOSITORY,
        "template_commit": TEMPLATE_COMMIT,
        "acm_source_commit": ACM_SOURCE_COMMIT,
        "template_sha256": styles,
        "generated_sha256": {
            name: sha256(content.encode()) for name, content in generated.items()
        },
        "mode": "check" if args.check else "build" if args.build else "generate",
        "publication_status": "working manuscript; unsubmitted",
        "author_metadata": {
            "name": "Youngmin Ko",
            "email": "rhdudals0505@naver.com",
            "affiliation": "Independent Researcher",
            "country": "Republic of Korea",
        },
    }, indent=2))


if __name__ == "__main__":
    main()
