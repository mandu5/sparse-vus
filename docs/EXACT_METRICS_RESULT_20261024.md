# Exact metric evaluation: 연구 결과와 투고 판단

2026-10-24. 이 문서는 새 range-metric 연구를 기존 VUS-only 결과와 구별한다.
**사용자 기준 6개 중 6개 통과. 실험 전에 정한 연구 투자 5점 조건을 충족하고,
6점의 새 일반화 경로도 충족했다.** 다음 단계는 아래 PVLDB cycle의 실제 투고다.
이는 근거를 갖춘 연구 투자 판단이며, 외부 reviewer의 평가나 채택 결정과는
구별한다. 독립 AI 모의 심사 세 건과 공개 원자료를 함께 제공한다.

## 여섯 기준의 최종 판정

| 기준 | 판정 | 확인된 근거와 범위 |
| --- | --- | --- |
| 1. 새로움 | 통과 | 2024–2026 primary paper 12편 비교와 필수 고전 알고리즘·public source 조사. 살아남은 차이는 flat reciprocal-cardinality range metric의 label-conditioned overlap/fragmentation을 한 점 활성화마다 O(1)에 갱신한다는 것이다. Component tree 자체의 발명이 아니다. |
| 2. 주 결과 | 통과 | NAB/SMAP/SMD에서 public same-contract comparator와 강한 자체 compiled raster를 비교. 모든 collection의 adjusted 95% speedup 하한 >1. Prefix/raster/sweep/bucket 네 방법으로 기여를 분리했다. |
| 3. 일반성 | 통과, 범위 한정 | 73개 실제 recording, 584개 score profile, Apple/AMD 두 CPU 환경. 재사용된 panel과 SMD label 의존성, low-cardinality 패배, public timeout, 전체 consumer의 작은 이득을 공개했다. |
| 4. 재현 | 통과 | 한 명령의 새 Linux VUS+range 실행 완료. 새 score 배열과 전체 curve를 보존하고, 네 독립 auditor를 다시 실행해 저장된 보고서와 byte 단위 동일성을 확인했다. 수치 주 표의 재현이며 모든 후속 실험이나 PDF 자동 조판을 포함한다는 뜻은 아니다. |
| 5. 모의 심사 | 통과 | 서로의 판단을 보지 않은 독립 AI 심사 3건. 실제 공개 채택·탈락 review와 공식 PVLDB 기준으로 보정하고 최종 PDF·재현 receipt를 재검토했다. 공개 calibration은 인접 ICLR 사례이며 PVLDB 채택률 추정이 아니다. |
| 6. 학회 | 통과 | PVLDB Vol.20, Regular Research / Foundations and Algorithms. 초록 2026-11-25, 본문 2026-12-01, 각각 17:00 PT. |

이 표의 통과는 명시한 연구 주장과 증거 요구의 충족을 뜻한다. 범위를
모든 metric·모든 workload·보편적 최적성으로 넓히면 동일 판정을 적용할 수 없다.

## 이전 4점 평가에서 무엇을 바꿨나

이전 sparse-vus sampling 원고의 108개 subgroup 중 실질적 선택 오류 4개라는
관찰을 부풀리지 않았다. 새 연구 질문은 **기존 metric의 값을 바꾸지 않고
모든 threshold를 실용적으로 평가할 수 있는가**다. VUS 단독 후속 연구에서는
강한 compiled conventional control이 released scalar를 전 사례에서 이겼고,
실제 nine-metric consumer 전체 이득은 1.031배였다. 이 결과를 실패 범위로
유지한 채 다른 metric의 반복 연산으로 일반화했다.

새 결과는 Tatbul range precision/recall의 flat positional bias와 reciprocal
cardinality에서 **새로운 한 점이 활성화될 때 overlap와 fragmentation 통계를
상수 시간에 갱신하는 정확한 알고리즘**이다. 정렬 이후 전체 threshold 상태를
한 번의 sweep으로 계산한다. 관측된 모든 score threshold에서는
`O(n log n + n + H)`, 정렬된 H개 query에서는 query bucketing으로
`O(n log(H+1) + n + H)`다. 임의 query 순서는 query 정렬 비용이 추가된다.

