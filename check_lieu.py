import sqlite3
conn = sqlite3.connect("import_data/bidul_archives.db")
cursor = conn.cursor()
print("=== lieu_ref ===")
cursor.execute("PRAGMA table_info(lieu_ref)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")
print("\n=== Exemple ===")
cursor.execute("SELECT * FROM lieu_ref LIMIT 2")
for row in cursor.fetchall():
    print(row)
conn.close()
