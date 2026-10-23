# Certified-sampling submission artifact and policy audit

Checked on 23 October 2026 against the live official TMLR pages, the live
OpenReview submission invitation, and the local manuscript. This is an artifact
and evidence audit, not an editorial decision, submission receipt, or an
attestation on behalf of the author. The starting public commit was
`eb98c59e1ea462507bcaf14f14f191d377181beb`; the submission derivative is being
built separately. Frozen experiment sources and measurement records were not
changed for this review.

## Concrete manuscript findings

The first anonymous PDF inspected was
`paper/certified_sampling_anonymous.pdf`, SHA-256
`3cb1207899cd9a2f4960860eda0c218ec958a4b120083edac3b458f01f28d2f5`:
12 physical pages, 143,144 bytes. PDF text, metadata and link annotations were
read directly. After the table-caption correction, the final inspected rebuild
is SHA-256 `cf8f874277593c490e1d12ddcff170e39e742bda55bca8e579ff6a7ed7e96a04`,
12 pages and 143,181 bytes. Its first-page disclosure and absence of personal
email, affiliation and local user identifiers were independently rechecked.
The root also visually inspected all twelve rebuilt pages and reported no
overflow; this audit's independent recheck used text, metadata and source order.

| Item | Verified finding | Remaining artifact action |
| --- | --- | --- |
| Author block and metadata | Anonymous author block; no PDF Author metadata; no personal email or local user path in extracted text. | Repeat these checks on the upload candidate after the final rebuild. |
| Current-work public link | The direct named GitHub reproduction link was replaced by a reference to the anonymous computational supplement. | Keep the actual supplement filename and instructions consistent with the PDF. |
| LLM disclosure | A first-page footnote explicitly names literature search, mathematical derivation, implementation, orchestration and drafting; it distinguishes internal agent checks from external peer review. | Retain the footnote and detailed disclosure. This addresses disclosure, not the separate human-origin expectation below. |
| Template | Default TMLR review mode, using the vendored official style. Its review header is a template convention, not evidence of an actual submission. | Keep the named public draft in preprint mode. |
| Table captions | The initial seven caption placements were corrected. All seven now precede their tabular environments; the anonymous PDF was rebuilt. | Resolved. No experimental source or result changed. |
| Length | The inspected anonymous PDF has only 12 pages including references. | Select Regular submission; recheck after the final build. |

