from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path


DEFAULT_CHUNK_SIZE = 900


def _collapse_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _first_match(pattern: str, text: str, default: str = "확인 실패", *, dotall: bool = True) -> str:
    flags = re.MULTILINE | (re.DOTALL if dotall else 0)
    match = re.search(pattern, text, flags=flags)
    if not match:
        return default
    return _collapse_spaces(match.group(1))


def _section(text: str, heading: str) -> str:
    pattern = rf"(^#+\s+{re.escape(heading)}.*?)(?=^#+\s+|\Z)"
    return _first_match(pattern, text, default="", dotall=True)


def _subsection(text: str, heading: str) -> str:
    lines = text.splitlines()
    start: int | None = None
    start_level = 0
    for index, line in enumerate(lines):
        match = re.match(r"^(#+)\s+(.+?)\s*$", line)
        if match and match.group(2) == heading:
            start = index + 1
            start_level = len(match.group(1))
            break
    if start is None:
        return ""

    end = len(lines)
    for index in range(start, len(lines)):
        match = re.match(r"^(#+)\s+(.+?)\s*$", lines[index])
        if match and len(match.group(1)) <= start_level:
            end = index
            break
    return _collapse_spaces("\n".join(lines[start:end]))


def _table_value(text: str, label: str) -> str:
    pattern = rf"^\|\s*{re.escape(label)}\s*\|\s*([^|]+?)\s*\|"
    return _first_match(pattern, text, dotall=False)


def build_kakao_summary(report_text: str, *, max_chars: int = 1700) -> str:
    title = _first_match(r"^#\s+([^\n]+)$", report_text, "투자 분석 리포트", dotall=False)
    recommendation = _first_match(r"^- Recommendation:\s*([^\n]+)$", report_text, dotall=False)
    confidence = _first_match(r"^- Confidence:\s*([^\n]+)$", report_text, dotall=False)
    current_price = _table_value(report_text, "현재가")
    entry = _table_value(report_text, "진입 후보")
    support_1 = _table_value(report_text, "1차 지지선")
    support_2 = _table_value(report_text, "2차 지지선")
    resistance_1 = _table_value(report_text, "1차 저항선")
    resistance_2 = _table_value(report_text, "2차 저항선")
    stop_loss = _table_value(report_text, "손절 기준")
    target_1 = _table_value(report_text, "1차 목표가")
    target_2 = _table_value(report_text, "2차 목표가")

    next_probability = _first_match(
        r"★\s*자동 분석 결과\s*-\s*다음 봉 예측:\s*([^\n]+)$",
        report_text,
        default="",
        dotall=False,
    )
    if not next_probability:
        next_probability = _subsection(report_text, "다음 거래일/금일 캔들 확률")[:280] or "확인 실패"

    buy_plan = _subsection(report_text, "추가매수 전략") or _subsection(report_text, "신규 진입자")
    exit_plan = _subsection(report_text, "손절/익절 전략") or _subsection(report_text, "손절/익절")
    risk = _section(report_text, "리스크 관리")

    new_entry = _subsection(report_text, "신규 진입자")
    risk = re.sub(r"^#+\s+리스크 관리\s*", "", risk)

    summary = (
        f"[투자 리포트 핵심요약]\n"
        f"{title}\n"
        f"판단: {recommendation} / 신뢰도 {confidence}\n"
        f"현재가: {current_price}\n"
        f"타점: {entry}\n"
        f"지지: 1차 {support_1} / 2차 {support_2}\n"
        f"저항: 1차 {resistance_1} / 2차 {resistance_2}\n"
        f"손절: {stop_loss}\n"
        f"목표: 1차 {target_1} / 2차 {target_2}\n"
        f"다음 봉 확률: {next_probability}\n"
        f"진입 판단: {_collapse_spaces(new_entry)[:260] or '추격매수보다 눌림목/지지 확인 후 분할 접근. 저항 돌파 전 전액 진입은 비추천.'}\n"
        f"추매 계획: {_collapse_spaces(buy_plan)[:360] or '확인 실패'}\n"
        f"손절/익절: {_collapse_spaces(exit_plan)[:260] or '확인 실패'}\n"
        f"리스크: {_collapse_spaces(risk)[:240] or '손절 기준 이탈, 거래량 없는 반등, 과열 구간 추격매수 주의'}"
    )

    if len(summary) <= max_chars:
        return summary
    return summary[: max_chars - 40].rstrip() + " ... 자세한 내용은 analysis.md 확인"


def _chunk_text(text: str, chunk_size: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)] or [""]


def send_report_to_kakao_me(
    report_path: str | Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    kakaocli_path: str | None = None,
    summary_only: bool = True,
) -> list[str]:
    report = Path(report_path).expanduser().resolve()
    if not report.exists():
        raise FileNotFoundError(f"analysis.md 파일을 찾을 수 없습니다: {report}")
    if not report.is_file():
        raise ValueError(f"전송 대상이 파일이 아닙니다: {report}")

    command = kakaocli_path or shutil.which("kakaocli")
    if command is None:
        raise RuntimeError("kakaocli를 찾을 수 없습니다. KakaoTalk Mac CLI 설치와 권한 설정이 필요합니다.")

    content = report.read_text(encoding="utf-8")
    if summary_only:
        content = build_kakao_summary(content)
    chunks = _chunk_text(content, chunk_size)
    total = len(chunks)
    sent_messages: list[str] = []

    for index, chunk in enumerate(chunks, start=1):
        header = f"[투자 분석 요약] {report.name} ({index}/{total})\n"
        message = header + chunk
        try:
            subprocess.run(
                [command, "send", "_", message, "--me"],
                check=True,
                text=True,
                capture_output=True,
                timeout=45,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            stdout = (exc.stdout or "").strip()
            detail = stderr or stdout or str(exc)
            raise RuntimeError(f"KakaoTalk 전송 실패 ({index}/{total}): {detail}") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"KakaoTalk 전송 시간 초과 ({index}/{total}): 메시지가 너무 길거나 UI 자동화가 멈췄습니다") from exc
        sent_messages.append(f"{report.name} {index}/{total} 전송 완료")

    return sent_messages


def main() -> None:
    parser = argparse.ArgumentParser(description="Send an investment analysis markdown report to KakaoTalk 'me'.")
    parser.add_argument("report_path", nargs="?", default="analysis.md", help="Markdown report path to send")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help="Message chunk size")
    parser.add_argument("--kakaocli-path", default=None, help="Optional kakaocli binary path")
    parser.add_argument("--full", action="store_true", help="Send full markdown instead of dense KakaoTalk summary")
    args = parser.parse_args()

    try:
        results = send_report_to_kakao_me(
            args.report_path,
            chunk_size=args.chunk_size,
            kakaocli_path=args.kakaocli_path,
            summary_only=not args.full,
        )
    except Exception as exc:
        raise SystemExit(f"카카오톡 나에게 보내기 실패: {exc}") from exc

    for result in results:
        print(result)


if __name__ == "__main__":
    main()
