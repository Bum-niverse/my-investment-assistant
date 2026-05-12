from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _get_korean_font_properties() -> Any:
    import platform

    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    system = platform.system()
    preferred_fonts = {
        "Darwin": ["AppleGothic"],
        "Windows": ["Malgun Gothic"],
        "Linux": ["NanumGothic", "Noto Sans CJK KR", "Noto Sans KR", "UnDotum"],
    }
    fallback_fonts = ["AppleGothic", "Malgun Gothic", "NanumGothic", "Noto Sans CJK KR", "Noto Sans KR", "DejaVu Sans"]
    candidates = preferred_fonts.get(system, []) + fallback_fonts

    available = {font.name: font.fname for font in font_manager.fontManager.ttflist}
    for font_name in candidates:
        if font_name in available:
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            return font_manager.FontProperties(fname=available[font_name])

    plt.rcParams["axes.unicode_minus"] = False
    return font_manager.FontProperties()


def _apply_font_to_axes(ax: Any, font_properties: Any) -> None:
    ax.title.set_fontproperties(font_properties)
    ax.xaxis.label.set_fontproperties(font_properties)
    ax.yaxis.label.set_fontproperties(font_properties)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_properties)
    legend = ax.get_legend()
    if legend:
        for text in legend.get_texts():
            text.set_fontproperties(font_properties)
        if legend.get_title():
            legend.get_title().set_fontproperties(font_properties)


def _prepare_close_data(df: pd.DataFrame) -> pd.DataFrame:
    if "Close" not in df.columns:
        raise ValueError("시나리오 차트 생성을 위한 Close 컬럼이 없습니다")
    chart_df = df[["Close"]].apply(pd.to_numeric, errors="coerce").dropna().copy()
    if len(chart_df) < 30:
        raise ValueError("시나리오 차트 생성을 위한 OHLCV 데이터가 30개 미만입니다")
    if not isinstance(chart_df.index, pd.DatetimeIndex):
        chart_df.index = pd.to_datetime(chart_df.index)
    return chart_df.tail(180)


def build_scenarios(
    current_price: float,
    levels: dict[str, Any],
    periods: int = 20,
) -> dict[str, np.ndarray]:
    target_1 = float(levels.get("target_1", current_price * 1.08))
    support_1 = float(levels.get("support_1", current_price * 0.97))
    stop_loss = float(levels.get("stop_loss", current_price * 0.94))

    x = np.linspace(0, 1, periods)
    bullish = current_price + (target_1 - current_price) * (x ** 1.2)
    neutral = current_price + (support_1 - current_price) * 0.25 * np.sin(np.pi * x)
    bearish = current_price + (stop_loss - current_price) * (x ** 1.1)

    return {
        "bullish": bullish,
        "neutral": neutral,
        "bearish": bearish,
    }


def render_forecast_chart(
    df: pd.DataFrame,
    levels: dict[str, Any],
    output_path: str | Path,
    title: str = "향후 주가 시나리오 전망",
) -> str:
    import matplotlib.pyplot as plt

    font_properties = _get_korean_font_properties()
    chart_df = _prepare_close_data(df)
    current_price = float(chart_df["Close"].iloc[-1])
    scenarios = build_scenarios(current_price, levels)

    future_index = pd.bdate_range(chart_df.index[-1], periods=len(scenarios["bullish"]) + 1)[1:]

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(chart_df.index, chart_df["Close"], color="#111827", linewidth=1.8, label="실제 종가")
    ax.plot(future_index, scenarios["bullish"], color="#dc2626", linestyle="--", linewidth=1.8, label="상승 시나리오")
    ax.plot(future_index, scenarios["neutral"], color="#64748b", linestyle="--", linewidth=1.8, label="중립 시나리오")
    ax.plot(future_index, scenarios["bearish"], color="#2563eb", linestyle="--", linewidth=1.8, label="하락 시나리오")

    for key, label, color in [
        ("target_1", "상승 확인/1차 목표", "#dc2626"),
        ("support_1", "중립 방어선", "#16a34a"),
        ("stop_loss", "무효화/손절", "#111827"),
    ]:
        value = levels.get(key)
        if value is None:
            continue
        ax.axhline(float(value), color=color, linestyle=":", linewidth=1.1, alpha=0.85)
        ax.text(future_index[-1], float(value), f" {label} {float(value):,.0f}", color=color, va="center", fontsize=9, fontproperties=font_properties)

    ax.axvline(chart_df.index[-1], color="#94a3b8", linestyle=":", linewidth=1.2)
    ax.text(chart_df.index[-1], current_price, " 현재", color="#111827", fontsize=9, va="bottom", fontproperties=font_properties)

    ax.set_title(title, fontproperties=font_properties, fontsize=15, fontweight="bold", pad=14)
    ax.set_xlabel("날짜", fontproperties=font_properties)
    ax.set_ylabel("가격", fontproperties=font_properties)
    ax.grid(True, color="#e5e7eb")
    legend = ax.legend(loc="best", prop=font_properties)
    if legend.get_title():
        legend.get_title().set_fontproperties(font_properties)
    ax.text(
        0.01,
        0.02,
        "미래 구간은 예측이 아니라 조건부 시나리오입니다. 점선은 실제 가격이 아닙니다.",
        transform=ax.transAxes,
        fontsize=10,
        fontproperties=font_properties,
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "#f8fafc", "edgecolor": "#94a3b8", "alpha": 0.92},
    )
    _apply_font_to_axes(ax, font_properties)
    for text in fig.texts:
        text.set_fontproperties(font_properties)

    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(output)
