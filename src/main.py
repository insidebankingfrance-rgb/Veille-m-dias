from __future__ import annotations

import os
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .config import LINKEDIN_POST_COUNT
from .curator import curate
from .email_sender import build_html, send_email
from .sources import fetch_recent_articles
from .writer import write_linkedin_posts


PARIS_TZ = ZoneInfo("Europe/Paris")
TARGET_HOUR = 7


def _should_run() -> bool:
    if os.environ.get("FORCE_SEND", "").lower() in ("1", "true", "yes"):
        return True
    now_paris = datetime.now(PARIS_TZ)
    if now_paris.hour == TARGET_HOUR:
        return True
    print(f"[main] Paris hour is {now_paris.hour}h, not {TARGET_HOUR}h — skipping. "
          f"Set FORCE_SEND=true to bypass.")
    return False


def run() -> int:
    if not _should_run():
        return 0

    today = date.today()
    print(f"[main] starting daily digest for {today}")

    articles = fetch_recent_articles()
    if not articles:
        print("[main] no articles fetched — aborting")
        return 1

    print("[main] curating top news with Claude...")
    curation = curate(articles)
    if not curation["top_news"]:
        print("[main] curator returned no top news — aborting")
        return 1
    print(f"[main] curator selected {len(curation['top_news'])} articles, "
          f"{len(curation['linkedin_picks'])} for LinkedIn")

    # Build LinkedIn picks input: (index, Article, angle)
    angle_by_index = {meta["index"]: meta["angle"] for meta in curation["top_news"]}
    picks_input = []
    for idx in curation["linkedin_picks"][:LINKEDIN_POST_COUNT]:
        if 0 <= idx < len(articles):
            picks_input.append((idx, articles[idx], angle_by_index.get(idx, "")))

    print(f"[main] writing {len(picks_input)} LinkedIn posts with Claude...")
    posts = write_linkedin_posts(picks_input)
    print(f"[main] generated {len(posts)} posts")

    html_body = build_html(curation, articles, posts, today)
    send_email(html_body, today)
    return 0


if __name__ == "__main__":
    sys.exit(run())
