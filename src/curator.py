from __future__ import annotations

import json
from typing import TypedDict

import anthropic

from .config import CURATOR_MODEL, GEO_SECTIONS, LINKEDIN_POST_COUNT, TOP_NEWS_COUNT, load_prompt
from .sources import Article


class CuratedArticle(TypedDict):
    index: int
    geo: str
    relevance_score: int
    angle: str
    rank: int


class CurationResult(TypedDict):
    top_news: list[CuratedArticle]
    linkedin_picks: list[int]


CURATOR_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "top_news": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "index": {"type": "integer", "description": "Index of the article in the input list (0-based)"},
                    "geo": {"type": "string", "enum": GEO_SECTIONS},
                    "relevance_score": {"type": "integer", "minimum": 0, "maximum": 100,
                                         "description": "How well this matches the editorial line (0-100)"},
                    "angle": {"type": "string", "description": "One-sentence angle explaining why this matters for Inside Banking"},
                    "rank": {"type": "integer", "minimum": 1, "description": "Overall rank (1 = top story)"},
                },
                "required": ["index", "geo", "relevance_score", "angle", "rank"],
            },
        },
        "linkedin_picks": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "Indices (from the input list) of the 3 articles BEST suited to LinkedIn posts in Richard's editorial line",
        },
    },
    "required": ["top_news", "linkedin_picks"],
}


def _format_articles_for_prompt(articles: list[Article]) -> str:
    lines = []
    for i, art in enumerate(articles):
        lines.append(
            f"[{i}] {art.source} ({art.section}) — {art.published.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"    Titre : {art.title}\n"
            f"    Résumé : {art.summary or '(pas de résumé fourni par le flux)'}\n"
            f"    Lien : {art.link}"
        )
    return "\n\n".join(lines)


def curate(articles: list[Article]) -> CurationResult:
    if not articles:
        return {"top_news": [], "linkedin_picks": []}

    client = anthropic.Anthropic()
    style_reference = load_prompt("style_reference.md")

    system_prompt = f"""Tu es l'éditeur de la veille quotidienne d'Inside Banking, la marque média de Richard Michaud.

Ton rôle : sélectionner les {TOP_NEWS_COUNT} actualités financières les plus pertinentes des dernières 24 heures, en t'appuyant strictement sur la ligne éditoriale ci-dessous.

{style_reference}

Règles de curation :
1. Sélectionne au maximum {TOP_NEWS_COUNT} articles classés du plus pertinent (rank=1) au moins pertinent.
2. Réparties-les sur 4 zones géographiques : France, Europe, États-Unis, Reste du monde. Vise un équilibre : idéalement 3-4 France, 2-3 Europe, 2-3 US, 1-2 Reste du monde.
3. Note chaque article de 0 à 100 selon sa pertinence pour la ligne éditoriale (transformations bancaires, investissement Bourse, crypto/stablecoins/tokenisation, IA appliquée à la finance, vulgarisation financière).
4. Écarte le bruit : faits divers, communiqués corporate sans portée stratégique, brèves sans information neuve.
5. Pour chaque article retenu, écris un `angle` en UNE phrase expliquant pourquoi cet article mérite d'être lu par un décideur du secteur financier.
6. Identifie les **3 articles parfaits pour un post LinkedIn** : ceux qui combinent (a) forte pertinence éditoriale, (b) angle pédagogique/décryptage évident, (c) chiffres ou faits saillants exploitables, (d) résonance avec les sujets phares de Richard.

Retourne ta réponse via l'outil `submit_curation`."""

    user_message = f"""Voici les {len(articles)} articles candidats des dernières 24h. Sélectionne, classe et identifie les 3 meilleurs candidats pour LinkedIn.

{_format_articles_for_prompt(articles)}"""

    response = client.messages.create(
        model=CURATOR_MODEL,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=system_prompt,
        tools=[{
            "name": "submit_curation",
            "description": "Submit the curated list of top news with geo categorization, relevance scores, and LinkedIn post picks.",
            "input_schema": CURATOR_SCHEMA,
        }],
        tool_choice={"type": "tool", "name": "submit_curation"},
        messages=[{"role": "user", "content": user_message}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_curation":
            return block.input  # type: ignore[return-value]

    raise RuntimeError("Curator did not return a tool_use block")
