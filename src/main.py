from __future__ import annotations

import os
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .curator import curate
from .email_sender import build_html, send_email
from .sources import fetch_recent_articles


PARIS_TZ = ZoneInfo("Europe/Paris")
# Fenêtre d'envoi acceptée : matin élargi pour tolérer les retards de cron GitHub.
# Observé : les crons GitHub peuvent être retardés de 4 à 6h (best-effort). On
# accepte donc tout déclenchement entre 5h et 14h Paris pour qu'un cron retardé
# envoie quand même la veille, plutôt que d'être silencieusement sauté.
ALLOWED_PARIS_HOURS = range(5, 15)  # 5h, 6h, …, 14h inclus


def _should_run() -> bool:
    if os.environ.get("FORCE_SEND", "").lower() in ("1", "true", "yes"):
        return True
    now_paris = datetime.now(PARIS_TZ)
    if now_paris.hour in ALLOWED_PARIS_HOURS:
        return True
    print(f"[main] Paris hour is {now_paris.hour}h, outside allowed window "
          f"{ALLOWED_PARIS_HOURS.start}-{ALLOWED_PARIS_HOURS.stop - 1}h — skipping. "
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

    print("[main] running heuristic curation...")
    curation = curate(articles)
    if not curation["top_news"]:
        print("[main] curator returned no top news — aborting")
        return 1
    print(f"[main] curator selected {len(curation['top_news'])} articles, "
          f"{len(curation['linkedin_picks'])} LinkedIn candidates")

    html_body = build_html(curation, articles, today)
    send_email(html_body, today)
    return 0


if __name__ == "__main__":
    sys.exit(run())
