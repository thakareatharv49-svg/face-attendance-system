import sqlite3
from datetime import datetime

DB_NAME = "attendance.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def mark_attendance(name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if this person was already marked today
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT * FROM attendance WHERE name = ? AND timestamp LIKE ?
    """, (name, f"{today}%"))
    already_marked = cursor.fetchone()

    if already_marked:
        conn.close()
        return False  # already marked today, skip

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO attendance (name, timestamp) VALUES (?, ?)", (name, timestamp))
    conn.commit()
    conn.close()
    return True  # newly marked

def get_all_attendance():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows