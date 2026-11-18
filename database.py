"""SQLite persistence for the AI attendance system."""
import os
import sqlite3
from datetime import datetime, date
from contextlib import contextmanager

DB_NAME = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "attendance.db"))


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
        # Keep historical duplicates intact; the index protects new writes.
        duplicates = conn.execute("""
            SELECT lower(name) AS n, attendance_date AS d
            FROM attendance WHERE attendance_date IS NOT NULL
            GROUP BY lower(name), attendance_date HAVING COUNT(*) > 1
        """).fetchall()
        for item in duplicates:
            rows = conn.execute("""
                SELECT id FROM attendance
                WHERE lower(name) = ? AND attendance_date = ?
                ORDER BY id
            """, (item["n"], item["d"])).fetchall()
            for row in rows[1:]:
                conn.execute("DELETE FROM attendance WHERE id = ?", (row["id"],))
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_attendance_person_day
            ON attendance(lower(name), attendance_date)
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance(timestamp DESC)")


def mark_attendance(name):
    """Atomically mark a person once per local calendar day."""
    now = datetime.now()
    with connection() as conn:
        cursor = conn.execute("""
            INSERT OR IGNORE INTO attendance(name, timestamp, attendance_date)
            VALUES (?, ?, ?)
        """, (name, now.strftime("%Y-%m-%d %H:%M:%S"), now.date().isoformat()))
        return cursor.rowcount == 1


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
    today = date.today().isoformat()
    with connection() as conn:
        total_people = conn.execute("SELECT COUNT(DISTINCT name) FROM attendance").fetchone()[0]
        today_count = conn.execute("SELECT COUNT(*) FROM attendance WHERE attendance_date = ?", (today,)).fetchone()[0]
        total_records = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    return {"today": today_count, "people_seen": total_people, "total": total_records}
