# 최종 원고의 핵심 결과와 저자 검토 요약

대상 원고: **When Threshold Sampling Reverses VUS Rankings: Exact and Certified Evaluation of Anomaly Scores**. [12페이지 원고](../paper/certified_sampling.pdf), [실험 전체 결과](../artifacts/msad-sampling-20261023/README.md), [검토 지적 해소](certified_sampling_review_resolution_20261023.md).

이 연구의 기여는 **anomaly detector를 비교하는 VUS-PR 계산이 모델 선택을 바꾸는 구체적인 원인을 증명하고, 실제 공개 score에서 그 손실을 정수 기반으로 검증한 것**이다. 대상은 공식 구현의 `opt`, 250개 rank threshold, dynamic positive mass, right-step PR이라는 명시된 정의다.

## 확정한 결과

- 사전에 정한 128개 시계열·12개 공개 score configuration·16개 데이터군에서, 주평가 `L=30,H=250`의 선택 8건은 exhaustive VUS-PR 손실이 0.01 이상이다. 4개 데이터군에 걸쳐 발생하며, 최대 손실은 **[0.3985750301665, 0.3985750302756]** 안에 있다.
- 이 8건만 손실 하한이 기준을 넘는다는 데서 끝나지 않는다. 나머지 120건의 손실 상한도 0.01 미만임을 integer certificate로 확인했다. 전체 128건의 unique exhaustive winner 역시 보장했다.
- 새로 분석한 `post-saturation soft-mass inflation`은 recall이 이미 1이 된 뒤에도 buffer의 양의 mass가 precision을 높일 수 있다는 성질이다. sampling이 saturation 지점을 생략하면, 뒤의 높은 precision을 앞서 발생한 recall 증가에 잘못 배정한다. 실제 LOF 사례에서도 이 성분을 분해해 확인했다.
- 잘못 선택된 8개 시계열의 12개 모델 모두를 조사했다. 각 width의 첫 saturation threshold를 하나 추가하면 3건은 올바른 선택으로 돌아오고, 5건은 남는다. 따라서 전체 오류를 이 한 원인으로 설명하지 않는다.
- 공개 score는 모두 고유값이 101개 이하다. 250개 **rank**를 뽑아도 큰 tie를 반복 방문하며 희귀 score class를 놓칠 수 있다. 이 panel에서는 모든 score class를 평가하는 것이 간단하고 완전한 해결책이다.

## 수학적 보장의 의미

각 모델의 이상적인 real-arithmetic VUS-PR를 `[L_m,U_m]`에 넣는다. Square-root weight는 integer square root로 감싸고, 이후 계산은 방향을 정한 정수 나눗셈으로 처리한다. 한 모델의 `L_m`이 다른 모든 모델의 `U_j`보다 크면 그 모델의 우위를 보장한다.

Sampling이 선택한 tied winner 집합을 W라고 하면, best-case regret는 `max(E_j) - max(E_m for m in W)`다. 모든 모델의 lower endpoint 중 최댓값에서 W의 upper endpoint 최댓값을 뺀 값이 `1/100` 이상이면, W 안에서 가장 유리한 모델을 골라도 손실이 0.01 이상임을 보장한다. 실제 판정에는 반올림된 표시 숫자나 epsilon을 사용하지 않는다.

수학적 대상과 특정 floating-point 합산 결과는 구별한다. 원고의 `89/90` 사례는 이 차이를 보여준다. 반올림된 reference가 interval 밖으로 약 `7.63e-16` 나갔지만, 직접 도출한 정확한 값 `89/90`는 interval 안에 있었다. 이 차이는 실용적인 모델 선택 개선 수치가 아니다.

## 비용과 적용 범위

동일 compiled 계열에서 numerical exhaustive evaluator의 geometric speed ratio는 sampled evaluator 대비 **1.044배**, family bootstrap interval은 `[1.029,1.062]`였다. Whole public call에 입력 검증과 준비를 포함했고, JIT warmup과 입력 파일 decoding은 제외했다.

정수 certificate는 더 강한 보장의 비용을 지불한다. Numerical exhaustive 대비 geometric time ratio는 partial certificate **2.683배**, full certificate **3.290배**다. Partial certificate는 250 thresholds에서 63/128, 1,000에서 94/128 winner를 확인하지만, 잘못된 sampled 선택을 직접 판정하지 못했다. Full-grid certificate가 128/128을 해결했다.

과거 입력과 endpoint 한 점 차이로 겹친 시계열이 20개 있었다. 사전에 고정한 전체 128개는 그대로 보고했고, 나머지 108개의 기술적 분석에서는 4건·2개 데이터군이 기준 이상의 손실을 보였다. 완전히 새로운 physical recording이나 모든 anomaly detection 문제에서의 오류 빈도로 일반화하지 않는다. `8/128`의 family bootstrap interval도 population prevalence가 5% 이상임을 보장하지 않는다.

## 선행 연구와의 차이

Davis–Goadrich와 Keilwagen 등은 PR interpolation 및 weighted PR 문제를 이미 분석했다. PAULA는 monotonicity 가정과 미지의 label을 수집하는 설정에서 precision bounds를 제공했다. 본 연구는 **사용 가능한 전체 label/score, clipped dynamic recall, component existence, complete ties**를 대상으로 monotone precision을 가정하지 않는 enclosure와 machine-sound integer 구현을 제공한다. 광범위한 최초성 대신, 이 정확한 대상과 메커니즘으로 기여를 주장한다.

## 투고 판단

TMLR의 [공식 평가 기준](https://jmlr.org/tmlr/acceptance-criteria.html)은 주장을 뒷받침하는 정확하고 설득력 있는 증거와, 독자가 배울 수 있는 명료한 결과를 중심으로 한다. 이 원고는 **evaluation reliability** 연구로 제출할 근거를 갖췄다. 독립적인 내부 검토에서 지적된 공식 default 인용, PAULA 비교, 고정 artifact 접근 경로를 모두 수정했고, 현재 주장에 필요한 추가 대규모 실험은 요구되지 않았다.

현재 공개 PDF는 실명이 들어간 preprint다. TMLR의 실제 제출 파일은 [author guide](https://jmlr.org/tmlr/author-guide.html)에 따라 anonymous 원고와 supplement를 사용한다. 원고의 AI assistance 내용은 실제 수행 범위를 밝힌다. 저자는 원고의 기여·증명·실험 범위와 한계를 이해하고 자신의 설명으로 책임질 수 있어야 한다. 내부 agent 검토는 외부 학술 심사의 결과로 표시하지 않는다.
