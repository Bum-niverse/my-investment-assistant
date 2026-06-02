from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SequenceProbabilityResult:
    current_sequence_direction: str
    current_sequence_count: int
    historical_sample_size: int
    sequence_bullish_probability: float | None
    sequence_bearish_probability: float | None
    bb_position: str
    bb_upper_breakout_probability: float | None
    bb_upper_reversal_probability: float | None
    bb_upper_sample_size: int
    bb_lower_bounce_probability: float | None
    bb_lower_breakdown_probability: float | None
    bb_lower_sample_size: int
    next_bullish_probability: float | None
    next_bearish_probability: float | None
    prediction: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_sequence_direction": self.current_sequence_direction,
            "current_sequence_count": self.current_sequence_count,
            "historical_sample_size": self.historical_sample_size,
            "sequence_bullish_probability": self.sequence_bullish_probability,
            "sequence_bearish_probability": self.sequence_bearish_probability,
            "bb_position": self.bb_position,
            "bb_upper_breakout_probability": self.bb_upper_breakout_probability,
            "bb_upper_reversal_probability": self.bb_upper_reversal_probability,
            "bb_upper_sample_size": self.bb_upper_sample_size,
            "bb_lower_bounce_probability": self.bb_lower_bounce_probability,
            "bb_lower_breakdown_probability": self.bb_lower_breakdown_probability,
            "bb_lower_sample_size": self.bb_lower_sample_size,
            "next_bullish_probability": self.next_bullish_probability,
            "next_bearish_probability": self.next_bearish_probability,
            "prediction": self.prediction,
            "summary": self.summary,
        }


def _pct(numerator: int | float, denominator: int | float) -> float | None:
    if denominator <= 0:
        return None
    return float(numerator) / float(denominator) * 100


def _fmt_pct(value: float | None) -> str:
    return "샘플 부족" if value is None else f"{value:.2f}%"


def _direction_label(direction: int) -> str:
    if direction > 0:
        return "양봉"
    if direction < 0:
        return "음봉"
    return "도지/중립"


def _prediction_label(bullish_probability: float | None, bearish_probability: float | None) -> str:
    if bullish_probability is None or bearish_probability is None:
        return "샘플 부족"
    if bullish_probability > bearish_probability:
        return "양봉 우위"
    if bearish_probability > bullish_probability:
        return "음봉 우위"
    return "중립"


