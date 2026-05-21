"""
Orchestrateur "from scratch" : DROP/CREATE Postgres → migrate → imports.

Enchaîne les commandes existantes (import_from_sql, import_from_indexer) en
partant d'une base Postgres vide. Les commandes individuelles restent
utilisables indépendamment pour les ré-imports partiels.

Usage minimal (reset + schéma seuls, sans imports) :
    python manage.py reset_and_import --confirm

Usage complet :
    python manage.py reset_and_import --confirm \\
        --wp-sql=/chemin/dump.sql \\
        --wp-prefix=f4yxrr34kc_ \\
        --wp-media=/chemin/media/images \\
        --wp-documents=/chemin/media/documents \\
        --indexer-db=/chemin/bidul_archives.db

Sans reset (juste enchainer les imports sur une BDD déjà migrate) :
    python manage.py reset_and_import --skip-reset \\
        --wp-sql=... --indexer-db=...
"""

from pathlib import Path

import psycopg2
from psycopg2 import sql as psql

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections


class Command(BaseCommand):
    help = "DROP/CREATE Postgres + migrate + import WordPress + import indexer."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirme la destruction de la base existante (requis sauf si --skip-reset).",
        )
        parser.add_argument(
            "--skip-reset",
            action="store_true",
            help="N'effectue ni DROP ni migrate. Enchaîne seulement les imports.",
        )
        parser.add_argument(
            "--admin-db",
            default="postgres",
            help="Base Postgres d'administration utilisée pour DROP/CREATE (défaut: postgres).",
        )

        # WordPress
        parser.add_argument("--wp-sql", help="Chemin vers le dump MySQL WordPress.")
        parser.add_argument(
            "--wp-prefix",
            default="f4yxrr34kc_",
            help="Préfixe des tables WordPress (défaut: f4yxrr34kc_).",
        )
        parser.add_argument("--wp-media", help="Dossier media/images WordPress.")
        parser.add_argument("--wp-documents", help="Dossier media/documents WordPress.")

        # Indexer
        parser.add_argument("--indexer-db", help="Chemin vers bidul_archives.db.")
        parser.add_argument(
            "--indexer-limit",
            type=int,
            help="Limite le nombre d'événements importés (debug).",
        )
        parser.add_argument(
            "--indexer-since-numero",
            type=int,
            help="N'importe que les biduls de numéro >= N.",
        )

    def handle(self, *args, **opts):
        if not opts["skip_reset"] and not opts["confirm"]:
            raise CommandError(
                "Opération destructive. Ajoute --confirm pour valider "
                "(ou --skip-reset pour ne faire que les imports)."
            )

        wp_sql = opts.get("wp_sql")
        indexer_db = opts.get("indexer_db")

        for path_opt in ("wp_sql", "wp_media", "wp_documents", "indexer_db"):
            value = opts.get(path_opt)
            if value and not Path(value).exists():
                raise CommandError(f"--{path_opt.replace('_', '-')} : introuvable ({value})")

        # 1. DROP + CREATE Postgres
        if not opts["skip_reset"]:
            self._reset_database(opts["admin_db"])
            self._migrate()
        else:
            self.stdout.write(self.style.WARNING("Reset BDD sauté (--skip-reset)."))

        # 2. Import WordPress (articles, images, documents, catégories, auteurs)
        if wp_sql:
            self.stdout.write(self.style.MIGRATE_HEADING("Import WordPress"))
            wp_args = ["--sql", wp_sql, "--prefix", opts["wp_prefix"]]
            if opts.get("wp_media"):
                wp_args += ["--media", opts["wp_media"]]
            if opts.get("wp_documents"):
                wp_args += ["--documents", opts["wp_documents"]]
            call_command("import_from_sql", *wp_args)
        else:
            self.stdout.write(self.style.WARNING("Import WordPress sauté (--wp-sql absent)."))

        # 3. Import Indexer (biduls, lieux, événements)
        if indexer_db:
            self.stdout.write(self.style.MIGRATE_HEADING("Import Indexer"))
            idx_args = ["--db", indexer_db]
            if opts.get("indexer_limit"):
                idx_args += ["--limit", str(opts["indexer_limit"])]
            if opts.get("indexer_since_numero"):
                idx_args += ["--since-numero", str(opts["indexer_since_numero"])]
            call_command("import_from_indexer", *idx_args)
        else:
            self.stdout.write(
                self.style.WARNING("Import Indexer sauté (--indexer-db absent).")
            )

        self.stdout.write(self.style.SUCCESS("\nReset + imports terminés."))
        self.stdout.write(
            "Pense à créer un superuser : python manage.py createsuperuser"
        )

    def _reset_database(self, admin_db):
        """DROP + CREATE de la base cible via une connexion à la base d'admin."""
        db = settings.DATABASES["default"]
        target = db["NAME"]

        # Ferme toutes les connexions Django à la base cible avant DROP.
        connections.close_all()

        self.stdout.write(
            self.style.MIGRATE_HEADING(f"DROP + CREATE DATABASE {target}")
        )

        conn = psycopg2.connect(
            dbname=admin_db,
            user=db["USER"],
            password=db["PASSWORD"],
            host=db["HOST"],
            port=db["PORT"],
        )
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                # WITH (FORCE) requiert Postgres >= 13 et coupe les connexions
                # actives sur la base cible avant le drop.
                cur.execute(
                    psql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                        psql.Identifier(target)
                    )
                )
                cur.execute(
                    psql.SQL("CREATE DATABASE {}").format(psql.Identifier(target))
                )
        finally:
            conn.close()

        self.stdout.write(self.style.SUCCESS(f"  Base {target} recréée."))

    def _migrate(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Migrations"))
        call_command("migrate", verbosity=1)
