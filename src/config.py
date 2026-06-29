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
    # Les Échos : flux RSS natifs (services.lesechos.fr) en backup, mais Google News est
    # plus robuste (les flux natifs Les Échos rejettent parfois feedparser). On part en
    # Google News RSS pour toutes les sources : même schéma, même fiabilité.
    ("Les Échos", "Finance",
     "https://news.google.com/rss/search?q=site:lesechos.fr+(finance+OR+banque+OR+marchés+OR+investissement+OR+crypto+OR+bourse)&hl=fr&gl=FR&ceid=FR:fr"),

    ("Bloomberg", "Finance",
     "https://news.google.com/rss/search?q=site:bloomberg.com+(finance+OR+banking+OR+markets+OR+crypto)&hl=en&gl=US&ceid=US:en"),
    ("Financial Times", "Finance",
     "https://news.google.com/rss/search?q=site:ft.com+(finance+OR+banking+OR+markets+OR+crypto)&hl=en&gl=GB&ceid=GB:en"),
    ("Reuters", "Finance",
     "https://news.google.com/rss/search?q=site:reuters.com+(finance+OR+banking+OR+markets+OR+crypto)&hl=en&gl=US&ceid=US:en"),
]

# User-Agent navigateur — certains flux RSS rejettent l'UA par défaut de feedparser.
FEEDPARSER_AGENT = "Mozilla/5.0 (compatible; InsideBankingDigest/1.0; +https://github.com/insidebankingfrance-rgb/veille-m-dias)"


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")
