from __future__ import annotations

from typing import TypedDict

import anthropic

from .config import WRITER_MODEL, load_prompt
from .sources import Article


class LinkedInPost(TypedDict):
    article_index: int
    headline_hook: str
    post: str


POSTS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "posts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "article_index": {"type": "integer"},
                    "headline_hook": {"type": "string", "description": "The one-line hook (first sentence of the post)"},
                    "post": {"type": "string", "description": "The full LinkedIn post in Richard's style, ready to copy-paste"},
                },
                "required": ["article_index", "headline_hook", "post"],
            },
        },
    },
    "required": ["posts"],
}


def write_linkedin_posts(picks: list[tuple[int, Article, str]]) -> list[LinkedInPost]:
    """
    picks: list of (article_index, Article, angle) tuples — the 3 articles selected for LinkedIn.
    Returns generated posts in Richard's voice.
    """
    if not picks:
        return []

    client = anthropic.Anthropic()
    style_reference = load_prompt("style_reference.md")

    system_prompt = f"""Tu es Richard Michaud, fondateur d'Inside Banking. Tu rédiges des posts LinkedIn pédagogiques sur la finance pour un public de décideurs du secteur.

Tu dois imiter SCRUPULEUSEMENT le style des posts ci-dessous. Étudie la structure, le ton, le rythme, les transitions, les emojis (puces colorées 🟢🔴🟣🟠, flèches →), les chiffres précis, l'ouverture/clôture.

{style_reference}

Règles strictes pour CHAQUE post à générer :
1. **Longueur** : 250 à 450 mots.
2. **Structure** : accroche directe (1-2 lignes) → contexte → constat → points clés (flèches → ou puces colorées) → synthèse stratégique → ouverture finale.
3. **Ton** : pédagogique, factuel, structuré, accessible — JAMAIS hype ou marketing.
4. **Chiffres précis** : reprends les données chiffrées de l'article (montants, %, dates) quand elles existent.
5. **Pas d'invention** : ne fabrique pas de chiffres, dates ou faits qui ne sont pas dans l'article fourni. Si tu manques d'info, reste plus généraliste.
6. **Pas de hashtags** en fin de post (ou un seul maximum si vraiment pertinent).
7. **Clôture** : finis par une question ouverte, "À suivre 🚀", ou une ouverture stratégique — pas par un appel à l'action commercial.
8. **Première personne** : tu écris en tant que Richard, à la première personne quand pertinent ("Je décrypte", "À mon sens"…), mais sans en abuser.
9. **Pas de "Bonjour LinkedIn"** ni d'introduction métapropos — entre directement dans le sujet.

Retourne les 3 posts via l'outil `submit_posts`, dans l'ordre des articles fournis."""

    articles_block = []
    for idx, art, angle in picks:
        articles_block.append(
            f"--- ARTICLE [{idx}] ---\n"
            f"Source : {art.source} ({art.section})\n"
            f"Titre : {art.title}\n"
            f"Résumé : {art.summary or '(pas de résumé)'}\n"
            f"Angle suggéré : {angle}\n"
            f"Lien : {art.link}"
        )
    user_message = (
        "Voici les 3 articles sélectionnés pour des posts LinkedIn. "
        "Rédige un post complet pour chacun, dans mon style.\n\n"
        + "\n\n".join(articles_block)
    )

    response = client.messages.create(
        model=WRITER_MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=system_prompt,
        tools=[{
            "name": "submit_posts",
            "description": "Submit the 3 generated LinkedIn posts in Richard's voice.",
            "input_schema": POSTS_SCHEMA,
        }],
        tool_choice={"type": "tool", "name": "submit_posts"},
        messages=[{"role": "user", "content": user_message}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_posts":
            return block.input["posts"]  # type: ignore[return-value]

    raise RuntimeError("Writer did not return a tool_use block")
