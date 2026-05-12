from __future__ import annotations

from pathlib import Path
from textwrap import wrap
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


def _wrapped(text: str, width: int) -> str:
    if text in {"확인 실패", "데이터 없음"}:
        return text
    return "\n".join(wrap(text, width=width, break_long_words=False, replace_whitespace=False))


def _draw_section_title(ax: Any, x: float, y: float, title: str, font_properties: Any) -> None:
    from matplotlib.patches import FancyBboxPatch

    accent = FancyBboxPatch(
        (x, y - 0.024),
        0.006,
        0.048,
        boxstyle="round,pad=0,rounding_size=0.003",
        linewidth=0,
        facecolor="#2563eb",
        transform=ax.transAxes,
        zorder=2,
    )
    ax.add_patch(accent)
    ax.text(
        x + 0.018,
        y,
        title,
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=15,
        fontweight="bold",
        color="#0f172a",
        fontproperties=font_properties,
        zorder=3,
    )


def _draw_box(
    ax: Any,
    x: float,
    y: float,
    w: float,
    h: float,
    edge: str = "#d8dee9",
    face: str = "#ffffff",
    alpha: float = 1.0,
) -> None:
    from matplotlib.patches import FancyBboxPatch

    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        linewidth=1.0,
        edgecolor=edge,
        facecolor=face,
        alpha=alpha,
        transform=ax.transAxes,
        zorder=1,
    )
    ax.add_patch(box)


def _draw_chip(ax: Any, x: float, y: float, label: str, value: str, font_properties: Any) -> None:
    _draw_box(ax, x, y, 0.145, 0.052, edge="#d6dbea", face="#ffffff")
    ax.text(x + 0.016, y + 0.032, label, transform=ax.transAxes, ha="left", va="center", fontsize=8.8, color="#64748b", fontproperties=font_properties, zorder=3)
    ax.text(x + 0.078, y + 0.027, value, transform=ax.transAxes, ha="center", va="center", fontsize=12, fontweight="bold", color="#111827", fontproperties=font_properties, zorder=3)


def _draw_price_card(
    ax: Any,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    value: str,
    sub_label: str,
    sub_value: str,
    color: str,
    face: str,
    font_properties: Any,
) -> None:
    _draw_box(ax, x, y, w, h, edge="#d8dee9", face=face)
    ax.text(x + 0.02, y + h - 0.035, title, transform=ax.transAxes, ha="left", va="center", fontsize=11.5, fontweight="bold", color=color, fontproperties=font_properties, zorder=3)
    ax.text(x + 0.02, y + h - 0.074, value, transform=ax.transAxes, ha="left", va="center", fontsize=17, fontweight="bold", color="#0f172a", fontproperties=font_properties, zorder=3)
    ax.plot([x + 0.02, x + w - 0.02], [y + 0.048, y + 0.048], transform=ax.transAxes, color="#e5e7eb", linewidth=1, zorder=2)
    ax.text(x + 0.02, y + 0.024, sub_label, transform=ax.transAxes, ha="left", va="center", fontsize=9.5, fontweight="bold", color="#475569", fontproperties=font_properties, zorder=3)
    ax.text(x + w - 0.02, y + 0.024, sub_value, transform=ax.transAxes, ha="right", va="center", fontsize=10.5, fontweight="bold", color=color, fontproperties=font_properties, zorder=3)


def _draw_analysis_card(
    ax: Any,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    text: str,
    color: str,
    font_properties: Any,
    wide: bool = False,
) -> None:
    _draw_box(ax, x, y, w, h, edge="#d8dee9", face="#ffffff")
    ax.text(x + 0.018, y + h - 0.036, f"●  {title}", transform=ax.transAxes, ha="left", va="center", fontsize=10.8, fontweight="bold", color=color, fontproperties=font_properties, zorder=3)
    ax.text(
        x + 0.018,
        y + h - 0.075,
        _wrapped(text, 72 if wide else 29),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10.5,
        color="#1f2937",
        fontproperties=font_properties,
        linespacing=1.45,
        zorder=3,
    )


