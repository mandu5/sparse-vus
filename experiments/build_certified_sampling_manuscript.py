"""Build the anonymous certified-sampling manuscript without changing the public source.

Requires tectonic. This generates local review files; it neither submits nor
attests to author intellectual contribution or editorial declarations.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import zipfile


def main():
    root=Path(__file__).resolve().parents[1]
    paper=root/'paper'
    out=paper/'certified-sampling-submission'
    out.mkdir(exist_ok=True)
    source=(paper/'certified_sampling.tex').read_text()
    source=source.replace('% Working preprint. The template\'s preprint option makes no review-status claim.', '% Anonymous review copy generated from the public manuscript.')
    source=source.replace(r'\usepackage[preprint]{tmlr-style/tmlr}',r'\usepackage{tmlr-style/tmlr}')
    source,n=re.subn(r'\\author\{\\name Youngmin Ko.*?Independent Researcher, Republic of Korea\}',lambda _: r'\author{Anonymous authors}', source, flags=re.S)
    assert n==1
    start=source.index('Code, tests, frozen protocols, outcome records, raw integer witnesses and')
    end=source.index('Its standard-library audit',start)
    source=source[:start]+'''Code, tests, frozen protocols, outcome records, raw integer witnesses and
    input-reacquisition instructions accompany this manuscript in the anonymous
    computational supplement. The supplement README identifies its independently
    verifiable ledgers and commands. Its transformation manifest distinguishes
    original byte commitments from metadata redacted for anonymous review.
    '''+source[end:]
    source=source.replace('The public working draft\ndoes not attest to author completion of a submission\'s review declarations.', 'Author responsibility and any submission declarations are separate from\nthese computational checks.')
    assert not re.search(r'Youngmin|rhdudals|mandu5|gosmain|naver',source,re.I)
    (out/'main.tex').write_text(source)
    files=['sampling_theory.tex','sampling_empirical.tex','sparse_vus_references.bib','sampling_references.bib','figures/sampling_witnesses.pdf','tmlr-style/tmlr.sty','tmlr-style/tmlr.bst','tmlr-style/fancyhdr.sty','tmlr-style/LICENSE']
    for name in files:
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(paper/name,target)
    (out/'README.txt').write_text('Anonymous manuscript source. Compile from this directory with: tectonic main.tex\nThe official default TMLR review header is a template convention, not a submission receipt.\nPublished prior software is cited in the third person; its bibliographic author is preserved.\nThe paper discloses LLM use in a first-page footnote and its reproducibility paragraph.\n')
    receipt={'source_sha256':hashlib.sha256((paper/'certified_sampling.tex').read_bytes()).hexdigest(),'transformations':['official review style instead of preprint','anonymous author block','new evidence linked to anonymous supplement, not identifying public repository','review-status-neutral responsibility statement'],'unchanged_dependencies':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in files}}
    (out/'generation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    subprocess.run(['tectonic','--keep-logs','main.tex'],cwd=out,check=True)
    shutil.copyfile(out/'main.pdf',paper/'certified_sampling_anonymous.pdf')
    print(json.dumps({'pdf_sha256':hashlib.sha256((out/'main.pdf').read_bytes()).hexdigest(),'bytes':(out/'main.pdf').stat().st_size}))
    archive = paper / "certified_sampling_anonymous_source.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name in sorted([*files, "main.tex", "README.txt", "generation.json"]):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, (out / name).read_bytes())
    print(json.dumps({"source_zip_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                      "source_zip_bytes": archive.stat().st_size}))


if __name__ == "__main__":
    main()
