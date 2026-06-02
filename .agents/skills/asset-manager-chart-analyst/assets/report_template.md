# 종목 차트 분석 리포트

## 1. 최종 판단

- Recommendation: {{ recommendation }}
- Confidence: {{ confidence }}%
- 투자 관점: {{ investment_horizon }}
- 핵심 요약: {{ summary }}

## 2. 데이터 확인 결과

- OHLCV: {{ ohlcv_status }}
- RSI: {{ rsi_status }}
- MACD: {{ macd_status }}
- Bollinger Band: {{ bollinger_status }}
- 이동평균선: {{ moving_average_status }}
- 재무제표/실적: {{ fundamentals_status }}
- 뉴스: {{ news_status }}
- 데이터 기준일: {{ data_as_of }}
- 실패한 데이터 소스: {{ failed_sources }}

## 3. 주요 가격대

| 구분 | 가격 | 의미 |
|---|---:|---|
| 현재가 | {{ current_price }} | 현재 차트상 가격 |
| 진입 후보 | {{ entry_price }} | 진입 후보 구간 |
| 1차 지지선 | {{ support_1 }} | 단기 지지 구간 |
| 2차 지지선 | {{ support_2 }} | 중기 지지 구간 |
| 1차 저항선 | {{ resistance_1 }} | 단기 저항 구간 |
| 2차 저항선 | {{ resistance_2 }} | 강한 저항 구간 |
| 손절 기준 | {{ stop_loss }} | 리스크 관리 기준 |
| 1차 목표가 | {{ target_1 }} | 일부 익절 후보 |
| 2차 목표가 | {{ target_2 }} | 추가 상승 목표 |

## 4. 이미지 기반 분석과 데이터 기반 분석 비교

- 이미지상 판단: {{ image_based_view }}
- 실제 데이터상 판단: {{ data_based_view }}
- 일치하는 부분: {{ matching_points }}
- 다른 부분: {{ different_points }}
- 최종 해석: {{ final_interpretation }}

## 5. 기술적 분석

### 추세
{{ trend_analysis }}

### 이동평균선
{{ ma_analysis }}

### RSI
{{ rsi_analysis }}

### MACD
{{ macd_analysis }}

### Bollinger Band
{{ bollinger_analysis }}

### 자동 연속성/Bollinger 다음 봉 확률
{{ sequence_probability_analysis }}

### 거래량
{{ volume_analysis }}

### 캔들/패턴
{{ pattern_analysis }}

### 지지와 저항
{{ level_analysis }}

## 6. 생성된 차트 이미지

- 분석 차트 이미지 경로: {{ annotated_chart_path }}
- 시나리오 차트 이미지 경로: {{ forecast_chart_path }}
- 리포트 카드 이미지 경로: {{ report_card_path }}

## 7. 시나리오 해석

- 상승 시나리오: {{ bullish_scenario }}
- 중립 시나리오: {{ neutral_scenario }}
- 하락 시나리오: {{ bearish_scenario }}
- 무효화 조건: {{ invalidation_condition }}

## 8. 매매 전략

### 신규 진입자
{{ new_entry_strategy }}

### 보유자
{{ holder_strategy }}

### 추가매수
{{ add_strategy }}

### 손절/익절
{{ exit_strategy }}

## 9. 리스크 관리

- 손절 기준: {{ stop_loss_comment }}
- 손실 허용 범위: {{ max_loss_comment }}
- 추격매수 위험: {{ chasing_risk }}
- 변동성 위험: {{ volatility_risk }}
- 확인해야 할 조건: {{ confirmation_conditions }}

## 10. 운용사 비서 코멘트

{{ portfolio_comment }}

## 11. 한계

{{ limitations }}

## Disclaimer

이 분석은 투자 참고용이며, 최종 투자 판단과 책임은 사용자에게 있다.