Component tree, 1D endpoint 처리, 정렬과 offline bucketing은 선행기법이다.
특히 Najman–Couprie 2006과 Menotti–Najman–Araújo 2007을 직접 인용한다.
새로움의 범위는 label-conditioned metric aggregate 갱신이다. TimeSeAD가
이미 모든 관측 threshold를 검색한다는 사실도 인정한다. 전 세계 최초라는
포괄적 주장을 하지 않고, 조사한 primary literature와 source에서 살아남은
차이를 명시한다.

## 측정된 주 결과

동일한 NAB 20 / SMAP 17 / SMD 36개 실제 recording, 8개 고정 score 생성
절차를 사용했다. 기존 데이터를 재사용한 exploratory successor이며 held-out
dataset이라고 부르지 않는다. 모든 숫자는 Apple M1 Pro의 원래 고정 실행이다.
새 Linux 실행은 별도 행으로 보고하며 두 host를 합산하지 않는다.

| 비교 | NAB | SMAP | SMD |
| --- | ---: | ---: | ---: |
| 모든 관측 threshold, compiled raster / sweep | 27.80× | 21.44× | 128.08× |
| 3개 collection 조정 95% interval | [18.74, 41.94] | [8.57, 43.14] | [95.09, 154.61] |
| Grid100, compiled raster / bucket | 1.719× | 1.994× | 1.969× |
| 3개 collection 조정 95% interval | [1.625, 1.814] | [1.817, 2.252] | [1.884, 2.095] |

사전에 canonical로 선택한 새 Linux 실행의 결과는 다음과 같다. 두 환경의
숫자를 pooling하거나 더 빠른 실행만 선택하지 않았다.

| AMD EPYC 7763의 동일 비교 | NAB | SMAP | SMD |
| --- | ---: | ---: | ---: |
| 모든 관측 threshold, compiled raster / sweep | 29.35× | 27.76× | 163.60× |
| 3개 collection 조정 95% interval | [18.81, 46.08] | [11.63, 53.75] | [125.92, 193.02] |
| Grid100, compiled raster / bucket | 1.900× | 2.898× | 3.574× |
| 3개 collection 조정 95% interval | [1.616, 2.239] | [2.624, 3.260] | [3.412, 3.789] |

Baseline은 Python 재구현만이 아니다. 같은 compiler로 만든 fused raster는
각 threshold에서 배열을 한 번 읽고 상수 reducer workspace만 사용한다.
Prefix 재계산, fused raster, score-sorted sweep, query bucket의 네 방식으로
정렬 비용과 반복 scan 제거를 분리했다. Public TSB-AD와 TimeSeAD의 비교는
각 원래 query/alpha/precision 계약에서 별도로 수행했다.

최대 전체 curve 차이는 `2.998e-15`, 같은 계약의 방법 사이 winner-set 차이는
0개다. Grid100에서 전체 관측 threshold로 바꾸면 winner set이 24/73에서
달라지고, **15/73은 공통 winner가 없으며, 12/73은 regret >= .01**이다.
최대 regret은 .439/.150/.127이다. 이는 test-label metric의 oracle 선택
차이이며 detector accuracy 향상이나 label-free deployment 성과가 아니다.
Linux에서도 총 24/15/12개지만 SMD188과 SMD200이 change/nonoverlap 상태를
서로 바꾸고, SMD 최대 regret은 .07966이다. Raw observation/label은 동일하나
73개 전체 score matrix는 모두 host 간 다르며, 차이가 항상 작지도 않다.
따라서 동일 입력의 metric parity와 host에 따른 score 생성 차이를 구별한다.

## 재현 완료 근거

