"""
Import des données depuis la base SQLite du Bidul Indexer.

Ordre d'import : Bidul → Lieu → Evenement.
Idempotent : ré-exécutable sans créer de doublons.

Usage :
    python manage.py import_from_indexer --db=/chemin/bidul_archives.db --dry-run
    python manage.py import_from_indexer --db=/chemin/bidul_archives.db
    python manage.py import_from_indexer --db=/chemin/bidul_archives.db --limit=100
    python manage.py import_from_indexer --db=/chemin/bidul_archives.db --since-numero=300
"""

import re
import sqlite3
from datetime import date, datetime, time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.agenda.models import Bidul, Evenement, Lieu


HEURE_PATTERNS = [
    re.compile(r"^(\d{1,2})\s*[h:]\s*(\d{2})$"),
    re.compile(r"^(\d{1,2})\s*h\s*(\d{1,2})?$"),
    re.compile(r"^(\d{1,2}):(\d{2})$"),
]


def parse_heure(raw):
    """Parse une chaîne d'heure libre. Retourne datetime.time ou None."""
    if not raw:
        return None
    s = str(raw).strip().lower()
    if not s:
        return None
    for pattern in HEURE_PATTERNS:
        m = pattern.match(s)
        if not m:
            continue
        hh = int(m.group(1))
        mm = int(m.group(2)) if m.group(2) else 0
        if 0 <= hh < 24 and 0 <= mm < 60:
            return time(hh, mm)
    return None


def parse_date(raw):
    """Parse une date au format ISO. Retourne datetime.date ou None."""
    if not raw:
        return None
    if isinstance(raw, date):
        return raw
    s = str(raw).strip()[:10]
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def unique_slug(base, used):
    """Retourne un slug unique en suffixant -2, -3, ... si nécessaire."""
    slug = base or "lieu"
    if slug not in used:
        used.add(slug)
        return slug
    i = 2
    while f"{slug}-{i}" in used:
        i += 1
    slug = f"{slug}-{i}"
    used.add(slug)
    return slug


