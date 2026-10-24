# Sparse VUS 연구 판정 — 2026-10-24

최종 판정은 추가 blind review 집계 후 확정한다. 현재 완료된 과학적 검증은
사전에 정한 **연구 5점 조건을 충족**하며, **6점 조건은 통과하지 못했다**.
이 점수는 연구 투자 판단이며 학회 점수나 채택확률이 아니다.

## 연구 대상과 PVLDB를 선택한 이유

논문은 **Exact VUS Evaluation by Support Events and Shared Interval Geometry**다.
기존 dynamic VUS의 정확한 값을 유지하면서, 비활성 threshold와 매 width마다
반복되는 전체 시계열 작업을 제거한다. Complete global ties, dynamic denominator,
component overlap와 ROC predecessor correction을 포함한다. 비교 기반 복잡도와
고정 binary64 radix 기반 `O(n + (L+1)Q)`를 구별한다.

원래 exact evaluator 전체의 목표가 PVLDB였다. TMLR은 별도의
`certified_sampling` 원고, 즉 threshold sampling 오류와 certificate 연구에서
검토한 후보였다. 이번 판정은 그 좁은 논문이나 새 batching increment만의
판정이 아니다. 공개된 unrefereed v0.3.0 precursor를 밝히는 전체 evaluator의
첫 archival 논문 후보를 평가한다.