[Canonical Linux 실행 40062043152](https://github.com/mandu5/sparse-vus/actions/runs/40062043152)은
source commit `e2405e39ec23486a3d228240569b48785de32cb4`에서 **05:07:05 UTC**에
VUS primary/supplement와 range main/public/validation을 완료했다. GitHub
artifact의 SHA-256은 `cf9e0531b3ab00bc9f3f6d28113d62497f1ebe1c66b5eae2fe0fae915c898ec7`이다.
다운로드 후 실제 배열·source·원자료를 사용한 네 auditor의 재계산 결과가
각각 저장된 보고서와 동일하다. Validation receipt의 산술과 parent binding도
확인했다. 별도 auxiliary 실행은 별도 기록으로 유지했다.

[전체 scientific archive](../artifacts/pvldb-research-20261024/range-sweep/linux-combined/README.md)는
568개 파일, 147,330,993 bytes의 manifest와 생성된 NPZ 73개, canonical range
curve 438개, pinned comparator source를 포함한다. Fresh execution과
저장 기록 재검산은 별개이며, 둘 다 완료 기록을 보존했다.

```sh
python experiments/reproduce_range_sweep.py --include-vus --output /tmp/exact-metrics-replica
```

## 실패·대가·일반성

- Distinct score가 3–11개뿐인 SMAP534에서는 raster 0.838ms, sweep 2.012ms로
  sweep이 진다. Grid100 bucket은 73개 case median 모두에서 raster보다 빠르다.
- 가장 빠른 자체 grid100 bucket과 비교하면 exhaustive sweep은 기하평균
  2.19/2.14/3.01배 비싸다. 이는 다른 출력 계약 사이의 사후 기술 통계이며,
  exact coverage가 항상 최저 비용이라는 주장을 하지 않는다.
- SMD 36개 recording은 9개 동일 label block을 가진다. Equal-block 분석의
  distinct speedup은 112.34 [46.21,167.79]이며, 독립적인 36개 source라는
  해석은 하지 않는다.
- Public comparison은 collection별 길이가 가장 짧은 3개를 사전에 선택했다.
  TimeSeAD의 SMD187 두 호출은 60초 제한을 넘었다. 이를 scalar parity 성공이나
  실제 완료시간으로 바꾸지 않았다. 전체 73개 compiled 비교와 구분한다.
- 선택된 1,168개 cut의 값은 unchanged TSB-AD와 일치했다. 이 확인만으로
  나머지 threshold의 maximality를 독립 증명했다고 부르지 않는다.
- 100만 점 세 numerical stress case의 최대 차이는 `2.225e-12`로 사전
  tolerance `1e-9` 이내였다. 임의 길이의 formal rounding proof는 아니다.
- 이번 range 연구는 새로운 nine-metric 전체 가속을 측정하지 않았다.
  기존 전체 consumer 1.031배 결과를 그대로 유지한다.

## 5점과 6점의 사전 조건

[실험 전 정한 조건](superpowers/specs/2026-10-24-pvldb-evidence-design.md)을 유지한다.
이는 연구 투자 점수이며 학회 reviewer score나 채택확률이 아니다.

**5점:** 식별 가능한 기여, 3개 실제 full-precision collection, 동일 target의
성능비 신뢰구간 하한 >1, 가장 강한 eligible public baseline 대비 VUS
stored-profile workflow >=1.5배, validity 결함 해결, 사용자 여섯 근거 항목.
이전 VUS 연구에서 확보한 workflow 증거에 새 range 알고리즘의 실질적 기여가
추가되었다. 서로 다른 metric의 속도를 곱하거나 합산하지 않는다.

**6점:** 위 조건에 더해 released VUS 대비 각 collection >=1.25배 또는
동등하게 실질적인 새 일반화, external workflow >=2배, 두 CPU 환경,
독립 심사 3개에서 해결되지 않은 major scope/novelty/baseline/validity 반론 없음.
원래 SMD batch 1.207배는 여전히 실패다. 새 range 방법이 일반화 arm에
해당한다는 판단은 세 독립 reviewer가 각각 지지했다. 모두 자기 리뷰에 남은
major scope/novelty/baseline/validity blocker가 없다고 명시했다. 이는 baseline
결과를 고르거나 1.25 기준을 사후 낮춘 결론이 아니다. 두 CPU 환경과
external stored-profile workflow >=2배 조건도 실제 기록으로 충족했다.

| 독립 AI review | 최종 내부 추천 / surrogate 점수 | confidence | 가장 큰 한계 |
| --- | --- | --- | --- |
| [Independent](reviews/20261024/exact-metrics-independent-review.md) | Weak Accept / 7 | 4/5 | specialized 기여, 재사용 panel, 전체 consumer 1.031× |
| [Theory](reviews/20261024/exact-metrics-theory-review.md) | Weak Accept / 6 | 3/5 | metric-specific 일반화이며 더 넓은 conceptual 결과는 아니다 |
| [Blind](reviews/20261024/exact-metrics-blind-review.md) | Accept / 7 | 4/5 | specialized operator의 제한된 conceptual breadth와 application reach |

점수를 평균내어 채택확률로 바꾸지 않는다. 원래 VUS-only 7/5/5 심사와 그때의
6점 미달 판단도 수정하지 않았다. 새 결과에 대한 별도 세 심사가 판단 근거다.
Blind reviewer의 최초 Revise 6은 기록에 보존했고, 자신의 재현·표현·직접
선행연구 반영 조건이 닫힌 최종본에서 Accept 7로 변경했다. 나머지 두 명은
각각 7과 6을 유지했다. 모두 상대 reviewer의 점수를 보지 않고 판단했다.

더 강한 publication 추천 또는 투자 7점으로 높일 때의 쟁점은 좁은 operator의
conceptual/application significance다. 그 쟁점을 겨냥한 세 검증 경로는 다음과
같다. 이들은 현재 성과로 세지 않는다.

1. Flat specialization을 넘어 front/back/middle positional weighting까지
   공통 sufficient-statistic theorem으로 확장한다. 기존 Tatbul 설정의 범위를
   정확히 열거하고, 독립 oracle와 같은 compiled control로 각 경우를 검증한다.
2. 새 public workload에서 실제로 소비되는 전체 평가 호출의 시간을 측정한다.
   Affiliation이 남는 nine-metric 결과의 1.031배를 부분 metric 속도로 대체하지
   않는다. 가속하려는 단계가 전체 시간의 얼마인지 먼저 고정한다.
3. 원래 73개와 겹치지 않는 공개 score workload를 결과 확인 전에 선택하고
   low-cardinality, dense/fragmented labels, 긴 real recordings를 포함한다.
   추가 데이터 수보다 새로운 반례와 적용 범위가 reviewer 판단을 바꾸는지 본다.

## PVLDB와 TMLR

원래 exact-evaluator 전체의 목표는 **PVLDB**였다. TMLR은 별도
`certified_sampling` 원고의 sampling/certificate 결과를 위해 검토한 후보다.
이번 주력은 **PVLDB Volume 20, Regular Research / Foundations and Algorithms**다.
공식 call은 formal algorithm과 prototype evidence를 받으며, 기존 data-management
연구에 실제로 기초할 것을 요구한다. VUS의 PVLDB/VLDB Journal 연구에 직접
이어지는 exact analytical operator로 relevance를 설명한다.

TMLR은 정확하고 설득력 있는 증거와 독자의 관심을 기준으로 하며, novelty나
benchmark SOTA 자체를 필수로 요구하지 않는다. 이는 별도의 venue fit이며
사용자가 요구한 novelty 기준을 낮추기 위한 대체로 사용하지 않는다.

선택한 PVLDB cycle은 초록 **2026-11-25 17:00 PT**, 본문 **2026-12-01
17:00 PT**다. KST로 11월26일/12월2일 오전10시다. 개인 연구의 확정 저자
정보는 Youngmin Ko / Independent Researcher / rhdudals0505@naver.com이다.

공식 근거: [research call](https://www.vldb.org/2027/call-for-research-track.html),
[dates](https://www.vldb.org/2027/important-dates.html),
[TMLR criteria](https://jmlr.org/tmlr/acceptance-criteria.html).

## 산출물

- [현재 원고](../paper/exact_metrics_pvldb20261024.pdf)와 LaTeX source.
- [한 명령 재현](REPRODUCE_PVLDB_20261024.md).
- [새 range 원자료·protocol·audit](../artifacts/pvldb-research-20261024/range-sweep/).
- [독립 prior-art 조사](reviews/20261024/range-sweep-novelty-feasibility.md)와
  [후속 직접 선행연구 확인](../artifacts/pvldb-research-20261024/range-sweep-novelty/component-tree-followup.json).
- [기존 VUS-only 판정과 실패 기록](RESEARCH_DECISION_20261024.md).

투고 준비 자료와 실제 외부 심사 결정은 별도의 기록으로 관리한다.
