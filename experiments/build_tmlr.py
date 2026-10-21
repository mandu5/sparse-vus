"""Build the anonymous TMLR variant without editing the released manuscript.

Default: verify the unmodified official style and generate anonymous sources.
--fetch-styles downloads missing pinned upstream files. --build explicitly
compiles the PDF; do not run builds during controlled benchmark timings.
--source-zip packages only the anonymous manuscript and its dependencies.
This does not submit anything or attest to human authorship/COI declarations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
TEMPLATE = PAPER / "tmlr-template"
TEMPLATE_REPOSITORY = "https://github.com/JmlrOrg/tmlr-style-file"
TEMPLATE_COMMIT = "7bf90efe3a0debbba703c05c43f3ff7e4d4a2992"
STYLE_HASHES = {
    "tmlr.sty": "816214ff5919aa457b6b443bee52b15d9561421417b7f8a50cc84651519f0002",
    "tmlr.bst": "306fd454cf40771bee01293eeb98d2c1cd5f4e11ed0cd7296b335f354fc45206",
    "fancyhdr.sty": "3d2922548e0e5f1a6c5676eda6ebb6dc20d7d305b4d8c2be5f1c833fb1084e6d",
    "LICENSE": "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
    "README.md": "91310b3f169ecd2d48f6c62ca8b2c9fb3f537d432d8e5d6aa4b6ac88f5c064f9",
    "main.tex": "85a994256fae53477e935bbacdf45b7e0e031abff660991485a61bff9bd4704c",
}
IDENTIFIERS = re.compile(
    r"Youngmin\s+Ko|rhdudals0505|gosmain|/Users/|penn\s+state|naver\.com",
    re.IGNORECASE,
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_styles(fetch: bool) -> dict[str, str]:
    receipts = {}
    for name, expected in STYLE_HASHES.items():
        target = TEMPLATE / name
        if not target.exists() and fetch:
            url = f"https://raw.githubusercontent.com/JmlrOrg/tmlr-style-file/{TEMPLATE_COMMIT}/{name}"
            with tempfile.TemporaryDirectory(prefix="tmlr-template-") as tmp:
                downloaded = Path(tmp) / name
                subprocess.run(["curl", "--fail", "--location", "--silent",
                                "--show-error", "--output", str(downloaded), url], check=True)
                data = downloaded.read_bytes()
            if digest(data) != expected:
                raise ValueError(f"Unexpected official template bytes: {name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        if not target.exists() or digest(target.read_bytes()) != expected:
            raise ValueError(f"Missing or modified official style: {name}; use --fetch-styles")
        receipts[name] = expected
    return receipts


def section(text: str, start: str, end: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"Expected exactly one marker pair: {start}, {end}")
    return text.split(start, 1)[1].split(end, 1)[0].strip()


def move_table_caption(match: re.Match[str]) -> str:
    block = match.group(0)
    start = block.index(r"\caption{")
    pos = start + len(r"\caption{")
    depth = 1
    while depth:
        if block[pos] == "{" and block[pos - 1] != "\\":
            depth += 1
        elif block[pos] == "}" and block[pos - 1] != "\\":
            depth -= 1
        pos += 1
    label = re.match(r"\s*\\label\{[^}]+\}", block[pos:])
    if label:
        pos += label.end()
    caption = block[start:pos]
    remaining = block[:start] + block[pos:]
    opening = re.match(r"\\begin\{table\}(?:\[[^]]*\])?", remaining)
    assert opening is not None
    return remaining[:opening.end()] + "\n" + caption + "\n" + remaining[opening.end():]


def generated_sources() -> tuple[dict[str, str], dict[str, str]]:
    main = (PAPER / "main.tex").read_text()
    title_match = re.search(r"^\\title\{(.+)\}$", main, re.MULTILINE)
    if title_match is None:
        raise ValueError("Expected one-line title command")
    title = title_match.group(1)
    abstract = section(main, r"\begin{abstract}", r"\end{abstract}")
    body = section(main, "% BEGIN SHARED BODY", "% END SHARED BODY")
    inputs = {"main.tex": digest(main.encode())}

    def expand(match: re.Match[str]) -> str:
        path = (PAPER / match.group(1)).resolve()
        if path.parent != PAPER.resolve() or path.suffix != ".tex":
            raise ValueError(f"Unexpected manuscript input: {path.name}")
        content = path.read_text()
        inputs[path.name] = digest(content.encode())
        return content.rstrip() + "\n"

    # Resolve the optional result wrapper before recursively expanding inputs.
    body = re.sub(
        r"\\IfFileExists\{([^}]+)\}\{\\input\{\1\}\}\{\}",
        lambda m: r"\input{" + m.group(1) + "}" if (PAPER / m.group(1)).exists() else "",
        body,
    )
    for _ in range(10):
        if not re.search(r"\\input\{([^}]+)\}", body):
            break
        body = re.sub(r"\\input\{([^}]+)\}", expand, body)
    else:
        raise ValueError("Recursive manuscript input")

    bib = (PAPER / "vldb-references.bib").read_text()
    inputs["vldb-references.bib"] = digest(bib.encode())
    if set(re.findall(r"\\bibitem\{([^}]+)\}", body)) != set(re.findall(r"@\w+\{([^,]+),", bib)):
        raise ValueError("Manuscript and BibTeX keys differ")
    body, count = re.subn(r"\\begin\{thebibliography\}\{[^}]+\}.*?\\end\{thebibliography\}",
                          "", body, flags=re.DOTALL)
    if count != 1:
        raise ValueError("Expected exactly one bibliography")
    body = body.replace(r"\cite{", r"\citep{")
    body = re.sub(r"\\begin\{table\}(?:\[[^]]*\])?.*?\\end\{table\}",
                  move_table_caption, body, flags=re.DOTALL)
    body = body.replace(
        "AI assistance supported software development, mathematical derivation,",
        "AI systems were used extensively in software development, mathematical derivation,",
    )
    before_appendix, appendix = body.split(r"\appendix", 1)
    body = (before_appendix.rstrip() + "\n\n\\clearpage\n"
            + "\\bibliographystyle{tmlr-template/tmlr}\n\\bibliography{tmlr-references}\n"
            + "\\clearpage\n\\appendix" + appendix)
    macros = "\n".join(line for line in main.splitlines()
                       if line.startswith((r"\newtheorem", r"\newcommand")))
    results = (PAPER / "results.tex").read_text()
    inputs["results.tex"] = digest(results.encode())
    wrapper = r"""% Anonymous TMLR preparation; this file is not a submission receipt.
