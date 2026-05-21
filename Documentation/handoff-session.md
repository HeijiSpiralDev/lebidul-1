# Passation de session — refonte BDD lebidul.com

Document de reprise pour la prochaine session Claude Code.

## Contexte

Refonte du site `lebidul.com` (agenda culturel Le Mans) vers Django/Wagtail. La
session précédente s'est concentrée sur **la conception et l'implémentation du
schéma de la BDD du site** — pas l'import des données, pas le front.

Le dépôt est plus avancé que ne le laisse penser le terme "primitif" employé
par l'utilisateur : les modèles Snippets (`Bidul`, `Lieu`, `Categorie`,
`Auteur`), le Model `Evenement` + `SnippetViewSet`, et toutes les Pages CMS
(`HomePage`, `BidulPage`, `LieuPage`, `ArticlePage`, `FlexiblePage`,
`AgendaPage`, indexes) sont déjà en place. La commande d'import WordPress
`apps/migration/management/commands/import_from_sql.py` est fonctionnelle.

## Décisions de schéma actées

1. **`Bidul.mois`** : passé de `CharField(max_length=20)` à
   `PositiveSmallIntegerField` avec `Bidul.Mois` (IntegerChoices 1→12).
   `get_mois_display()` exposé via la property `mois_nom`. `BidulPage` utilise
   `mois_nom` dans `get_url_parts` pour préserver l'URL
   `/le-bidul-de-{mois_nom}-{annee}-{numero}/`.

2. **`Lieu` — index pour la vue carte** : ajout d'un
   `Index(fields=["latitude", "longitude"])` dans `Lieu.Meta.indexes`. Permet
   les requêtes bounding-box rapides de Leaflet (filtrage
   `latitude__range=..., longitude__range=...` à chaque pan/zoom).

3. **Pas de pollution du schéma site par les champs techniques de l'indexer**
   (`confidence`, `review_status`, `raw_text`, `lieu_raw`, `is_generic`,
   `geo_source`, `prix_min/max`, `is_regional`, etc.). Ces données sont
   stockées dans `Evenement.data_source` (JSONField déjà prévu) à l'import si
   on veut les conserver pour audit/traçabilité, mais ne sont pas exposées au
   métier.

4. **Pas de GeoDjango/PostGIS pour la v1**. ~760 lieux, l'ORM standard suffit.
   PostGIS deviendra utile si on fait "événements à <X km de moi".

5. **`Artiste` reporté**. Pas de modèle `Artiste` ni de table
   `Programmation` pour l'instant. Les noms d'artistes resteront dans
   `Evenement.description` ou dans `data_source`. À reprendre plus tard pour
   les "fiches artistes" mentionnées dans les notes UX.

6. **Schéma `Evenement` inchangé** par rapport à
   `lebidul_database_schema_v2.md` (titre, slug, description, date_debut/fin,
   heure_debut/fin, FK lieu CASCADE, FK categorie SET_NULL, FK source_bidul
   SET_NULL, prix CharField libre, url, image, data_source JSON, statut,
   timestamps, index sur date_debut, (statut, date_debut), (lieu, date_debut),
   source_bidul).

7. **Schéma `Lieu` inchangé** sinon (adresse reste un seul `CharField` libre
   — pas de découpe numero/voie).

## Migration générée

`apps/agenda/migrations/0002_bidul_mois_int_lieu_coord_index.py` —
`AlterField bidul.mois` + `AddIndex lieu(latitude, longitude)`.

`manage.py check` passe sans erreur.

## Source de données indexer (pour l'import futur)

Fichier SQLite : `bidul_archives.db` (~318 Ko, fourni par l'utilisateur, non
commité). Tables utiles :

| Table | Lignes | Notes |
|---|---|---|
| `bidul` | 305 | n° 1→311 (trous), `mois` INT 1-12, `pdf_filename`, `raw_text`, `extraction_status` |
| `lieu_ref` | 760 | **758 géolocalisés**, 147 `is_generic=1`, `nom_osm`, `geo_source/precision`, `adresse_numero/voie/code_postal` |
| `lieu_alias` | 689 | variantes — utile pour matching futur |
| `ville_ref` | 359 | |
| `evenement` | **30 363** | tous `review_status='pending'`, `lieu_ref_id` FK, `tarif_raw`+`prix_min/max`+`gratuit`, `confidence`, `is_regional`, `raw_text` |
| `contenu_evenement` | **36 726** | `artiste`, `nom_spectacle`, `style`, `ordre`, `artiste_ref_id` |
| `artiste_ref` | 1 966 | reporté (pas dans le schéma) |
| `artiste_alias` | 161 | reporté |

