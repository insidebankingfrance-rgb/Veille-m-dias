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

STYLE À IMITER :
- Phrases courtes, paragraphes courts (1-2 lignes).
- Accroche directe + emoji ouvrant (💸 ⚙️ 🟢 🔴 💣) en 1-2 lignes.
- Structure : contexte → constat → points clés (flèches → et puces colorées 🟢🔴🟣🟠 pour acteurs) → synthèse → ouverture.
- Drapeaux 🇫🇷 🇩🇪 🇮🇹 🇪🇸 🇵🇹 dans les listes M&A pour les pays.
- Mini-icônes en début de section : 🚧 (chantier), 🎯 (ambition), 💸 (budget), 🛠️ (concrètement).
- Pointeurs 👉 et 👇 pour orienter le lecteur.
- Chiffres précis (Md€, %, dates) toujours quand l'article les fournit.
- Connecteurs : "Le point commun ?", "Les différences ?", "Ce qui va changer concrètement 👇", "Alors concrètement, que propose X ?".
- Ancres : "Je vous le disais déjà…", "C'est le thème de ma chronique pour Les Échos" (rare, seulement si pertinent).
- Clôture : "À suivre 🚀" ou question stratégique ouverte qui invite au commentaire.
- 250-450 mots. Pas de hashtags, pas de "Bonjour LinkedIn".
- N'invente JAMAIS de chiffres ou faits hors article.

INTERDIT — marqueurs IA :
- AUCUN mot entre guillemets pour cadrer/souligner. Soit tu dis le mot, soit tu ne le dis pas.
- AUCUN tiret cadratin (—) dans une phrase. Sépare par retour à la ligne.
- Bannir : "Plus qu'un X c'est un Y", "Dans un monde où…", "L'enjeu n'est pas X mais Y", "Une révolution silencieuse", "Un tournant majeur", "Il est important de noter", "Il convient de souligner", "Force est de constater", "Véritablement", "littéralement", "en effet", "à proprement parler", "indéniablement".
- Pas de balancement artificiel "d'un côté X / de l'autre Y" qui n'est pas dans la source.

PÉDAGOGIE OBLIGATOIRE :
Chaque post transmet 2 à 3 leçons clés que le lecteur retient : un concept financier, un mécanisme, un enjeu stratégique, un précédent comparable. Pas juste "voici l'actu" — explique POURQUOI ça compte, CE QUI change, CE QU'IL FAUT SURVEILLER.

CHECK FINAL (marqueurs IA) :
Avant de me donner le post, relis-le. Supprime tout guillemet de cadrage, tout tiret cadratin dans une phrase, toute formule de la liste interdite. Réécris sec et direct, conversationnel.

FACT-CHECK OBLIGATOIRE :
1. Ouvre le lien de l'article ci-dessous (utilise web_fetch/web_search si disponibles dans ta session).
2. Chaque chiffre, date, montant, nom, citation, % dans ton post DOIT être sourcé depuis l'article. Aucune invention, aucune extrapolation. Sinon, retire-le.
3. Si l'article est inaccessible (paywall, 404, lien mort), travaille STRICTEMENT à partir du titre + résumé fournis dans ce prompt.
4. À la fin de ta réponse, livre un bloc "🔍 Fact-check" avec :
   - Les 3 à 5 faits chiffrés ou nominatifs du post, chacun avec sa source (extrait de l'article, ou "titre/résumé RSS" en fallback).
   - Les faits que tu as RETIRÉS du post par manque de source (transparence).
   - Statut : "article fetch réussi" ou "article inaccessible — fallback RSS".

IDÉES D'ILLUSTRATION :
Ajoute un bloc séparé "💡 Idées d'illustration" avec 2-3 propositions concrètes. Une phrase chacune : QUOI montrer + FORMAT (tableau comparatif chiffré, infographie, graphique, photo conceptuelle, schéma)."""


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


def _build_linkedin_prompt_for(article: Article, article_number: int) -> str:
    """Construit le prompt Claude.ai pour UN SEUL article (un bouton = un post = une conversation)."""
    parts = [
        COMPACT_STYLE_BRIEF,
        "",
        f"ARTICLE À TRAITER (post #{article_number} de la veille du jour) :",
        f"Source : {article.source} ({article.section})",
        f"Titre : {article.title}",
        f"Résumé : {article.summary or '(résumé non fourni par le flux)'}",
        f"Lien : {article.link}",
        "",
        "Livre maintenant, en 3 blocs séparés et clairement titrés :",
        "1. Le POST LinkedIn complet (fact-checké, prêt à copier-coller)",
        "2. 🔍 Fact-check (faits vérifiés + faits retirés + statut)",
        "3. 💡 Idées d'illustration (2 à 3 propositions)",
    ]
    return "\n".join(parts)


def _claude_cta_html(picks: list[Article]) -> str:
    if not picks:
        return ""

    article_blocks = []
    for i, art in enumerate(picks, 1):
        prompt_text = _build_linkedin_prompt_for(art, i)
        deep_link = f"{CLAUDE_AI_BASE}?q={urllib.parse.quote(prompt_text)}"

        article_blocks.append(f"""
            <div style="margin-bottom:24px;padding:18px 20px;background:#f8fafc;border-left:4px solid #1e3a8a;border-radius:4px;">
              <div style="font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:#1e3a8a;font-weight:600;margin-bottom:6px;">
                Post #{i} · {_esc(art.source)}
              </div>
              <div style="font-size:15px;font-weight:600;line-height:1.4;color:#0f172a;margin-bottom:14px;">
                <a href="{_esc(art.link)}" style="color:#0f172a;text-decoration:none;">{_esc(art.title)}</a>
              </div>
              <div style="margin-bottom:10px;">
                <a href="{_esc(deep_link)}"
                   style="display:inline-block;background:#1e3a8a;color:#ffffff;padding:10px 20px;
                          font-size:14px;font-weight:600;text-decoration:none;border-radius:6px;">
                  🚀 Générer ce post dans Claude.ai
                </a>
              </div>
              <details style="margin-top:6px;">
                <summary style="cursor:pointer;font-size:12px;color:#6b7280;">
                  Voir / copier le prompt (pour relancer manuellement)
                </summary>
                <pre style="margin:10px 0 0;padding:12px;background:#ffffff;border:1px solid #e5e7eb;border-radius:4px;
                            font-family:Menlo,Consolas,monospace;font-size:11px;line-height:1.5;color:#0f172a;
                            white-space:pre-wrap;word-break:break-word;max-width:100%;overflow-x:auto;">{_esc(prompt_text)}</pre>
              </details>
            </div>
        """)

    return f"""
        <h2 style="font-size:20px;color:#0f172a;border-bottom:2px solid #1e3a8a;padding-bottom:6px;margin:40px 0 16px;">
          ✍️ Génère un post LinkedIn (à ton rythme)
        </h2>

        <div style="font-size:14px;color:#6b7280;line-height:1.5;margin-bottom:20px;">
          Un bouton par article, une conversation Claude.ai indépendante à chaque clic.
          Choisis les posts qui t'inspirent, saute les autres — pas de génération inutile.
        </div>

        {''.join(article_blocks)}
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
