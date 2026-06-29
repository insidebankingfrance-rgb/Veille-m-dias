# Veille Inside Banking

Agent quotidien qui envoie à 7h (Europe/Paris) :
- Le top 10 des actualités finance (Les Échos, Bloomberg, FT, Reuters), réparties par zone géo (France / Europe / US / Reste du monde).
- 3 propositions de posts LinkedIn dans le style d'Inside Banking, générés à partir des 3 news les plus pertinentes.

## Stack

- **GitHub Actions** : cron quotidien (5h et 6h UTC, le script vérifie qu'il est 7h Paris).
- **Claude Opus 4.8** (`claude-opus-4-8`) avec adaptive thinking pour la curation et la rédaction.
- **RSS** : flux natifs Les Échos + Google News RSS (avec filtre `site:`) pour Bloomberg / FT / Reuters.
- **Resend** pour l'envoi de l'email HTML.

## Setup

### 1. Secrets GitHub à configurer

Dans **Settings → Secrets and variables → Actions → New repository secret** :

- `ANTHROPIC_API_KEY` — clé API Claude (console.anthropic.com)
- `RESEND_API_KEY` — clé API Resend (resend.com)

### 2. Variables (optionnelles, dans **Settings → Variables**)

- `DIGEST_RECIPIENT` — par défaut `richard@inside-company.fr`
- `DIGEST_SENDER` — par défaut `Veille Inside Banking <onboarding@resend.dev>`. Pour utiliser une vraie adresse @inside-company.fr, vérifie le domaine sur resend.com puis mets `Veille Inside Banking <veille@inside-company.fr>`.

### 3. Tester localement

```bash
pip install -r requirements.txt
cp .env.example .env  # remplis les clés
export $(cat .env | xargs)
FORCE_SEND=true python -m src.main
```

### 4. Tester en GitHub Action

Onglet **Actions → Daily finance digest → Run workflow** (l'input `force_send` est à `true` par défaut pour ce déclenchement manuel).

## Tuner le style des posts

Édite `prompts/style_reference.md` — c'est le few-shot qui définit la voix. Plus tu y mets de posts récents et bien écrits, mieux Claude imitera ton style.

## Tuner les sources

Édite la liste `RSS_SOURCES` dans `src/config.py`. Pour ajouter un média, soit utilise un flux RSS natif, soit un flux Google News avec filtre `site:` :

```
https://news.google.com/rss/search?q=site:agefi.fr+finance&hl=fr&gl=FR&ceid=FR:fr
```
