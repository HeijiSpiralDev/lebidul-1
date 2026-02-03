#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'extraction des événements WordPress depuis un dump SQL.

Extrait les événements depuis wp_posts (tribe_events, ai1ec_event, feedback)
et génère un script import_to_wagtail.py prêt à l'emploi.

Usage:
    python extract_wordpress_events.py "chemin/vers/dump.sql"
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime

def parse_sql_value(value):
    """Parse une valeur SQL en Python."""
    if value == 'NULL' or value is None:
        return None
    # Enlever les quotes
    if value.startswith("'") and value.endswith("'"):
        value = value[1:-1]
    # Décoder les échappements SQL
    value = value.replace("\\'", "'")
    value = value.replace('\\"', '"')
    value = value.replace('\\n', '\n')
    value = value.replace('\\r', '\r')
    value = value.replace('\\\\', '\\')
    return value

def extract_insert_values(sql_line):
    """Extrait les valeurs d'une ligne INSERT INTO."""
    # Pattern pour capturer les valeurs entre parenthèses
    pattern = r'\(([^)]+(?:\([^)]*\)[^)]*)*)\)'
    matches = re.finditer(pattern, sql_line)
    
    rows = []
    for match in matches:
        values_str = match.group(1)
        # Split sur les virgules mais pas celles entre quotes
        values = []
        current = []
        in_quotes = False
        escape_next = False
        paren_depth = 0
        
        for char in values_str:
            if escape_next:
                current.append(char)
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                current.append(char)
                continue
            
            if char == '(' and not in_quotes:
                paren_depth += 1
                current.append(char)
                continue
                
            if char == ')' and not in_quotes:
                paren_depth -= 1
                current.append(char)
                continue
                
            if char == "'" and paren_depth == 0:
                in_quotes = not in_quotes
                current.append(char)
                continue
            
            if char == ',' and not in_quotes and paren_depth == 0:
                values.append(''.join(current).strip())
                current = []
                continue
            
            current.append(char)
        
        if current:
            values.append(''.join(current).strip())
        
        rows.append([parse_sql_value(v) for v in values])
    
    return rows

