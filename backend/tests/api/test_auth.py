import logging

USER = {"email": "Ana@Example.com", "display_name": "Ana", "password": "secreta123"}


def register(client, **overrides):
    return client.post("/auth/register", json={**USER, **overrides})


def test_register_returns_token_and_user(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["access_token"]
    assert body["user"]["email"] == "ana@example.com"  # normalised to lowercase
    assert body["user"]["display_name"] == "Ana"
    # free plan with its limits, and the personal notebook created on the spot
    assert body["user"]["plan"] == "free"
    assert body["user"]["max_recipes"] == 15
    assert body["user"]["max_shared_with"] == 0
    assert body["user"]["notebook_id"] > 0


def test_register_creates_one_notebook_named_after_the_user(client, db_session):
    from app.models import Notebook

    register(client)
    notebooks = db_session.query(Notebook).all()
    assert len(notebooks) == 1
    assert notebooks[0].name == "Cuaderno de Ana"


def test_register_duplicate_email_is_rejected_in_spanish_and_english(client):
    register(client)
    r = register(client)
    assert r.status_code == 409
    assert r.json()["detail"] == "Ya existe una cuenta con ese correo."
    r = client.post("/auth/register", json=USER, headers={"Accept-Language": "en-GB"})
    assert r.json()["detail"] == "An account with that email already exists."
    r = client.post("/auth/register", json=USER, headers={"Accept-Language": "nl"})
    assert r.json()["detail"] == "Er bestaat al een account met dat e-mailadres."
    r = client.post("/auth/register", json=USER, headers={"Accept-Language": "it"})
    assert r.json()["detail"] == "Ya existe una cuenta con ese correo."


def test_every_language_has_the_same_message_keys():
    from app.i18n import _CATALOGS, LANGUAGES

    assert tuple(_CATALOGS) == LANGUAGES
    keys = set(_CATALOGS["es"])
    for code, texts in _CATALOGS.items():
        assert set(texts) == keys, code
        assert all(v.strip() for v in texts.values()), code


def test_register_in_french_names_the_notebook_in_french(client, db_session):
    from app.models import Notebook

    r = register(client, language="fr")
    assert r.status_code == 201
    assert r.json()["user"]["language"] == "fr"
    assert db_session.query(Notebook).one().name == "Carnet de Ana"


def test_register_short_password_is_rejected(client):
    r = register(client, password="corta")
    assert r.status_code == 422


def test_login_and_me(client):
    register(client)
    r = client.post("/auth/login", json={"email": "ana@example.com", "password": "secreta123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "ana@example.com"


def test_login_wrong_password(client):
    register(client)
    r = client.post("/auth/login", json={"email": "ana@example.com", "password": "otra12345"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Correo o contraseña incorrectos."


def test_me_without_token(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_forgot_and_reset_password(client, caplog):
    register(client)
    with caplog.at_level(logging.INFO, logger="app.services.auth"):
        r = client.post("/auth/forgot-password", json={"email": "ana@example.com"})
    assert r.status_code == 200
    reset_logs = [r for r in caplog.records if r.name == "app.services.auth"]
    code = reset_logs[-1].getMessage().rsplit(": ", 1)[1]
    assert len(code) == 6

    r = client.post(
        "/auth/reset-password",
        json={"email": "ana@example.com", "code": code, "new_password": "nueva12345"},
    )
    assert r.status_code == 200
    # old password no longer works, new one does
    login = lambda pw: client.post(  # noqa: E731
        "/auth/login", json={"email": "ana@example.com", "password": pw}
    )
    assert login("secreta123").status_code == 401
    assert login("nueva12345").status_code == 200
    # the code cannot be reused
    r = client.post(
        "/auth/reset-password",
        json={"email": "ana@example.com", "code": code, "new_password": "otra123456"},
    )
    assert r.status_code == 400


def test_forgot_password_unknown_email_gives_same_answer(client):
    r = client.post("/auth/forgot-password", json={"email": "nadie@example.com"})
    assert r.status_code == 200
    assert "código" in r.json()["message"]


def test_change_my_language(client, make_user):
    headers, user = make_user()
    assert user["language"] == "es"
    r = client.patch("/auth/me", json={"language": "en"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["language"] == "en"
    assert client.get("/auth/me", headers=headers).json()["language"] == "en"


def test_change_my_language_accepts_the_five_languages_only(client, make_user):
    headers, _ = make_user()
    for code in ("fr", "nl", "de"):
        r = client.patch("/auth/me", json={"language": code}, headers=headers)
        assert r.status_code == 200 and r.json()["language"] == code
    assert client.patch("/auth/me", json={"language": "it"}, headers=headers).status_code == 422
    assert client.patch("/auth/me", json={"language": "en"}).status_code == 401
