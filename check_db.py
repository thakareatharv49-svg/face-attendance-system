from database import get_all_attendance

records = get_all_attendance()
if not records:
    print("No records in database.")
else:
    for r in records:
        print(r)