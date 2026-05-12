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

    fig, ax = plt.subplots(figsize=(16, 9), facecolor="#ffffff")
    fig.subplots_adjust(top=0.9, bottom=0.1, left=0.06, right=0.9)
    ax.set_facecolor("#ffffff")
    ax.axvspan(future_index[0], future_index[-1], color="#f1f5f9", alpha=0.85, zorder=0)
    ax.plot(chart_df.index, chart_df["Close"], color="#111827", linewidth=2.0, label="실제 종가", zorder=3)
    ax.plot(future_index, scenarios["bullish"], color="#dc2626", linestyle=(0, (5, 4)), linewidth=2.8, label="상승 시나리오", zorder=4)
    ax.plot(future_index, scenarios["neutral"], color="#64748b", linestyle=(0, (3, 4)), linewidth=2.5, label="중립 시나리오", zorder=4)
    ax.plot(future_index, scenarios["bearish"], color="#2563eb", linestyle=(0, (5, 4)), linewidth=2.8, label="하락 시나리오", zorder=4)

    for key, label, color in [
        ("target_1", "상승 확인/1차 목표", "#dc2626"),
        ("support_1", "중립 방어선", "#16a34a"),
        ("stop_loss", "무효화/손절", "#111827"),
    ]:
        value = levels.get(key)
        if value is None:
            continue
        ax.axhline(float(value), color=color, linestyle=":", linewidth=1.1, alpha=0.85)
        ax.text(
            0.992,
            float(value),
            f"{label} {float(value):,.0f}",
            transform=ax.get_yaxis_transform(),
            color=color,
            va="center",
            ha="left",
            fontsize=9.5,
            fontproperties=font_properties,
            bbox={"boxstyle": "round,pad=0.22", "facecolor": "#ffffff", "edgecolor": color, "alpha": 0.92},
        )

    ax.axvline(chart_df.index[-1], color="#94a3b8", linestyle=":", linewidth=1.2)
    ax.text(chart_df.index[-1], current_price, " 현재", color="#111827", fontsize=9.5, va="bottom", fontproperties=font_properties)
    ax.text(
        0.77,
        0.965,
        "점선 구간은 조건부 시나리오",
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=10.5,
        fontproperties=font_properties,
        color="#475569",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#ffffff", "edgecolor": "#cbd5e1", "alpha": 0.92},
    )
    scenario_labels = [
        (scenarios["bullish"][-1], "상승", "#dc2626"),
        (scenarios["neutral"][-1], "중립", "#64748b"),
        (scenarios["bearish"][-1], "하락", "#2563eb"),
    ]
    for y_value, label, color in scenario_labels:
        ax.text(future_index[-1], y_value, f" {label}", color=color, va="center", fontsize=11, fontweight="bold", fontproperties=font_properties)

    ax.set_title(title, fontproperties=font_properties, fontsize=17, fontweight="bold", loc="left", pad=18)
    ax.set_xlabel("날짜", fontproperties=font_properties)
    ax.set_ylabel("가격", fontproperties=font_properties)
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax.grid(True, color="#eef2f7", linewidth=0.9)
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    legend = ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.02), ncol=4, frameon=True, prop=font_properties)
    if legend.get_title():
        legend.get_title().set_fontproperties(font_properties)
    ax.text(
        0.01,
        0.045,
        "미래 구간은 예측이 아니라 조건부 시나리오입니다.\n상승/중립/하락 경로는 조건 확인용이며 실제 가격이 아닙니다.",
        transform=ax.transAxes,
        fontsize=10.5,
        fontproperties=font_properties,
        linespacing=1.35,
        bbox={"boxstyle": "round,pad=0.55", "facecolor": "#f8fafc", "edgecolor": "#64748b", "linewidth": 1.1, "alpha": 0.96},
    )
    _apply_font_to_axes(ax, font_properties)
    for text in fig.texts:
        text.set_fontproperties(font_properties)

    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(output)
