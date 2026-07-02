from __future__ import annotations

from typing import TypedDict

from .config import GEO_SECTIONS, LINKEDIN_POST_COUNT, TOP_NEWS_COUNT
from .sources import Article


# Seuil minimum de pertinence pour qu'un article soit retenu.
# Calibré pour qu'un article doive mentionner au moins un sujet phare de
# la ligne éditoriale (banque française, crypto, IA finance, M&A…) et pas
# seulement un mot générique comme « bourse » ou « rendement ».
MIN_RELEVANCE_SCORE = 12


class CuratedArticle(TypedDict):
    index: int
    geo: str
    relevance_score: int
    angle: str
    rank: int


class CurationResult(TypedDict):
    top_news: list[CuratedArticle]
    linkedin_picks: list[int]


# Mots-clés pondérés selon la ligne éditoriale d'Inside Banking.
# Les acteurs/sujets phares pèsent plus lourd.
EDITORIAL_KEYWORDS: dict[str, int] = {
    # Grandes banques françaises (cœur de ligne)
    "bnp paribas": 12, "société générale": 12, "crédit agricole": 12, "bpce": 12,
    "crédit mutuel": 10, "boursobank": 10, "natixis": 9, "banque de france": 9,
    "caisse d'épargne": 8, "banque populaire": 8, "axa": 6,
    # Régulateurs / institutions
    "bce": 9, "ecb": 9, "fed": 8, "amf": 9, "sec ": 7, "treasury": 6,
    # Vocabulaire bancaire
    "banque": 6, "banques": 7, "banking": 5, "bank ": 5,
    "fintech": 8, "néobanque": 8, "neobank": 7, "challenger bank": 7,
    # Investissement / marchés
    "etf": 9, "etn": 8, "obligation": 6, "obligations": 6, "actions": 5,
    "bourse": 7, "marchés": 5, "investissement": 7, "allocation": 6,
    "rendement": 5, "dividende": 5, "private equity": 6, "capital-investissement": 6,
    # Crypto / tokenisation
    "crypto": 10, "cryptomonnaie": 10, "cryptomonnaies": 10,
    "bitcoin": 9, "ethereum": 8, "solana": 6, "stablecoin": 10, "stablecoins": 10,
    "tokenisation": 10, "tokenization": 10, "blockchain": 7, "defi": 8,
    # IA et finance
    "intelligence artificielle": 9, "genai": 9, "machine learning": 7,
    "llm": 7, "openai": 6, "anthropic": 7, "mistral": 6,
    # Stratégie / corporate
    "résultats": 5, "trimestriels": 6, "annuels": 5, "stratégie": 5,
    "transformation": 6, "acquisition": 7, "fusion": 7, "m&a": 8,
    "régulation": 6, "supervision": 5, "compliance": 5,

    # Grandes banques US (relevantes pour Europe/US/RoW)
    "jpmorgan": 10, "jp morgan": 10,
    "goldman sachs": 10, "morgan stanley": 10,
    "bank of america": 10, "citigroup": 10, "wells fargo": 10,
    "state street": 8, "bny mellon": 8, "us bancorp": 7,

    # Grandes banques européennes (en français ET anglais)
    "deutsche bank": 10, "santander": 10, "banco santander": 10,
    "ubs": 9, "credit suisse": 8,
    "hsbc": 10, "barclays": 10, "standard chartered": 8,
    "bbva": 9, "unicredit": 9, "commerzbank": 9,
    "ing group": 8, "ing bank": 8,
    "lloyds": 8, "natwest": 8,
    "intesa sanpaolo": 8,

    # Banques asiatiques / RoW (couverture "reste du monde")
    "icbc": 8, "china construction bank": 8,
    "mitsubishi ufj": 8, "sumitomo mitsui": 7, "mizuho": 7,
    "dbs bank": 7, "ocbc": 6, "hdfc bank": 7, "sbi ": 6,
    "itaú": 7, "bradesco": 6, "banco do brasil": 6,

    # Asset managers globaux (contexte ETF/tokenisation)
    "blackrock": 10, "vanguard": 8, "fidelity": 7,
    "state street global": 8, "amundi": 10, "invesco": 7, "schroders": 6,

    # Fintech / néobanques (anglais)
    "digital bank": 7, "challenger bank": 7,
    "banking-as-a-service": 8, "banking as a service": 8, "baas": 6,
    "open banking": 7, "embedded finance": 7,
    "revolut": 8, "monzo": 6, "n26": 6, "starling bank": 6,
    "chime": 6, "klarna": 7, "wise ": 6, "nubank": 7,

    # Crypto / tokenisation en anglais
    "spot bitcoin etf": 12, "spot ether etf": 12, "bitcoin etf": 10,
    "tokenized": 10, "tokenised": 10, "tokenization": 10,
    "digital asset": 8, "digital assets": 8,
    "on-chain": 8, "onchain": 8,
    "cbdc": 9, "central bank digital currency": 10,

    # IA appliquée à la finance (anglais)
    "generative ai": 9, "gen ai": 8,
    "ai banking": 10, "ai in banking": 10, "ai in finance": 10,
    "agentic ai": 9, "ai agent": 7,

    # Régulation US / UK (contexte crypto & banque)
    "occ ": 6, "fdic": 7, "cftc": 6, "consumer financial protection": 6,
    "fca ": 6, "pra ": 5,

    # M&A / corporate en anglais
    "merger": 7, "cross-border": 7, "buyout": 6, "spin-off": 6, "divestiture": 6,
    "earnings": 5, "quarterly results": 6,
}

