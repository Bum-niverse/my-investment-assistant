from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class PriceLevels:
    current_price: float
    support_1: float
    support_2: float
    resistance_1: float
    resistance_2: float
    entry_price: float
    stop_loss: float
    target_1: float
    target_2: float
    reason: str
    support_1_meaning: str
    support_2_meaning: str
    resistance_1_meaning: str
    resistance_2_meaning: str
    entry_meaning: str
    stop_loss_meaning: str
    target_1_meaning: str
    target_2_meaning: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_price": self.current_price,
            "support_1": self.support_1,
            "support_2": self.support_2,
            "resistance_1": self.resistance_1,
            "resistance_2": self.resistance_2,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "target_1": self.target_1,
            "target_2": self.target_2,
            "reason": self.reason,
            "support_1_meaning": self.support_1_meaning,
            "support_2_meaning": self.support_2_meaning,
            "resistance_1_meaning": self.resistance_1_meaning,
            "resistance_2_meaning": self.resistance_2_meaning,
            "entry_meaning": self.entry_meaning,
            "stop_loss_meaning": self.stop_loss_meaning,
            "target_1_meaning": self.target_1_meaning,
            "target_2_meaning": self.target_2_meaning,
        }


def _numeric_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"OHLCV 필수 컬럼 누락: {', '.join(missing)}")
    numeric = df[required].apply(pd.to_numeric, errors="coerce").dropna()
    if len(numeric) < 30:
        raise ValueError("지지선/저항선 탐지를 위한 OHLCV 데이터가 30개 미만입니다")
    return numeric


def _pivot_lows(df: pd.DataFrame, window: int = 3) -> pd.Series:
    lows = df["Low"]
    return lows[(lows == lows.rolling(window * 2 + 1, center=True).min())]


def _pivot_highs(df: pd.DataFrame, window: int = 3) -> pd.Series:
    highs = df["High"]
    return highs[(highs == highs.rolling(window * 2 + 1, center=True).max())]


def _nearest_below(values: list[float], price: float, fallback: float) -> float:
    below = [value for value in values if value < price]
    return max(below) if below else fallback


def _nearest_above(values: list[float], price: float, fallback: float) -> float:
    above = [value for value in values if value > price]
    return min(above) if above else fallback


def _nearest_candidate_below(
    candidates: list[tuple[float, str]],
    price: float,
    fallback: tuple[float, str],
) -> tuple[float, str]:
    below = [(value, meaning) for value, meaning in candidates if value < price]
    return max(below, key=lambda item: item[0]) if below else fallback


def _nearest_candidate_above(
    candidates: list[tuple[float, str]],
    price: float,
    fallback: tuple[float, str],
) -> tuple[float, str]:
    above = [(value, meaning) for value, meaning in candidates if value > price]
    return min(above, key=lambda item: item[0]) if above else fallback


def _high_volume_price_levels(df: pd.DataFrame, bins: int = 12, top_n: int = 4) -> list[float]:
    try:
        working = df[["Close", "Volume"]].dropna().copy()
        if working.empty or working["Close"].nunique() < 3:
            return []
        working["price_bin"] = pd.cut(working["Close"], bins=bins)
        grouped = working.groupby("price_bin", observed=True)["Volume"].sum().sort_values(ascending=False)
        levels: list[float] = []
        for interval in grouped.head(top_n).index:
            levels.append(float((interval.left + interval.right) / 2))
        return levels
    except Exception:
        return []


