from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any


def _format_price(value: Any) -> str:
    if value is None:
        return "확인 실패"
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def _format_percent(value: Any) -> str:
    if value is None:
        return "확인 실패"
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return str(value)


def _parse_price(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", "").replace("원", "").strip()
    if not text or "확인 실패" in text:
        return None
    try:
        return float(text.split()[0])
    except (TypeError, ValueError, IndexError):
        return None


def _format_signed_percent(value: float | None) -> str:
    if value is None:
        return "데이터 없음"
    return f"{value:+.2f}%"


def _calculate_card_metrics(current_price: str, entry_price: str, stop_loss: str, target_1: str) -> dict[str, str]:
    entry = _parse_price(entry_price)
    stop = _parse_price(stop_loss)
    target = _parse_price(target_1)
    current = _parse_price(current_price)
    base = entry or current
    if base is None:
        return {"risk": "데이터 없음", "reward": "데이터 없음", "risk_reward": "데이터 없음"}

    risk_pct = ((stop - base) / base * 100) if stop is not None else None
    reward_pct = ((target - base) / base * 100) if target is not None else None
    risk_abs = abs(risk_pct) if risk_pct is not None else None
    reward_abs = abs(reward_pct) if reward_pct is not None else None
    if risk_abs and reward_abs and risk_abs > 0:
        risk_reward = f"1:{reward_abs / risk_abs:.2f}"
    else:
        risk_reward = "데이터 없음"
    return {
        "risk": _format_signed_percent(risk_pct),
        "reward": _format_signed_percent(reward_pct),
        "risk_reward": risk_reward,
    }


def _judge_rsi(value: float | None) -> str:
    if value is None:
        return "확인 실패"
    if value >= 70:
        return "과열권"
    if value <= 30:
        return "침체권"
    if value >= 55:
        return "상승 우위"
    if value <= 45:
        return "약세 우위"
    return "중립"


def _judge_macd(macd: dict[str, float]) -> str:
    if not macd:
        return "확인 실패"
    histogram = macd.get("Histogram")
    macd_value = macd.get("MACD")
    signal = macd.get("Signal")
    if histogram is None or macd_value is None or signal is None:
        return "확인 실패"
    if histogram > 0 and macd_value > signal:
        return "상승 모멘텀 우위"
    if histogram < 0 and macd_value < signal:
        return "하락 모멘텀 우위"
    return "중립 또는 전환 구간"


def _judge_bollinger(latest_close: float | None, bands: dict[str, float]) -> str:
    if latest_close is None or not bands:
        return "확인 실패"
    upper = bands.get("BB_Upper")
    middle = bands.get("BB_Middle")
    lower = bands.get("BB_Lower")
    if upper is None or middle is None or lower is None:
        return "확인 실패"
    if latest_close >= upper:
        return "상단 밴드 근접/돌파, 단기 과열 가능"
    if latest_close <= lower:
        return "하단 밴드 근접, 단기 낙폭 과대 가능"
    if latest_close >= middle:
        return "중심선 위, 추세 양호"
    return "중심선 아래, 추세 확인 필요"


def _judge_ma_alignment(moving_averages: dict[str, float]) -> str:
    ma5 = moving_averages.get("MA_5")
    ma20 = moving_averages.get("MA_20")
    ma60 = moving_averages.get("MA_60")
    ma120 = moving_averages.get("MA_120")
    if None in {ma5, ma20, ma60, ma120}:
        return "확인 실패"
    if ma5 >= ma20 >= ma60 >= ma120:
        return "정배열"
    if ma5 <= ma20 <= ma60 <= ma120:
        return "역배열"
    return "혼조"


def _build_price_levels(ohlcv: dict[str, Any], indicators: dict[str, Any]) -> dict[str, str]:
    current = indicators.get("latest_close") or ohlcv.get("latest_close")
    recent_high = ohlcv.get("recent_high_60")
    recent_low = ohlcv.get("recent_low_60")
    ma = indicators.get("moving_averages", {})
    ma20 = ma.get("MA_20")
    ma60 = ma.get("MA_60")
    bands = indicators.get("bollinger_bands", {})

    support_1 = ma20 or recent_low
    support_2 = ma60 or recent_low
    resistance_1 = recent_high
    resistance_2 = bands.get("BB_Upper") or recent_high
    stop_loss = support_1 * 0.97 if isinstance(support_1, (int, float)) else None
    target_1 = resistance_1
    target_2 = resistance_2

    return {
        "current_price": _format_price(current),
        "support_1": _format_price(support_1),
        "support_2": _format_price(support_2),
        "resistance_1": _format_price(resistance_1),
        "resistance_2": _format_price(resistance_2),
        "entry": f"{_format_price(support_1)} 부근 지지 확인 후" if support_1 else "확인 실패",
        "stop_loss": _format_price(stop_loss),
        "target_1": _format_price(target_1),
        "target_2": _format_price(target_2),
        "current_price_meaning": "실제 OHLCV 기준 최근 종가",
        "entry_meaning": "20일선 또는 단기 지지 후보 확인 후 분할 진입",
        "support_1_meaning": "20일선 또는 단기 지지 후보" if ma20 else "최근 저점 기반 지지 후보",
        "support_2_meaning": "60일선 또는 중기 지지 후보" if ma60 else "최근 저점 기반 지지 후보",
        "resistance_1_meaning": "최근 고점 기반 저항 후보",
        "resistance_2_meaning": "Bollinger Band 상단 또는 최근 고점 기반 저항 후보",
        "stop_loss_meaning": "1차 지지선 이탈 기준",
        "target_1_meaning": "최근 고점 기반 저항 후보",
        "target_2_meaning": "Bollinger Band 상단 또는 최근 고점 기반 저항 후보",
    }


def _format_detected_levels(levels: dict[str, Any] | None, fallback: dict[str, str]) -> dict[str, str]:
    if not levels:
        return fallback
    return {
        "current_price": _format_price(levels.get("current_price")),
        "support_1": _format_price(levels.get("support_1")),
        "support_2": _format_price(levels.get("support_2")),
        "resistance_1": _format_price(levels.get("resistance_1")),
        "resistance_2": _format_price(levels.get("resistance_2")),
        "entry": f"{_format_price(levels.get('entry_price'))} 부근 지지 확인 후",
        "stop_loss": _format_price(levels.get("stop_loss")),
        "target_1": _format_price(levels.get("target_1")),
        "target_2": _format_price(levels.get("target_2")),
        "current_price_meaning": "실제 OHLCV 기준 최근 종가",
        "entry_meaning": str(levels.get("entry_meaning") or "지지선 확인 후 분할 진입 후보"),
        "support_1_meaning": str(levels.get("support_1_meaning") or "지지 후보"),
        "support_2_meaning": str(levels.get("support_2_meaning") or "지지 후보"),
        "resistance_1_meaning": str(levels.get("resistance_1_meaning") or "저항 후보"),
        "resistance_2_meaning": str(levels.get("resistance_2_meaning") or "저항 후보"),
        "stop_loss_meaning": str(levels.get("stop_loss_meaning") or "1차 지지선 이탈 기준"),
        "target_1_meaning": str(levels.get("target_1_meaning") or "1차 저항 기반 일부 익절 후보"),
        "target_2_meaning": str(levels.get("target_2_meaning") or "2차 저항 기반 추가 상승 목표"),
    }


def _safe_filename(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())
    return safe or "stock"


def _generate_chart_images(
    df: Any,
    levels: dict[str, Any] | None,
    stock_label: str,
    output_dir: str | None,
    summary: str,
) -> tuple[dict[str, str], list[str]]:
    if not levels:
        return {"analysis_chart": "생성 실패", "forecast_chart": "생성 실패"}, ["이미지 생성 실패 이유: 가격대 탐지 결과가 없습니다"]

    failures: list[str] = []
    output_root = Path(output_dir or "analysis_outputs").resolve()
    safe_label = _safe_filename(stock_label)
    analysis_path = output_root / f"{safe_label}_분석_차트.png"
    forecast_path = output_root / f"{safe_label}_향후_주가_시나리오_전망.png"

    paths = {"analysis_chart": "생성 실패", "forecast_chart": "생성 실패"}

    try:
        from render_annotated_chart import render_annotated_chart

        paths["analysis_chart"] = render_annotated_chart(
            df=df,
            levels=levels,
            output_path=analysis_path,
            title=f"{stock_label} 분석 차트",
            summary=summary,
        )
    except Exception as exc:
        failures.append(f"이미지 생성 실패 이유: 분석 차트 생성 실패 - {exc}")

    try:
        from render_forecast_chart import render_forecast_chart

        paths["forecast_chart"] = render_forecast_chart(
            df=df,
            levels=levels,
            output_path=forecast_path,
            title="향후 주가 시나리오 전망",
        )
    except Exception as exc:
        failures.append(f"이미지 생성 실패 이유: 시나리오 차트 생성 실패 - {exc}")

    return paths, failures


def _generate_report_card_image(
    card_data: dict[str, Any],
    output_dir: str | None,
) -> tuple[str, str | None]:
    output_root = Path(output_dir or "outputs").resolve()
    report_card_path = output_root / "report_card.png"
    try:
        from render_report_card import render_report_card

        return render_report_card(card_data, report_card_path), None
    except Exception as exc:
        return "생성 실패", f"리포트 카드 이미지 생성 실패: {exc}"


def build_report(
    ticker: str,
    stock_name: str | None,
    horizon: str,
    image_notes: str | None = None,
    output_dir: str | None = None,
) -> str:
    try:
        from fetch_fundamentals import fetch_fundamentals
        from fetch_market_data import fetch_ohlcv, summarize_ohlcv
        from fetch_news import fetch_news
        from technical_indicators import build_indicator_summary
    except Exception as exc:
        return build_dependency_failure_report(ticker, stock_name, horizon, image_notes, output_dir, exc)

    market_result = fetch_ohlcv(ticker)
    ohlcv_summary = summarize_ohlcv(market_result)
    failures = list(market_result.failures)

    indicators: dict[str, Any] = {}
    indicator_error = None
    if market_result.ok:
        try:
            indicators = build_indicator_summary(market_result.data)
        except Exception as exc:
            indicator_error = f"기술지표 계산 실패: {exc}"
            failures.append(indicator_error)
    else:
        failures.append("기술지표 계산 생략: OHLCV 데이터 없음")

    fundamentals = fetch_fundamentals(ticker)
    failures.extend(fundamentals.failures)

    news = fetch_news(stock_name or ticker, ticker=ticker)
    failures.extend(news.failures)

    detected_levels: dict[str, Any] | None = None
    if market_result.ok:
        try:
            from detect_levels import detect_price_levels

            detected_levels = detect_price_levels(market_result.data).to_dict()
        except Exception as exc:
            failures.append(f"가격대 자동 탐지 실패: {exc}")

    fallback_price_levels = _build_price_levels(ohlcv_summary, indicators) if market_result.ok else {
        "current_price": "확인 실패",
        "support_1": "확인 실패",
        "support_2": "확인 실패",
        "resistance_1": "확인 실패",
        "resistance_2": "확인 실패",
        "entry": "확인 실패",
        "stop_loss": "확인 실패",
        "target_1": "확인 실패",
        "target_2": "확인 실패",
        "current_price_meaning": "OHLCV 확인 실패",
        "entry_meaning": "OHLCV 확인 실패",
        "support_1_meaning": "OHLCV 확인 실패",
        "support_2_meaning": "OHLCV 확인 실패",
        "resistance_1_meaning": "OHLCV 확인 실패",
        "resistance_2_meaning": "OHLCV 확인 실패",
        "stop_loss_meaning": "OHLCV 확인 실패",
        "target_1_meaning": "OHLCV 확인 실패",
        "target_2_meaning": "OHLCV 확인 실패",
    }
    price_levels = _format_detected_levels(detected_levels, fallback_price_levels)

    latest_rsi = indicators.get("rsi_14")
    macd = indicators.get("macd", {})
    bands = indicators.get("bollinger_bands", {})
    latest_close = indicators.get("latest_close")

    rsi_judgment = _judge_rsi(latest_rsi)
    macd_judgment = _judge_macd(macd)
    band_judgment = _judge_bollinger(latest_close, bands)
    moving_averages = indicators.get("moving_averages", {})
    ma_alignment = _judge_ma_alignment(moving_averages) if isinstance(moving_averages, dict) else "확인 실패"

    data_based_judgment = "데이터 부족"
    if market_result.ok:
        positive_count = sum(
            [
                rsi_judgment in {"상승 우위", "중립"},
                macd_judgment == "상승 모멘텀 우위",
                band_judgment in {"중심선 위, 추세 양호", "상단 밴드 근접/돌파, 단기 과열 가능"},
            ]
        )
        data_based_judgment = "상승 추세 우위" if positive_count >= 2 else "확인 필요 또는 중립"

    stock_label = stock_name or ticker
    data_date = indicators.get("latest_date") or ohlcv_summary.get("end_date") or "확인 실패"

    news_lines = []
    for article in news.articles[:5]:
        title = str(article.get("title") or "").strip()
        if not title:
            continue
        source = str(article.get("source") or article.get("publisher") or "").strip()
        published_at = str(article.get("published_at") or "").strip()
        meta = ", ".join(value for value in [source, published_at] if value)
        news_lines.append(f"- {title} ({meta})" if meta else f"- {title}")
    news_text = "\n".join(news_lines) if news_lines else "- 뉴스 확인 실패: 유효한 뉴스 제목을 파싱하지 못함"

    fundamentals_text = _format_fundamentals(fundamentals.data) if fundamentals.ok else "확인 실패"
    image_text = image_notes or "차트 이미지가 제공되지 않았거나 별도 이미지 메모가 없음"

    chart_summary = (
        f"판단: {data_based_judgment}\n"
        f"RSI: {_format_percent(latest_rsi) if latest_rsi is not None else '확인 실패'}\n"
        f"MACD: {macd_judgment}\n"
        f"전략: 지지 확인 후 분할 접근"
    )
    chart_paths = {"analysis_chart": "생성 실패", "forecast_chart": "생성 실패", "report_card": "생성 실패"}
    chart_failures: list[str] = []
    if market_result.ok:
        chart_paths, chart_failures = _generate_chart_images(
            df=market_result.data,
            levels=detected_levels,
            stock_label=stock_label,
            output_dir=output_dir,
            summary=chart_summary,
        )
    else:
        chart_failures.append("이미지 생성 실패 이유: OHLCV 데이터가 없어 차트 이미지를 생성할 수 없습니다")
    report_card_data = {
        **_calculate_card_metrics(price_levels["current_price"], price_levels["entry"], price_levels["stop_loss"], price_levels["target_1"]),
        "stock_name": stock_label,
        "ticker": ticker,
        "data_as_of": data_date,
        "recommendation": "WATCH",
        "confidence": "60%",
        "current_price": price_levels["current_price"],
        "entry_price": price_levels["entry"],
        "stop_loss": price_levels["stop_loss"],
        "target_1": price_levels["target_1"],
        "target_2": price_levels["target_2"],
        "rsi": f"{_format_percent(latest_rsi)} / {rsi_judgment}" if latest_rsi is not None else "확인 실패",
        "macd": macd_judgment,
        "bollinger": band_judgment,
        "ma_status": ma_alignment,
        "summary": f"{stock_label}는 현재 `{data_based_judgment}`로 판단됩니다. 데이터가 부족하거나 일부 소스가 실패한 경우에는 보수적으로 접근해야 합니다.",
        "trend_analysis": f"{data_based_judgment}. 이동평균선과 가격 위치를 함께 확인해 추세 유지 여부를 판단합니다.",
        "pattern_analysis": image_text if image_notes else "이미지 기반 패턴은 제공된 차트 메모가 있을 때만 확정합니다. 현재는 지지/저항과 지표 중심으로 판단합니다.",
        "indicator_analysis": f"RSI: {rsi_judgment}, MACD: {macd_judgment}, Bollinger: {band_judgment}, MA 배열: {ma_alignment}",
        "new_entry_strategy": f"{price_levels['entry']} 전략을 우선하고 추격매수는 피합니다.",
        "holder_strategy": "1차 목표가에서 일부 익절을 검토하고 손절 기준 이탈 시 스윙 관점 훼손으로 봅니다.",
        "risk_management": "손절 기준, 변동성, 뉴스/실적 리스크를 확인하고 전체 자산 대비 비중을 제한합니다.",
        "trade_strategy": f"신규 진입자는 {price_levels['entry']} 구간에서 지지 확인 후 분할 접근합니다. 손절 기준은 {price_levels['stop_loss']}, 1차 목표가는 {price_levels['target_1']}로 두고, 지표 과열이나 주요 지지선 이탈 시 비중을 줄입니다.",
    }
    report_card_path, report_card_error = _generate_report_card_image(report_card_data, output_dir)
    chart_paths["report_card"] = report_card_path
    if report_card_error:
        chart_failures.append(report_card_error)
    failures.extend(chart_failures)
    failed_sources = "\n".join(f"- {failure}" for failure in failures) if failures else "- 없음"

    return f"""# 종목 차트 분석 리포트

## 1. 최종 판단

- Recommendation: WATCH
- Confidence: 60%
- 투자 관점: {horizon}
- 핵심 요약: {stock_label}의 실제 데이터 확인 결과는 `{data_based_judgment}`입니다. 다만 데이터 소스 실패가 있을 수 있으므로, 확인된 데이터와 이미지 기반 판단을 분리해서 해석해야 합니다.

## 2. 데이터 확인 결과

- OHLCV: {"확인 완료" if market_result.ok else "확인 실패"} / 출처: {market_result.source or "없음"} / 행 수: {ohlcv_summary.get("rows", 0)}
- RSI: {_format_percent(latest_rsi) if latest_rsi is not None else "확인 실패"} / 판단: {rsi_judgment}
- MACD: {macd_judgment} / 값: {macd if macd else "확인 실패"}
- Bollinger Band: {band_judgment} / 값: {bands if bands else "확인 실패"}
- 이동평균선: {indicators.get("moving_averages", "확인 실패")}
- 재무제표/실적: {fundamentals_text}
- 뉴스:
{news_text}
- 데이터 기준일: {data_date}
- 데이터 조회 시각: {market_result.timestamp}
- 실패한 데이터 소스:
{failed_sources}

## 3. 주요 가격대

| 구분 | 가격 | 의미 |
|---|---:|---|
| 현재가 | {price_levels["current_price"]} | {price_levels["current_price_meaning"]} |
| 진입 후보 | {price_levels["entry"]} | {price_levels["entry_meaning"]} |
| 1차 지지선 | {price_levels["support_1"]} | {price_levels["support_1_meaning"]} |
| 2차 지지선 | {price_levels["support_2"]} | {price_levels["support_2_meaning"]} |
| 1차 저항선 | {price_levels["resistance_1"]} | {price_levels["resistance_1_meaning"]} |
| 2차 저항선 | {price_levels["resistance_2"]} | {price_levels["resistance_2_meaning"]} |
| 손절 기준 | {price_levels["stop_loss"]} | {price_levels["stop_loss_meaning"]} |
| 1차 목표가 | {price_levels["target_1"]} | {price_levels["target_1_meaning"]} |
| 2차 목표가 | {price_levels["target_2"]} | {price_levels["target_2_meaning"]} |

## 4. 이미지 기반 분석과 데이터 기반 분석 비교

- 이미지상 판단: {image_text}
- 실제 데이터상 판단: {data_based_judgment}
- 일치하는 부분: 실제 데이터와 이미지가 모두 상승 추세 또는 지지 확인을 보여줄 때만 매수 판단의 신뢰도가 올라갑니다.
- 다른 부분: 이미지상 강해 보여도 RSI 과열, MACD 약화, 볼린저 상단 과열이면 추격매수 위험을 우선합니다.
- 최종 해석: 데이터와 이미지가 충돌하면 더 보수적인 판단을 적용하고, 신규 진입은 지지선 확인 후 분할 접근합니다.

## 5. 기술적 분석

### 추세
{data_based_judgment}

### 이동평균선
{indicators.get("moving_averages", "확인 실패")}

### RSI
{rsi_judgment}

### MACD
{macd_judgment}

### Bollinger Band
{band_judgment}

### 거래량
최근 거래량: {_format_price(ohlcv_summary.get("latest_volume")) if market_result.ok else "확인 실패"}

### 캔들/패턴
이미지 기반 패턴은 별도 이미지 메모가 있을 때만 확정합니다. 실제 데이터만으로는 지지/저항과 추세 중심으로 판단합니다.

### 지지와 저항
{detected_levels.get("reason") if detected_levels else "확인 실패"}

## 6. 생성된 차트 이미지

- 분석 차트 이미지 경로: {chart_paths["analysis_chart"]}
- 시나리오 차트 이미지 경로: {chart_paths["forecast_chart"]}
- 리포트 카드 이미지 경로: {chart_paths["report_card"]}

## 7. 시나리오 해석

- 상승 시나리오: 1차 저항선 돌파 후 거래량이 동반되면 {price_levels["target_1"]} 부근까지 상승 시나리오를 봅니다.
- 중립 시나리오: {price_levels["support_1"]} 부근을 지키면서 박스권 흐름을 유지하는 경우입니다.
- 하락 시나리오: {price_levels["support_1"]} 이탈 후 회복하지 못하면 {price_levels["stop_loss"]} 손절 기준까지 열어둡니다.
- 무효화 조건: 손절가 이탈, 거래량 동반 장대음봉, 주요 이동평균선 이탈이 동시에 발생하는 경우입니다.

## 8. 매매 전략

### 신규 진입자
현재 위치에서 무리한 추격매수보다 `{price_levels["entry"]}` 전략을 우선합니다. 저항선 돌파 시에는 거래량 증가와 다음 날 지지 여부를 확인합니다.

### 보유자
보유자는 1차 목표가에서 일부 익절을 검토하고, 손절가 이탈 시 스윙 관점 훼손으로 봅니다.

### 추가매수
추가매수는 1차 지지선에서 반등하거나 1차 저항선 돌파 후 눌림이 확인될 때만 검토합니다.

### 손절/익절
- 손절가: {price_levels["stop_loss"]}
- 1차 목표가: {price_levels["target_1"]}
- 2차 목표가: {price_levels["target_2"]}

## 9. 리스크 관리

- 손절 기준: 1차 지지선 이탈 또는 손절가 이탈
- 손실 허용 범위: 총자산 기준 사전에 정한 손실 한도 안에서만 진입
- 추격매수 위험: RSI 과열 또는 볼린저 상단 근접 시 WATCH 우선
- 변동성 위험: 변동성이 높을수록 분할 진입과 작은 비중이 적절
- 확인해야 할 조건: 거래량 동반 돌파, 지지선 재확인, 뉴스/실적 리스크

## 10. 운용사 비서 코멘트

운용 관점에서는 수익 가능성보다 먼저 손절 기준과 포지션 크기를 확정해야 합니다. 데이터 확인이 완전하지 않거나 일부 소스가 실패한 경우에는 확신도를 낮추고, 이미지 기반 판단만으로 큰 비중을 싣지 않는 것이 적절합니다.

## 11. 한계

데이터 제공처의 지연, 누락, 네트워크 실패, API 제한이 있을 수 있습니다. 확인 실패 항목은 투자 판단에 반영하지 않았으며, 수치를 임의로 생성하지 않았습니다.

## Disclaimer

이 분석은 투자 참고용이며 수익을 보장하지 않습니다. 최종 투자 판단과 책임은 사용자에게 있습니다. 레버리지, 신용, 미수, 몰빵 투자는 권장하지 않습니다.
"""


def build_dependency_failure_report(
    ticker: str,
    stock_name: str | None,
    horizon: str,
    image_notes: str | None,
    output_dir: str | None,
    error: Exception,
) -> str:
    stock_label = stock_name or ticker
    image_text = image_notes or "차트 이미지가 제공되지 않았거나 별도 이미지 메모가 없음"
    report_card_path, report_card_error = _generate_report_card_image(
        {
            "stock_name": stock_label,
            "ticker": ticker,
            "data_as_of": "확인 실패",
            "recommendation": "WATCH",
            "confidence": "40%",
            "current_price": "확인 실패",
            "entry_price": "확인 실패",
            "stop_loss": "확인 실패",
            "target_1": "확인 실패",
            "target_2": "확인 실패",
            "rsi": "확인 실패",
            "macd": "확인 실패",
            "bollinger": "확인 실패",
            "ma_status": "확인 실패",
            "new_entry_strategy": "데이터 확인 전에는 신규 진입을 보류합니다.",
            "holder_strategy": "보유자는 실제 OHLCV 확인 후 손절 기준을 재설정합니다.",
            "risk_management": "데이터 의존성 또는 네트워크 문제가 해결되기 전에는 비중을 확대하지 않습니다.",
            "summary": "실제 데이터 확인에 실패해 이미지 또는 사용자 제공 정보만 참고할 수 있습니다.",
            "trend_analysis": "확인 실패",
            "pattern_analysis": image_text,
            "indicator_analysis": "RSI, MACD, Bollinger Band, MA 배열 모두 확인 실패",
            "trade_strategy": "데이터 확인 전에는 신규 진입을 보류하고, 기존 보유자는 손절 기준을 재확인해야 합니다.",
            "risk": "데이터 없음",
            "reward": "데이터 없음",
            "risk_reward": "데이터 없음",
        },
        output_dir,
    )
    report_card_failure_line = f"- 리포트 카드 이미지 생성 실패 이유: {report_card_error}\n" if report_card_error else ""

    return f"""# 종목 차트 분석 리포트

## 1. 최종 판단

- Recommendation: WATCH
- Confidence: 40%
- 투자 관점: {horizon}
- 핵심 요약: {stock_label} 데이터 분석 의존성 로딩에 실패해 실제 데이터 기반 분석은 수행하지 못했습니다. 확인된 정보만 사용해야 합니다.

## 2. 데이터 확인 결과

- OHLCV: 확인 실패
- RSI: 확인 실패
- MACD: 확인 실패
- Bollinger Band: 확인 실패
- 이동평균선: 확인 실패
- 재무제표/실적: 확인 실패
- 뉴스: 확인 실패
- 데이터 기준일: 확인 실패
- 실패한 데이터 소스:
- 데이터 분석 의존성 로딩 실패: {error}

## 3. 주요 가격대

| 구분 | 가격 | 의미 |
|---|---:|---|
| 현재가 | 확인 실패 | OHLCV 확인 실패 |
| 진입 후보 | 확인 실패 | OHLCV 확인 실패 |
| 1차 지지선 | 확인 실패 | OHLCV 확인 실패 |
| 2차 지지선 | 확인 실패 | OHLCV 확인 실패 |
| 1차 저항선 | 확인 실패 | OHLCV 확인 실패 |
| 2차 저항선 | 확인 실패 | OHLCV 확인 실패 |
| 손절 기준 | 확인 실패 | OHLCV 확인 실패 |
| 1차 목표가 | 확인 실패 | OHLCV 확인 실패 |
| 2차 목표가 | 확인 실패 | OHLCV 확인 실패 |

## 4. 이미지 기반 분석과 데이터 기반 분석 비교

- 이미지상 판단: {image_text}
- 실제 데이터상 판단: 확인 실패
- 일치하는 부분: 실제 데이터 확인 실패로 비교 불가
- 다른 부분: 실제 데이터 확인 실패로 비교 불가
- 최종 해석: requirements.txt 설치 후 다시 실행해야 RSI, MACD, Bollinger Band, 재무제표, 뉴스 확인이 가능합니다.

## 5. 기술적 분석

### 추세
확인 실패

### 이동평균선
확인 실패

### RSI
확인 실패

### MACD
확인 실패

### Bollinger Band
확인 실패

### 거래량
확인 실패

### 캔들/패턴
{image_text}

### 지지와 저항
확인 실패

## 6. 생성된 차트 이미지

- 분석 차트 이미지 경로: 생성 실패
- 시나리오 차트 이미지 경로: 생성 실패
- 리포트 카드 이미지 경로: {report_card_path}
- 이미지 생성 실패 이유: 데이터 분석 의존성 로딩 실패로 OHLCV 차트 렌더링 불가
{report_card_failure_line}

## 7. 시나리오 해석

- 상승 시나리오: 확인 실패
- 중립 시나리오: 확인 실패
- 하락 시나리오: 확인 실패
- 무효화 조건: 실제 OHLCV 확인 전까지 산정 불가

## 8. 매매 전략

### 신규 진입자
확인 실패

### 보유자
확인 실패

### 추가매수
확인 실패

### 손절/익절
확인 실패

## 9. 리스크 관리

- 데이터 확인 전에는 큰 비중 진입을 피합니다.
- 이미지 기반 판단만으로 매수 결정을 확정하지 않습니다.
- 손절가와 목표가는 실제 OHLCV 확인 후 산정합니다.

## 10. 운용사 비서 코멘트

데이터 의존성 또는 네트워크 문제가 해결되기 전에는 투자 판단의 확신도를 낮춰야 합니다.

## 11. 한계

실제 OHLCV, 재무제표, 뉴스, 차트 이미지 생성이 모두 확인 실패 상태입니다.

## Disclaimer

이 분석은 투자 참고용이며 수익을 보장하지 않습니다. 최종 투자 판단과 책임은 사용자에게 있습니다.
"""


def _format_fundamentals(data: dict[str, Any]) -> str:
    if not data:
        return "확인 실패"
    labels = {
        "market_cap": "시가총액",
        "trailing_pe": "PER",
        "price_to_book": "PBR",
        "return_on_equity": "ROE",
        "debt_to_equity": "부채비율",
        "total_revenue": "매출",
        "operating_margins": "영업이익률",
        "profit_margins": "순이익률",
        "earnings_quarterly_growth": "분기 이익 성장률",
        "revenue_growth": "매출 성장률",
    }
    parts = []
    for key, label in labels.items():
        if key in data:
            parts.append(f"{label}: {data[key]}")
    return ", ".join(parts) if parts else str(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Korean stock analysis report with verified data.")
    parser.add_argument("--ticker", required=True, help="Stock ticker, e.g. 005930, 005930.KS, AAPL")
    parser.add_argument("--stock-name", "--name", dest="stock_name", default=None, help="Korean stock name or display name")
    parser.add_argument("--horizon", default="스윙", help="Investment horizon")
    parser.add_argument("--image-notes", default=None, help="Optional image-based chart notes")
    parser.add_argument("--output", default=None, help="Optional output markdown path")
    parser.add_argument("--output-dir", default="outputs", help="Directory for generated PNG chart images")
    args = parser.parse_args()

    report = build_report(
        ticker=args.ticker,
        stock_name=args.stock_name,
        horizon=args.horizon,
        image_notes=args.image_notes,
        output_dir=args.output_dir,
    )

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    else:
        print(report)


if __name__ == "__main__":
    main()