PENALTY_KEYWORDS: dict[str, int] = {
    # Off-topic général
    "football": -25, "rugby": -25, "tennis": -25, "olympique": -20, "sport": -10,
    "people": -15, "célébrité": -20, "cinéma": -20, "musique": -15,
    "horoscope": -30, "météo": -20, "fait divers": -20,

    # Stock-picking et conseils d'investissement individuels
    # (vocabulaire newsletter trader, hors ligne éditoriale pédagogique)
    "à prendre via": -40, "à prendre sur": -30,
    "bonus cappés": -35, "bonus cappé": -35,
    "warrant": -25, "turbo": -25, "leverage certificate": -25,
    "objectif de cours": -30, "price target": -25,
    "à acheter": -20, "à vendre": -20, "valeur à privilégier": -20,

    # NAV reports et disclosures réglementaires automatisées
    "net asset value": -50, " nav ": -40, "nav)": -40,
    "ucits etf -": -40, "ucits etf –": -40,
    "daily nav": -50, "weekly nav": -50,

    # Analyst notes individuelles sur titres hors banque
    "atteindre de nouveaux records": -20,
    "voit l'éditeur": -30, "voit le titre": -25, "voit la marque": -25,
    "relève son objectif": -20, "abaisse son objectif": -20,

    # Jeux vidéo / divertissement / lifestyle
    "jeu vidéo": -25, "jeux vidéo": -25, "gaming": -20,
    "gta vi": -30, "rockstar games": -25, "take-two": -25,
    "streaming vidéo": -15, "netflix": -10,
}

FRANCE_KEYWORDS: set[str] = {
    "france", "français", "française", "françaises", "paris", "macron", "matignon",
    "bercy", "bnp paribas", "société générale", "crédit agricole", "bpce",
    "crédit mutuel", "boursobank", "natixis", "banque de france", "amf",
    "caisse d'épargne", "banque populaire", "axa",
}

EUROPE_KEYWORDS: set[str] = {
    "europe", "european", "européen", "européenne", "européens", "ue ",
    "union européenne", "eurozone", "zone euro", "bce", "ecb",
    "allemagne", "allemand", "italie", "italien", "espagne", "espagnol",
    "royaume-uni", "uk ", "london", "londres", "suisse", "irlande",
    "deutsche bank", "santander", "ubs", "credit suisse", "ing ", "barclays",
    "hsbc", "bbva", "intesa", "unicredit", "lloyds", "natwest",
}

