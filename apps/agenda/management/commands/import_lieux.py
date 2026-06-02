"""
Importe les lieux depuis lieu_ref ET relie les événements
À placer dans : apps/agenda/management/commands/import_lieux.py
"""

import os
import sqlite3
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from apps.agenda.models.snippets import Lieu
from apps.agenda.models.evenement import Evenement


class Command(BaseCommand):
    help = "Importe les lieux et relie les événements"

    def add_arguments(self, parser):
        parser.add_argument("--db", type=str, default="import_data/bidul_archives.db")
        parser.add_argument("--confirm", action="store_true")

    def handle(self, *args, **options):
        db_path = options["db"]
        
        if not os.path.exists(db_path):
            raise CommandError(f"❌ Fichier non trouvé: {db_path}")
        
        self.stdout.write(self.style.SUCCESS(f"✅ DB trouvée: {db_path}"))
        
        if not options["confirm"]:
            response = input("⚠️  Continuer? (oui/Non) ")
            if response.lower() != "oui":
                return
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # === IMPORT DES LIEUX ===
        self.stdout.write("\n📍 Import des LIEUX...")
        cursor.execute("SELECT * FROM lieu_ref")
        
        # Mapping ancien_id -> objet Lieu
        lieu_mapping = {}
        lieu_count = 0
        
        for row in cursor.fetchall():
            old_id = row["id"]
            nom = row["nom"] or "Lieu inconnu"
            
            # Adresse
            adresse_parts = []
            if row["adresse_numero"]:
                adresse_parts.append(str(row["adresse_numero"]))
            if row["adresse_voie"]:
                adresse_parts.append(str(row["adresse_voie"]))
            adresse = " ".join(adresse_parts)
            
            # Lat/Lng (arrondi pour DecimalField)
            try:
                lat = Decimal(str(round(float(row["latitude"]), 6))) if row["latitude"] else None
            except:
                lat = None
            try:
                lng = Decimal(str(round(float(row["longitude"]), 6))) if row["longitude"] else None
            except:
                lng = None
            
            # Slug unique
            base_slug = slugify(nom)[:40] or "lieu"
            slug = f"{base_slug}-{old_id}"
            
            try:
                lieu, created = Lieu.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "nom": nom[:200],
                        "adresse": adresse[:255],
                        "code_postal": (row["code_postal"] or "")[:10],
                        "ville": (row["ville"] or "Le Mans")[:100],
                        "latitude": lat,
                        "longitude": lng,
                        "actif": bool(row["actif"]) if row["actif"] is not None else True,
                    }
                )
                lieu_mapping[old_id] = lieu
                if created:
                    lieu_count += 1
                
                if lieu_count % 100 == 0 and created:
                    self.stdout.write(f"    ... {lieu_count} lieux")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"    ⚠️  {nom[:30]}: {str(e)[:40]}"))
        
        self.stdout.write(self.style.SUCCESS(f"  ✅ {lieu_count} lieux créés"))
        
        # === RE-LIER LES ÉVÉNEMENTS ===
        self.stdout.write("\n🔗 Liaison des événements aux lieux...")
        
        # Charge le mapping evenement_id -> lieu_ref_id
        cursor.execute("SELECT id, lieu_ref_id FROM evenement WHERE lieu_ref_id IS NOT NULL")
        evt_lieu_map = {row["id"]: row["lieu_ref_id"] for row in cursor.fetchall()}
        
        updated = 0
        not_found = 0
        
        # Parcourt tous les événements Wagtail
        for evt in Evenement.objects.all().iterator():
            try:
                original_id = evt.data_source.get("original_id") if evt.data_source else None
                if not original_id:
                    continue
                
                lieu_ref_id = evt_lieu_map.get(original_id)
                if not lieu_ref_id:
                    not_found += 1
                    continue
                
                new_lieu = lieu_mapping.get(lieu_ref_id)
                if new_lieu:
                    evt.lieu = new_lieu
                    evt.save(update_fields=["lieu"])
                    updated += 1
                    
                    if updated % 1000 == 0:
                        self.stdout.write(f"    ... {updated} événements reliés")
            except Exception as e:
                if updated < 3:
                    self.stdout.write(self.style.WARNING(f"    ⚠️  {str(e)[:40]}"))
        
        self.stdout.write(self.style.SUCCESS(f"  ✅ {updated} événements reliés ({not_found} sans lieu)"))
        
        # === RÉSUMÉ ===
        self.stdout.write(self.style.SUCCESS("\n" + "="*50))
        self.stdout.write(f"📍 Lieux: {Lieu.objects.count()}")
        self.stdout.write(f"📅 Événements: {Evenement.objects.count()}")
        self.stdout.write(self.style.SUCCESS("="*50))
        
        conn.close()
