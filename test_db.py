from database import init_db, mark_attendance, get_all_attendance

init_db()

result1 = mark_attendance("you")
print("First mark:", result1)  # should be True

result2 = mark_attendance("you")
print("Second mark (same day):", result2)  # should be False, already marked

print("\nAll attendance records:")
for row in get_all_attendance():
    print(row)