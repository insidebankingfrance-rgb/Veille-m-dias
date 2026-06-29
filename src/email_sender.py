from __future__ import annotations

import html
import os
from datetime import date

import resend

from .config import GEO_SECTIONS
from .curator import CurationResult
from .sources import Article
from .writer import LinkedInPost


def _esc(s: str) -> str:
    return html.escape(s or "")


def _section_html(geo: str, items: list[tuple[Article, dict]]) -> str:
    if not items:
        return ""
    cards = []
    for art, meta in items:
        score = meta.get("relevance_score", "")
        angle = meta.get("angle", "")
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
              <div style="font-size:13px;color:#1e3a8a;font-style:italic;margin-bottom:10px;">
                ▸ {_esc(angle)}
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


def _linkedin_html(posts: list[LinkedInPost], articles_by_index: dict[int, Article]) -> str:
    if not posts:
        return ""
    blocks = []
    for i, post in enumerate(posts, 1):
        art = articles_by_index.get(post["article_index"])
        source_line = ""
        if art:
            source_line = f"""
              <div style="font-size:12px;color:#6b7280;margin-bottom:10px;">
                Source : <a href="{_esc(art.link)}" style="color:#1e3a8a;">{_esc(art.source)} — {_esc(art.title)}</a>
              </div>
            """
        body = _esc(post["post"]).replace("\n", "<br>")
        blocks.append(f"""
            <div style="margin-bottom:28px;padding:20px;background:#f8fafc;border-left:4px solid #1e3a8a;border-radius:4px;">
              <div style="font-size:13px;letter-spacing:0.5px;text-transform:uppercase;color:#1e3a8a;font-weight:600;margin-bottom:10px;">
                Post LinkedIn #{i}
              </div>
              {source_line}
              <div style="font-size:14px;line-height:1.6;color:#0f172a;white-space:pre-wrap;font-family:'Helvetica Neue',Arial,sans-serif;">
                {body}
              </div>
            </div>
        """)
    return f"""
        <h2 style="font-size:20px;color:#0f172a;border-bottom:2px solid #1e3a8a;padding-bottom:6px;margin:40px 0 16px;">
          ✍️ 3 posts LinkedIn prêts à publier
        </h2>
        {''.join(blocks)}
    """


def build_html(
    curation: CurationResult,
    articles: list[Article],
    posts: list[LinkedInPost],
    today: date,
) -> str:
    articles_by_index = {i: art for i, art in enumerate(articles)}

    # Group curated articles by geo, preserving rank order
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
    linkedin_block = _linkedin_html(posts, articles_by_index)

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
                Top {len(sorted_top)} actualités finance · {len(posts)} posts LinkedIn générés
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 36px 36px;">
              {sections_html}
              {linkedin_block}
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

    recipient = os.environ.get("DIGEST_RECIPIENT", "richard@inside-company.fr")
    sender = os.environ.get("DIGEST_SENDER", "Veille Inside Banking <onboarding@resend.dev>")

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
