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
    ("Les Échos", "Finance & Marchés", "https://services.lesechos.fr/rss/les-echos-finance-marches.xml"),
    ("Les Échos", "Économie", "https://services.lesechos.fr/rss/les-echos-economie.xml"),
    ("Les Échos", "Monde", "https://services.lesechos.fr/rss/les-echos-monde.xml"),
    ("Les Échos", "Entreprises", "https://services.lesechos.fr/rss/les-echos-entreprises.xml"),

    ("Bloomberg", "Finance",
     "https://news.google.com/rss/search?q=site:bloomberg.com+(finance+OR+banking+OR+markets+OR+crypto)&hl=en&gl=US&ceid=US:en"),
    ("Financial Times", "Finance",
     "https://news.google.com/rss/search?q=site:ft.com+(finance+OR+banking+OR+markets+OR+crypto)&hl=en&gl=GB&ceid=GB:en"),
    ("Reuters", "Finance",
     "https://news.google.com/rss/search?q=site:reuters.com+(finance+OR+banking+OR+markets+OR+crypto)&hl=en&gl=US&ceid=US:en"),
]


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")
