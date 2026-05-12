from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _require_close(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        raise ValueError("OHLCV data is empty")
    if "Close" not in df.columns:
        raise ValueError("OHLCV data must include a Close column")
    close = pd.to_numeric(df["Close"], errors="coerce").dropna()
    if close.empty:
        raise ValueError("Close column has no numeric data")
    return close


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    close = _require_close(df)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def calculate_macd(
    df: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> pd.DataFrame:
    close = _require_close(df)
    ema_fast = close.ewm(span=fast_period, adjust=False).mean()
    ema_slow = close.ewm(span=slow_period, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    histogram = macd - signal
    return pd.DataFrame({"MACD": macd, "Signal": signal, "Histogram": histogram})


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    num_std: float = 2.0,
) -> pd.DataFrame:
    close = _require_close(df)
    middle = close.rolling(window=period, min_periods=period).mean()
    std = close.rolling(window=period, min_periods=period).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return pd.DataFrame({"BB_Upper": upper, "BB_Middle": middle, "BB_Lower": lower})


def calculate_moving_averages(df: pd.DataFrame, windows: tuple[int, ...] = (5, 20, 60, 120)) -> pd.DataFrame:
    close = _require_close(df)
    return pd.DataFrame({f"MA_{window}": close.rolling(window=window, min_periods=1).mean() for window in windows})


def calculate_recent_volatility(df: pd.DataFrame, period: int = 20) -> float:
    close = _require_close(df)
    returns = close.pct_change().dropna()
    if returns.empty:
        return 0.0
    return float(returns.tail(period).std() * np.sqrt(252) * 100)


def build_indicator_summary(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        raise ValueError("OHLCV data is empty")

    rsi = calculate_rsi(df)
    macd = calculate_macd(df)
    bands = calculate_bollinger_bands(df)
    moving_averages = calculate_moving_averages(df)
    volatility = calculate_recent_volatility(df)

    latest_date = df.index[-1]
    latest_close = float(pd.to_numeric(df["Close"], errors="coerce").dropna().iloc[-1])
    latest_rsi = float(rsi.dropna().iloc[-1])
    latest_macd = macd.dropna().iloc[-1].to_dict() if not macd.dropna().empty else {}
    latest_bands = bands.dropna().iloc[-1].to_dict() if not bands.dropna().empty else {}
    latest_ma = moving_averages.dropna().iloc[-1].to_dict() if not moving_averages.dropna().empty else {}

    return {
        "latest_date": str(latest_date.date() if hasattr(latest_date, "date") else latest_date),
        "latest_close": latest_close,
        "rsi_14": latest_rsi,
        "macd": {key: float(value) for key, value in latest_macd.items()},
        "bollinger_bands": {key: float(value) for key, value in latest_bands.items()},
        "moving_averages": {key: float(value) for key, value in latest_ma.items()},
        "recent_volatility_annualized_percent": volatility,
    }
