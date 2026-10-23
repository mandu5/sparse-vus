# Full-grid integer certificate baseline

The separately frozen baseline completed all 1,536 calls on the existing 128-series, twelve-configuration panel at maximum width 30, with zero failures. The unchanged `certified_sampled_pr` API used `thresholds=n`, which retains every complete global score tie. Every series has a uniquely certified winner: one model's integer lower bound strictly exceeds every competitor's integer upper bound.

This is a same-guarantee exhaustive baseline, not a new algorithm. It was specified after the original sampled-certificate and primary numerical findings were known, but before observing any full-grid certificate outcomes. The protocol records that timing and all known motivating results. The original corpus and frozen certificate studies remain unchanged.

| Integer certificate grid | Certified unique winners | Median retained states | Median interval width |
|---|---:|---:|---:|
| Uniform-rank H=250 | 63/128 | 50 | 0.00623657 |
| Uniform-rank H=1,000 | 94/128 | 68 | 0.000389964 |
| Every distinct global score tie | 128/128 | 96 | 2.76624e-11 |

The full grid retains between one and 101 distinct states across the score vectors. Its maximum interval width is 1.71387e-9. A requested rank-grid budget greater than the number of distinct values does not ensure that every value is retained: large ties can consume several sampled ranks while rare score values are skipped. The full-grid baseline removes that omission on these published, quantized scores.

Using full-grid lower/upper endpoints to evaluate the entire previously declared sampled winner sets gives:

| Sampled selector | Strict suboptimality certified | Regret at least 0.01 certified | Largest regret lower bound |
|---|---:|---:|---:|
| H=250 | 10/128 | 8/128 | 0.39857503016651635 |
| H=1,000 | 1/128 | 0/128 | 0.0018926253154655515 |

These are bounds on ideal real-arithmetic exhaustive VUS-PR regret, obtained by exact rational comparisons. The display decimals do not define the decisions. The eight primary cases span YAHOO (four), KDD21 (two), MGAB (one), and GHL (one), reproducing the independently observed primary numerical result with rigorous ideal-target guarantees. Their series indices are 15, 20, 21, 32, 41, 66, 83, and 112.

All previously certified unique winners remain certified with the same identities. Every prior/full interval pair overlaps. Raw integer intervals are not always nested because independently rounded enclosure expressions can have different rounding/weight-uncertainty slack: 18 pairs at H=250 and 46 pairs at H=1,000 lack containment, with maximum endpoint escape below 9.43e-12. Intersect valid intervals if a nested refinement contract is required. This finding does not weaken strict ordering, which uses the full intervals directly.

The certificate runner's five synthetic decision tests passed. A separate standard-library-only replay imports no study or metric code and verifies all 1,536 endpoint records, 3,072 interval comparisons, 256 decisions, source/input hashes, and the per-family primary counts. The code and protocol still match their frozen hashes. This replay audits the ledger and its interpretation; the earlier independent arithmetic tests and proof support the underlying certificate implementation.

The baseline closes the earlier same-guarantee comparison gap for accuracy. Costs belong to the separately frozen three-method timing addendum; this study makes no runtime claim. In this panel, an exhaustive distinct-score certificate is the natural remedy and should be reported alongside the less effective sampled certificates. Performance on full-precision detector outputs with many more distinct scores remains a separate question.

Artifacts:

- `experiments/msad_full_certificate_study.py`: baseline runner and exact decision report.
- `tests/test_msad_full_certificate.py`: five synthetic checks, including decisions below float resolution.
- `artifacts/msad-full-certificate-20261023/protocol.json`: SHA-256 `fb1e1ba34bdcf6b4c21c098386fbd8e0efa46fe457c20a41d9c6905877d2ee66`.
- `artifacts/msad-full-certificate-20261023/records.jsonl`: SHA-256 `604a96f3f5ef1c42326a8786ae349381d49f715fac347196cafc5dc307eb4a46`.
- `artifacts/msad-full-certificate-20261023/report.json`: full scalar comparisons and model-selection decisions.
- `artifacts/msad-full-certificate-20261023/independent-ledger-audit.json`: independent replay receipt.
- `experiments/exploration/audit_msad_full_certificate_20261023.py`: standard-library ledger audit.
