from __future__ import annotations

import html
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Iterable

import feedparser
from dateutil import parser as date_parser

from .config import LOOKBACK_HOURS, RSS_SOURCES


@dataclass
class Article:
    title: str
    summary: str
    link: str
    source: str
    section: str
    published: datetime

    def to_dict(self) -> dict:
        d = asdict(self)
        d["published"] = self.published.isoformat()
        return d


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = _TAG_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text)
    return text.strip()


def _parse_date(entry) -> datetime | None:
    for field in ("published", "updated", "pubDate"):
        value = entry.get(field)
        if not value:
            continue
        try:
            dt = date_parser.parse(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


def _fetch_feed(source: str, section: str, url: str, cutoff: datetime) -> list[Article]:
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"[sources] failed to parse {source}/{section}: {e}")
        return []

    articles: list[Article] = []
    for entry in feed.entries:
        published = _parse_date(entry)
        if published is None or published < cutoff:
            continue
        title = _clean(entry.get("title", ""))
        summary = _clean(entry.get("summary", "") or entry.get("description", ""))
        link = entry.get("link", "").strip()
        if not title or not link:
            continue
        articles.append(Article(
            title=title,
            summary=summary[:600],
            link=link,
            source=source,
            section=section,
            published=published,
        ))
    return articles


def _dedupe(articles: Iterable[Article]) -> list[Article]:
    seen_links: set[str] = set()
    seen_titles: set[str] = set()
    out: list[Article] = []
    for art in sorted(articles, key=lambda a: a.published, reverse=True):
        title_key = re.sub(r"\W+", "", art.title.lower())[:80]
        if art.link in seen_links or title_key in seen_titles:
            continue
        seen_links.add(art.link)
        seen_titles.add(title_key)
        out.append(art)
    return out


def fetch_recent_articles() -> list[Article]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    all_articles: list[Article] = []
    for source, section, url in RSS_SOURCES:
        items = _fetch_feed(source, section, url, cutoff)
        print(f"[sources] {source}/{section}: {len(items)} articles")
        all_articles.extend(items)
    deduped = _dedupe(all_articles)
    print(f"[sources] total after dedup: {len(deduped)}")
    return deduped
