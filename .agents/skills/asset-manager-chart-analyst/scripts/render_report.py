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
    support_1: str
    support_2: str
    resistance_1: str
    resistance_2: str
    stop_loss: str
    target_1: str
    target_2: str
    trend_analysis: str
    ma_analysis: str
    volume_analysis: str
    pattern_analysis: str
    level_analysis: str
    new_entry_strategy: str
    holder_strategy: str
    add_strategy: str
    exit_strategy: str
    stop_loss_comment: str
    max_loss_comment: str
    chasing_risk: str
    volatility_risk: str
    confirmation_conditions: str
    portfolio_comment: str
    limitations: str


def render_report(report: ChartReport) -> str:
    return f"""# {report.ticker} 차트 분석 리포트

## 1. 최종 판단

- Recommendation: {report.recommendation}
- Confidence: {report.confidence}%
- 투자 관점: {report.investment_horizon}
- 핵심 요약: {report.summary}

## 2. 주요 가격대

| 구분 | 가격 | 의미 |
|---|---:|---|
| 현재가 | {report.current_price} | 현재 차트상 가격 |
| 1차 지지선 | {report.support_1} | 단기 지지 구간 |
| 2차 지지선 | {report.support_2} | 중기 지지 구간 |
| 1차 저항선 | {report.resistance_1} | 단기 저항 구간 |
| 2차 저항선 | {report.resistance_2} | 강한 저항 구간 |
| 손절 기준 | {report.stop_loss} | 리스크 관리 기준 |
| 1차 목표가 | {report.target_1} | 일부 익절 후보 |
| 2차 목표가 | {report.target_2} | 추가 상승 목표 |

## 3. 기술적 분석

### 추세
{report.trend_analysis}

### 이동평균선
{report.ma_analysis}

### 거래량
{report.volume_analysis}

### 캔들/패턴
{report.pattern_analysis}

### 지지와 저항
{report.level_analysis}

## 4. 매매 전략

### 신규 진입자
{report.new_entry_strategy}

### 보유자
{report.holder_strategy}

### 추가매수
{report.add_strategy}

### 손절/익절
{report.exit_strategy}

## 5. 리스크 관리

- 손절 기준: {report.stop_loss_comment}
- 손실 허용 범위: {report.max_loss_comment}
- 추격매수 위험: {report.chasing_risk}
- 변동성 위험: {report.volatility_risk}
- 확인해야 할 조건: {report.confirmation_conditions}

## 6. 운용사 비서 코멘트

{report.portfolio_comment}

## 7. 한계

{report.limitations}

## Disclaimer

이 분석은 투자 참고용이며, 최종 투자 판단과 책임은 사용자에게 있다.
"""
