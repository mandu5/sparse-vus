# Sparse VUS 연구 판정 — 2026-10-24

**사용자 근거 항목 6/6 수행·검증, 사전 연구 투자 5점 조건 충족. 현재 11쪽 원고의
PVLDB 모의 판정은 Accept 7 / Revise 5 / Reject 5로 갈린다.** 따라서 근거표를
채웠다는 사실을 강한 채택 전망으로 바꾸지 않는다. 6점 조건은 미통과다.

다음 연구는 같은 VUS timing의 반복이 아니라, 실제 공개 consumer에서 드러난
다른 range-metric 연산으로 일반화하는 것이다. 새 endpoint sweep과 가장 강한
단순 compiled raster, query bucketing, 공개 TimeSeAD comparator를 별도 protocol로
비교한다. 기존 결과와 심사 원문은 보존하며, 새 결과는 기존 원고의 점수로
미리 합산하지 않는다. 이 점수는 연구 투자 판단이며 학회 점수나 채택확률이 아니다.

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
| 5. 모의 심사 | 통과, 판정은 불일치 | 서로의 심사를 읽지 않은 3개 독립 최종 심사: Accept 7, Revise 5, Reject 5. 모두 동일 11쪽 PDF를 확인했고 이전 심사와 점수 변경을 보존했다. 타 심사 점수에 노출된 별도 실험 심사자는 이 3회에 세지 않았다. 가장 큰 약점은 novelty 규모와 실제 application significance다. |
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

선택은 **연구 투자 5점의 재현 가능한 whole-evaluator 성과를 보존하고, PVLDB 제출
직전의 significance 판단은 새 일반화 결과까지 보고 갱신**하는 것이다. 현재 두
심사자의 주요 반론을 무시하고 강한 Accept 수준이라고 보고하지 않는다. TMLR로
venue만 바꾸어도 새로움과 중요성의 문제는 해결되지 않는다.

## 더 강한 반증 실험과 바뀐 해석

- Conventional direct-ramp compiled control이 released scalar를 **73개 모두에서
  앞섰다**. Control/stream case ratio는 NAB 1.357, SMAP 1.201, SMD 1.166이고,
  전체 VUS workflow에서는 1.177/1.126/1.152다. 기존 큰 public-library 대비
  차이를 geometry 고유의 이득으로 돌릴 수 없다.
- 실제 pinned TSB-AD nine-metric consumer는 VUS 시간이 **0.929초 → 0.0141초**,
  전체가 **34.26초 → 33.23초(1.031배)**였다. Public baseline에서 VUS의 비중이
  약 2.7%였기 때문이다. 두 번씩 측정한 단일 입력의 기술 통계이며 population CI가 아니다.
- 새 Mac/Linux score probe는 입력과 standardized matrix가 byte-identical인 상태에서
  SVM support가 104/105개로 달라짐을 보였다. 두 저장 score를 같은 evaluator에서
  계산해 차이를 재현했다. 특정 BLAS의 인과 효과나 원래 Linux 배열의 복원은 주장하지 않는다.

독립 최종 심사와 원고의 SHA는 [post-review 대응 자료](reviews/20261024/post-review-additions.md)에
연결되어 있다. 강한 control과 실제 consumer를 넣자 두 평가가 낮아졌다. 이는
검증 수행 자체를 성과의 중요성과 동일시하면 안 된다는 직접적인 근거다.

새 연구의 설계와 통과 조건은 [range-sweep 계획](superpowers/plans/2026-10-24-range-sweep-generalization.md),
독립 이론·선행연구 검토는 `docs/reviews/20261024/range-sweep-*-feasibility.md`에 있다.
기존 component-tree의 threshold activation과 TimeSeAD의 exhaustive observed-threshold
F1을 선행연구로 인정한다. 후보 차이는 Tatbul metric의 cardinality와 overlap을
국소 통계로 갱신해 반복 배열 순회를 제거하는 데 한정한다.

## 산출물과 상태

- [최종 원고](../paper/sparse_vus_pvldb20261024.pdf), [LaTeX source](../paper/sparse_vus_pvldb20261024.tex).
- [재현 명령](REPRODUCE_PVLDB_20261024.md), [원자료·protocol·audits](../artifacts/pvldb-research-20261024/).
- [완료된 fresh Linux 실행](https://github.com/mandu5/sparse-vus/actions/runs/40049786600).
- [제출용 제목·저자·SAR·일정](PVLDB_SUBMISSION_PACKAGE_20261024.md).
- [반론과 수정 대응표](reviews/20261024/revision-response.md).

저자는 확인된 **Youngmin Ko / Independent Researcher / rhdudals0505@naver.com**이다.
졸업 학교를 현재 연구 소속으로 표기하지 않았다. 본 문서는 완료된 연구 증거와
투고 판단이며, CMT 접수증이나 외부 편집 결정문을 대신하지 않는다.