def render_report_card(data: dict[str, Any], output_path: str | Path) -> str:
    import matplotlib.pyplot as plt

    font_properties = _get_korean_font_properties()
    fig, ax = plt.subplots(figsize=(16, 9), facecolor="#f5f7fb")
    ax.set_axis_off()

    stock_name = _value(data, "stock_name", "종목명 확인 실패")
    ticker = _value(data, "ticker")
    data_as_of = _value(data, "data_as_of")
    recommendation = _value(data, "recommendation", "WATCH")
    confidence = _value(data, "confidence")

    ax.text(0.045, 0.94, stock_name, transform=ax.transAxes, ha="left", va="center", fontsize=22, fontweight="bold", color="#0f172a", fontproperties=font_properties)
    ax.text(0.045, 0.902, f"{ticker}  |  기준일 {data_as_of}", transform=ax.transAxes, ha="left", va="center", fontsize=10.8, color="#64748b", fontproperties=font_properties)
    _draw_box(ax, 0.74, 0.887, 0.215, 0.075, edge="#bfdbfe", face="#eff6ff")
    ax.text(0.755, 0.93, f"Recommendation  {recommendation}", transform=ax.transAxes, ha="left", va="center", fontsize=11.7, fontweight="bold", color="#1e40af", fontproperties=font_properties)
    ax.text(0.755, 0.902, f"Confidence  {confidence}", transform=ax.transAxes, ha="left", va="center", fontsize=10.2, color="#475569", fontproperties=font_properties)

    _draw_section_title(ax, 0.045, 0.84, "주요 가격대", font_properties)
    chip_data = [
        ("현재가", _value(data, "current_price")),
        ("진입", _value(data, "entry_price")),
        ("손절", _value(data, "stop_loss")),
        ("목표1", _value(data, "target_1")),
        ("목표2", _value(data, "target_2")),
    ]
    for index, (label, value) in enumerate(chip_data):
        _draw_chip(ax, 0.045 + index * 0.155, 0.77, label, value, font_properties)

    _draw_price_card(ax, 0.045, 0.61, 0.285, 0.125, "진입가", _value(data, "entry_price"), "Risk/Reward", _value(data, "risk_reward", "데이터 없음"), "#2563eb", "#f8fbff", font_properties)
    _draw_price_card(ax, 0.36, 0.61, 0.285, 0.125, "손절가", _value(data, "stop_loss"), "Risk", _value(data, "risk", "데이터 없음"), "#ef4444", "#fffafa", font_properties)
    _draw_price_card(ax, 0.675, 0.61, 0.28, 0.125, "익절가", _value(data, "target_1"), "Reward", _value(data, "reward", "데이터 없음"), "#16a34a", "#f8fffb", font_properties)

    _draw_section_title(ax, 0.045, 0.545, "상세 분석", font_properties)
    _draw_analysis_card(ax, 0.045, 0.405, 0.91, 0.105, "요약", _value(data, "summary"), "#2563eb", font_properties, wide=True)
    _draw_analysis_card(ax, 0.045, 0.19, 0.285, 0.18, "추세 분석", _value(data, "trend_analysis"), "#d946ef", font_properties)
    _draw_analysis_card(ax, 0.36, 0.19, 0.285, 0.18, "패턴 인식", _value(data, "pattern_analysis"), "#6366f1", font_properties)
    _draw_analysis_card(ax, 0.675, 0.19, 0.28, 0.18, "기술적 지표", _value(data, "indicator_analysis"), "#14b8a6", font_properties)

    _draw_box(ax, 0.045, 0.055, 0.91, 0.105, edge="#fed7aa", face="#fffaf5")
    ax.text(0.07, 0.125, "매매 전략", transform=ax.transAxes, ha="left", va="center", fontsize=12, fontweight="bold", color="#ea580c", fontproperties=font_properties)
    ax.text(
        0.07,
        0.095,
        _wrapped(_value(data, "trade_strategy"), 82),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=11.2,
        fontweight="bold",
        color="#111827",
        fontproperties=font_properties,
        linespacing=1.35,
    )

    ax.text(0.045, 0.02, "투자 참고용 카드이며, 최종 투자 판단과 책임은 사용자에게 있습니다.", transform=ax.transAxes, ha="left", va="center", fontsize=8.8, color="#94a3b8", fontproperties=font_properties)

    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(output)
