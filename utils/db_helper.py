# utils/db_helper.py
import sqlite3
from datetime import datetime

DB_PATH = "data/simplification_logs.db"

def init_db():
    """Initialize database and create logs table if not exists."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS simplification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            level TEXT,
            text_length INTEGER,
            simplified_length INTEGER
        )
    """)
    conn.commit()
    conn.close()

def log_simplification(level: str, original_text: str, simplified_text: str):
    """Insert a simplification record into the database."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO simplification_logs (timestamp, level, text_length, simplified_length)
        VALUES (?, ?, ?, ?)
    """, (datetime.now().isoformat(), level, len(original_text), len(simplified_text)))
    conn.commit()
    conn.close()

def get_summary():
    """Return count and stats by level."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT level, COUNT(*), AVG(text_length - simplified_length)
        FROM simplification_logs
        GROUP BY level
    """)
    rows = cur.fetchall()
    conn.close()
    return rows
