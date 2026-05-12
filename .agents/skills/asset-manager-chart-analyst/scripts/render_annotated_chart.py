from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


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


def _configure_korean_font() -> None:
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    available_fonts = {font.name for font in font_manager.fontManager.ttflist}
    for font_name in ["AppleGothic", "Malgun Gothic", "NanumGothic", "DejaVu Sans"]:
        if font_name in available_fonts:
            plt.rcParams["font.family"] = font_name
            break
    plt.rcParams["axes.unicode_minus"] = False


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

    _configure_korean_font()
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
        gridcolor="#e5e7eb",
        facecolor="#ffffff",
    )

    fig, axes = mpf.plot(
        chart_df,
        type="candle",
        volume=True,
        addplot=add_plots,
        style=style,
        title=title,
        figsize=(14, 9),
        returnfig=True,
        panel_ratios=(4, 1),
        tight_layout=True,
    )

    ax_price = axes[0]
    line_specs = [
        ("support_1", "1차 지지", "#16a34a"),
        ("support_2", "2차 지지", "#15803d"),
        ("resistance_1", "1차 저항", "#dc2626"),
        ("resistance_2", "2차 저항", "#991b1b"),
        ("entry_price", "진입가", "#0891b2"),
        ("stop_loss", "손절가", "#111827"),
        ("target_1", "1차 목표", "#ea580c"),
        ("target_2", "2차 목표", "#c2410c"),
    ]

    right_x = len(chart_df) - 1
    for key, label, color in line_specs:
        value = levels.get(key)
        if value is None:
            continue
        value = float(value)
        ax_price.axhline(value, color=color, linestyle="--", linewidth=1.0, alpha=0.85)
        ax_price.annotate(
            f"{label} {value:,.0f}",
            xy=(right_x, value),
            xytext=(8, 0),
            textcoords="offset points",
            color=color,
            fontsize=9,
            va="center",
        )

    ax_price.text(
        0.01,
        0.97,
        summary,
        transform=ax_price.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.5", "facecolor": "#f8fafc", "edgecolor": "#94a3b8", "alpha": 0.92},
    )

    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")

    import matplotlib.pyplot as plt

    plt.close(fig)
    return str(output)
