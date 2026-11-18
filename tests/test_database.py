import tempfile
from pathlib import Path

import database


def use_temp_db(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_NAME", str(tmp_path / "test.db"))
    database.init_db()


def test_attendance_only_once_per_day(monkeypatch, tmp_path):
    use_temp_db(monkeypatch, tmp_path)
    assert database.mark_attendance("Ada Lovelace") is True
    assert database.mark_attendance("Ada Lovelace") is False
    assert len(database.get_all_attendance()) == 1


def test_names_are_case_insensitive_for_daily_duplicates(monkeypatch, tmp_path):
    use_temp_db(monkeypatch, tmp_path)
    assert database.mark_attendance("Ada") is True
    assert database.mark_attendance("ada") is False


def test_filtered_attendance(monkeypatch, tmp_path):
    use_temp_db(monkeypatch, tmp_path)
    database.mark_attendance("Grace Hopper")
    rows = database.get_attendance(name="Grace")
    assert len(rows) == 1
    assert rows[0][1] == "Grace Hopper"
