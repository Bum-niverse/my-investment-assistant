from __future__ import annotations

from pathlib import Path
from typing import Any


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


def _value(data: dict[str, Any], key: str, default: str = "확인 실패") -> str:
    value = data.get(key)
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _draw_card(ax: Any, x: float, y: float, w: float, h: float, title: str, font_properties: Any) -> None:
    from matplotlib.patches import FancyBboxPatch

    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        linewidth=1.0,
        edgecolor="#d8dee9",
        facecolor="#ffffff",
        transform=ax.transAxes,
        zorder=1,
    )
    ax.add_patch(box)
    ax.text(
        x + 0.025,
        y + h - 0.055,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=14,
        fontweight="bold",
        color="#1f2937",
        fontproperties=font_properties,
        zorder=2,
    )


def _draw_metric_rows(
    ax: Any,
    rows: list[tuple[str, str]],
    x: float,
    y_top: float,
    row_gap: float,
    font_properties: Any,
) -> None:
    for index, (label, value) in enumerate(rows):
        y = y_top - index * row_gap
        ax.text(
            x,
            y,
            label,
            transform=ax.transAxes,
            ha="left",
            va="center",
            fontsize=11,
            color="#64748b",
            fontproperties=font_properties,
            zorder=2,
        )
        ax.text(
            x + 0.22,
            y,
            value,
            transform=ax.transAxes,
            ha="left",
            va="center",
            fontsize=12.5,
            fontweight="bold",
            color="#111827",
            fontproperties=font_properties,
            zorder=2,
        )


def render_report_card(data: dict[str, Any], output_path: str | Path) -> str:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    font_properties = _get_korean_font_properties()

    fig, ax = plt.subplots(figsize=(16, 9), facecolor="#f4f7fb")
    ax.set_axis_off()

    ax.text(
        0.045,
        0.93,
        _value(data, "stock_name", "종목명 확인 실패"),
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=24,
        fontweight="bold",
        color="#111827",
        fontproperties=font_properties,
    )
    ax.text(
        0.045,
        0.885,
        f"Ticker: {_value(data, 'ticker')}   기준일: {_value(data, 'data_as_of')}",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=11.5,
        color="#64748b",
        fontproperties=font_properties,
    )

    recommendation = _value(data, "recommendation", "WATCH")
    confidence = _value(data, "confidence", "확인 실패")
    badge = FancyBboxPatch(
        (0.72, 0.875),
        0.23,
        0.085,
        boxstyle="round,pad=0.012,rounding_size=0.025",
        linewidth=1.0,
        edgecolor="#dbeafe",
        facecolor="#eff6ff",
        transform=ax.transAxes,
    )
    ax.add_patch(badge)
    ax.text(
        0.735,
        0.918,
        f"Recommendation  {recommendation}",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=12.5,
        fontweight="bold",
        color="#1e40af",
        fontproperties=font_properties,
    )
    ax.text(
        0.735,
        0.888,
        f"Confidence  {confidence}",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=11,
        color="#475569",
        fontproperties=font_properties,
    )

    _draw_card(ax, 0.045, 0.45, 0.43, 0.36, "핵심 가격대", font_properties)
    price_rows = [
        ("현재가", _value(data, "current_price")),
        ("진입 후보", _value(data, "entry_price")),
        ("손절가", _value(data, "stop_loss")),
        ("1차 목표가", _value(data, "target_1")),
        ("2차 목표가", _value(data, "target_2")),
    ]
    _draw_metric_rows(ax, price_rows, 0.075, 0.72, 0.055, font_properties)

    _draw_card(ax, 0.525, 0.45, 0.43, 0.36, "기술지표", font_properties)
    indicator_rows = [
        ("RSI", _value(data, "rsi")),
        ("MACD", _value(data, "macd")),
        ("Bollinger", _value(data, "bollinger")),
        ("MA 배열", _value(data, "ma_status")),
    ]
    _draw_metric_rows(ax, indicator_rows, 0.555, 0.72, 0.065, font_properties)

    _draw_card(ax, 0.045, 0.105, 0.91, 0.27, "운용 코멘트", font_properties)
    comments = [
        ("신규 진입자 전략", _value(data, "new_entry_strategy")),
        ("보유자 전략", _value(data, "holder_strategy")),
        ("리스크 관리", _value(data, "risk_management")),
    ]
    for index, (label, value) in enumerate(comments):
        y = 0.295 - index * 0.073
        ax.text(
            0.075,
            y,
            label,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=11.5,
            fontweight="bold",
            color="#334155",
            fontproperties=font_properties,
        )
        ax.text(
            0.22,
            y,
            value,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=11.2,
            color="#111827",
            fontproperties=font_properties,
            wrap=True,
        )

    ax.text(
        0.045,
        0.045,
        "본 리포트 카드는 투자 참고용이며, 최종 투자 판단과 책임은 사용자에게 있습니다.",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=9.5,
        color="#94a3b8",
        fontproperties=font_properties,
    )

    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(output)
