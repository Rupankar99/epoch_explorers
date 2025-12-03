import os
import sqlite3
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Read DB_PATH from .env, fallback to default
db_path_env = os.getenv("DB_PATH")
if db_path_env:
    # Use the path from .env (can be absolute or relative)
    DB_PATH = Path(db_path_env)
    if not DB_PATH.is_absolute():
        # Make it relative to project root (4 levels up from this file)
        # connection.py -> db -> database -> src -> project_root
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        DB_PATH = project_root / db_path_env
else:
    # Fallback: use DB_NAME or default
    DB_NAME = os.getenv("DB_NAME", "incident_iq.db")
    DB_PATH = Path(__file__).resolve().parent.parent / "data" / DB_NAME

def get_connection():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


