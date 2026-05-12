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
            for item in news_items[:limit]:
                published = item.get("providerPublishTime")
                published_at = datetime.fromtimestamp(published).isoformat(timespec="seconds") if published else None
                articles.append(
                    {
                        "title": item.get("title"),
                        "publisher": item.get("publisher"),
                        "published_at": published_at,
                        "link": item.get("link"),
                    }
                )
            if articles:
                return articles, None
            errors.append(f"{candidate}: 뉴스 데이터 없음")
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
        articles = [
            {
                "title": item.get("title"),
                "publisher": None,
                "published_at": item.get("pubDate"),
                "link": item.get("originallink") or item.get("link"),
            }
            for item in items[:limit]
        ]
        if articles:
            return articles, None
        return [], "네이버 뉴스 확인 실패: 검색 결과 없음"
    except Exception as exc:
        return [], f"네이버 뉴스 확인 실패: {exc}"


def fetch_news(query: str, ticker: str | None = None, limit: int = 5) -> NewsResult:
    timestamp = datetime.now().isoformat(timespec="seconds")
    failures: list[str] = []

    if ticker:
        articles, error = fetch_yfinance_news(ticker, limit=limit)
        if articles:
            return NewsResult(query=query, source="yfinance", articles=articles, timestamp=timestamp, failures=failures)
        if error:
            failures.append(error)

    articles, error = fetch_naver_news(query, limit=limit)
    if articles:
        return NewsResult(query=query, source="naver", articles=articles, timestamp=timestamp, failures=failures)
    if error:
        failures.append(error)

    return NewsResult(query=query, source=None, articles=[], timestamp=timestamp, failures=failures)
