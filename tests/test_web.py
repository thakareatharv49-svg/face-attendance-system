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


def test_admin_pages_render(monkeypatch):
    import app as app_module
    import database
    database.init_db()
    app_module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    app_module.login_manager.session_protection = None
    client = app_module.app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = "admin"
        session["_fresh"] = True
    assert client.get("/admin").status_code == 200
    assert client.get("/admin/register").status_code == 200
    assert client.get("/admin/people").status_code == 200
