from __future__ import annotations

import os
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .curator import curate
from .email_sender import build_html, send_email
from .sources import fetch_recent_articles


PARIS_TZ = ZoneInfo("Europe/Paris")
SENT_MARKER = Path(".sent-marker")
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
        # Flux RSS injoignables — cas rare. On sort proprement (exit 0) pour
        # ne PAS déclencher le mail d'échec GitHub. Pas de veille ce jour-là.
        print("[main] no articles fetched (RSS unreachable?) — no email, exiting cleanly")
        return 0

    print("[main] running heuristic curation...")
    curation = curate(articles)
    if not curation["top_news"]:
        # Aucun article finance pertinent (même en mode élargi, tout à score 0).
        # On sort proprement sans mail d'échec plutôt que d'envoyer du hors-sujet.
        print("[main] no relevant finance news today (all articles scored 0) — "
              "no email, exiting cleanly")
        return 0

    mode = "élargi (jour calme)" if curation.get("relaxed") else "normal"
    print(f"[main] curator selected {len(curation['top_news'])} articles "
          f"(mode {mode}), {len(curation['linkedin_picks'])} LinkedIn candidates")

    html_body = build_html(curation, articles, today)
    send_email(html_body, today)

    # Marqueur d'envoi effectif — le workflow s'en sert pour le dedup via cache.
    # N'est écrit QUE si send_email() a réussi (pas de fallback sur les guards).
    SENT_MARKER.write_text(
        datetime.now(PARIS_TZ).isoformat(timespec="seconds"),
        encoding="utf-8",
    )
    print(f"[main] sent-marker written to {SENT_MARKER}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
