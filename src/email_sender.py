from __future__ import annotations

import html
import os
import urllib.parse
from datetime import date

import resend

from .config import GEO_SECTIONS
from .curator import CurationResult
from .sources import Article


CLAUDE_AI_BASE = "https://claude.ai/new"

# Prompt compact embarqué dans l'URL du deep-link (limite ~5-7K chars URL-encoded).
COMPACT_STYLE_BRIEF = """Tu es Richard Michaud (Inside Banking). Tu vulgarises la finance pour des décideurs du secteur, en français.

STYLE À IMITER STRICTEMENT :
- Phrases courtes. Paragraphes courts (1-2 lignes).
- Accroche directe en 1-2 lignes qui pose le sujet.
- Structure : contexte → constat → points clés (flèches → et puces colorées 🟢🔴🟣🟠 pour distinguer acteurs/angles) → synthèse stratégique → ouverture.
- Chiffres précis (Md€, %, dates) systématiques quand l'article les fournit.
- Connecteurs récurrents : "Le point commun ?", "Les différences ?", "Les sujets à avoir en tête 👇".
- Clôture par "À suivre 🚀" ou une question stratégique ouverte.
- 250 à 450 mots par post. Pas de hashtags. Pas de "Bonjour LinkedIn".
- 1ère personne avec parcimonie ("Je décrypte", "À mon sens"…).
- N'invente JAMAIS de chiffres ou faits hors article ; si l'info manque, reste plus généraliste.

Pour CHAQUE article ci-dessous, rédige UN post LinkedIn complet, prêt à publier dans mon style."""


def _esc(s: str) -> str:
    return html.escape(s or "")


def _section_html(geo: str, items: list[tuple[Article, dict]]) -> str:
    if not items:
        return ""
    cards = []
    for art, meta in items:
        score = meta.get("relevance_score", "")
        cards.append(f"""
            <div style="margin-bottom:22px;padding-bottom:18px;border-bottom:1px solid #e5e7eb;">
              <div style="font-size:11px;letter-spacing:0.5px;text-transform:uppercase;color:#6b7280;margin-bottom:6px;">
                {_esc(art.source)} · {_esc(art.section)} · pertinence {score}/100
              </div>
              <a href="{_esc(art.link)}" style="color:#0f172a;text-decoration:none;">
                <div style="font-size:17px;font-weight:600;line-height:1.35;margin-bottom:8px;color:#0f172a;">
                  {_esc(art.title)}
                </div>
              </a>
              <div style="font-size:14px;color:#374151;line-height:1.5;margin-bottom:10px;">
                {_esc(art.summary)}
              </div>
              <a href="{_esc(art.link)}" style="font-size:13px;color:#1e3a8a;text-decoration:underline;">
                Lire l'article →
              </a>
            </div>
        """)
    return f"""
        <h2 style="font-size:20px;color:#0f172a;border-bottom:2px solid #1e3a8a;padding-bottom:6px;margin:32px 0 16px;">
          {_esc(geo)}
        </h2>
        {''.join(cards)}
    """


def _build_linkedin_prompt(picks: list[Article]) -> str:
    """Construit le prompt complet à coller dans Claude.ai pour générer les 3 posts."""
    parts = [COMPACT_STYLE_BRIEF, "", "ARTICLES SÉLECTIONNÉS POUR AUJOURD'HUI :", ""]
    for i, art in enumerate(picks, 1):
        parts.append(f"--- ARTICLE {i} ---")
        parts.append(f"Source : {art.source} ({art.section})")
        parts.append(f"Titre : {art.title}")
        parts.append(f"Résumé : {art.summary or '(résumé non fourni par le flux)'}")
        parts.append(f"Lien : {art.link}")
        parts.append("")
    parts.append("Rédige les 3 posts maintenant, séparés clairement (Post 1, Post 2, Post 3).")
    return "\n".join(parts)


