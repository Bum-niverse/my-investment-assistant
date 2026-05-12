from __future__ import annotations

from pathlib import Path
from typing import Any

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


def _spread_label_positions(values: list[float], min_gap_ratio: float = 0.035) -> dict[float, float]:
    if not values:
        return {}
    unique_values = sorted(set(float(value) for value in values))
    y_min = min(unique_values)
    y_max = max(unique_values)
    span = max(y_max - y_min, abs(y_max) * 0.05, 1.0)
    min_gap = span * min_gap_ratio
    adjusted: list[float] = []
    for value in unique_values:
        if adjusted and value - adjusted[-1] < min_gap:
            adjusted.append(adjusted[-1] + min_gap)
        else:
            adjusted.append(value)
    return dict(zip(unique_values, adjusted))


def _prepare_chart_data(df: pd.DataFrame) -> pd.DataFrame:
    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"차트 렌더링 필수 컬럼 누락: {', '.join(missing)}")
    chart_df = df[required].apply(pd.to_numeric, errors="coerce").dropna().copy()
    if len(chart_df) < 30:
        raise ValueError("차트 이미지 생성을 위한 OHLCV 데이터가 30개 미만입니다")
    if not isinstance(chart_df.index, pd.DatetimeIndex):
        chart_df.index = pd.to_datetime(chart_df.index)
    return chart_df.tail(180)


def render_annotated_chart(
    df: pd.DataFrame,
    levels: dict[str, Any],
    output_path: str | Path,
    title: str,
    summary: str,
) -> str:
    try:
        import mplfinance as mpf
    except Exception as exc:
        raise RuntimeError(f"mplfinance import 실패: {exc}") from exc

    font_properties = _get_korean_font_properties()
    chart_df = _prepare_chart_data(df)

    for window in (5, 20, 60, 120):
        chart_df[f"MA{window}"] = chart_df["Close"].rolling(window, min_periods=1).mean()

    add_plots = [
        mpf.make_addplot(chart_df["MA5"], color="#16a34a", width=1.0),
        mpf.make_addplot(chart_df["MA20"], color="#dc2626", width=1.0),
        mpf.make_addplot(chart_df["MA60"], color="#f97316", width=1.0),
        mpf.make_addplot(chart_df["MA120"], color="#7c3aed", width=1.0),
    ]

    style = mpf.make_mpf_style(
        base_mpf_style="yahoo",
        marketcolors=mpf.make_marketcolors(up="#ef4444", down="#2563eb", edge="inherit", wick="inherit", volume="inherit"),
        gridstyle="-",
        gridcolor="#eef2f7",
        facecolor="#ffffff",
        figcolor="#ffffff",
    )

    fig, axes = mpf.plot(
        chart_df,
        type="candle",
        volume=True,
        addplot=add_plots,
        style=style,
        figsize=(16, 9),
        returnfig=True,
        panel_ratios=(5, 1.35),
        tight_layout=True,
    )

    ax_price = axes[0]
    ax_volume = axes[2] if len(axes) > 2 else axes[-1]
    fig.subplots_adjust(top=0.91, bottom=0.09, left=0.055, right=0.89, hspace=0.08)
    fig.suptitle(title, x=0.055, y=0.975, ha="left", fontproperties=font_properties, fontsize=17, fontweight="bold", color="#111827")
    ax_price.set_title("")
    ax_price.set_ylabel("가격", fontproperties=font_properties)
    ax_volume.set_ylabel("거래량", fontproperties=font_properties)
    ax_price.yaxis.tick_right()
    ax_price.yaxis.set_label_position("right")
    ax_volume.yaxis.tick_right()
    ax_volume.yaxis.set_label_position("right")
    ax_price.grid(True, color="#eef2f7", linewidth=0.9)
    ax_volume.grid(True, axis="y", color="#eef2f7", linewidth=0.9)
    ax_price.spines["bottom"].set_color("#cbd5e1")
    ax_volume.spines["top"].set_color("#cbd5e1")
    line_specs = [
        ("resistance_2", "2차 저항", "#991b1b", "-"),
        ("resistance_1", "1차 저항", "#dc2626", "-"),
        ("target_2", "2차 목표", "#c2410c", "--"),
        ("target_1", "1차 목표", "#ea580c", "--"),
        ("entry_price", "진입 후보", "#0891b2", "--"),
        ("support_1", "1차 지지", "#16a34a", "-"),
        ("support_2", "2차 지지", "#15803d", "-"),
        ("stop_loss", "손절 기준", "#111827", ":"),
    ]

    label_values = [float(levels[key]) for key, *_ in line_specs if levels.get(key) is not None]
    if label_values:
        y_min = min(float(chart_df["Low"].min()), min(label_values))
        y_max = max(float(chart_df["High"].max()), max(label_values))
        y_margin = max((y_max - y_min) * 0.08, abs(y_max) * 0.015, 1.0)
        ax_price.set_ylim(y_min - y_margin, y_max + y_margin)
    label_y_positions = _spread_label_positions(label_values)
    from matplotlib import transforms
    from matplotlib.lines import Line2D

    ma_legend = [
        Line2D([0], [0], color="#16a34a", linewidth=1.4, label="MA5"),
        Line2D([0], [0], color="#dc2626", linewidth=1.4, label="MA20"),
        Line2D([0], [0], color="#f97316", linewidth=1.4, label="MA60"),
        Line2D([0], [0], color="#7c3aed", linewidth=1.4, label="MA120"),
    ]
    ax_price.legend(handles=ma_legend, loc="upper left", bbox_to_anchor=(0.0, 1.02), ncol=4, frameon=True, prop=font_properties)

    right_label_transform = transforms.blended_transform_factory(ax_price.transAxes, ax_price.transData)
    for key, label, color, linestyle in line_specs:
        value = levels.get(key)
        if value is None:
            continue
        value = float(value)
        label_y = label_y_positions.get(value, value)
        ax_price.axhline(value, color=color, linestyle=linestyle, linewidth=1.35, alpha=0.9)
        if label_y != value:
            ax_price.plot([0.965, 0.985], [value, label_y], transform=right_label_transform, color=color, linewidth=0.8, alpha=0.65)
        ax_price.text(
            0.992,
            label_y,
            f"{label} {value:,.0f}",
            transform=right_label_transform,
            color=color,
            fontsize=9.5,
            ha="left",
            va="center",
            fontproperties=font_properties,
            bbox={"boxstyle": "round,pad=0.22", "facecolor": "#ffffff", "edgecolor": color, "alpha": 0.92},
        )

    ax_price.text(
        0.01,
        0.965,
        summary,
        transform=ax_price.transAxes,
        va="top",
        ha="left",
        fontsize=10.5,
        fontproperties=font_properties,
        color="#111827",
        linespacing=1.35,
        bbox={"boxstyle": "round,pad=0.65", "facecolor": "#f8fafc", "edgecolor": "#64748b", "linewidth": 1.1, "alpha": 0.96},
    )

    ax_price.text(
        0.985,
        0.965,
        "검증 데이터 분석",
        transform=ax_price.transAxes,
        va="top",
        ha="right",
        fontsize=10,
        fontproperties=font_properties,
        color="#475569",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#ffffff", "edgecolor": "#cbd5e1", "alpha": 0.9},
    )

    for axis in axes:
        _apply_font_to_axes(axis, font_properties)
    for text in fig.texts:
        text.set_fontproperties(font_properties)

    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")

    import matplotlib.pyplot as plt

    plt.close(fig)
    return str(output)
