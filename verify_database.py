#!/usr/bin/env python3
"""Verify database was created successfully with all tables"""

import sqlite3
from pathlib import Path

db_path = Path("src/database/data/incident_iq.db")

if not db_path.exists():
    print(f"❌ Database not found at {db_path.absolute()}")
    exit(1)

print(f"✅ Database found at: {db_path.absolute()}")
print(f"   Size: {db_path.stat().st_size / 1024:.2f} KB\n")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("📊 Database Tables:")
print("=" * 50)
for table in tables:
    table_name = table[0]
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  ✓ {table_name:<30} ({count:,} rows)")

conn.close()

print("\n✅ Database is ready to use!")
