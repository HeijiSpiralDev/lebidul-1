"""
Migration WordPress SQL dump → Wagtail.

Parse directement le fichier SQL sans nécessiter MySQL local.

Usage:
    python manage.py import_from_sql --sql=wordpress_dump.sql --dry-run
    python manage.py import_from_sql --sql=wordpress_dump.sql
    python manage.py import_from_sql --sql=wordpress_dump.sql --media=./uploads/
"""

import re
from datetime import datetime
from pathlib import Path

from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from wagtail.images.models import Image
from wagtail.models import Page

from apps.agenda.models import Auteur, Categorie
from apps.content.models import ArticleIndexPage, ArticlePage, HomePage


class SQLDumpParser:
    """
    Parse un dump SQL MySQL et extrait les données des tables WordPress.
    """

    def __init__(self, sql_path, table_prefix="wp_"):
        self.sql_path = Path(sql_path)
        self.prefix = table_prefix
        self.tables = {}

    def parse(self):
        """Parse le fichier SQL et extrait les INSERT statements."""
        print(f"Parsing {self.sql_path}...")
        
        current_table = None
        insert_buffer = ""
        in_insert = False

        with open(self.sql_path, "r", encoding="utf-8", errors="replace") as f:
            for line_num, line in enumerate(f, 1):
                # Détecter le début d'un INSERT
                insert_match = re.match(
                    r"INSERT INTO `?(\w+)`?\s+(?:\([^)]+\)\s+)?VALUES",
                    line,
                    re.IGNORECASE
                )
                
                if insert_match:
                    current_table = insert_match.group(1)
                    if current_table not in self.tables:
                        self.tables[current_table] = []
                    in_insert = True
                    insert_buffer = line
                elif in_insert:
                    insert_buffer += line
                
                # Fin de l'INSERT (ligne se terminant par ;)
                if in_insert and line.rstrip().endswith(";"):
                    self._parse_insert(current_table, insert_buffer)
                    insert_buffer = ""
                    in_insert = False

                # Progress
                if line_num % 100000 == 0:
                    print(f"  ... {line_num} lignes lues")

        print(f"Tables trouvées: {list(self.tables.keys())}")
        return self.tables

    def _parse_insert(self, table_name, insert_sql):
        """Parse un INSERT statement et extrait les valeurs."""
        # Extraire la partie VALUES (...)
        values_match = re.search(r"VALUES\s*(.+);?\s*$", insert_sql, re.DOTALL | re.IGNORECASE)
        if not values_match:
            return

        values_str = values_match.group(1)
        
        # Extraire chaque tuple de valeurs
        rows = self._extract_value_tuples(values_str)
        self.tables[table_name].extend(rows)

    def _extract_value_tuples(self, values_str):
        """Extrait les tuples de valeurs d'un INSERT."""
        rows = []
        current_tuple = []
        current_value = ""
        in_string = False
        string_char = None
        escape_next = False
        paren_depth = 0

        i = 0
        while i < len(values_str):
            char = values_str[i]

            if escape_next:
                current_value += char
                escape_next = False
                i += 1
                continue

            if char == "\\" and in_string:
                escape_next = True
                current_value += char
                i += 1
                continue

            if char in ("'", '"') and not in_string:
                in_string = True
                string_char = char
                i += 1
                continue
            elif char == string_char and in_string:
                # Vérifier si c'est un double quote (escape)
                if i + 1 < len(values_str) and values_str[i + 1] == string_char:
                    current_value += char
                    i += 2
                    continue
                in_string = False
                string_char = None
                i += 1
                continue

            if in_string:
                current_value += char
                i += 1
                continue

            # Hors string
            if char == "(":
                if paren_depth == 0:
                    current_value = ""
                    current_tuple = []
                paren_depth += 1
                if paren_depth > 1:
                    current_value += char
                i += 1
                continue

            if char == ")":
                paren_depth -= 1
                if paren_depth == 0:
                    # Fin du tuple
                    current_tuple.append(self._clean_value(current_value))
                    rows.append(current_tuple)
                    current_value = ""
                elif paren_depth > 0:
                    current_value += char
                i += 1
                continue

            if char == "," and paren_depth == 1:
                current_tuple.append(self._clean_value(current_value))
                current_value = ""
                i += 1
                continue

            if paren_depth >= 1:
                current_value += char

            i += 1

        return rows

    def _clean_value(self, value):
        """Nettoie une valeur extraite."""
        value = value.strip()
        if value.upper() == "NULL":
            return None
        # Unescape
        value = value.replace("\\'", "'")
        value = value.replace('\\"', '"')
        value = value.replace("\\n", "\n")
        value = value.replace("\\r", "\r")
        value = value.replace("\\t", "\t")
        value = value.replace("\\\\", "\\")
        return value

    def get_table(self, name):
        """Récupère les données d'une table."""
        full_name = f"{self.prefix}{name}"
        return self.tables.get(full_name, [])


