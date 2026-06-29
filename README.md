# Veille Inside Banking

Agent quotidien qui envoie chaque matin à 7h (Europe/Paris) un email contenant :

- **Top 10 des actualités finance** issues de Les Échos, Bloomberg, FT et Reuters, classées par zone géo (France / Europe / US / Reste du monde).
- **Un bouton « Générer 3 posts LinkedIn dans Claude.ai »** qui pré-remplit Claude.ai avec les 3 articles les plus pertinents + ton style éditorial, prêt à envoyer en un clic.

## Stack — 100% gratuit

- **GitHub Actions** : cron quotidien à 5h et 6h UTC (le script vérifie l'heure Paris).
- **Curation heuristique** : pondération par mots-clés de la ligne éditoriale (banques françaises, ETF, crypto, IA en finance) + classification géo par mots-clés et source.
- **Pas d'appel API LLM** : la génération des posts se fait dans Claude.ai (utilise ton abonnement existant Pro/Max).
- **Resend** pour l'envoi de l'email HTML.

## Setup

### 1. Clé Resend dans GitHub Secrets

Dans **Settings → Secrets and variables → Actions → New repository secret** :

- Nom : `RESEND_API_KEY`
- Valeur : ta clé `re_…` (resend.com)

### 2. Variables optionnelles (Settings → Variables)

- `DIGEST_RECIPIENT` — par défaut `inside.banking.france@gmail.com`
- `DIGEST_SENDER` — par défaut `Veille Inside Banking <onboarding@resend.dev>`. Pour expédier depuis `veille@inside-company.fr`, vérifie d'abord ton domaine sur resend.com.

### 3. Premier test

Onglet **Actions → Daily finance digest → Run workflow** (l'input `force_send` est à `true` par défaut). Tu reçois l'email dans la minute.

### 4. Test local (optionnel)

```bash
pip install -r requirements.txt
cp .env.example .env  # renseigne RESEND_API_KEY
export $(cat .env | xargs)
FORCE_SEND=true python -m src.main
```

## Comment ça marche, au quotidien

1. Le matin à 7h, tu reçois l'email avec le top 10 des news.
2. Tu cliques sur **« 🚀 Générer les 3 posts dans Claude.ai »** : Claude.ai s'ouvre avec un prompt déjà rempli (3 articles + ton style).
3. Tu envoies, Claude te génère les 3 posts. Tu choisis, tu copies, tu postes.

Si le prompt pré-rempli ne suffit pas ou si tu veux affiner, l'email contient aussi un bloc dépliable **« Voir / copier le prompt complet »** que tu peux coller manuellement dans Claude.ai pour une qualité optimale.

## Tuner la ligne éditoriale

- **Pondération des sujets** : `src/curator.py` → dictionnaire `EDITORIAL_KEYWORDS`. Ajoute / retire des mots-clés pour orienter la curation (ex. donner plus de poids à « tokenisation » ou pénaliser un thème).
- **Style des posts** : `src/email_sender.py` → constante `COMPACT_STYLE_BRIEF` (le brief embarqué dans le prompt Claude.ai).
- **Sources RSS** : `src/config.py` → liste `RSS_SOURCES`. Tu peux ajouter d'autres médias en flux natif, ou en passant par Google News RSS :

  ```
  https://news.google.com/rss/search?q=site:agefi.fr+finance&hl=fr&gl=FR&ceid=FR:fr
  ```