선택한 venue는 **PVLDB Volume 20, Regular Research, Foundations and Algorithms**다.
기존 PVLDB/VLDB Journal의 평가 operator를 정확히 보존하는 알고리즘이며,
저장된 detector profile을 읽고 평가·선택하여 결과를 쓰는 반복 분석 작업에서
효과를 측정했다. 이는 공식 [research call](https://www.vldb.org/2027/call-for-research-track.html)의
알고리즘 중심 범주와 연결된다. DBMS 전체나 새로운 detector라고 주장하지 않는다.

## 사용자 기준 1–6

| 항목 | 판정 | 근거와 범위 |
| --- | --- | --- |
| 1. 새로움 | 통과, 좁은 주장 | 2024–2026 primary paper 12편을 비교했다. 직접적인 가속 경쟁자와 contextual metric/benchmark 논문을 구별했다. 차이는 **기존 dynamic VUS의 정확한 scalar를 global ties와 ROC 보정까지 유지하며 support-event와 interval geometry로 계산하는 전체 표현**이다. PR threshold 제한 하나만의 깊은 새로움은 주장하지 않는다. |
| 2. 주 결과 | 통과 | NAB/SMAP/SMD 73개 완전한 실제 시계열, 8개 고정 detector 절차, 584개 float64 score vector. 가장 빠른 측정 공개 exact PR comparator인 Klein과 같은 target으로 비교하고, 모든 collection의 조정 신뢰구간 하한이 1보다 크다. 동일 compiled dense, geometry-only, stream, minimal-Klein ablation으로 원인을 분리했다. |
| 3. 일반성 | 통과, 명시한 범위 | 실제 MITDB/SWaT 9개를 추가하여 최대 650,000점을 측정했다. 합성 16조건은 별도 mechanism test로 표시했다. dense support, width 0, M=1, 메모리 증가, 불확실한 긴 데이터 batch increment, 재사용·label 의존성을 공개했다. |
| 4. 재현 | 통과, 주 표 기준 | 한 명령으로 fresh checkout/download/score generation/primary/supplement/audit를 실제 Linux EPYC에서 완료했다. 새 Mac 결과와 host별로 구별했다. 후속 실험에는 별도 frozen protocol과 명령이 있다. |
| 5. 모의 심사 | 최종 집계 중 | 독립적인 최초 심사 3회와 후속 심사를 보존한다. 최종 재심 중 한 건의 이전 타 심사 점수 노출을 공개하고, 이를 추가 blind review로 세지 않는다. 현재 추가 unexposed review 진행 중. |
| 6. 학회 | 통과 | PVLDB 20 Regular Research / Foundations and Algorithms. 초록 2026-11-25 17:00 America/Los_Angeles, 논문 2026-12-01 17:00. KST는 각각 11월 26일/12월 2일 오전 10시. |

심사 형식은 공개된 PVLDB 기준에 맞춘 internal surrogate다. 비공개 CMT 원본
양식을 확보했다고 주장하지 않는다. 같은 TSAD 분야의 실제 채택·탈락
OpenReview note 네 사례를 공개 데이터 mirror로 읽어 반론을 보정했다.
직접 origin bytes 검증 실패, adjacent-venue 성격과 점수 scale 차이를 명시했다.
그 점수 평균으로 PVLDB 채택확률을 계산하지 않았다.

## 실제로 얻은 결과

모두 **exact VUS 계산시간**에 관한 결과이며 detector accuracy SOTA가 아니다.

| 결과 | NAB | SMAP | SMD |
| --- | ---: | ---: | ---: |
| Mac primary Klein/stream case geometric ratio | 30.513 | 25.772 | 25.172 |
| 3-collection-adjusted 95% interval | [27.399,33.652] | [22.941,28.940] | [23.475,26.695] |
| Mac primary complete-workflow ratio | 23.03 | 22.16 | 22.57 |
| Fresh Linux complete-workflow ratio | 20.06 | 20.28 | 16.17 |
| Matched compiled dense/released ratio, batch 제외 | 2.368 | 2.905 | 3.279 |
| Minimal patched Klein/released case ratio | 12.052 | 9.067 | 6.969 |

Minimal patched Klein은 threshold 식 하나를 바꾼 **새로 구성한 ablation**이다.
그 수정만으로 Klein은 1.654/2.274/2.968배 빨라졌다. 남은 차이는 geometry/ranking과
NumPy·compiled 구현 차이를 함께 포함한다. 순수 support compression의 인과 근거는
별도의 matched compiled dense 비교다. 새로운 public baseline인 것처럼 표시하지 않는다.

긴 실제 workload에서는 MITDB 전체가 **53.14초 → 2.30초**, SWaT가
**4.34초 → 0.245초**다. 같은 ROC+PR 출력끼리의 workflow ratio는
MITDB 29.50, SWaT 25.66이다. SWaT는 단일 recording이고 MITDB는 8개 series,
7개 label geometry다. 3회 workflow 측정은 완전히 position-balanced하지 않다.

실패 범위도 측정했다. 90% positive 조건의 dense/released paired geometric ratio는
**0.980 [0.962,0.9994]**로 support 압축 이득이 사라진다. 긴 실제 데이터의
추가 batch sharing workflow interval은 두 collection 모두 1을 포함한다.
큰 dense resource 조건에서 stream의 lifetime RSS는 225.0 MiB로 released
175.2 MiB와 dense 210.6 MiB보다 크다. 이 조건들을 제외하거나 재명명하지 않았다.

## 5점과 6점의 구분

실험 전에 기록한 [판정 기준](superpowers/specs/2026-10-24-pvldb-evidence-design.md)을 유지한다.

5점 조건은 식별 가능한 기여, 실제 full-precision 3 collection, collection별
같은 target 성능비의 신뢰구간 하한 >1, strongest eligible external 대비
workflow >=1.5배, 열린 수학·측정 validity 결함 없음, 여섯 근거 항목 수행이다.
현재 과학적 조건이 충족되었다. 가장 큰 판단 위험은 특수 operator 개선의
conceptual significance다.

6점은 여기에 released implementation을 넘어서는 새 mechanism을 요구했다:
각 primary collection의 geometric ratio >=1.25 및 하한 >1, 또는 동등하게
실질적인 새 일반화다. **Mac SMD 1.207 [1.193,1.221]**은 이 기준을 넘지 못한다.
Klein-control 재측정에서도 1.205였다. 더 좋은 Linux 값이나 다른 width로
primary 결과를 대체하지 않는다. 긴 데이터 검증은 기존 core의 범위 검증이지
release 이후의 새로운 mechanism이 아니다.

## 시도한 방법과 다음 선택

1. **Full-distinct exact evaluation:** 73개 full-precision panel과 public comparator를
   실제 측정하여 기존 저-cardinality panel에만 성립한다는 문제를 해결했다.
2. **Shared geometry / width-major streaming:** 개발 단계 1.193배, primary
   collection별 1.496/1.271/1.207배. geometry-only가 이득의 상당 부분을 설명한다.
3. **Partial integer certificate + exact fallback:** 개발 workload에서 33.93배
   느렸고 조기 선택 인증은 0건이었다. 속도 개선 주장에 사용하지 않는다.
4. **Operating-range 보완:** 긴 실제 recording, controlled factor intervention,
   독립 재구성한 visited-count라는 서로 다른 세 근거로 범위·실패를 확인했다.
5. **가장 가까운 코드의 최소 수정:** Klein threshold 식 하나만 고쳐 단순한
   개선으로 설명되는 몫과 그 이후의 전체 evaluator 차이를 분리했다.

선택은 **5점의 전체 evaluator 논문을 PVLDB에 추진**하는 것이다. 6점으로 올리려면
다른 host에서 유리한 숫자를 얻거나 같은 실험을 늘리는 대신, release를 넘어서는
새 알고리즘 또는 새 target에 대한 실질적 일반화를 별도 hypothesis로 검증해야 한다.
TMLR로 venue만 바꾸는 것으로 이 novelty 조건은 해결되지 않는다.

## 산출물과 상태

- [최종 원고](../paper/sparse_vus_pvldb20261024.pdf), [LaTeX source](../paper/sparse_vus_pvldb20261024.tex).
- [재현 명령](REPRODUCE_PVLDB_20261024.md), [원자료·protocol·audits](../artifacts/pvldb-research-20261024/).
- [완료된 fresh Linux 실행](https://github.com/mandu5/sparse-vus/actions/runs/40049786600).
- [제출용 제목·저자·SAR·일정](PVLDB_SUBMISSION_PACKAGE_20261024.md).
- [반론과 수정 대응표](reviews/20261024/revision-response.md).

저자는 확인된 **Youngmin Ko / Independent Researcher / rhdudals0505@naver.com**이다.
졸업 학교를 현재 연구 소속으로 표기하지 않았다. 본 문서는 완료된 연구 증거와
투고 판단이며, CMT 접수증이나 외부 편집 결정문을 대신하지 않는다.
