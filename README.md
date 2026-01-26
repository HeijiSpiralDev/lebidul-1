# Le Bidul - Site Web

Site web de l'agenda culturel Le Bidul, construit avec Django et Wagtail.

## Architecture

```
lebidul/
├── apps/
│   ├── agenda/         # Snippets (Bidul, Lieu, Categorie, Auteur) + Evenement
│   ├── content/        # Pages CMS (BidulPage, LieuPage, ArticlePage...)
│   └── theme/          # ThemeSettings personnalisable
├── lebidul/            # Configuration Django
├── templates/          # Templates globaux
└── static/             # Assets statiques
```

## Prérequis

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Docker (optionnel, pour les services)

## Installation rapide

### 1. Cloner et installer

```bash
git clone <repo-url>
cd lebidul

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -e ".[dev]"
```

### 2. Configuration

```bash
# Copier le fichier de configuration
cp .env.example .env

# Éditer .env avec vos paramètres
```

### 3. Démarrer les services (Docker)

```bash
# Démarrer PostgreSQL et Redis
make db-start
# ou
docker-compose up -d
```

### 4. Initialiser la base de données

```bash
# Créer les migrations
make makemigrations

# Appliquer les migrations
make migrate

# Créer un superuser
make createsuperuser
```

### 5. Lancer le serveur

```bash
make run
# ou
python manage.py runserver
```

Accéder à :
- Site : http://localhost:8000
- Admin Wagtail : http://localhost:8000/admin/

## Commandes utiles

```bash
make help           # Affiche toutes les commandes
make dev            # Lance tout (db + migrations + serveur)
make test           # Lance les tests
make lint           # Vérifie le code
make format         # Formate le code
make shell          # Shell Django interactif
```

## Structure des modèles

### Snippets (données métier)

| Modèle | Description |
|--------|-------------|
| `Bidul` | Numéro du magazine (numero, mois, annee) |
| `Lieu` | Lieu culturel géolocalisé |
| `Categorie` | Catégorie (événements + articles) |
| `Auteur` | Auteur des chroniques |

### Pages CMS

| Page | Lié à | Description |
|------|-------|-------------|
| `BidulPage` | `Bidul` (OneToOne) | Contenu éditorial d'un numéro |
| `LieuPage` | `Lieu` (OneToOne) | Page publique d'un lieu |
| `ArticlePage` | `Auteur` (FK) | Chroniques et articles |
| `AgendaPage` | - | Page agenda avec calendrier/carte |

### Model Django

| Modèle | Description |
|--------|-------------|
| `Evenement` | Événement culturel (gros volume, API) |

## API

- `GET /api/evenements/` - Liste des événements (filtres: date_min, date_max, lieu, categorie, ville)
- `GET /api/lieux/` - Liste des lieux
- `GET /api/lieux/geojson/` - Export GeoJSON pour Leaflet

## Licence

Propriétaire - Radio Alpa / Le Bidul
