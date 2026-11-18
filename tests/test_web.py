import importlib


def test_health_and_home(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "web.db"))
    import database
    monkeypatch.setattr(database, "DB_NAME", str(tmp_path / "web.db"))
    import app as app_module
    app_module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app_module.app.test_client()
    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 200


def test_frame_endpoint_rejects_invalid_payload():
    import app as app_module
    app_module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    response = app_module.app.test_client().post("/process_frame", json={})
    assert response.status_code == 400


def test_admin_requires_login():
    import app as app_module
    app_module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    response = app_module.app.test_client().get("/admin")
    assert response.status_code in (302, 401)
