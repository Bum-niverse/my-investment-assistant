# 종목 차트 분석 리포트

## 1. 최종 판단

- Recommendation: {{ recommendation }}
- Confidence: {{ confidence }}%
- 투자 관점: {{ investment_horizon }}
- 핵심 요약: {{ summary }}

## 2. 주요 가격대

| 구분 | 가격 | 의미 |
|---|---:|---|
| 현재가 | {{ current_price }} | 현재 차트상 가격 |
| 1차 지지선 | {{ support_1 }} | 단기 지지 구간 |
| 2차 지지선 | {{ support_2 }} | 중기 지지 구간 |
| 1차 저항선 | {{ resistance_1 }} | 단기 저항 구간 |
| 2차 저항선 | {{ resistance_2 }} | 강한 저항 구간 |
| 손절 기준 | {{ stop_loss }} | 리스크 관리 기준 |
| 1차 목표가 | {{ target_1 }} | 일부 익절 후보 |
| 2차 목표가 | {{ target_2 }} | 추가 상승 목표 |

## 3. 기술적 분석

### 추세
{{ trend_analysis }}

### 이동평균선
{{ ma_analysis }}

### 거래량
{{ volume_analysis }}

### 캔들/패턴
{{ pattern_analysis }}

### 지지와 저항
{{ level_analysis }}

## 4. 매매 전략

### 신규 진입자
{{ new_entry_strategy }}

### 보유자
{{ holder_strategy }}

### 추가매수
{{ add_strategy }}

### 손절/익절
{{ exit_strategy }}

## 5. 리스크 관리

- 손절 기준: {{ stop_loss_comment }}
- 손실 허용 범위: {{ max_loss_comment }}
- 추격매수 위험: {{ chasing_risk }}
- 변동성 위험: {{ volatility_risk }}
- 확인해야 할 조건: {{ confirmation_conditions }}

## 6. 운용사 비서 코멘트

{{ portfolio_comment }}

## 7. 한계

{{ limitations }}

## Disclaimer

이 분석은 투자 참고용이며, 최종 투자 판단과 책임은 사용자에게 있다.
