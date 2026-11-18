"""SQLite persistence for the AI attendance system."""
import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from contextlib import contextmanager

DB_NAME = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "attendance.db"))
APP_TIMEZONE = ZoneInfo(os.environ.get("APP_TIMEZONE", "Asia/Kolkata"))


@contextmanager
def connection():
    conn = sqlite3.connect(DB_NAME, timeout=15)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 15000")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_NAME)), exist_ok=True)
    with connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(attendance)")}
        if "attendance_date" not in columns:
            conn.execute("ALTER TABLE attendance ADD COLUMN attendance_date TEXT")
        conn.execute("""
            UPDATE attendance
            SET attendance_date = substr(timestamp, 1, 10)
            WHERE attendance_date IS NULL OR attendance_date = ''
        """)
        # A separate guard table prevents new duplicates without deleting or rewriting
        # any historical attendance rows from an earlier version of the app.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attendance_daily_guard (
                name_key TEXT NOT NULL,
                attendance_date TEXT NOT NULL,
                PRIMARY KEY (name_key, attendance_date)
            )
        """)
        conn.execute("""
            INSERT OR IGNORE INTO attendance_daily_guard(name_key, attendance_date)
            SELECT lower(name), attendance_date FROM attendance
            WHERE attendance_date IS NOT NULL AND attendance_date != ''
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance(timestamp DESC)")


def mark_attendance(name):
    """Atomically mark a person once per local calendar day."""
    now = datetime.now(APP_TIMEZONE)
    name = name.strip()
    day = now.date().isoformat()
    with connection() as conn:
        guard = conn.execute("""
            INSERT OR IGNORE INTO attendance_daily_guard(name_key, attendance_date)
            VALUES (?, ?)
        """, (name.casefold(), day))
        if guard.rowcount != 1:
            return False
        conn.execute("""
            INSERT INTO attendance(name, timestamp, attendance_date)
            VALUES (?, ?, ?)
        """, (name, now.strftime("%Y-%m-%d %H:%M:%S"), day))
        return True


def get_all_attendance(limit=1000):
    with connection() as conn:
        rows = conn.execute("""
            SELECT id, name, timestamp FROM attendance
            ORDER BY timestamp DESC LIMIT ?
        """, (max(1, min(int(limit), 10000)),)).fetchall()
        return [tuple(row) for row in rows]


def get_attendance(date_from=None, date_to=None, name=None, limit=1000):
    clauses, params = [], []
    if date_from:
        clauses.append("attendance_date >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("attendance_date <= ?")
        params.append(date_to)
    if name:
        clauses.append("name LIKE ?")
        params.append(f"%{name}%")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(max(1, min(int(limit), 10000)))
    with connection() as conn:
        rows = conn.execute(f"""
            SELECT id, name, timestamp FROM attendance {where}
            ORDER BY timestamp DESC LIMIT ?
        """, params).fetchall()
        return [tuple(row) for row in rows]


def get_dashboard_stats():
    today = datetime.now(APP_TIMEZONE).date().isoformat()
    with connection() as conn:
        total_people = conn.execute("SELECT COUNT(DISTINCT name) FROM attendance").fetchone()[0]
        today_count = conn.execute("SELECT COUNT(*) FROM attendance WHERE attendance_date = ?", (today,)).fetchone()[0]
        total_records = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    return {"today": today_count, "people_seen": total_people, "total": total_records}
