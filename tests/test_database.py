import os
import tempfile
import unittest

import database


class UserAccountDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db = database.DB_NAME
        database.DB_NAME = os.path.join(self.temp_dir.name, "test-attendance.db")
        database.init_db()
        database.ensure_user_table()

    def tearDown(self):
        database.DB_NAME = self.original_db
        self.temp_dir.cleanup()

    def test_user_account_round_trip(self):
        user_id = database.create_user("demo.user", "Demo User", "hashed-password")
        user = database.get_user_by_username("demo.user")
        self.assertEqual(user["id"], user_id)
        self.assertEqual(user["name"], "Demo User")
        self.assertEqual(database.get_user_by_id(str(user_id))["username"], "demo.user")

    def test_user_records_are_scoped_by_name(self):
        database.mark_attendance("Demo User")
        database.mark_attendance("Other User")
        rows = database.get_attendance_for_name("Demo User")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "Demo User")

    def test_password_update_and_date_range_report(self):
        user_id = database.create_user("demo.user", "Demo User", "old-hash")
        self.assertTrue(database.update_user_password(user_id, "new-hash"))
        self.assertEqual(database.get_user_by_username("demo.user")["password_hash"], "new-hash")
        database.mark_attendance("Demo User")
        today = database.datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(len(database.get_attendance_between(today, today)), 1)

    def test_deleting_account_does_not_delete_attendance(self):
        user_id = database.create_user("demo.user", "Demo User", "hashed-password")
        database.mark_attendance("Demo User")
        database.delete_user(user_id)
        self.assertIsNone(database.get_user_by_username("demo.user"))
        self.assertEqual(len(database.get_attendance_for_name("Demo User")), 1)


if __name__ == "__main__":
    unittest.main()
