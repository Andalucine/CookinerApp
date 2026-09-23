"""Shared test fixtures: in-memory SQLite database and API client."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (register tables)
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seeded(db_session):
    """Catalogues loaded (categories, tags, spices, sections...)."""
    from scripts.seed_catalogs import run

    run(db_session)
    return db_session


@pytest.fixture
def make_user(client):
    """Register a user and return the auth headers for them."""

    def _make(name="Ana", email=None, language="es"):
        r = client.post(
            "/auth/register",
            json={
                "email": email or f"{name.lower()}@example.com",
                "display_name": name,
                "password": "secreta123",
                "language": language,
            },
        )
        assert r.status_code == 201, r.text
        body = r.json()
        return {"Authorization": f"Bearer {body['access_token']}"}, body["user"]

    return _make


@pytest.fixture
def share(client, db_session):
    """Give `guest` access to `owner`'s notebook with a role (owner moved to individual plan)."""
    from sqlalchemy import select

    from app.models import User

    def _share(owner_headers, owner_email, guest_headers, role="editor"):
        owner = db_session.scalar(select(User).where(User.email == owner_email))
        owner.plan, owner.max_recipes, owner.max_shared_with = "individual", None, 2
        db_session.commit()
        r = client.post("/notebooks/mine/invitations", json={"role": role}, headers=owner_headers)
        assert r.status_code == 201, r.text
        r = client.post("/notebooks/join", json={"code": r.json()["code"]}, headers=guest_headers)
        assert r.status_code == 200, r.text
        return owner.notebook.id

    return _share