US_KEYWORDS: set[str] = {
    " us ", "u.s.", "united states", "america", "american", "wall street",
    "federal reserve", " fed ", "sec ", "nyse", "nasdaq", "trump", "biden",
    "treasury", "white house", "dollar",
    "jpmorgan", "jp morgan", "goldman", "morgan stanley", "bank of america",
    "citigroup", "wells fargo", "blackrock", "vanguard", "fidelity",
}


def _normalize(text: str) -> str:
    return (" " + text.lower() + " ").replace("\n", " ")


def _score_relevance(article: Article) -> int:
    text = _normalize(article.title + " " + article.summary)
    score = 0
    for kw, weight in EDITORIAL_KEYWORDS.items():
        if kw in text:
            score += weight
    for kw, penalty in PENALTY_KEYWORDS.items():
        if kw in text:
            score += penalty
    return max(0, min(100, score))


def _classify_geo(article: Article) -> str:
    text = _normalize(article.title + " " + article.summary)
    scores: dict[str, float] = {
        "France": sum(2 for kw in FRANCE_KEYWORDS if kw in text),
        "Europe": sum(2 for kw in EUROPE_KEYWORDS if kw in text),
        "États-Unis": sum(2 for kw in US_KEYWORDS if kw in text),
    }
    # Indice source (faible poids — surchargé par les mots-clés du texte)
    if article.source == "Les Échos":
        scores["France"] += 1
    elif article.source == "Financial Times":
        scores["Europe"] += 1
    elif article.source == "Bloomberg":
        scores["États-Unis"] += 1

    if max(scores.values()) == 0:
        return "Reste du monde"
    return max(scores, key=lambda k: scores[k])


def curate(articles: list[Article]) -> CurationResult:
    if not articles:
        return {"top_news": [], "linkedin_picks": []}

    scored = [
        (i, art, _score_relevance(art), _classify_geo(art))
        for i, art in enumerate(articles)
    ]
    # Tri : score décroissant, puis fraîcheur décroissante
    scored.sort(key=lambda x: (-x[2], -x[1].published.timestamp()))

    # Cibles géo (best-effort, non strict)
    geo_targets = {"France": 4, "Europe": 3, "États-Unis": 2, "Reste du monde": 2}
    geo_counts = {g: 0 for g in GEO_SECTIONS}
    picked: list[tuple[int, Article, int, str]] = []
    picked_indices: set[int] = set()

    # 1er passage : respecter les cibles géo, en exigeant un score minimum
    for entry in scored:
        if len(picked) >= TOP_NEWS_COUNT:
            break
        if entry[2] < MIN_RELEVANCE_SCORE:
            continue
        if geo_counts[entry[3]] >= geo_targets[entry[3]]:
            continue
        picked.append(entry)
        picked_indices.add(entry[0])
        geo_counts[entry[3]] += 1

    # 2e passage : combler avec les meilleurs restants (même seuil minimum)
    for entry in scored:
        if len(picked) >= TOP_NEWS_COUNT:
            break
        if entry[0] in picked_indices or entry[2] < MIN_RELEVANCE_SCORE:
            continue
        picked.append(entry)
        picked_indices.add(entry[0])

    top_news: list[CuratedArticle] = [
        {
            "index": idx,
            "geo": geo,
            "relevance_score": score,
            "angle": "",
            "rank": rank,
        }
        for rank, (idx, _art, score, geo) in enumerate(picked, 1)
    ]

    # 3 articles avec le meilleur score pour les posts LinkedIn
    linkedin_picks = [item["index"] for item in top_news[:LINKEDIN_POST_COUNT]]

    print(f"[curator] {len(top_news)} articles retenus, "
          f"répartition : {dict(geo_counts)}")
    return {"top_news": top_news, "linkedin_picks": linkedin_picks}
