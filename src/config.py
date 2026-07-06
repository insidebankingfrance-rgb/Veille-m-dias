from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"

LOOKBACK_HOURS = 24
TOP_NEWS_COUNT = 10
LINKEDIN_POST_COUNT = 3

GEO_SECTIONS = ["France", "Europe", "États-Unis", "Reste du monde"]

CURATOR_MODEL = "claude-opus-4-8"
WRITER_MODEL = "claude-opus-4-8"

RSS_SOURCES = [
    # Les Échos : requête large pour maximiser la remontée d'articles FR
    ("Les Échos", "Finance",
     "https://news.google.com/rss/search?q=site:lesechos.fr+(banque+OR+finance+OR+bourse+OR+crypto+OR+fintech+OR+ETF+OR+tokenisation+OR+fusion+OR+acquisition)&hl=fr&gl=FR&ceid=FR:fr"),

    # Sources anglo-saxonnes : requêtes resserrées sur banking/crypto/fintech
    # pour éviter le bruit "markets close +0.5%" et remonter du contenu éditorialisable.
    ("Bloomberg", "Finance",
     "https://news.google.com/rss/search?q=site:bloomberg.com+(bank+OR+banking+OR+fintech+OR+crypto+OR+stablecoin+OR+tokenization+OR+%22asset+management%22+OR+%22digital+bank%22+OR+neobank)&hl=en&gl=US&ceid=US:en"),
    ("Financial Times", "Finance",
     "https://news.google.com/rss/search?q=site:ft.com+(bank+OR+banking+OR+fintech+OR+crypto+OR+stablecoin+OR+tokenization+OR+%22asset+management%22+OR+%22digital+bank%22+OR+neobank)&hl=en&gl=GB&ceid=GB:en"),
    ("Reuters", "Finance",
     "https://news.google.com/rss/search?q=site:reuters.com+(bank+OR+banking+OR+fintech+OR+crypto+OR+stablecoin+OR+tokenization+OR+%22asset+management%22+OR+%22digital+bank%22+OR+neobank)&hl=en&gl=US&ceid=US:en"),
]

# User-Agent navigateur — certains flux RSS rejettent l'UA par défaut de feedparser.
FEEDPARSER_AGENT = "Mozilla/5.0 (compatible; InsideBankingDigest/1.0; +https://github.com/insidebankingfrance-rgb/veille-m-dias)"


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")
