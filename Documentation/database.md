# Base de données — choix et reconstruction from scratch

## Moteur retenu : PostgreSQL

Le projet utilise **PostgreSQL** (configuré dans `lebidul/settings/base.py:96-105`).
Paramètres pilotés par variables d'environnement, avec des défauts
développement :

| Variable        | Défaut      |
|-----------------|-------------|
| `DB_NAME`       | `lebidul`   |
| `DB_USER`       | `lebidul`   |
| `DB_PASSWORD`   | `lebidul`   |
| `DB_HOST`       | `localhost` |
| `DB_PORT`       | `5432`      |

### Pourquoi Postgres (et pas SQLite ni MySQL)

- **Volume** : ~30 000 événements + 760 lieux + ~120 articles. SQLite gère,
  mais Postgres reste plus serein pour les requêtes filtrées par date +
  lieu + statut qu'on va empiler dans l'agenda.
- **`JSONField`** : on stocke des données brutes de l'indexer dans
  `Evenement.data_source`. Postgres a un type `jsonb` natif avec index ; les
  autres moteurs sérialisent en texte.
- **Index géographique** : `Lieu(latitude, longitude)` sert les requêtes
  bounding-box de Leaflet. Postgres ouvre aussi la porte à PostGIS si on
  veut un jour faire "événements à <X km de moi" sans réécrire les modèles.
- **Wagtail + production** : Wagtail recommande Postgres en prod ;
  rester sur le même moteur en dev évite les surprises de migration.

## Modèle de données

Les modèles Django sont la **source de vérité du schéma**. Aucun SQL n'est
écrit à la main — `manage.py migrate` génère et applique tout.

Trois apps :

- `apps/agenda/models/` — `Bidul`, `Lieu`, `Categorie`, `Auteur`, `Evenement`
- `apps/content/models.py` — `HomePage`, `BidulPage`, `LieuPage`,
  `ArticlePage`, `ArticleIndexPage`, `FlexiblePage`, `AgendaPage`
- `apps/theme/` — réglages d'apparence

Voir `lebidul_database_schema_v2.md` pour le diagramme et le détail.

## Reconstruction from scratch en une commande

`apps/migration/management/commands/reset_and_import.py` orchestre tout :

1. **DROP + CREATE** de la base Postgres (via une connexion à la base
   d'admin `postgres`, avec `DROP DATABASE … WITH (FORCE)` qui coupe les
   sessions actives — nécessite Postgres ≥ 13).
2. **`migrate`** — crée toutes les tables à partir des modèles Django.
3. **Import WordPress** — délègue à `import_from_sql` (articles, images,
   documents, catégories, auteurs, HomePage, ArticleIndexPage).
4. **Import Indexer** — délègue à `import_from_indexer` (Biduls, Lieux,
   Événements depuis `bidul_archives.db`).

Les trois commandes individuelles (`import_from_sql`, `import_from_indexer`,
`clear_import`) restent disponibles pour les ré-imports partiels et le
debug.

### Pré-requis

- Postgres ≥ 13 démarré et accessible avec les credentials du `.env`
- L'utilisateur Postgres a les droits `CREATEDB` (sinon `DROP/CREATE`
  échoue avec `permission denied`)
- Le venv Python est activé et les `requirements.txt` installés

### Exemple complet

```bash
python manage.py reset_and_import --confirm \
  --wp-sql=/chemin/Dump20260209.sql \
  --wp-prefix=f4yxrr34kc_ \
  --wp-media=/chemin/media/images \
  --wp-documents=/chemin/media/documents \
  --indexer-db=/chemin/bidul_archives.db
```

### Variantes

- **Reset + schéma seuls, sans imports** (utile pour partir vraiment vide) :
  ```bash
  python manage.py reset_and_import --confirm
  ```

- **Imports seulement, sans toucher à la BDD** (utile si on a déjà fait
  `migrate` et qu'on veut juste rejouer les imports) :
  ```bash
  python manage.py reset_and_import --skip-reset \
    --wp-sql=... --indexer-db=...
  ```

- **Indexer seul, sur un sous-ensemble** :
  ```bash
  python manage.py reset_and_import --skip-reset \
    --indexer-db=/chemin/bidul_archives.db \
    --indexer-since-numero=300 \
    --indexer-limit=500
  ```

### Arguments

| Arg                       | Défaut          | Effet                                                       |
|---------------------------|-----------------|-------------------------------------------------------------|
| `--confirm`               | —               | Requis pour le reset destructif                             |
| `--skip-reset`            | `False`         | Ne fait ni `DROP` ni `migrate`                              |
| `--admin-db`              | `postgres`      | Base Postgres utilisée pour faire le `DROP/CREATE`          |
| `--wp-sql`                | —               | Si absent, l'import WordPress est sauté                     |
| `--wp-prefix`             | `f4yxrr34kc_`   | Préfixe des tables WordPress                                |
| `--wp-media`              | —               | Dossier images WP                                           |
| `--wp-documents`          | —               | Dossier documents WP                                        |
| `--indexer-db`            | —               | Si absent, l'import Indexer est sauté                       |
| `--indexer-limit`         | —               | Limite le nombre d'événements (debug)                       |
| `--indexer-since-numero`  | —               | N'importe que les biduls de numéro ≥ N                      |

## Après l'import

- Créer un superuser : `python manage.py createsuperuser`
- Vérifier dans l'admin Wagtail (`/admin/`) :
  - Pages → Accueil / Chroniques (articles importés)
  - Snippets → Biduls, Lieux, Catégories, Auteurs
  - Événements (menu dédié dans la barre latérale)

## Commandes individuelles (rappel)

Détaillées dans `réimportation.md` et dans le code source :

- `import_from_sql --sql=… --prefix=… --media=… --documents=…`
- `import_from_indexer --db=… [--dry-run] [--limit=N] [--since-numero=N]`
- `clear_import --confirm` — vide articles/images/documents/catégories/auteurs
  sans toucher aux Biduls/Lieux/Événements
