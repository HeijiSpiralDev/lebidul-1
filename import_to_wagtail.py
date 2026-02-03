"""
Script d'import des événements dans Wagtail.

Généré automatiquement le 2026-02-02 14:13:44

À exécuter dans l'environnement Django:
    python manage.py shell < import_to_wagtail.py
"""

import os
import sys
import re
import django
from datetime import datetime, date, time
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lebidul.settings.dev')
django.setup()

from apps.agenda.models import Evenement, Lieu, Categorie

print("🚀 Début de l'import des données WordPress...")

# ========== DONNÉES À IMPORTER ==========
LOCATIONS_DATA = []

EVENTS_DATA = []

# ========== IMPORT DES LIEUX ==========
print("\n📍 Import des lieux...")

lieu_mapping = {}  # WordPress ID -> Wagtail Lieu

for loc_data in LOCATIONS_DATA:
    wp_id = loc_data.get('location_id')
    
    # Vérifier si existe déjà
    lieu_slug = f"lieu-wp-{wp_id}"
    
    try:
        lieu = Lieu.objects.get(slug=lieu_slug)
        created = False
    except Lieu.DoesNotExist:
        lieu = Lieu(
            slug=lieu_slug,
            nom=loc_data.get('location_name', 'Lieu inconnu')[:255],
            adresse=loc_data.get('location_address', '')[:255],
            ville=loc_data.get('location_town', 'Le Mans')[:100],
            code_postal=loc_data.get('location_postcode', '72000')[:10],
            actif=True,
        )
        lieu.save()
        created = True
    
    lieu_mapping[wp_id] = lieu
    
    if created:
        print(f"   ✅ Créé: {lieu.nom}")
    else:
        print(f"   ⏭️  Existe: {lieu.nom}")

print(f"\n✅ {len(lieu_mapping)} lieux traités\n")

# ========== CATÉGORIE PAR DÉFAUT ==========
print("🏷️  Création catégorie par défaut...")

try:
    categorie_defaut = Categorie.objects.get(slug="evenement-wordpress")
    created = False
except Categorie.DoesNotExist:
    categorie_defaut = Categorie(
        slug="evenement-wordpress",
        nom='Événement WordPress',
        description='Événements importés depuis WordPress',
        couleur='#E63946',
        ordre=999,
    )
    categorie_defaut.save()
    created = True

if created:
    print(f"   ✅ Créé: {categorie_defaut.nom}")
else:
    print(f"   ⏭️  Existe: {categorie_defaut.nom}")

# ========== IMPORT DES ÉVÉNEMENTS ==========
print("\n📅 Import des événements...")

imported_count = 0
skipped_count = 0
error_count = 0

for event_data in EVENTS_DATA:
    try:
        wp_event_id = event_data.get('event_id')
        wp_location_id = event_data.get('location_id')
        
        # Récupérer le lieu
        lieu = lieu_mapping.get(wp_location_id)
        if not lieu:
            print(f"   ⚠️  Pas de lieu pour événement {wp_event_id}, création lieu par défaut")
            lieu = lieu_mapping.get(1)  # Lieu par défaut
        
        # Parser les dates
        date_debut_str = event_data.get('event_start_date')
        date_fin_str = event_data.get('event_end_date')
        heure_debut_str = event_data.get('event_start_time')
        heure_fin_str = event_data.get('event_end_time')
        
        try:
            date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date() if date_debut_str else None
            date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date() if date_fin_str else date_debut
            
            if heure_debut_str:
                try:
                    heure_debut = datetime.strptime(heure_debut_str, '%H:%M:%S').time()
                except:
                    try:
                        heure_debut = datetime.strptime(heure_debut_str, '%H:%M').time()
                    except:
                        heure_debut = None
            else:
                heure_debut = None
                
            if heure_fin_str:
                try:
                    heure_fin = datetime.strptime(heure_fin_str, '%H:%M:%S').time()
                except:
                    try:
                        heure_fin = datetime.strptime(heure_fin_str, '%H:%M').time()
                    except:
                        heure_fin = None
            else:
                heure_fin = None
                
        except Exception as e:
            print(f"   ⚠️  Erreur parsing date pour événement {wp_event_id}: {e}")
            date_debut = None
        
        if not date_debut:
            print(f"   ⚠️  Pas de date pour événement {wp_event_id}, skip")
            skipped_count += 1
            continue
        
        # Créer ou mettre à jour l'événement
        slug = f"event-wp-{wp_event_id}"
        
        try:
            event = Evenement.objects.get(slug=slug)
            created = False
            # Mettre à jour
            event.titre = (event_data.get('event_name') or 'Sans titre')[:255]
            event.description = event_data.get('post_content', '')
            event.date_debut = date_debut
            event.date_fin = date_fin
            event.heure_debut = heure_debut
            event.heure_fin = heure_fin
            event.lieu = lieu
            event.categorie = categorie_defaut
            event.statut = 'publie' if event_data.get('event_status') == '1' else 'brouillon'
            event.save()
        except Evenement.DoesNotExist:
            event = Evenement(
                slug=slug,
                titre=(event_data.get('event_name') or 'Sans titre')[:255],
                description=event_data.get('post_content', ''),
                date_debut=date_debut,
                date_fin=date_fin,
                heure_debut=heure_debut,
                heure_fin=heure_fin,
                lieu=lieu,
                categorie=categorie_defaut,
                statut='publie' if event_data.get('event_status') == '1' else 'brouillon',
            )
            event.save()
            created = True
        
        if created:
            print(f"   ✅ Créé: {event.titre} ({event.date_debut})")
            imported_count += 1
        else:
            print(f"   🔄 MAJ: {event.titre} ({event.date_debut})")
            imported_count += 1
            
    except Exception as e:
        print(f"   ❌ Erreur événement {event_data.get('event_id')}: {e}")
        import traceback
        traceback.print_exc()
        error_count += 1
        continue

print(f"\n" + "="*60)
print(f"📊 RÉSUMÉ IMPORT")
print(f"="*60)
print(f"✅ Importés/MAJ: {imported_count}")
print(f"⏭️  Ignorés: {skipped_count}")
print(f"❌ Erreurs: {error_count}")
print(f"="*60)

print("\n🎉 Import terminé!")
