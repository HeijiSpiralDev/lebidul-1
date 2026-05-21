# Onboarding développeur

Guide pour démarrer sur le projet en moins d'une heure. À lire avant tout le
reste.

## Le projet en 30 secondes

Refonte du site `lebidul.com` (agenda culturel Le Mans) vers une stack
**Django 5 + Wagtail 6** sur **Postgres**. Le code remplace progressivement
un ancien WordPress dont les articles sont importés via un dump SQL. Les
événements de l'agenda (~30 000) viennent d'un outil externe — le **Bidul
Indexer** — qui les extrait des PDFs des numéros papier et les fournit dans
une base SQLite.

Trois apps Django :

| App           | Rôle                                                    |
|---------------|---------------------------------------------------------|
| `apps.agenda` | Données métier (Snippets `Bidul`, `Lieu`, `Categorie`, `Auteur` + Model `Evenement`) |
| `apps.content`| Pages CMS Wagtail (`HomePage`, `BidulPage`, `LieuPage`, `ArticlePage`, `FlexiblePage`, `AgendaPage`) |
| `apps.theme`  | Réglages d'apparence éditables dans l'admin             |
| `apps.migration` | Commandes d'import (WordPress + Indexer)             |

Pas de modèle `Artiste` pour l'instant — c'est un report. Voir
`handoff-session.md` pour les décisions de schéma actées.

## Pré-requis machine

- **Python 3.12+** (Django 6.0 et Wagtail 7.2 l'exigent)
- **Postgres ≥ 13** — la fonctionnalité `DROP DATABASE … WITH (FORCE)` du
  script de reset l'exige. Utilisateur avec droit `CREATEDB`.
- **Redis ≥ 7** — utilisé pour le cache Django. Optionnel en dev si on
  désactive le cache à la main.
- **Git**
- **Docker + Docker Compose** — recommandé, le `docker-compose.yml` du
  repo monte Postgres 16 + Redis 7 d'un coup.

## Installation

### 1. Cloner et créer le venv

```bash
git clone https://github.com/lebidul/lebidul.git
cd lebidul
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate           # Windows PowerShell

pip install -e ".[dev]"
```

### 2. Configurer l'environnement

```bash
cp .env.example .env
# Adapte les valeurs si besoin (par défaut elles collent au docker-compose).
```

### 3. Démarrer Postgres et Redis

Le plus simple : Docker.

```bash
make db-start
# équivalent : docker compose up -d
```

Sans Docker, installe Postgres ≥ 13 et Redis ≥ 7 en natif via ton
gestionnaire de paquets, puis crée la base et l'utilisateur :

```bash
sudo -u postgres psql -c "CREATE USER lebidul WITH PASSWORD 'lebidul' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE lebidul OWNER lebidul;"
```

Vérifie que Postgres répond :

```bash
psql -h localhost -U lebidul -d postgres -c '\l'
```

### 4. Première initialisation : créer le schéma et importer

Tu as deux options.

**Option A — Tu n'as pas les dumps WordPress/Indexer** (cas du nouveau
développeur qui veut juste lancer le site) :

```bash
python manage.py reset_and_import --confirm
python manage.py createsuperuser
python manage.py runserver
```

Tu auras un site vide avec uniquement le schéma. Tu peux créer des contenus
de test depuis l'admin.

**Option B — Tu as les dumps complets** (workflow de prod / staging) :

```bash
python manage.py reset_and_import --confirm \
  --wp-sql=/chemin/Dump20260209.sql \
  --wp-prefix=f4yxrr34kc_ \
  --wp-media=/chemin/media/images \
  --wp-documents=/chemin/media/documents \
  --indexer-db=/chemin/bidul_archives.db

python manage.py createsuperuser
python manage.py runserver
```

Détails du script et variantes : voir `database.md`.

### 5. Vérifier

- Site public : http://localhost:8000
- Admin Wagtail : http://localhost:8000/admin

Dans l'admin :

- **Pages** → `Accueil`, `Chroniques` (les articles WordPress, s'ils ont
  été importés)
- **Snippets** → `Biduls`, `Lieux`, `Catégories`, `Auteurs`
- **Événements** (menu dédié dans la barre latérale)

## Workflow de dev quotidien

```bash
python manage.py runserver               # serveur dev
python manage.py shell                   # shell Django interactif
python manage.py makemigrations <app>    # après modif d'un modèle
python manage.py migrate                 # appliquer
python manage.py test                    # tests
```

Outils de style (configurés dans `pyproject.toml`) :

```bash
black .                                  # format
isort .                                  # imports
ruff check .                             # lint
```

## Architecture en deux mots

### Snippet vs Page

Décision documentée dans `modelsVsSnippets.part1.md` /
`modelsVsSnippets.part2.md`. En résumé :

- **Snippets** (`Bidul`, `Lieu`, `Categorie`, `Auteur`) — données métier
  pures, choisies depuis des choosers dans l'admin, ré-utilisables, pas de
  position dans l'arbre des pages.
- **Pages CMS** (`BidulPage`, `LieuPage`, `ArticlePage`) — contenu
  éditorial avec URL publique, gérées par Wagtail (workflow, prévisualisation,
  versioning).
- **Model Django** (`Evenement`) — gros volume (~30k entrées), pas un
  Snippet pour des raisons de perf, mais exposé via `SnippetViewSet` pour
  une UI admin Wagtail standard.

### Imports

Trois commandes, toutes dans `apps/migration/management/commands/` :

| Commande               | Source              | Cible                                  |
|------------------------|---------------------|----------------------------------------|
| `import_from_sql`      | Dump MySQL WP       | `ArticlePage`, `Categorie`, `Auteur`, `Image`, `Document` |
| `import_from_indexer`  | SQLite Indexer      | `Bidul`, `Lieu`, `Evenement`           |
| `reset_and_import`     | Orchestre les 2     | DROP/CREATE Postgres + migrate + imports |
| `clear_import`         | —                   | Supprime les contenus WP (pas les biduls) |

## Pour lire la suite

Ordre conseillé dans `Documentation/` :

1. `onboarding.md` (ce fichier) — démarrer
2. `database.md` — choix Postgres, script de reset, modèle de données
3. `handoff-session.md` — état d'avancement et décisions actées
4. `réimportation.md` — détail du workflow de ré-import WP
5. `models template snippet.md` / `modelsVsSnippets.part*.md` —
   justifications d'architecture
6. `groupes.md`, `collections.md` — configuration de l'admin Wagtail

Schéma de référence (à la racine, pas dans `Documentation/`) :
`lebidul_database_schema_v2.md`.

## Pièges connus

- **Postgres droits** : l'utilisateur configuré dans `.env` doit pouvoir
  créer des bases (sinon `reset_and_import` échoue). Avec le
  `docker-compose.yml` du repo c'est déjà le cas. Sur une install Postgres
  native : `ALTER USER lebidul CREATEDB;` depuis `psql` en tant que postgres.
- **HomePage Wagtail** : après `migrate`, Wagtail crée une page d'accueil
  par défaut `slug='home'`. `import_from_sql` crée une `HomePage` séparée
  `slug='accueil'`. Si tu n'importes pas WordPress, supprime la page par
  défaut et crée une `HomePage` à la main, sinon le routage public ne
  pointera pas sur la bonne page.

## Où poser des questions

Issues GitHub sur `lebidul/lebidul`. Les sessions Claude précédentes ont
laissé des notes dans `handoff-session.md` à chaque passation.