def _claude_cta_html(picks: list[Article]) -> str:
    if not picks:
        return ""

    prompt_text = _build_linkedin_prompt(picks)
    deep_link = f"{CLAUDE_AI_BASE}?q={urllib.parse.quote(prompt_text)}"

    picks_summary = "".join(
        f"<li style='margin-bottom:6px;'><strong>{_esc(art.source)}</strong> — "
        f"<a href='{_esc(art.link)}' style='color:#1e3a8a;'>{_esc(art.title)}</a></li>"
        for art in picks
    )

    return f"""
        <h2 style="font-size:20px;color:#0f172a;border-bottom:2px solid #1e3a8a;padding-bottom:6px;margin:40px 0 16px;">
          ✍️ Générer 3 posts LinkedIn
        </h2>

        <div style="font-size:14px;color:#374151;line-height:1.5;margin-bottom:14px;">
          Les 3 articles les plus pertinents pour ta ligne éditoriale :
        </div>
        <ol style="font-size:14px;color:#0f172a;line-height:1.5;padding-left:20px;margin:0 0 20px 0;">
          {picks_summary}
        </ol>

        <div style="text-align:center;margin:24px 0;">
          <a href="{_esc(deep_link)}"
             style="display:inline-block;background:#1e3a8a;color:#ffffff;padding:14px 28px;
                    font-size:15px;font-weight:600;text-decoration:none;border-radius:6px;">
            🚀 Générer les 3 posts dans Claude.ai
          </a>
        </div>

        <div style="font-size:12px;color:#6b7280;text-align:center;margin-bottom:24px;">
          Le bouton ouvre Claude.ai avec un prompt pré-rempli — il suffit d'envoyer.
        </div>

        <details style="margin-top:24px;padding:16px;background:#f8fafc;border-left:4px solid #1e3a8a;border-radius:4px;">
          <summary style="cursor:pointer;font-size:13px;font-weight:600;color:#1e3a8a;letter-spacing:0.3px;text-transform:uppercase;">
            Voir / copier le prompt complet (pour relancer manuellement)
          </summary>
          <pre style="margin:14px 0 0;padding:14px;background:#ffffff;border:1px solid #e5e7eb;border-radius:4px;
                      font-family:Menlo,Consolas,monospace;font-size:12px;line-height:1.5;color:#0f172a;
                      white-space:pre-wrap;word-break:break-word;max-width:100%;overflow-x:auto;">{_esc(prompt_text)}</pre>
        </details>
    """


def build_html(
    curation: CurationResult,
    articles: list[Article],
    today: date,
) -> str:
    articles_by_index = {i: art for i, art in enumerate(articles)}

    grouped: dict[str, list[tuple[Article, dict]]] = {g: [] for g in GEO_SECTIONS}
    sorted_top = sorted(curation["top_news"], key=lambda x: x.get("rank", 99))
    for meta in sorted_top:
        idx = meta["index"]
        if idx not in articles_by_index:
            continue
        geo = meta["geo"]
        if geo in grouped:
            grouped[geo].append((articles_by_index[idx], meta))

    sections_html = "".join(_section_html(geo, grouped[geo]) for geo in GEO_SECTIONS)

    picks = [articles_by_index[i] for i in curation["linkedin_picks"] if i in articles_by_index]
    cta_html = _claude_cta_html(picks)

    date_str = today.strftime("%A %d %B %Y")
    fr_months = {
        "January": "janvier", "February": "février", "March": "mars",
        "April": "avril", "May": "mai", "June": "juin",
        "July": "juillet", "August": "août", "September": "septembre",
        "October": "octobre", "November": "novembre", "December": "décembre",
    }
    fr_days = {
        "Monday": "lundi", "Tuesday": "mardi", "Wednesday": "mercredi",
        "Thursday": "jeudi", "Friday": "vendredi", "Saturday": "samedi", "Sunday": "dimanche",
    }
    for en, fr in {**fr_months, **fr_days}.items():
        date_str = date_str.replace(en, fr)

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Veille Inside Banking — {date_str}</title>
</head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
  <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f3f4f6;">
    <tr>
      <td align="center" style="padding:32px 16px;">
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width:680px;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
          <tr>
            <td style="padding:32px 36px 24px;border-bottom:3px solid #1e3a8a;">
              <div style="font-size:12px;letter-spacing:1.5px;text-transform:uppercase;color:#1e3a8a;font-weight:600;">
                Inside Banking · Veille du jour
              </div>
              <h1 style="font-size:26px;color:#0f172a;margin:8px 0 4px;font-weight:700;">
                {date_str}
              </h1>
              <div style="font-size:14px;color:#6b7280;">
                Top {len(sorted_top)} actualités finance · {len(picks)} candidats LinkedIn
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 36px 36px;">
              {sections_html}
              {cta_html}
              <div style="margin-top:32px;padding-top:20px;border-top:1px solid #e5e7eb;font-size:11px;color:#9ca3af;text-align:center;">
                Veille générée automatiquement · Sources : Les Échos, Bloomberg, FT, Reuters
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_email(html_body: str, today: date) -> None:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not set")
    resend.api_key = api_key

    # `or` instead of dict default so we also fall back when the env var is set but empty
    # (GitHub Actions injects "" when a `vars.X` reference resolves to undefined).
    recipient = os.environ.get("DIGEST_RECIPIENT") or "inside.banking.france@gmail.com"
    sender = os.environ.get("DIGEST_SENDER") or "Veille Inside Banking <onboarding@resend.dev>"

    date_str = today.strftime("%d/%m/%Y")
    subject = f"Veille Inside Banking — {date_str}"

    params: resend.Emails.SendParams = {
        "from": sender,
        "to": [recipient],
        "subject": subject,
        "html": html_body,
    }
    result = resend.Emails.send(params)
    print(f"[email] sent: id={result.get('id')} to={recipient}")
