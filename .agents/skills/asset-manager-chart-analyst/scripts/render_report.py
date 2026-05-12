from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChartReport:
    ticker: str
    recommendation: str
    confidence: int
    investment_horizon: str
    summary: str
    current_price: str
    entry_price: str
    support_1: str
    support_2: str
    resistance_1: str
    resistance_2: str
    stop_loss: str
    target_1: str
    target_2: str
    ohlcv_status: str = "확인 실패"
    rsi_status: str = "확인 실패"
    macd_status: str = "확인 실패"
    bollinger_status: str = "확인 실패"
    moving_average_status: str = "확인 실패"
    fundamentals_status: str = "확인 실패"
    news_status: str = "확인 실패"
    data_as_of: str = "확인 실패"
    failed_sources: str = "없음"
    image_based_view: str = "확인 실패"
    data_based_view: str = "확인 실패"
    matching_points: str = "확인 실패"
    different_points: str = "확인 실패"
    final_interpretation: str = "확인 실패"
    trend_analysis: str = "확인 실패"
    ma_analysis: str = "확인 실패"
    rsi_analysis: str = "확인 실패"
    macd_analysis: str = "확인 실패"
    bollinger_analysis: str = "확인 실패"
    volume_analysis: str = "확인 실패"
    pattern_analysis: str = "확인 실패"
    level_analysis: str = "확인 실패"
    annotated_chart_path: str = "생성 실패"
    forecast_chart_path: str = "생성 실패"
    report_card_path: str = "생성 실패"
    bullish_scenario: str = "확인 실패"
    neutral_scenario: str = "확인 실패"
    bearish_scenario: str = "확인 실패"
    invalidation_condition: str = "확인 실패"
    new_entry_strategy: str = "확인 실패"
    holder_strategy: str = "확인 실패"
    add_strategy: str = "확인 실패"
    exit_strategy: str = "확인 실패"
    stop_loss_comment: str = "확인 실패"
    max_loss_comment: str = "확인 실패"
    chasing_risk: str = "확인 실패"
    volatility_risk: str = "확인 실패"
    confirmation_conditions: str = "확인 실패"
    portfolio_comment: str = "확인 실패"
    limitations: str = "확인 실패"


def render_report(report: ChartReport) -> str:
    return f"""# 종목 차트 분석 리포트

## 1. 최종 판단

- Recommendation: {report.recommendation}
- Confidence: {report.confidence}%
- 투자 관점: {report.investment_horizon}
- 핵심 요약: {report.ticker} - {report.summary}

## 2. 데이터 확인 결과

- OHLCV: {report.ohlcv_status}
- RSI: {report.rsi_status}
- MACD: {report.macd_status}
- Bollinger Band: {report.bollinger_status}
- 이동평균선: {report.moving_average_status}
- 재무제표/실적: {report.fundamentals_status}
- 뉴스: {report.news_status}
- 데이터 기준일: {report.data_as_of}
- 실패한 데이터 소스: {report.failed_sources}

## 3. 주요 가격대

| 구분 | 가격 | 의미 |
|---|---:|---|
| 현재가 | {report.current_price} | 현재 차트상 가격 |
| 진입 후보 | {report.entry_price} | 진입 후보 구간 |
| 1차 지지선 | {report.support_1} | 단기 지지 구간 |
| 2차 지지선 | {report.support_2} | 중기 지지 구간 |
| 1차 저항선 | {report.resistance_1} | 단기 저항 구간 |
| 2차 저항선 | {report.resistance_2} | 강한 저항 구간 |
| 손절 기준 | {report.stop_loss} | 리스크 관리 기준 |
| 1차 목표가 | {report.target_1} | 일부 익절 후보 |
| 2차 목표가 | {report.target_2} | 추가 상승 목표 |

## 4. 이미지 기반 분석과 데이터 기반 분석 비교

- 이미지상 판단: {report.image_based_view}
- 실제 데이터상 판단: {report.data_based_view}
- 일치하는 부분: {report.matching_points}
- 다른 부분: {report.different_points}
- 최종 해석: {report.final_interpretation}

## 5. 기술적 분석

### 추세
{report.trend_analysis}

### 이동평균선
{report.ma_analysis}

### RSI
{report.rsi_analysis}

### MACD
{report.macd_analysis}

### Bollinger Band
{report.bollinger_analysis}

### 거래량
{report.volume_analysis}

### 캔들/패턴
{report.pattern_analysis}

### 지지와 저항
{report.level_analysis}

## 6. 생성된 차트 이미지

- 분석 차트 이미지 경로: {report.annotated_chart_path}
- 시나리오 차트 이미지 경로: {report.forecast_chart_path}
- 리포트 카드 이미지 경로: {report.report_card_path}

## 7. 시나리오 해석

- 상승 시나리오: {report.bullish_scenario}
- 중립 시나리오: {report.neutral_scenario}
- 하락 시나리오: {report.bearish_scenario}
- 무효화 조건: {report.invalidation_condition}

## 8. 매매 전략

### 신규 진입자
{report.new_entry_strategy}

### 보유자
{report.holder_strategy}

### 추가매수
{report.add_strategy}

### 손절/익절
{report.exit_strategy}

## 9. 리스크 관리

- 손절 기준: {report.stop_loss_comment}
- 손실 허용 범위: {report.max_loss_comment}
- 추격매수 위험: {report.chasing_risk}
- 변동성 위험: {report.volatility_risk}
- 확인해야 할 조건: {report.confirmation_conditions}

## 10. 운용사 비서 코멘트

{report.portfolio_comment}

## 11. 한계

{report.limitations}

## Disclaimer

이 분석은 투자 참고용이며, 최종 투자 판단과 책임은 사용자에게 있다.
"""
