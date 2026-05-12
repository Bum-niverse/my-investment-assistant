from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import requests


@dataclass
class NewsResult:
    query: str
    source: str | None
    articles: list[dict[str, Any]]
    timestamp: str
    failures: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.articles)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_text(*values: Any) -> str | None:
    for value in values:
        text = _clean_text(value)
        if text:
            return text
    return None


def _extract_yfinance_article(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    content = item.get("content") if isinstance(item.get("content"), dict) else {}
    provider = content.get("provider") if isinstance(content.get("provider"), dict) else {}
    click_through_url = content.get("clickThroughUrl") if isinstance(content.get("clickThroughUrl"), dict) else {}
    canonical_url = content.get("canonicalUrl") if isinstance(content.get("canonicalUrl"), dict) else {}

    title = _first_text(item.get("title"), content.get("title"))
    if not title:
        return None

    published_raw = item.get("providerPublishTime") or content.get("pubDate") or content.get("displayTime")
    published_at = _format_published_at(published_raw)

    source = _first_text(
        item.get("source"),
        item.get("publisher"),
        provider.get("displayName"),
        provider.get("name"),
    )
    link = _first_text(item.get("link"), click_through_url.get("url"), canonical_url.get("url"), content.get("canonicalUrl"))

    return {
        "title": title,
        "source": source,
        "published_at": published_at,
        "link": link,
    }


def _format_published_at(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value).isoformat(timespec="seconds")
        except (OSError, OverflowError, ValueError):
            return None
    return _clean_text(value)


def _valid_articles(articles: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    valid: list[dict[str, Any]] = []
    for article in articles:
        if not isinstance(article, dict):
            continue
        title = _clean_text(article.get("title"))
        if not title:
            continue
        valid.append(
            {
                "title": title,
                "source": _first_text(article.get("source"), article.get("publisher")),
                "published_at": _format_published_at(article.get("published_at")),
                "link": _clean_text(article.get("link")),
            }
        )
        if len(valid) >= limit:
            break
    return valid


def fetch_yfinance_news(ticker: str, limit: int = 5) -> tuple[list[dict[str, Any]], str | None]:
    try:
        import yfinance as yf
    except Exception as exc:
        return [], f"yfinance 뉴스 import 실패: {exc}"

    candidates = [ticker]
    if ticker.isdigit() and len(ticker) == 6:
        candidates.extend([f"{ticker}.KS", f"{ticker}.KQ"])

    errors: list[str] = []
    for candidate in candidates:
        try:
            news_items = yf.Ticker(candidate).news or []
            articles: list[dict[str, Any]] = []
            for item in news_items:
                article = _extract_yfinance_article(item)
                if article:
                    articles.append(article)
                if len(articles) >= limit:
                    break
            if articles:
                return articles, None
            errors.append(f"{candidate}: 유효한 뉴스 제목을 파싱하지 못함")
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")

    return [], "yfinance 뉴스 확인 실패: " + "; ".join(errors)


def fetch_naver_news(query: str, limit: int = 5) -> tuple[list[dict[str, Any]], str | None]:
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        return [], "네이버 뉴스 확인 생략: NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경변수 없음"

    try:
        response = requests.get(
            "https://openapi.naver.com/v1/search/news.json",
            params={"query": query, "display": min(limit, 10), "sort": "date"},
            headers={"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret},
            timeout=10,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
        articles = _valid_articles(
            [
                {
                    "title": item.get("title"),
                    "source": None,
                    "published_at": item.get("pubDate"),
                    "link": item.get("originallink") or item.get("link"),
                }
                for item in items
            ],
            limit=limit,
        )
        if articles:
            return articles, None
        return [], "네이버 뉴스 확인 실패: 유효한 뉴스 제목을 파싱하지 못함"
    except Exception as exc:
        return [], f"네이버 뉴스 확인 실패: {exc}"


def fetch_news(query: str, ticker: str | None = None, limit: int = 5) -> NewsResult:
    timestamp = datetime.now().isoformat(timespec="seconds")
    failures: list[str] = []

    if ticker:
        articles, error = fetch_yfinance_news(ticker, limit=limit)
        valid_articles = _valid_articles(articles, limit=limit)
        if valid_articles:
            return NewsResult(query=query, source="yfinance", articles=valid_articles, timestamp=timestamp, failures=failures)
        if error:
            failures.append(error)

    articles, error = fetch_naver_news(query, limit=limit)
    valid_articles = _valid_articles(articles, limit=limit)
    if valid_articles:
        return NewsResult(query=query, source="naver", articles=valid_articles, timestamp=timestamp, failures=failures)
    if error:
        failures.append(error)
    failures.append("뉴스 확인 실패: 유효한 뉴스 제목을 파싱하지 못함")

    return NewsResult(query=query, source=None, articles=[], timestamp=timestamp, failures=failures)
