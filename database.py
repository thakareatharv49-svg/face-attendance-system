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

# User accounts are separate from attendance rows so existing attendance history is preserved.
def ensure_user_table():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def create_user(username, name, password_hash):
    ensure_user_table()
    conn = sqlite3.connect(DB_NAME)
    try:
        cur = conn.execute(
            "INSERT INTO users (username, name, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username, name, password_hash, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user_by_username(username):
    ensure_user_table()
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id):
    ensure_user_table()
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_users():
    ensure_user_table()
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in conn.execute(
            "SELECT id, username, name, created_at FROM users ORDER BY name"
        ).fetchall()]
    finally:
        conn.close()


def delete_user(user_id):
    ensure_user_table()
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def get_attendance_for_name(name):
    conn = sqlite3.connect(DB_NAME)
    try:
        return conn.execute(
            "SELECT * FROM attendance WHERE name = ? ORDER BY timestamp DESC", (name,)
        ).fetchall()
    finally:
        conn.close()


def get_today_attendance_count():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    try:
        return conn.execute(
            "SELECT COUNT(DISTINCT name) FROM attendance WHERE timestamp LIKE ?", (today + "%",)
        ).fetchone()[0]
    finally:
        conn.close()
