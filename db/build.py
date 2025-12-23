import os
import json
import gzip
import ijson
import sqlite3

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "instance")
DB_PATH = os.path.join(DB_DIR, "cities.db")

SCHEMA_PATH = os.path.join(BASE_DIR, "db", "schema.sql")
COUNTRIES_PATH = os.path.join(BASE_DIR, "db", "countries.json")
CITIES_PATH = os.path.join(BASE_DIR, "db", "city.list.json.gz")

# -----------------------------
# Ensure instance/ and DB exist
# -----------------------------
os.makedirs(DB_DIR, exist_ok=True)

# -----------------------------
# Connect DB
# -----------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# -----------------------------
# Apply schema
# -----------------------------
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    schema = f.read()

# Execute each statement separately
for stmt in schema.split(";"):
    stmt = stmt.strip()
    if stmt:
        cur.execute(stmt)

print("Schema applied")

# -----------------------------
# Insert countries
# -----------------------------
with open(COUNTRIES_PATH, "r", encoding="utf-8") as f:
    countries = json.load(f)

cur.execute("BEGIN")
for c in countries:
    cur.execute(
        "INSERT INTO countries (code, name) VALUES (?, ?)",
        (c["code"], c["name"])
    )
conn.commit()
print(f"Inserted {len(countries)} countries")

# -----------------------------
# Stream + insert cities
# -----------------------------
total = 0
cur.execute("BEGIN")

with gzip.open(CITIES_PATH, "rt", encoding="utf-8") as f:
    for city in ijson.items(f, "item"):
        cur.execute(
            """
            INSERT INTO cities (id, name, state, country, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                int(city["id"]),
                city["name"],
                city.get("state"),
                city["country"],
                float(city["coord"]["lat"]),  # float handled natively
                float(city["coord"]["lon"])   # float handled natively
            )
        )
        total += 1

conn.commit()
print(f"Inserted {total} cities")
print("Build complete: instance/cities.db")

conn.close()