def extract_events_from_sql(sql_file_path):
    """Extrait les événements depuis le dump SQL."""
    print(f"📖 Lecture du fichier SQL: {sql_file_path}")
    
    events = []
    feedback_submissions = []
    
    try:
        with open(sql_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            current_insert = ""
            in_insert = False
            
            for line_num, line in enumerate(f, 1):
                if line_num % 10000 == 0:
                    print(f"   Ligne {line_num:,}...")
                
                # Détecter début INSERT INTO wp_posts
                if 'INSERT INTO' in line and 'posts' in line.lower():
                    in_insert = True
                    current_insert = line
                elif in_insert:
                    current_insert += line
                    
                    # Si la ligne se termine par ;, on a l'insert complet
                    if line.rstrip().endswith(';'):
                        # Parser l'insert
                        rows = extract_insert_values(current_insert)
                        
                        for row in rows:
                            if len(row) < 24:  # wp_posts a normalement ~23 colonnes
                                continue
                            
                            post_id = row[0]
                            post_date = row[2]
                            post_content = row[4]
                            post_title = row[5]
                            post_status = row[7]
                            post_type = row[21] if len(row) > 21 else None
                            
                            # Filtrer les événements
                            if post_type in ['tribe_events', 'ai1ec_event']:
                                events.append({
                                    'post_id': post_id,
                                    'post_date': post_date,
                                    'post_title': post_title,
                                    'post_content': post_content,
                                    'post_status': post_status,
                                    'post_type': post_type,
                                })
                            
                            # Formulaires de soumission d'événements (feedback)
                            elif post_type == 'feedback':
                                # Extraire les données JSON si présentes
                                json_data = None
                                if 'JSON_DATA' in post_content:
                                    try:
                                        json_match = re.search(r'JSON_DATA\s*\n({.*?})\n', post_content, re.DOTALL)
                                        if json_match:
                                            json_str = json_match.group(1)
                                            json_data = json.loads(json_str)
                                    except:
                                        pass
                                
                                feedback_submissions.append({
                                    'post_id': post_id,
                                    'post_date': post_date,
                                    'post_title': post_title,
                                    'post_content': post_content,
                                    'json_data': json_data,
                                })
                        
                        in_insert = False
                        current_insert = ""
    
    except Exception as e:
        print(f"❌ Erreur lecture: {e}")
        raise
    
    return events, feedback_submissions

def generate_import_script(events, feedback_submissions, output_path):
    """Génère le script import_to_wagtail.py avec les données."""
    
    print(f"\n📝 Génération du script d'import...")
    
    # Préparer les données d'événements
    events_data = []
    
    # Convertir les événements tribe/ai1ec
    for event in events:
        events_data.append({
            'event_id': event['post_id'],
            'event_name': event['post_title'],
            'post_content': event['post_content'],
            'event_start_date': event['post_date'][:10] if event['post_date'] else None,
            'event_status': '1' if event['post_status'] == 'publish' else '0',
            'location_id': 1,  # Lieu par défaut
        })
    
    # Convertir les soumissions feedback avec données structurées
    for fb in feedback_submissions:
        if fb['json_data']:
            json_data = fb['json_data']
            
            # Extraire les infos selon le format
            nom = json_data.get("1_Nom de l'événement", '') or json_data.get('event_name', '')
            lieu = json_data.get("2_Lieu de l'événement", '') or json_data.get('event_location', '')
            date_str = json_data.get("3_Date", '') or json_data.get('event_date', '')
            heure = json_data.get("4_Heure", '') or json_data.get('event_time', '')
            descriptif = json_data.get("8_Descriptif", '') or json_data.get('description', '')
            
            # Parser la date
            event_date = None
            if date_str:
                # Essayer plusieurs formats
                for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                    try:
                        event_date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                        break
                    except:
                        continue
            
            if not event_date:
                event_date = fb['post_date'][:10] if fb['post_date'] else None
            
            events_data.append({
                'event_id': f"feedback-{fb['post_id']}",
                'event_name': nom or fb['post_title'] or 'Sans titre',
                'post_content': descriptif or fb['post_content'],
                'event_start_date': event_date,
                'event_status': '1',
                'location_id': 1,
                'location_name': lieu,
            })
    
    # Créer les lieux uniques
    locations_data = []
    unique_locations = {}
    
    for event in events_data:
        loc_name = event.get('location_name', 'Lieu inconnu')
        if loc_name not in unique_locations:
            loc_id = len(unique_locations) + 1
            unique_locations[loc_name] = loc_id
            locations_data.append({
                'location_id': loc_id,
                'location_name': loc_name,
                'location_address': '',
                'location_town': 'Le Mans',
                'location_postcode': '72000',
            })
        
        event['location_id'] = unique_locations[loc_name]
    
    # Générer le script Python
    script_content = f'''"""
Script d'import des événements dans Wagtail.

Généré automatiquement le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

À exécuter dans l'environnement Django:
    python manage.py shell < import_to_wagtail.py
"""

import os
import sys
import django
from datetime import datetime, date, time
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lebidul.settings.dev')
django.setup()

from agenda.models import Evenement, Lieu, Categorie

print("🚀 Début de l'import des données WordPress...")

# ========== DONNÉES À IMPORTER ==========
LOCATIONS_DATA = {locations_data!r}

EVENTS_DATA = {events_data!r}

# ========== IMPORT DES LIEUX ==========
print("\\n📍 Import des lieux...")

lieu_mapping = {{}}  # WordPress ID -> Wagtail Lieu

for loc_data in LOCATIONS_DATA:
    wp_id = loc_data.get('location_id')
    
    # Vérifier si existe déjà
    lieu_slug = f"lieu-wp-{{wp_id}}"
    
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
        print(f"   ✅ Créé: {{lieu.nom}}")
    else:
        print(f"   ⏭️  Existe: {{lieu.nom}}")

print(f"\\n✅ {{len(lieu_mapping)}} lieux traités\\n")

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
    print(f"   ✅ Créé: {{categorie_defaut.nom}}")
else:
    print(f"   ⏭️  Existe: {{categorie_defaut.nom}}")

# ========== IMPORT DES ÉVÉNEMENTS ==========
print("\\n📅 Import des événements...")

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
            print(f"   ⚠️  Pas de lieu pour événement {{wp_event_id}}, création lieu par défaut")
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
            print(f"   ⚠️  Erreur parsing date pour événement {{wp_event_id}}: {{e}}")
            date_debut = None
        
        if not date_debut:
            print(f"   ⚠️  Pas de date pour événement {{wp_event_id}}, skip")
            skipped_count += 1
            continue
        
        # Créer ou mettre à jour l'événement
        slug = f"event-wp-{{wp_event_id}}"
        
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
            print(f"   ✅ Créé: {{event.titre}} ({{event.date_debut}})")
            imported_count += 1
        else:
            print(f"   🔄 MAJ: {{event.titre}} ({{event.date_debut}})")
            imported_count += 1
            
    except Exception as e:
        print(f"   ❌ Erreur événement {{event_data.get('event_id')}}: {{e}}")
        import traceback
        traceback.print_exc()
        error_count += 1
        continue

print(f"\\n" + "="*60)
print(f"📊 RÉSUMÉ IMPORT")
print(f"="*60)
print(f"✅ Importés/MAJ: {{imported_count}}")
print(f"⏭️  Ignorés: {{skipped_count}}")
print(f"❌ Erreurs: {{error_count}}")
print(f"="*60)

print("\\n🎉 Import terminé!")
'''
    
    # Écrire le fichier
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ Script généré: {output_path}")
    print(f"   📊 {len(locations_data)} lieux")
    print(f"   📊 {len(events_data)} événements")

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_wordpress_events.py chemin/vers/dump.sql")
        sys.exit(1)
    
    sql_file = sys.argv[1]
    
    if not Path(sql_file).exists():
        print(f"❌ Fichier introuvable: {sql_file}")
        sys.exit(1)
    
    print("="*60)
    print("🔄 EXTRACTION ÉVÉNEMENTS WORDPRESS")
    print("="*60)
    print(f"📁 Fichier: {sql_file}")
    print(f"   Taille: {Path(sql_file).stat().st_size / (1024*1024):.2f} MB")
    print()
    
    # Extraire les événements
    events, feedback = extract_events_from_sql(sql_file)
    
    print(f"\n📊 Résumé extraction:")
    print(f"   • {len(events)} événements (tribe_events + ai1ec_event)")
    print(f"   • {len(feedback)} soumissions (feedback)")
    print(f"   • {len(events) + len(feedback)} total")
    
    # Générer le script d'import
    output_path = "import_to_wagtail.py"
    generate_import_script(events, feedback, output_path)
    
    print("\n" + "="*60)
    print("✅ EXTRACTION TERMINÉE")
    print("="*60)
    print("\n📝 Prochaines étapes:")
    print("1. Copiez le fichier 'import_to_wagtail.py' dans votre projet Django")
    print("2. Activez votre environnement virtuel Django")
    print("3. Exécutez: python manage.py shell < import_to_wagtail.py")
    print()

if __name__ == "__main__":
    main()