def detect_price_levels(df: pd.DataFrame) -> PriceLevels:
    ohlcv = _numeric_ohlcv(df)
    recent = ohlcv.tail(120)
    current = float(recent["Close"].iloc[-1])

    pivot_lows = _pivot_lows(recent).dropna().tail(12).tolist()
    pivot_highs = _pivot_highs(recent).dropna().tail(12).tolist()

    ma20 = float(recent["Close"].rolling(20, min_periods=1).mean().iloc[-1])
    ma60 = float(recent["Close"].rolling(60, min_periods=1).mean().iloc[-1])
    ma120 = float(ohlcv["Close"].rolling(120, min_periods=1).mean().iloc[-1])

    box_low = float(recent["Low"].tail(60).quantile(0.15))
    box_high = float(recent["High"].tail(60).quantile(0.85))
    recent_high = float(recent["High"].tail(60).max())
    recent_low = float(recent["Low"].tail(60).min())
    volume_levels = _high_volume_price_levels(recent)

    support_candidates = (
        [(float(value), "최근 저점 기반 지지 후보") for value in pivot_lows]
        + [(float(level), "거래량 집중 가격대 기반 지지 후보") for level in volume_levels if level < current]
        + [
            (ma20, "20일선 또는 단기 지지 후보"),
            (ma60, "60일선 또는 중기 지지 후보"),
            (ma120, "120일선 또는 장기 지지 후보"),
            (box_low, "박스권 하단 기반 지지 후보"),
            (recent_low, "최근 저점 기반 지지 후보"),
        ]
    )
    resistance_candidates = (
        [(float(value), "최근 고점 기반 저항 후보") for value in pivot_highs]
        + [(float(level), "거래량 집중 가격대 기반 저항 후보") for level in volume_levels if level > current]
        + [
            (box_high, "박스권 상단 기반 저항 후보"),
            (recent_high, "최근 고점 기반 저항 후보"),
        ]
    )

    fallback_support = min(
        [(ma20, "20일선 또는 단기 지지 후보"), (box_low, "박스권 하단 기반 지지 후보"), (recent_low, "최근 저점 기반 지지 후보")],
        key=lambda item: item[0],
    )
    support_1, support_1_meaning = _nearest_candidate_below(support_candidates, current, fallback_support)
    support_2, support_2_meaning = _nearest_candidate_below(
        [(value, meaning) for value, meaning in support_candidates if value < support_1],
        current,
        min(
            [(ma60, "60일선 또는 중기 지지 후보"), (ma120, "120일선 또는 장기 지지 후보"), (recent_low, "최근 저점 기반 지지 후보")],
            key=lambda item: item[0],
        ),
    )
    fallback_resistance = max(
        [(box_high, "박스권 상단 기반 저항 후보"), (recent_high, "최근 고점 기반 저항 후보")],
        key=lambda item: item[0],
    )
    resistance_1, resistance_1_meaning = _nearest_candidate_above(resistance_candidates, current, fallback_resistance)
    resistance_2, resistance_2_meaning = _nearest_candidate_above(
        [(value, meaning) for value, meaning in resistance_candidates if value > resistance_1],
        current,
        (max(recent_high, resistance_1 * 1.06), "최근 고점 기반 저항 후보"),
    )

    entry = support_1 * 1.01
    stop_loss = support_1 * 0.97
    target_1 = resistance_1
    target_2 = max(resistance_2, resistance_1 * 1.05)

    if not np.isfinite([support_1, support_2, resistance_1, resistance_2, entry, stop_loss, target_1, target_2]).all():
        raise ValueError("계산된 가격대에 유효하지 않은 값이 포함되어 있습니다")

    reason = "최근 pivot 고점/저점, 60거래일 박스권, MA20/MA60/MA120, 가능할 경우 거래량 집중 가격대를 함께 반영했습니다."
    return PriceLevels(
        current_price=current,
        support_1=float(support_1),
        support_2=float(support_2),
        resistance_1=float(resistance_1),
        resistance_2=float(resistance_2),
        entry_price=float(entry),
        stop_loss=float(stop_loss),
        target_1=float(target_1),
        target_2=float(target_2),
        reason=reason,
        support_1_meaning=support_1_meaning,
        support_2_meaning=support_2_meaning,
        resistance_1_meaning=resistance_1_meaning,
        resistance_2_meaning=resistance_2_meaning,
        entry_meaning=f"{support_1_meaning} 확인 후 분할 진입 후보",
        stop_loss_meaning=f"{support_1_meaning} 이탈 기준",
        target_1_meaning=resistance_1_meaning,
        target_2_meaning=resistance_2_meaning,
    )
