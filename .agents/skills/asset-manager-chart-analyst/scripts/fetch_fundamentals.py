from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class FundamentalsResult:
    ticker: str
    source: str | None
    data: dict[str, Any]
    timestamp: str
    failures: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.data)


def _safe_number(value: Any) -> Any:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def fetch_yfinance_fundamentals(ticker: str) -> tuple[dict[str, Any], str | None]:
    try:
        import yfinance as yf
    except Exception as exc:
        return {}, f"yfinance 재무 데이터 import 실패: {exc}"

    candidates = [ticker]
    if ticker.isdigit() and len(ticker) == 6:
        candidates.extend([f"{ticker}.KS", f"{ticker}.KQ"])

    errors: list[str] = []
    for candidate in candidates:
        try:
            info = yf.Ticker(candidate).get_info()
            if not info:
                errors.append(f"{candidate}: info 데이터 없음")
                continue
            data = {
                "symbol": info.get("symbol") or candidate,
                "short_name": info.get("shortName") or info.get("longName"),
                "market_cap": _safe_number(info.get("marketCap")),
                "trailing_pe": _safe_number(info.get("trailingPE")),
                "forward_pe": _safe_number(info.get("forwardPE")),
                "price_to_book": _safe_number(info.get("priceToBook")),
                "return_on_equity": _safe_number(info.get("returnOnEquity")),
                "debt_to_equity": _safe_number(info.get("debtToEquity")),
                "total_revenue": _safe_number(info.get("totalRevenue")),
                "operating_margins": _safe_number(info.get("operatingMargins")),
                "profit_margins": _safe_number(info.get("profitMargins")),
                "earnings_quarterly_growth": _safe_number(info.get("earningsQuarterlyGrowth")),
                "revenue_growth": _safe_number(info.get("revenueGrowth")),
            }
            cleaned = {key: value for key, value in data.items() if value is not None}
            if cleaned:
                return cleaned, None
            errors.append(f"{candidate}: 사용 가능한 핵심 재무 항목 없음")
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")

    return {}, "yfinance 재무제표/실적 확인 실패: " + "; ".join(errors)


def fetch_env_api_status() -> tuple[dict[str, Any], list[str]]:
    notes: dict[str, Any] = {}
    failures: list[str] = []

    dart_key = os.getenv("DART_API_KEY") or os.getenv("API_K_DART")
    if dart_key:
        notes["dart_api"] = "DART API key detected in environment; implement corp_code mapping before requesting filings."
    else:
        failures.append("DART 확인 생략: DART_API_KEY 또는 API_K_DART 환경변수 없음")

    return notes, failures


def fetch_fundamentals(ticker: str) -> FundamentalsResult:
    timestamp = datetime.now().isoformat(timespec="seconds")
    failures: list[str] = []

    data, error = fetch_yfinance_fundamentals(ticker)
    if error:
        failures.append(error)

    env_notes, env_failures = fetch_env_api_status()
    failures.extend(env_failures)
    if env_notes:
        data.update(env_notes)

    return FundamentalsResult(
        ticker=ticker,
        source="yfinance" if data else None,
        data=data,
        timestamp=timestamp,
        failures=failures,
    )