class Command(BaseCommand):
    help = "Importe biduls, lieux et événements depuis la base SQLite Bidul Indexer."

    def add_arguments(self, parser):
        parser.add_argument("--db", required=True, help="Chemin vers bidul_archives.db")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="N'écrit rien (transaction rollback à la fin).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limite le nombre d'événements importés (debug).",
        )
        parser.add_argument(
            "--since-numero",
            type=int,
            default=None,
            help="N'importe que les biduls de numéro >= N.",
        )

    def handle(self, *args, **opts):
        db_path = Path(opts["db"])
        if not db_path.exists():
            raise CommandError(f"Fichier introuvable : {db_path}")

        self.dry_run = opts["dry_run"]
        self.limit = opts["limit"]
        self.since_numero = opts["since_numero"]

        self.stdout.write(self.style.MIGRATE_HEADING(f"Import depuis {db_path}"))
        if self.dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN : rollback final."))

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        try:
            with transaction.atomic():
                bidul_map = self.import_biduls(conn)
                lieu_map = self.import_lieux(conn)
                self.import_evenements(conn, bidul_map, lieu_map)

                if self.dry_run:
                    self.stdout.write(self.style.WARNING("Rollback (dry-run)."))
                    transaction.set_rollback(True)
        finally:
            conn.close()

        self.stdout.write(self.style.SUCCESS("Import terminé."))

    # ----- Biduls -----

    def import_biduls(self, conn):
        self.stdout.write(self.style.MIGRATE_HEADING("Biduls"))

        sql = "SELECT * FROM bidul"
        params = []
        if self.since_numero is not None:
            sql += " WHERE numero >= ?"
            params.append(self.since_numero)
        sql += " ORDER BY numero"

        rows = conn.execute(sql, params).fetchall()
        bidul_map = {}  # numero indexer → instance Bidul
        created = updated = 0

        for row in rows:
            numero = row["numero"]
            mois = row["mois"]
            annee = row["annee"]
            if not numero or not mois or not annee:
                self.stdout.write(
                    self.style.WARNING(f"  Bidul ignoré (champs manquants) : {dict(row)}")
                )
                continue

            data_indexer = {
                "pdf_filename": row["pdf_filename"] if "pdf_filename" in row.keys() else None,
                "extraction_status": row["extraction_status"]
                if "extraction_status" in row.keys()
                else None,
            }

            defaults = {
                "mois": mois,
                "annee": annee,
                "date_publication": date(annee, mois, 1),
                "data_indexer": {k: v for k, v in data_indexer.items() if v is not None},
            }

            obj, was_created = Bidul.objects.update_or_create(
                numero=numero,
                defaults=defaults,
            )
            bidul_map[numero] = obj
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(f"  {len(bidul_map)} biduls ({created} créés, {updated} màj)")
        return bidul_map

    # ----- Lieux -----

    def import_lieux(self, conn):
        self.stdout.write(self.style.MIGRATE_HEADING("Lieux"))

        rows = conn.execute("SELECT * FROM lieu_ref ORDER BY id").fetchall()
        existing_slugs = set(Lieu.objects.values_list("slug", flat=True))
        lieu_map = {}  # id indexer → instance Lieu
        created = updated = 0

        for row in rows:
            cols = row.keys()
            nom = (row["nom"] or "").strip()
            if not nom:
                continue

            ville = (row["ville"] or "").strip() if "ville" in cols else ""

            adresse_parts = []
            if "adresse_numero" in cols and row["adresse_numero"]:
                adresse_parts.append(str(row["adresse_numero"]).strip())
            if "adresse_voie" in cols and row["adresse_voie"]:
                adresse_parts.append(str(row["adresse_voie"]).strip())
            adresse = " ".join(adresse_parts)

            is_generic = bool(row["is_generic"]) if "is_generic" in cols else False

            defaults = {
                "nom": nom,
                "adresse": adresse,
                "code_postal": (row["code_postal"] or "").strip() if "code_postal" in cols else "",
                "ville": ville,
                "latitude": row["latitude"] if "latitude" in cols else None,
                "longitude": row["longitude"] if "longitude" in cols else None,
                "actif": not is_generic,
            }

            # Idempotence : on match d'abord par (nom, ville) — plus stable que le slug
            # qui dépend du suffixe de désambiguïsation.
            existing = Lieu.objects.filter(nom=nom, ville=ville).first()
            if existing:
                for field, value in defaults.items():
                    setattr(existing, field, value)
                existing.save()
                lieu_map[row["id"]] = existing
                updated += 1
            else:
                base_slug = slugify(f"{nom}-{ville}") if ville else slugify(nom)
                defaults["slug"] = unique_slug(base_slug[:50], existing_slugs)
                lieu = Lieu.objects.create(**defaults)
                lieu_map[row["id"]] = lieu
                created += 1

        self.stdout.write(f"  {len(lieu_map)} lieux ({created} créés, {updated} màj)")
        return lieu_map

    # ----- Événements -----

    def import_evenements(self, conn, bidul_map, lieu_map):
        self.stdout.write(self.style.MIGRATE_HEADING("Événements"))

        sql = "SELECT * FROM evenement"
        if self.limit:
            sql += f" LIMIT {int(self.limit)}"

        rows = conn.execute(sql).fetchall()

        # Pré-charge les indexer_id déjà importés pour idempotence
        existing_ids = set()
        for ev_id in Evenement.objects.exclude(data_source={}).values_list(
            "data_source__indexer_id", flat=True
        ):
            if ev_id is not None:
                existing_ids.add(ev_id)

        created = skipped_no_lieu = skipped_no_date = updated = 0
        to_create = []

        for row in rows:
            cols = row.keys()
            indexer_id = row["id"]

            lieu_indexer_id = row["lieu_ref_id"] if "lieu_ref_id" in cols else None
            lieu = lieu_map.get(lieu_indexer_id) if lieu_indexer_id else None
            if lieu is None:
                skipped_no_lieu += 1
                continue

            date_debut = parse_date(row["date_evenement"] if "date_evenement" in cols else None)
            if not date_debut:
                skipped_no_date += 1
                continue

            heure_debut = parse_heure(row["heure"] if "heure" in cols else None)

            # Fallback titre : nom indexer, sinon lieu_raw, sinon nom du lieu
            titre = (row["nom"] or "").strip() if "nom" in cols else ""
            if not titre and "lieu_raw" in cols and row["lieu_raw"]:
                titre = str(row["lieu_raw"]).strip()
            if not titre:
                titre = lieu.nom
            titre = titre[:255]

            bidul_numero = row["bidul_numero"] if "bidul_numero" in cols else None
            source_bidul = bidul_map.get(bidul_numero) if bidul_numero else None

            data_source = {
                "indexer_id": indexer_id,
            }
            if "confidence" in cols and row["confidence"] is not None:
                data_source["confidence"] = row["confidence"]
            if "raw_text" in cols and row["raw_text"]:
                data_source["raw_text"] = row["raw_text"]
            if "lieu_raw" in cols and row["lieu_raw"]:
                data_source["lieu_raw"] = row["lieu_raw"]

            defaults = {
                "titre": titre,
                "description": "",
                "date_debut": date_debut,
                "heure_debut": heure_debut,
                "lieu": lieu,
                "source_bidul": source_bidul,
                "prix": (row["tarif_raw"] or "").strip()[:100]
                if "tarif_raw" in cols and row["tarif_raw"]
                else "",
                "data_source": data_source,
                "statut": Evenement.Statut.BROUILLON,
            }

            if indexer_id in existing_ids:
                # Update existant
                ev = Evenement.objects.filter(data_source__indexer_id=indexer_id).first()
                if ev:
                    for field, value in defaults.items():
                        setattr(ev, field, value)
                    ev.save()
                    updated += 1
                continue

            base_slug = slugify(titre)[:50]
            ev = Evenement(slug=f"{base_slug}-{date_debut}", **defaults)
            to_create.append(ev)

            if len(to_create) >= 1000:
                Evenement.objects.bulk_create(to_create, batch_size=500)
                created += len(to_create)
                to_create = []
                self.stdout.write(f"  ... {created} événements créés")

        if to_create:
            Evenement.objects.bulk_create(to_create, batch_size=500)
            created += len(to_create)

        self.stdout.write(
            f"  {created} créés, {updated} màj, "
            f"{skipped_no_lieu} sans lieu, {skipped_no_date} sans date"
        )