The official guide requires an anonymized PDF using its LaTeX template and an
anonymized PDF/ZIP supplement of at most 100 MB. Named public preprints are
allowed, but the anonymous submission must not link to a named version of
itself. Submissions carry CC BY 4.0 from submission. These rules support making
a separate review copy while retaining the public research package.
[TMLR author guide](https://jmlr.org/tmlr/author-guide.html)

The current upstream style revision and the vendored source both resolve to
`7bf90efe3a0debbba703c05c43f3ff7e4d4a2992`. The template explicitly places table
titles before tables. This is a formatting correction, not an experimental
change. [Official template](https://raw.githubusercontent.com/JmlrOrg/tmlr-style-file/7bf90efe3a0debbba703c05c43f3ff7e4d4a2992/main.tex)

### The remaining prior-work citation is a distinct issue

The anonymous PDF still cites the genuine public precursor as Ko (2026), with
its author and version-0.3.0 release URL in the bibliography. Those are the only
author/project-owner identifiers found in its text and URI annotations. The
body describes that work in the third person as an already released baseline;
it does not describe it as an anonymous contribution of this paper.

The official sources do not state that every ordinary self-citation must be
anonymized. The explicit prohibition concerns linking a named version of the
submission. Thus the prior release citation should not automatically be called
a policy violation. Preserving the genuine citation is a defensible choice,
and preserves the important distinction between the old evaluator and the
present contribution. A reviewer could infer a relationship from the public
project, but public-preprint availability itself is allowed. Do not erase the
precursor, change its chronology, or describe it as new to improve anonymity.
The direct link to this new study's named reproduction guide was the concrete
link that needed replacement.

## Anonymous computational supplement

The older `build_anonymous_supplement.py` targets the earlier active-prefix
paper; its scientific-document allowlist and generated instructions do not
establish completeness for this study. A separate certified-sampling package
is appropriate. Its final validation should show:

1. A neutral entry-point README explains this paper's target, numerical APIs,
   integer guarantees, and exact audit commands. It includes the new corpus,
   sampling, full-grid certificate, mechanism and cost evidence, not just the
   old exact-evaluator study.
2. The ZIP contains source, tests, public derived evidence, original protocol
   commitments, attribution and reacquisition instructions. Raw benchmark
   observations and score arrays stay outside the archive; they are not needed
   for the standard-library ledger audit and their redistribution license has
   not been established.
3. Metadata redactions and resulting hashes are explicit. An anonymized file's
   digest must not be presented as the original frozen file's digest. Preserve
   scientific values, executable behavior, third-party credits, and a coherent
   transport map between original commitments and anonymized bytes.
4. Extraction into a clean temporary directory passes the advertised audit.
   Include every file referenced by hash or explicitly classify external
   pinned-source commitments. A ZIP-level SHA alone does not prove this.
5. A recursive text/metadata scan finds no personal email, local home path,
   current-work named repository link, author-facing private checklist, Git
   history, caches, raw datasets, or accidental named manuscript. Legitimate
   third-party names and license notices should remain.
6. Record final ZIP size, SHA-256, extraction audit output and the PDF digest
   together. Upload it under `supplementary_material`, not `beyond_pdf`.

These are package acceptance checks proposed for this artifact. They do not
claim that the completed experiment was rerun on a second host or that the
reviewers are required to inspect the supplement.

The separate anonymous manuscript-source ZIP is
`paper/certified_sampling_anonymous_source.zip`, 57,353 bytes, SHA-256
`78b92e22c4cbd04383b2ad992fde708e13ff3225c9ffda13891764a869036c62`.
Its twelve members contain the TeX sources, figure, official style/license,
generation receipt and README; ZIP CRC validation passed and its `main.tex`
matches the generated anonymous source. This source ZIP is not the computational
evidence supplement. It can accompany that supplement inside the final single
review ZIP rather than occupying the interactive `beyond_pdf` field.

### Final computational ZIP receipt

The completed upload candidate is `paper/certified-sampling-supplement.zip`:
**5,162,442 bytes, 101 files**, SHA-256
`898d1550a8aaba59fe655c48ecfdbeb86690b062cafc36f3eab24efe1ee84214`.
This audit independently reread those ZIP bytes, reproduced the digest and
member count, and checked every member's CRC; no CRC failure occurred.

The fresh-extraction validation receipt
`/tmp/certified-sampling-supplement-validation.json` has SHA-256
`4af9cc25e0c2f29e917ccd033026fe112659fd59d1d5d945ac06fd5cbb183bcc`.
The extracted-package audit
`/tmp/certified-sampling-supplement-fresh-audit.json` has SHA-256
`428ed0a0da6222938c41f31d2847e4022a2b3ebaacb688e6e2b7635c23132220`.
Both receipts were read and their digests recomputed in this review.

The recorded extraction checks pass for transport checksums, the SHA-only
derived auditor, all 51 audited dependencies, eighteen sensitivity cells,
integer winner/regret decisions, 2,976 saturation witnesses and all 5,400
certificate-cost calls. Two hostname fields were redacted and eighteen metadata
files were transparently rebound. The receipt confirms unchanged originals,
byte-identical scientific code, and preserved numeric JSON lexemes, structure
and integer endpoint strings. It records eight passing builder tests and
2,682 passing included scientific tests with fetched reference implementations;
tested source/configuration bytes match the final ZIP. Those executions were
performed by the supplement builder agent, not repeated by this document audit.

These checks close the computational-package inventory. Their scope is evidence
transport and reproducibility validation: the extracted ledger audit does not
reacquire raw inputs, rerun metric measurements or repeat the timing experiment.
The final anonymous PDF, manuscript-source ZIP and computational ZIP are three
distinct artifacts; only the computational ZIP is needed in the optional
`supplementary_material` slot for this standard PDF submission.

## Actual initial OpenReview fields

The following fields were read directly from the live
[`TMLR/-/Submission` invitation](https://api2.openreview.net/invitations?id=TMLR/-/Submission),
not inferred from an old checklist. The account and author profile were not
accessed in this audit.

| Field | Schema / prepared value | What is still factual author information |
| --- | --- | --- |
| `title` | Required, at most 250 characters. `When Threshold Sampling Reverses VUS Rankings: Exact and Certified Evaluation of Anomaly Scores` | None beyond agreeing to this manuscript. |
| `abstract` | Required, at most 5,000 characters. Copy the final scientific abstract, without the footnote text embedded in it. | None beyond agreeing to the claims. |
| `authors` / `authorids` | Required names and OpenReview profiles. Manuscript author is Youngmin Ko; current affiliation in the named draft is Independent Researcher. | Actual active profile ID, profile history and complete author list. Do not infer current Penn State employment/enrollment from graduation history. |
| `pdf` | Required PDF, at most 50 MB. Use the final anonymous PDF. | None. |
| `submission_length` | Required. Regular submission means no more than 12 pages of main content before references/appendices. Current PDF qualifies. | None after final page check. |
| `supplementary_material` | Optional PDF/ZIP, at most 100 MB. Use the validated single anonymous ZIP. | None. |
| `beyond_pdf` | Optional interactive webpage ZIP only. | Leave unused for this standard PDF submission. It is not a LaTeX or code supplement field. |
| `previous_TMLR_submission_url` / `changes_since_last_submission` | Optional prior-rejection URL and change description, the latter at most 5,000 characters. | Actual prior TMLR submission history. A local draft is not a submission. |
| `competing_interests` | Required, at most 5,000 characters; covers relevant relationships during the previous 36 months beyond the profile. | Actual employment, funding, support, hardware/cloud gifts and other relevant relationships. Do not auto-fill N/A. |
| `human_subjects_reporting` | Required, at most 5,000 characters. | Actual applicable approval/oversight information; do not invent an IRB determination. |

No cover letter, keywords, funding or action-editor recommendation field appears
in this initial invitation schema. The author guide separately requests editor,
funding and conflict information; those may arise later in the workflow. Their
absence from this initial schema does not waive them. Do not create fictitious
field values or claim the account is ready merely because a login was reported.

A factual starting description for human-subject reporting is: this study
re-evaluates previously released score vectors and labels, recruits no
participants and collects no new human-subject data. Some underlying benchmark
families contain human-derived data. Original provenance is retained and raw
data are not redistributed in the supplement. This description is not a claim
of IRB exemption or approval.

## AI disclosure and human contribution are separate requirements

The FAQ requires an explicit first-page footnote for LLM use and separately
states an expectation that the ideas, claims and results be human-sourced.
The new footnote truthfully identifies broad assistance rather than describing
this work as proofreading-only. It does not establish the separate origin
expectation. [TMLR FAQ](https://jmlr.org/tmlr/faq.html)

Editorial policy permits assistive LLM tools while retaining human
responsibility, and its authorship criteria require substantial intellectual
contribution, drafting/revision, responsibility and awareness of submission.
It also restricts overlap with prior or concurrent archival peer-reviewed work;
a public preprint is a different category. Actual author contribution,
submission history, quota and conflicts must be represented accurately.
[TMLR editorial policies](https://jmlr.org/tmlr/editorial-policies.html)

Neither a signed checklist nor retrospective reading converts tool-originated
ideas into human-originated ideas. Conversely, the policy should not be
paraphrased as a blanket ban on AI assistance. This audit cannot attest the
author's intellectual contribution from executable tests or agent reviews.
The actual division of intellectual work needs to remain explicit, including
any substantive human corrections or decisions. No declaration on this issue
was made or submitted here.

## Scientific interest and remaining claim boundaries

This study is materially stronger than rerunning the old exact evaluator:

- It isolates a concrete dynamic-PR failure mechanism, proves finite bounds,
  and supplies same-label constructions at ordinary widths. The general claim
  that sampling or PR interpolation can be inaccurate is not presented as new.
- It implements real-target integer enclosures and uses exact endpoint
  comparisons to settle the 0.01 regret threshold on every one of the 128
  primary cases, including the 120 below the threshold.
- It re-evaluates twelve published configurations per series with independent
  controls, frozen selection, tie-aware regret, source-overlap sensitivity and
  complete cost accounting.
- It includes the simple full-grid certificate comparator. The practical
  lesson is to use numerical exhaustive integration for ordinary evaluation
  and full-grid integer certificates when rigorous ordering is required;
  partial certificates are not sold as a superior selector.

The reader learns why 250 sampled ranks can miss a score class even when there
are at most 101 distinct scores, what numerical exactness does and does not
guarantee, and how to audit a model-ranking claim. This is a direct evaluation
reliability contribution for anomaly-detection researchers. These are reasons
for TMLR audience interest, not a predicted review score or certification.

TMLR assesses convincing evidence and clear findings of interest to its
audience. Its criteria distinguish systematic studies with actionable lessons
from plain reruns, and do not require a benchmark SOTA result. The paper should
be assessed on those stated claims. [TMLR acceptance criteria](https://jmlr.org/tmlr/acceptance-criteria.html)

Boundaries already retained in the paper remain essential: one pinned dynamic
VUS-PR target, quantized released scores, one timing host, 20 bounded
endpoint-shift overlaps, four practical errors in the 108 nonmatching subgroup,
and partial intervals that do not prove any harmful sampled choice suboptimal.
The near-unit synthetic worst case is not an observed real-data prevalence.
Internal audits support the reported claims; they are not external acceptance.
No additional large experiment is identified by this submission-format audit.

## Three substantive author-reading questions

These are prompts for understanding and intellectual review, not attestations
to be ticked automatically:

1. **Why can precision increase after recall saturates, and why can retaining
   the later threshold change the PR area?** Explain the distinction between
   dynamic soft positive mass, clipped recall, and the assignment of a recall
   increment to a sampled precision. Then explain why adding the saturation
   threshold fixes only three of eight affected selections.
2. **What exactly does the integer certificate prove?** Derive the lower bound
   on best-case regret for the sampled tied-winner set, and explain why an
   exhaustive floating-point value can fall outside a very narrow interval
   for the ideal real-arithmetic target without refuting that interval.
3. **What should a benchmark practitioner change after reading this paper?**
   Explain why rank budget exceeding the number of distinct scores can still
   fail, why all score classes are a simple remedy on this corpus, and why the
   extra cost of full integer certification is justified only when its stronger
   guarantee is needed. State which conclusions remain valid for the 108-case
   nonmatching subgroup and which population claims are not supported.

The existing [Korean author brief](certified_sampling_author_brief_ko_20261023.md)
provides the relevant definitions and results. A useful author response should
identify an actual correction, decision, or interpretation where warranted;
answering these prompts alone does not establish the origin of the research.


## Final immutable-guide rebuild

The public PDF now links to the reproduction guide at commit `55f2304ca5a8abdb8e3a4da7c5d8a1f596d72ebc`, which includes the exact-byte report replay instruction. Its scientific snapshot remains `60e68af3`. Extracted public PDF text is unchanged; the anonymous transformation and scientific dependencies are unchanged. Final PDF/ZIP hashes and generated-source checks are recorded in `artifacts/certified-sampling-validation-20261023/submission-artifacts.json`. Both PDFs have 12 pages; the computational ZIP above is unchanged.