class Command(BaseCommand):
    help = "Importe depuis un dump SQL WordPress"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sql",
            type=str,
            required=True,
            help="Chemin vers le fichier SQL dump WordPress",
        )
        parser.add_argument(
            "--media",
            type=str,
            help="Chemin vers le dossier des médias WordPress (wp-content/uploads)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simule l'import sans modifier la base",
        )
        parser.add_argument(
            "--prefix",
            type=str,
            default="wp_",
            help="Préfixe des tables WordPress (défaut: wp_)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limiter le nombre d'articles importés (0 = tous)",
        )

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]
        self.sql_path = Path(options["sql"])
        self.media_path = Path(options["media"]) if options["media"] else None
        self.prefix = options["prefix"]
        self.limit = options["limit"]

        if not self.sql_path.exists():
            raise CommandError(f"Fichier non trouvé: {self.sql_path}")

        # Parser le SQL
        parser = SQLDumpParser(self.sql_path, self.prefix)
        self.data = parser.parse()

        # Identifier les colonnes (structure standard WordPress)
        self.columns = {
            "posts": [
                "ID", "post_author", "post_date", "post_date_gmt", "post_content",
                "post_title", "post_excerpt", "post_status", "comment_status",
                "ping_status", "post_password", "post_name", "to_ping", "pinged",
                "post_modified", "post_modified_gmt", "post_content_filtered",
                "post_parent", "guid", "menu_order", "post_type", "post_mime_type",
                "comment_count"
            ],
            "users": [
                "ID", "user_login", "user_pass", "user_nicename", "user_email",
                "user_url", "user_registered", "user_activation_key", "user_status",
                "display_name"
            ],
            "terms": ["term_id", "name", "slug", "term_group"],
            "term_taxonomy": [
                "term_taxonomy_id", "term_id", "taxonomy", "description",
                "parent", "count"
            ],
            "term_relationships": ["object_id", "term_taxonomy_id", "term_order"],
            "postmeta": ["meta_id", "post_id", "meta_key", "meta_value"],
        }

        # Stats
        self.stats = {
            "categories": 0,
            "authors": 0,
            "articles": 0,
            "media": 0,
            "skipped": 0,
            "errors": 0,
        }

        # Mappings
        self.category_map = {}  # term_id → Categorie
        self.author_map = {}    # user_id → Auteur
        self.media_map = {}     # post_id → Image
        self.term_taxonomy_map = {}  # term_taxonomy_id → term_id

        with transaction.atomic():
            if self.dry_run:
                self.stdout.write(self.style.WARNING("=== DRY RUN ===\n"))

            # Build term_taxonomy mapping
            self._build_term_taxonomy_map()

            # Import dans l'ordre
            self.import_categories()
            self.import_authors()
            self.import_media()
            self.import_articles()

            if self.dry_run:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("\nRollback (dry-run)"))

        # Résumé
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 40))
        self.stdout.write(self.style.SUCCESS("RÉSUMÉ DE L'IMPORT"))
        self.stdout.write(self.style.SUCCESS("=" * 40))
        for key, count in self.stats.items():
            self.stdout.write(f"  {key}: {count}")

    def _build_term_taxonomy_map(self):
        """Construit le mapping term_taxonomy_id → term_id."""
        rows = self.data.get(f"{self.prefix}term_taxonomy", [])
        for row in rows:
            if len(row) >= 3:
                data = dict(zip(self.columns["term_taxonomy"], row))
                self.term_taxonomy_map[data["term_taxonomy_id"]] = {
                    "term_id": data["term_id"],
                    "taxonomy": data["taxonomy"],
                }

    def _get_row_dict(self, table_name, row):
        """Convertit une row en dictionnaire."""
        columns = self.columns.get(table_name, [])
        if len(columns) == 0 or len(row) == 0:
            return {}
        # Ajuster si le nombre de colonnes diffère
        return dict(zip(columns, row))

    def import_categories(self):
        """Import des catégories WordPress."""
        self.stdout.write("\n→ Import des catégories...")

        terms = self.data.get(f"{self.prefix}terms", [])
        term_taxonomy = self.data.get(f"{self.prefix}term_taxonomy", [])

        # Trouver les term_id qui sont des catégories
        category_term_ids = set()
        for row in term_taxonomy:
            data = self._get_row_dict("term_taxonomy", row)
            if data.get("taxonomy") == "category":
                category_term_ids.add(data.get("term_id"))

        for row in terms:
            data = self._get_row_dict("terms", row)
            term_id = data.get("term_id")
            
            if term_id not in category_term_ids:
                continue

            name = data.get("name", "")
            slug = data.get("slug", "") or slugify(name)

            if not name:
                continue

            if not self.dry_run:
                obj, created = Categorie.objects.get_or_create(
                    slug=slug[:50],
                    defaults={"nom": name[:100]}
                )
                self.category_map[term_id] = obj
                if created:
                    self.stats["categories"] += 1
                    self.stdout.write(f"  + Catégorie: {name}")
            else:
                self.stats["categories"] += 1
                self.stdout.write(f"  [DRY] Catégorie: {name}")

    def import_authors(self):
        """Import des auteurs WordPress."""
        self.stdout.write("\n→ Import des auteurs...")

        users = self.data.get(f"{self.prefix}users", [])

        for row in users:
            data = self._get_row_dict("users", row)
            user_id = data.get("ID")
            login = data.get("user_login", "")
            display_name = data.get("display_name", "") or login
            email = data.get("user_email", "")

            if not login:
                continue

            if not self.dry_run:
                obj, created = Auteur.objects.get_or_create(
                    slug=login[:50],
                    defaults={
                        "nom": display_name[:100],
                        "email": email[:254] if email else "",
                    }
                )
                self.author_map[user_id] = obj
                if created:
                    self.stats["authors"] += 1
                    self.stdout.write(f"  + Auteur: {display_name}")
            else:
                self.stats["authors"] += 1
                self.stdout.write(f"  [DRY] Auteur: {display_name}")

    def import_media(self):
        """Import des médias (attachments)."""
        if not self.media_path:
            self.stdout.write("\n→ Import des médias: SKIPPED (pas de dossier --media)")
            return

        self.stdout.write("\n→ Import des médias...")

        posts = self.data.get(f"{self.prefix}posts", [])

        for row in posts:
            data = self._get_row_dict("posts", row)
            
            if data.get("post_type") != "attachment":
                continue

            post_id = data.get("ID")
            title = data.get("post_title", "") or "Sans titre"
            guid = data.get("guid", "")  # URL du fichier

            if not guid:
                continue

            # Extraire le chemin relatif depuis l'URL
            # Ex: https://lebidul.com/wp-content/uploads/2024/01/image.jpg
            # → 2024/01/image.jpg
            match = re.search(r"/uploads/(.+)$", guid)
            if not match:
                continue

            relative_path = match.group(1)
            local_path = self.media_path / relative_path

            if not local_path.exists():
                # Essayer sans le préfixe de date
                self.stats["skipped"] += 1
                continue

            if not self.dry_run:
                try:
                    with open(local_path, "rb") as f:
                        image = Image(title=title[:255])
                        image.file.save(local_path.name, ImageFile(f), save=True)
                        self.media_map[post_id] = image
                        self.stats["media"] += 1
                        self.stdout.write(f"  + Média: {local_path.name}")
                except Exception as e:
                    self.stats["errors"] += 1
                    self.stdout.write(self.style.ERROR(f"  ✗ Erreur média: {e}"))
            else:
                self.stats["media"] += 1
                self.stdout.write(f"  [DRY] Média: {local_path.name}")

    def import_articles(self):
        """Import des articles WordPress avec gestion des doublons."""
        self.stdout.write("\n→ Import des articles...")

        # ======================================================
        # SOLUTION 1 : Vérifier si les pages existent déjà
        # ======================================================
        
        # 1. Vérifier/créer la HomePage
        if not self.dry_run:
            # D'abord chercher une HomePage existante
            home = HomePage.objects.filter(slug='accueil').first()
            
            if home:
                self.stdout.write(self.style.WARNING('  ⚠ HomePage existe déjà, réutilisation...'))
            else:
                # Vérifier si une page avec ce slug existe déjà (peut-être d'un autre type)
                existing_page = Page.objects.filter(slug='accueil', depth=2).first()
                if existing_page:
                    self.stdout.write(self.style.ERROR(
                        f'  ✗ Une page avec le slug "accueil" existe déjà (type: {existing_page.specific_class.__name__})'
                    ))
                    self.stdout.write(self.style.WARNING('  💡 Supprime cette page ou utilise un autre slug'))
                    raise CommandError('Conflit de slug détecté. Impossible de continuer.')
                
                # Créer la HomePage
                root = Page.objects.get(depth=1)
                home = HomePage(title="Accueil", slug="accueil")
                root.add_child(instance=home)
                self.stdout.write(self.style.SUCCESS("  ✓ HomePage créée"))
        else:
            home = None

        # 2. Vérifier/créer l'ArticleIndexPage
        parent_page = ArticleIndexPage.objects.first()
        if not parent_page and not self.dry_run:
            # Chercher d'abord une ArticleIndexPage existante
            parent_page = ArticleIndexPage.objects.filter(slug='chroniques').first()
            
            if parent_page:
                self.stdout.write(self.style.WARNING('  ⚠ ArticleIndexPage existe déjà, réutilisation...'))
            else:
                # Vérifier conflit de slug
                existing_page = Page.objects.filter(slug='chroniques').child_of(home).first()
                if existing_page:
                    self.stdout.write(self.style.ERROR(
                        f'  ✗ Une page avec le slug "chroniques" existe déjà (type: {existing_page.specific_class.__name__})'
                    ))
                    raise CommandError('Conflit de slug détecté. Impossible de continuer.')
                
                parent_page = ArticleIndexPage(title="Chroniques", slug="chroniques")
                home.add_child(instance=parent_page)
                self.stdout.write(self.style.SUCCESS("  ✓ ArticleIndexPage créée"))

        # Récupérer les relations article → catégories
        term_relationships = self.data.get(f"{self.prefix}term_relationships", [])
        post_categories = {}  # post_id → [term_ids]
        for row in term_relationships:
            if len(row) >= 2:
                object_id = row[0]
                term_taxonomy_id = row[1]
                # Récupérer le term_id depuis term_taxonomy
                tt_info = self.term_taxonomy_map.get(term_taxonomy_id, {})
                if tt_info.get("taxonomy") == "category":
                    term_id = tt_info.get("term_id")
                    if object_id not in post_categories:
                        post_categories[object_id] = []
                    post_categories[object_id].append(term_id)

        # Récupérer les thumbnails (featured images)
        postmeta = self.data.get(f"{self.prefix}postmeta", [])
        post_thumbnails = {}  # post_id → thumbnail_id
        for row in postmeta:
            data = self._get_row_dict("postmeta", row)
            if data.get("meta_key") == "_thumbnail_id":
                post_thumbnails[data.get("post_id")] = data.get("meta_value")

        # Import des articles
        posts = self.data.get(f"{self.prefix}posts", [])
        count = 0

        for row in posts:
            data = self._get_row_dict("posts", row)

            # Filtrer: uniquement les posts (tous statuts)
            if data.get("post_type") != "post":
                continue
            
            # Garder seulement les articles publiés
            excluded_statuses = ["trash", "auto-draft", "draft", "pending", "future", "private", "inherit"]
            if data.get("post_status") in excluded_statuses:
                continue

            post_id = data.get("ID")
            title = data.get("post_title", "") or "Sans titre"
            raw_slug = data.get("post_name", "")
            
            # Nettoyer le slug WordPress (supprimer caractères spéciaux)
            if raw_slug:
                # Remplacer les caractères problématiques
                slug = raw_slug.replace("°", "").replace("–", "-").replace("—", "-")
                slug = slugify(slug)  # Réappliquer slugify pour nettoyer
            else:
                slug = slugify(title)
            
            content = data.get("post_content", "") or ""
            excerpt = data.get("post_excerpt", "")
            post_date = data.get("post_date", "")
            author_id = data.get("post_author")

            # Limiter si demandé
            if self.limit and count >= self.limit:
                break

            # Parser la date
            try:
                if isinstance(post_date, str):
                    pub_date = datetime.strptime(post_date[:10], "%Y-%m-%d").date()
                else:
                    pub_date = post_date.date() if hasattr(post_date, 'date') else None
            except (ValueError, AttributeError):
                pub_date = None

            # Nettoyer le contenu
            content = self.clean_html(content)
            intro = excerpt or self.extract_intro(content)

            if not self.dry_run:
                # Vérifier si existe déjà
                if ArticlePage.objects.filter(slug=slug[:255]).exists():
                    self.stdout.write(f"  ~ Existe déjà: {title[:50]}")
                    self.stats["skipped"] += 1
                    continue

                try:
                    article = ArticlePage(
                        title=title[:255],
                        slug=slug[:255],
                        introduction=intro[:500] if intro else "",
                        date_publication=pub_date,
                        auteur=self.author_map.get(author_id),
                    )

                    # Image à la une
                    thumbnail_id = post_thumbnails.get(post_id)
                    if thumbnail_id and thumbnail_id in self.media_map:
                        article.image_principale = self.media_map[thumbnail_id]

                    # Contenu StreamField
                    article.contenu = [("texte", content)]

                    # Ajouter comme enfant de la page index
                    parent_page.add_child(instance=article)

                    # Catégories (M2M)
                    cat_term_ids = post_categories.get(post_id, [])
                    cats = [
                        self.category_map[tid]
                        for tid in cat_term_ids
                        if tid in self.category_map
                    ]
                    if cats:
                        article.categories.set(cats)

                    self.stats["articles"] += 1
                    count += 1
                    self.stdout.write(f"  + Article: {title[:50]}")

                except Exception as e:
                    self.stats["errors"] += 1
                    self.stdout.write(self.style.ERROR(f"  ✗ Erreur ({title[:30]}): {e}"))
            else:
                self.stats["articles"] += 1
                count += 1
                self.stdout.write(f"  [DRY] Article: {title[:50]}")

    def clean_html(self, html):
        """Nettoie le HTML WordPress."""
        if not html:
            return ""

        # Supprimer les shortcodes WordPress [shortcode]...[/shortcode]
        html = re.sub(r'\[/?[^\]]+\]', '', html)

        # Supprimer les commentaires HTML
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

        # Supprimer les classes WordPress
        html = re.sub(r'\s+class="[^"]*"', '', html)

        # Supprimer les styles inline
        html = re.sub(r'\s+style="[^"]*"', '', html)

        # Supprimer les data-* attributes
        html = re.sub(r'\s+data-[a-z-]+="[^"]*"', '', html)

        # Nettoyer les espaces multiples
        html = re.sub(r'\n\s*\n', '\n\n', html)

        return html.strip()

    def extract_intro(self, html, max_chars=300):
        """Extrait le début du texte comme introduction."""
        from html import unescape

        # Supprimer les tags HTML
        text = re.sub(r'<[^>]+>', '', html)
        text = unescape(text).strip()

        # Limiter la longueur
        if len(text) > max_chars:
            # Couper à la fin d'une phrase si possible
            cut_point = text.rfind('. ', 0, max_chars)
            if cut_point > max_chars // 2:
                text = text[:cut_point + 1]
            else:
                text = text[:max_chars] + "..."

        return text