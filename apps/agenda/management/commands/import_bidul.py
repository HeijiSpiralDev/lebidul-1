"""
Commande d'import corrigée : bidul_archives.db → Wagtail models
Colonnes réelles de la DB SQLite
"""

import os
import sqlite3
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from django.utils.dateparse import parse_date, parse_time

from apps.agenda.models.snippets import Bidul, Lieu, Categorie, Auteur
from apps.agenda.models.evenement import Evenement


class Command(BaseCommand):
    help = "Importe les données de bidul_archives.db dans Wagtail"

    def add_arguments(self, parser):
        parser.add_argument(
            "--db",
            type=str,
            default="import_data/bidul_archives.db",
            help="Chemin vers bidul_archives.db"
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirme sans demander"
        )

    def handle(self, *args, **options):
        db_path = options["db"]
        
        if not os.path.exists(db_path):
            raise CommandError(f"❌ Fichier non trouvé: {db_path}")
        
        self.stdout.write(self.style.SUCCESS(f"✅ DB trouvée: {db_path}"))
        
        if not options["confirm"]:
            response = input("⚠️  Cela va IMPORTER les données. Continuer? (oui/Non) ")
            if response.lower() != "oui":
                self.stdout.write("❌ Annulation")
                return
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # === LIEU PAR DÉFAUT ===
        self.stdout.write("\n📍 Création lieu par défaut...")
        try:
            lieu_default, _ = Lieu.objects.get_or_create(
                nom="À déterminer",
                defaults={
                    "slug": "a-determiner",
                    "ville": "Le Mans",
                    "actif": True,
                }
            )
            self.stdout.write(self.style.SUCCESS(f"  ✅ Lieu défaut prêt: {lieu_default.nom}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Erreur lieu défaut: {str(e)}"))
            return
        
        # === CATÉGORIES (from type_evenement) ===
        self.stdout.write("\n🏷️  Import des CATÉGORIES...")
        try:
            cursor.execute("SELECT DISTINCT type_evenement FROM evenement WHERE type_evenement IS NOT NULL")
            cat_count = 0
            for row in cursor.fetchall():
                cat_name = row[0]
                if cat_name:
                    cat, created = Categorie.objects.get_or_create(
                        nom=cat_name[:100],
                        defaults={"slug": slugify(cat_name)[:50]}
                    )
                    if created:
                        cat_count += 1
            self.stdout.write(self.style.SUCCESS(f"  ✅ {cat_count} catégories créées"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  ⚠️  Catégories: {str(e)[:50]}"))
        
        # === BIDULS ===
        self.stdout.write("\n📕 Import des BIDULS...")
        try:
            cursor.execute("SELECT * FROM bidul ORDER BY numero DESC")
            bidul_count = 0
            for row in cursor.fetchall():
                numero = row[0]
                mois = row[1]
                annee = row[2]
                
                bidul, created = Bidul.objects.get_or_create(
                    numero=numero,
                    defaults={
                        "mois": mois or 0,
                        "annee": annee or 0,
                        "date_publication": None,
                        "nb_evenements": 0,
                        "data_indexer": {"source": "bidul_archives", "numero": numero},
                    }
                )
                if created:
                    bidul_count += 1
            self.stdout.write(self.style.SUCCESS(f"  ✅ {bidul_count} Biduls créés"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Erreur Biduls: {str(e)}"))
        
        # === ÉVÉNEMENTS ===
        self.stdout.write("\n📅 Import des ÉVÉNEMENTS (peut prendre du temps)...")
        try:
            cursor.execute("SELECT * FROM evenement ORDER BY date_evenement DESC LIMIT 50000")
            evt_count = 0
            evt_skip = 0
            
            for i, row in enumerate(cursor.fetchall()):
                try:
                    titre = row["nom"][:255] if row["nom"] else "Sans titre"
                    
                    try:
                        date_debut = parse_date(str(row["date_evenement"])) if row["date_evenement"] else None
                    except:
                        date_debut = None
                    
                    if not date_debut:
                        evt_skip += 1
                        continue
                    
                    try:
                        heure_str = row["heure"]
                        if heure_str:
                            heure_debut = parse_time(heure_str)
                        else:
                            heure_debut = None
                    except:
                        heure_debut = None
                    
                    lieu = None
                    if row["lieu_ref_id"]:
                        lieu = Lieu.objects.filter(id=row["lieu_ref_id"]).first()
                    if not lieu:
                        lieu = lieu_default
                    
                    categorie = None
                    if row["type_evenement"]:
                        categorie = Categorie.objects.filter(nom=row["type_evenement"]).first()
                    
                    bidul = None
                    if row["bidul_numero"]:
                        bidul = Bidul.objects.filter(numero=row["bidul_numero"]).first()
                    
                    prix = ""
                    if row["gratuit"]:
                        prix = "Gratuit"
                    elif row["prix_min"] and row["prix_max"]:
                        prix = f"{row['prix_min']}-{row['prix_max']}€"
                    elif row["prix_min"]:
                        prix = f"{row['prix_min']}€"
                    elif row["tarif_raw"]:
                        prix = row["tarif_raw"]
                    
                    evt, created = Evenement.objects.get_or_create(
                        titre=titre,
                        date_debut=date_debut,
                        defaults={
                            "slug": f"{slugify(titre)[:40]}-{date_debut}",
                            "description": row["raw_text_clean"] or "",
                            "date_fin": date_debut,
                            "heure_debut": heure_debut,
                            "heure_fin": None,
                            "lieu": lieu,
                            "categorie": categorie,
                            "source_bidul": bidul,
                            "prix": prix,
                            "url": "",
                            "statut": Evenement.Statut.PUBLIE,
                            "data_source": {
                                "source": "bidul_archives",
                                "original_id": row["id"],
                                "bidul_numero": row["bidul_numero"],
                                "confidence": float(row["confidence"]) if row["confidence"] else 0,
                            }
                        }
                    )
                    if created:
                        evt_count += 1
                    
                    if (i + 1) % 5000 == 0:
                        self.stdout.write(f"    ... {i + 1} traités")
                
                except Exception as e:
                    if evt_count < 5:
                        self.stdout.write(self.style.WARNING(f"    ⚠️  Erreur: {str(e)[:50]}"))
            
            self.stdout.write(self.style.SUCCESS(f"  ✅ {evt_count} événements créés ({evt_skip} ignorés)"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Erreur événements: {str(e)}"))
        
        # === RÉSUMÉ ===
        self.stdout.write(self.style.SUCCESS("\n" + "="*60))
        self.stdout.write(self.style.SUCCESS("✨ IMPORT TERMINÉ!"))
        self.stdout.write(self.style.SUCCESS("="*60))
        self.stdout.write(f"🏷️  Catégories: {Categorie.objects.count()}")
        self.stdout.write(f"📕 Biduls: {Bidul.objects.count()}")
        self.stdout.write(f"📅 Événements: {Evenement.objects.count()}")
        self.stdout.write(self.style.SUCCESS("="*60))
        
        conn.close()
