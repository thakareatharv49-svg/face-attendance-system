import sqlite3
from datetime import datetime

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

today = datetime.now().strftime("%Y-%m-%d")
cursor.execute("DELETE FROM attendance WHERE name = ? AND timestamp LIKE ?", ("you", f"{today}%"))
conn.commit()
conn.close()

print("Cleared today's record for testing")
