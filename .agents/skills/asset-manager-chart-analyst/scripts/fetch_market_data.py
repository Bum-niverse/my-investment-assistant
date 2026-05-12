from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import pandas as pd


@dataclass
class MarketDataResult:
    ticker: str
    source: str | None
    data: pd.DataFrame
    timestamp: str
    failures: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.data.empty


def normalize_korean_ticker(ticker: str) -> str:
    clean = ticker.strip()
    if clean.isdigit() and len(clean) == 6:
        return f"{clean}.KS"
    return clean


def _standardize_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [str(col[0]) for col in df.columns]
    rename_map = {
        "Open": "Open",
        "High": "High",
        "Low": "Low",
        "Close": "Close",
        "Adj Close": "Adj Close",
        "Volume": "Volume",
    }
    columns = [col for col in rename_map if col in df.columns]
    return df[columns].copy()


def fetch_yfinance_ohlcv(ticker: str, period: str = "1y", interval: str = "1d") -> tuple[pd.DataFrame, str | None]:
    try:
        import yfinance as yf
    except Exception as exc:
        return pd.DataFrame(), f"yfinance import 실패: {exc}"

    candidates = [ticker]
    normalized = normalize_korean_ticker(ticker)
    if normalized not in candidates:
        candidates.append(normalized)
    if ticker.isdigit() and len(ticker) == 6:
        candidates.append(f"{ticker}.KQ")

    errors: list[str] = []
    for candidate in candidates:
        try:
            df = yf.download(candidate, period=period, interval=interval, progress=False, auto_adjust=False)
            df = _standardize_yfinance_columns(df)
            if not df.empty:
                return df, None
            errors.append(f"{candidate}: 데이터 없음")
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")

    return pd.DataFrame(), "yfinance OHLCV 확인 실패: " + "; ".join(errors)


def fetch_pykrx_ohlcv(ticker: str, days: int = 365) -> tuple[pd.DataFrame, str | None]:
    if not (ticker.isdigit() and len(ticker) == 6):
        return pd.DataFrame(), "pykrx 확인 생략: 한국 6자리 숫자 티커가 아님"

    try:
        from pykrx import stock
    except Exception as exc:
        return pd.DataFrame(), f"pykrx 확인 실패: pykrx가 설치되어 있지 않거나 import 실패 ({exc})"

    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    try:
        raw = stock.get_market_ohlcv_by_date(start, end, ticker)
        if raw.empty:
            return pd.DataFrame(), "pykrx OHLCV 확인 실패: 데이터 없음"
        df = raw.rename(
            columns={
                "시가": "Open",
                "고가": "High",
                "저가": "Low",
                "종가": "Close",
                "거래량": "Volume",
            }
        )
        return df[["Open", "High", "Low", "Close", "Volume"]].copy(), None
    except Exception as exc:
        return pd.DataFrame(), f"pykrx OHLCV 확인 실패: {exc}"


def fetch_ohlcv(ticker: str, period: str = "1y", interval: str = "1d") -> MarketDataResult:
    timestamp = datetime.now().isoformat(timespec="seconds")
    failures: list[str] = []

    yf_df, yf_error = fetch_yfinance_ohlcv(ticker, period=period, interval=interval)
    if not yf_df.empty:
        if yf_error:
            failures.append(yf_error)
        return MarketDataResult(ticker=ticker, source="yfinance", data=yf_df, timestamp=timestamp, failures=failures)
    if yf_error:
        failures.append(yf_error)

    pykrx_df, pykrx_error = fetch_pykrx_ohlcv(ticker)
    if not pykrx_df.empty:
        if pykrx_error:
            failures.append(pykrx_error)
        return MarketDataResult(ticker=ticker, source="pykrx", data=pykrx_df, timestamp=timestamp, failures=failures)
    if pykrx_error:
        failures.append(pykrx_error)

    return MarketDataResult(ticker=ticker, source=None, data=pd.DataFrame(), timestamp=timestamp, failures=failures)


def summarize_ohlcv(result: MarketDataResult) -> dict[str, Any]:
    if result.data.empty:
        return {
            "ok": False,
            "source": result.source,
            "timestamp": result.timestamp,
            "failures": result.failures,
        }

    df = result.data.dropna(subset=["Close"])
    latest = df.iloc[-1]
    recent = df.tail(60)

    return {
        "ok": True,
        "ticker": result.ticker,
        "source": result.source,
        "timestamp": result.timestamp,
        "rows": int(len(df)),
        "start_date": str(df.index[0].date() if hasattr(df.index[0], "date") else df.index[0]),
        "end_date": str(df.index[-1].date() if hasattr(df.index[-1], "date") else df.index[-1]),
        "latest_close": float(latest["Close"]),
        "recent_high_60": float(recent["High"].max()) if "High" in recent else None,
        "recent_low_60": float(recent["Low"].min()) if "Low" in recent else None,
        "latest_volume": float(latest["Volume"]) if "Volume" in latest else None,
        "failures": result.failures,
    }