def calculate_sequence_probability(
    df: pd.DataFrame,
    *,
    scan_bars: int = 1500,
    max_sequence_cap: int = 20,
    bb_length: int = 20,
    bb_multiplier: float = 2.0,
    bb_lookahead: int = 3,
) -> SequenceProbabilityResult:
    required_columns = {"Open", "High", "Low", "Close"}
    missing_columns = required_columns.difference(df.columns)
    if df.empty or missing_columns:
        raise ValueError(f"OHLCV 데이터가 부족합니다. 누락 컬럼: {', '.join(sorted(missing_columns))}")

    data = df[list(required_columns)].copy()
    for column in required_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna()

    min_rows = max(bb_length + bb_lookahead + 5, 60)
    if len(data) < min_rows:
        raise ValueError(f"통계 계산에 필요한 봉 수가 부족합니다. 필요 최소 {min_rows}개, 현재 {len(data)}개")

    close = data["Close"]
    basis = close.rolling(bb_length, min_periods=bb_length).mean()
    std = close.rolling(bb_length, min_periods=bb_length).std()
    upper = basis + bb_multiplier * std
    lower = basis - bb_multiplier * std

    directions = np.sign((data["Close"] - data["Open"]).to_numpy(dtype=float)).astype(int)
    highs = data["High"].to_numpy(dtype=float)
    lows = data["Low"].to_numpy(dtype=float)
    closes = close.to_numpy(dtype=float)
    upper_values = upper.to_numpy(dtype=float)
    lower_values = lower.to_numpy(dtype=float)
    basis_values = basis.to_numpy(dtype=float)

    current_direction = int(directions[-1])
    current_sequence_count = 0
    if current_direction != 0:
        for direction in directions[::-1][:max_sequence_cap]:
            if int(direction) == current_direction:
                current_sequence_count += 1
            else:
                break

    scan_start = max(1, len(data) - min(scan_bars, len(data) - 1))
    last_historical_index = len(data) - 2

    sequence_bullish_count = 0
    sequence_bearish_count = 0
    historical_sample_size = 0

    if current_sequence_count > 0:
        for end_index in range(scan_start + current_sequence_count - 1, last_historical_index + 1):
            start_index = end_index - current_sequence_count + 1
            if start_index <= 0:
                continue
            same_sequence = np.all(directions[start_index : end_index + 1] == current_direction)
            exact_sequence_start = directions[start_index - 1] != current_direction
            next_direction = int(directions[end_index + 1])
            if same_sequence and exact_sequence_start and next_direction != 0:
                historical_sample_size += 1
                if next_direction > 0:
                    sequence_bullish_count += 1
                else:
                    sequence_bearish_count += 1

    sequence_bullish_probability = _pct(sequence_bullish_count, historical_sample_size)
    sequence_bearish_probability = _pct(sequence_bearish_count, historical_sample_size)

    upper_breakout_count = 0
    upper_reversal_count = 0
    upper_sample_size = 0
    lower_bounce_count = 0
    lower_breakdown_count = 0
    lower_sample_size = 0

    for index in range(max(scan_start, bb_length), len(data) - bb_lookahead):
        if np.isnan(upper_values[index]) or np.isnan(lower_values[index]) or np.isnan(basis_values[index]):
            continue

        upper_touch = highs[index] >= upper_values[index] or closes[index] >= upper_values[index]
        lower_touch = lows[index] <= lower_values[index] or closes[index] <= lower_values[index]

        if upper_touch:
            outcome = 0
            for forward in range(1, bb_lookahead + 1):
                future = index + forward
                breakout = closes[future] > upper_values[future] or highs[future] > highs[index]
                reversal = closes[future] < basis_values[future] or closes[future] < closes[index]
                if breakout:
                    outcome = 1
                    break
                if reversal:
                    outcome = -1
                    break
            if outcome == 1:
                upper_breakout_count += 1
                upper_sample_size += 1
            elif outcome == -1:
                upper_reversal_count += 1
                upper_sample_size += 1

        if lower_touch:
            outcome = 0
            for forward in range(1, bb_lookahead + 1):
                future = index + forward
                bounce = closes[future] > basis_values[future] or closes[future] > closes[index]
                breakdown = closes[future] < lower_values[future] or lows[future] < lows[index]
                if bounce:
                    outcome = 1
                    break
                if breakdown:
                    outcome = -1
                    break
            if outcome == 1:
                lower_bounce_count += 1
                lower_sample_size += 1
            elif outcome == -1:
                lower_breakdown_count += 1
                lower_sample_size += 1

    bb_upper_breakout_probability = _pct(upper_breakout_count, upper_sample_size)
    bb_upper_reversal_probability = _pct(upper_reversal_count, upper_sample_size)
    bb_lower_bounce_probability = _pct(lower_bounce_count, lower_sample_size)
    bb_lower_breakdown_probability = _pct(lower_breakdown_count, lower_sample_size)

    latest_high = highs[-1]
    latest_low = lows[-1]
    latest_close = closes[-1]
    latest_upper = upper_values[-1]
    latest_lower = lower_values[-1]

    current_upper_touch = not np.isnan(latest_upper) and (latest_high >= latest_upper or latest_close >= latest_upper)
    current_lower_touch = not np.isnan(latest_lower) and (latest_low <= latest_lower or latest_close <= latest_lower)

    bb_position = "현재 BB 중립권"
    bb_bullish_probability: float | None = None
    bb_bearish_probability: float | None = None
    bb_sample_for_now = 0
    if current_upper_touch:
        bb_position = "현재 BB 상단권"
        bb_bullish_probability = bb_upper_breakout_probability
        bb_bearish_probability = bb_upper_reversal_probability
        bb_sample_for_now = upper_sample_size
    elif current_lower_touch:
        bb_position = "현재 BB 하단권"
        bb_bullish_probability = bb_lower_bounce_probability
        bb_bearish_probability = bb_lower_breakdown_probability
        bb_sample_for_now = lower_sample_size

    sequence_weight = min(historical_sample_size / 30.0, 1.0) if historical_sample_size > 0 else 0.0
    bb_weight = min(bb_sample_for_now / 50.0, 1.0) if bb_sample_for_now > 0 else 0.0
    next_bullish_probability: float | None = None
    next_bearish_probability: float | None = None
    if sequence_weight + bb_weight > 0:
        sequence_bullish = sequence_bullish_probability if sequence_bullish_probability is not None else 50.0
        bb_bullish = bb_bullish_probability if bb_bullish_probability is not None else 50.0
        next_bullish_probability = (
            (sequence_bullish * sequence_weight) + (bb_bullish * bb_weight)
        ) / (sequence_weight + bb_weight)
        next_bearish_probability = 100.0 - next_bullish_probability

    prediction = _prediction_label(next_bullish_probability, next_bearish_probability)
    summary = (
        f"현재 감지된 패턴은 {current_sequence_count}일 연속 {_direction_label(current_direction)}입니다. "
        f"과거 동일 패턴 샘플은 {historical_sample_size}회이며, "
        f"다음 봉 통계는 양봉 {_fmt_pct(sequence_bullish_probability)} / 음봉 {_fmt_pct(sequence_bearish_probability)}입니다. "
        f"BB 상단 성향은 돌파형 {_fmt_pct(bb_upper_breakout_probability)} / 반전형 {_fmt_pct(bb_upper_reversal_probability)}이며, "
        f"최종 결합 확률은 양봉 {_fmt_pct(next_bullish_probability)} / 음봉 {_fmt_pct(next_bearish_probability)}로 {prediction}입니다."
    )

    return SequenceProbabilityResult(
        current_sequence_direction=_direction_label(current_direction),
        current_sequence_count=current_sequence_count,
        historical_sample_size=historical_sample_size,
        sequence_bullish_probability=sequence_bullish_probability,
        sequence_bearish_probability=sequence_bearish_probability,
        bb_position=bb_position,
        bb_upper_breakout_probability=bb_upper_breakout_probability,
        bb_upper_reversal_probability=bb_upper_reversal_probability,
        bb_upper_sample_size=upper_sample_size,
        bb_lower_bounce_probability=bb_lower_bounce_probability,
        bb_lower_breakdown_probability=bb_lower_breakdown_probability,
        bb_lower_sample_size=lower_sample_size,
        next_bullish_probability=next_bullish_probability,
        next_bearish_probability=next_bearish_probability,
        prediction=prediction,
        summary=summary,
    )