\documentclass[10pt]{article}
\makeatletter
\def\input@path{{tmlr-template/}}
\makeatother
\usepackage{tmlr}
\usepackage{amsmath,amssymb,amsthm,booktabs,graphicx,hyperref,url}
\hypersetup{pdfauthor={},pdftitle={Exact and Error-Bounded VUS Evaluation}}
\input{tmlr-macros.tex}
\input{tmlr-title.tex}
\author{Anonymous authors}
\begin{document}
\maketitle
\begin{abstract}
\input{tmlr-abstract.tex}
\end{abstract}
\input{tmlr-body.tex}
\end{document}
"""
    wrapper = wrapper.replace("Exact and Error-Bounded VUS Evaluation", title)
    generated = {
        "tmlr.tex": wrapper,
        "tmlr-title.tex": r"\title{" + title + "}\n",
        "tmlr-abstract.tex": abstract + "\n",
        "tmlr-macros.tex": macros + "\n" + results,
        "tmlr-body.tex": body.strip() + "\n",
        "tmlr-references.bib": bib,
    }
    for name, text in generated.items():
        if IDENTIFIERS.search(text):
            raise ValueError(f"Personal identifier found in anonymous source: {name}")
    return generated, inputs


def source_archive(generated: dict[str, str]) -> dict[str, object]:
    assets = sorted(set(re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}",
                                  generated["tmlr-body.tex"])))
    files = list(generated) + assets + [f"tmlr-template/{name}" for name in
                                       ("tmlr.sty", "tmlr.bst", "fancyhdr.sty", "LICENSE")]
    readme = ("# Anonymous manuscript source\n\n"
              "Compile from this directory using `tectonic tmlr.tex`.\n"
              "The TMLR style files are unmodified upstream files; their license is included.\n"
              "This archive contains manuscript sources and figures, not the computational artifact.\n"
              "The default TMLR header is a formatting convention, not proof of submission.\n")
    target = PAPER / "tmlr-anonymous-source.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.md", readme)
        for name in sorted(files):
            archive.write(PAPER / name, name)
    return {"path": target.name, "bytes": target.stat().st_size,
            "sha256": digest(target.read_bytes()), "file_count": len(files) + 1}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-styles", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--source-zip", action="store_true")
    args = parser.parse_args()
    if args.check and (args.build or args.source_zip):
        parser.error("--check cannot build or write a ZIP")
    styles = verify_styles(args.fetch_styles)
    generated, inputs = generated_sources()
    for name, content in generated.items():
        target = PAPER / name
        if args.check:
            if not target.exists() or target.read_text() != content:
                raise ValueError(f"Stale anonymous source: {name}")
        else:
            target.write_text(content)
    if args.build:
        subprocess.run(["tectonic", "--keep-intermediates", "--keep-logs", "tmlr.tex"],
                       cwd=PAPER, check=True, stdout=sys.stderr, stderr=sys.stderr)
    archive = source_archive(generated) if args.source_zip else None
    print(json.dumps({"template_repository": TEMPLATE_REPOSITORY,
                      "template_commit": TEMPLATE_COMMIT, "template_sha256": styles,
                      "input_sha256": inputs,
                      "generated_sha256": {n: digest(t.encode()) for n, t in generated.items()},
                      "source_archive": archive,
                      "external_submission_status": "not submitted by this script",
                      "human_authorship_and_declarations": "not attested by this script"}, indent=2))


if __name__ == "__main__":
    main()