Mappings à faire à l'import (étape suivante, **pas encore commencée**) :

- `bidul.mois` INT → `Bidul.mois` INT (direct)
- `bidul.numero/annee/pdf_filename` → `Bidul.numero/annee` (+ pdf dans
  `BidulPage.pdf` quand la BidulPage est créée séparément)
- `lieu_ref.nom/ville/code_postal/latitude/longitude` → `Lieu.nom/ville/...`
- `lieu_ref.adresse_numero` + `lieu_ref.adresse_voie` → concat dans
  `Lieu.adresse`
- `lieu_ref.is_generic=1` peut servir à **exclure** les lieux "génériques" à
  l'import (147 sur 760), ou à les importer avec `actif=False` (à trancher
  avec l'utilisateur)
- `evenement.nom` → `Evenement.titre` (NULL fréquent → fallback sur
  `raw_text_clean` ou `lieu_raw`)
- `evenement.date_evenement` → `Evenement.date_debut`
- `evenement.heure` → `Evenement.heure_debut` (parsing nécessaire, format
  texte libre)
- `evenement.lieu_ref_id` → FK `Evenement.lieu` (mappé via id indexer → id
  Lieu Wagtail)
- `evenement.bidul_numero` → FK `Evenement.source_bidul` (via Bidul.numero)
- `evenement.tarif_raw` → `Evenement.prix`
- Tous les events importés en `Evenement.statut="brouillon"` (puisque tous
  `review_status='pending'` côté indexer) → workflow de revue manuelle
- `evenement.{raw_text, confidence, review_status, lieu_raw, prix_min, prix_max, gratuit, is_regional, source, type_evenement, genre_evenement}`
  → tout dans `Evenement.data_source` JSON pour traçabilité (à voir si
  utile, sinon on jette)

## Import WordPress

Le dump SQL est côté Windows :
`C:\Users\thiba\tibo\bidul\stages\bts1.2026\20260521_bakcup_lebidul.com\20260521_bakcup_lebidul.com.sql`.

La commande `import_from_sql` existe et reste compatible avec le nouveau
schéma (elle ne touche pas à `Bidul`/`Lieu`/`Evenement` — elle alimente
`Categorie`, `Auteur`, `ArticlePage`, `Image`, `Document`).

Workflow inchangé :
```
python manage.py import_from_sql \
  --sql=...\20260521_bakcup_lebidul.com.sql \
  --prefix=f4yxrr34kc_ \
  --media=...\media\images \
  --documents=...\media\documents
```

## Prochaine étape

Écrire `apps/migration/management/commands/import_from_indexer.py` :
- arg `--db /chemin/bidul_archives.db` (+ `--dry-run`, `--limit`,
  `--since-numero`)
- ordre : `Bidul` → `Lieu` (à partir de `lieu_ref` géolocalisés en priorité,
  décision sur les `is_generic`) → `Evenement` (matching FK via lieu_ref_id
  et bidul_numero)
- idempotent (`get_or_create` sur `Bidul.numero` et `Lieu.slug`)
- statut `brouillon` pour tous les événements importés

L'utilisateur n'a **pas encore validé** quoi faire des `lieu_ref.is_generic`
ni s'il faut conserver les champs techniques indexer dans `data_source`.
Lui poser la question avant de coder.

## Documents de référence

Tous fournis par l'utilisateur, à relire en priorité dans la nouvelle session
si besoin de contexte :

- `lebidul_database_schema_v2.md` — schéma de référence (Mermaid + détail des
  modèles), c'est la source de vérité du schéma actuel.
- `lebidul_backlog_v2.md` — backlog complet (8 epics, 141 pts, 10 sprints).
- `modelsVsSnippets.part1.md` / `part2.md` — justification de l'architecture
  Snippet vs Page.
- `siteWeb.notes.txt.md` — exigences UX brutes de l'utilisateur (fiche
  artiste mentionnée).
- `images.template.md` / `template.md` / `template.implementation.md` —
  références templates Wagtail (utile pour la phase suivante).

## État git à la reprise

Branche : `claude/lebidul-redesign-Sdpgs`

Commits (à pousser depuis la machine de l'utilisateur si pas encore fait —
le push depuis la session précédente était bloqué en 403 le temps que la
GitHub App soit installée) :

- `9306e69` — Bidul.mois en entier + index géo sur Lieu
- (ce commit) — Documentation de passation
