import sqlite3

conn = sqlite3.connect('import_data/bidul_archives.db')
cursor = conn.cursor()

print("=== TABLE: bidul ===")
cursor.execute("PRAGMA table_info(bidul)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

print("\n=== TABLE: evenement ===")
cursor.execute("PRAGMA table_info(evenement)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

conn.close()
