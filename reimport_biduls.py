import sqlite3
from datetime import date
from apps.agenda.models.snippets import Bidul

conn = sqlite3.connect("import_data/bidul_archives.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT numero, mois, annee FROM bidul ORDER BY numero")

created = 0
errors = []
for row in cur.fetchall():
    try:
        bidul, was_created = Bidul.objects.get_or_create(
            numero=row["numero"],
            defaults={
                "mois": row["mois"],
                "annee": row["annee"],
                "date_publication": date(row["annee"], row["mois"], 1),
                "nb_evenements": 0,
                "data_indexer": {"source": "bidul_archives", "numero": row["numero"]},
            }
        )
        if was_created:
            created += 1
    except Exception as e:
        errors.append((row["numero"], str(e)))

print(f"Crees: {created}")
print(f"Erreurs: {len(errors)}")
for num, err in errors[:5]:
    print(f"  Bidul {num}: {err}")
print(f"Total Biduls en base: {Bidul.objects.count()}")
conn.close()
