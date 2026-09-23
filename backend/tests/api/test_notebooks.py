from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models import NotebookInvitation, User
from tests.api.test_recipes import marmitako


def test_my_notebook_and_rename(client, seeded, make_user):
    h, user = make_user("Ana")
    r = client.get("/notebooks/mine", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Cuaderno de Ana" and body["recipe_count"] == 0
    assert body["shared_with"] == 0 and body["max_shared_with"] == 0  # free plan
    r = client.patch("/notebooks/mine", json={"name": "Las recetas de casa"}, headers=h)
    assert r.json()["name"] == "Las recetas de casa"


def test_free_plan_cannot_invite(client, seeded, make_user):
    h, _ = make_user("Ana")
    r = client.post("/notebooks/mine/invitations", json={"role": "viewer"}, headers=h)
    assert r.status_code == 403
    assert "plan" in r.json()["detail"]


def _individual(db, email):
    user = db.scalar(select(User).where(User.email == email))
    user.plan, user.max_recipes, user.max_shared_with = "individual", None, 2
    db.commit()


def test_invite_join_roles_and_leave(client, seeded, make_user):
    ana_h, ana = make_user("Ana")
    luis_h, luis = make_user("Luis")
    _individual(seeded, "ana@example.com")
    rid = client.post("/recipes", json=marmitako(seeded), headers=ana_h).json()["id"]

    # Ana creates a viewer invitation
    r = client.post("/notebooks/mine/invitations", json={"role": "viewer"}, headers=ana_h)
    assert r.status_code == 201, r.text
    inv = r.json()
    code = inv["code"]
    assert len(code) == 8 and not set(code) & set("0O1I")
    assert [i["id"] for i in client.get("/notebooks/mine/invitations", headers=ana_h).json()] == [
        inv["id"]
    ]

    # Wrong code, own code
    assert (
        client.post("/notebooks/join", json={"code": "ZZZZZZZZ"}, headers=luis_h).status_code == 400
    )
    assert client.post("/notebooks/join", json={"code": code}, headers=ana_h).status_code == 400

    # Luis joins (lowercase code is accepted) and sees Ana's recipe
    r = client.post("/notebooks/join", json={"code": code.lower()}, headers=luis_h)
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "viewer" and r.json()["owner"]["display_name"] == "Ana"
    assert client.get(f"/recipes/{rid}", headers=luis_h).status_code == 200
    shared = client.get("/notebooks/shared-with-me", headers=luis_h).json()
    assert [(s["id"], s["role"]) for s in shared] == [(ana["notebook_id"], "viewer")]
    # the code is spent
    assert client.post("/notebooks/join", json={"code": code}, headers=luis_h).status_code == 400
    assert client.get("/notebooks/mine/invitations", headers=ana_h).json() == []

    # A second code with role editor upgrades Luis instead of failing
    code2 = client.post(
        "/notebooks/mine/invitations", json={"role": "editor"}, headers=ana_h
    ).json()["code"]
    r = client.post("/notebooks/join", json={"code": code2}, headers=luis_h)
    assert r.status_code == 200 and r.json()["role"] == "editor"
    accesses = client.get("/notebooks/mine/access", headers=ana_h).json()
    assert [(a["user"]["display_name"], a["role"]) for a in accesses] == [("Luis", "editor")]
    assert client.get("/notebooks/mine", headers=ana_h).json()["shared_with"] == 1

    # Owner changes the role back and Luis can no longer edit
    r = client.patch(f"/notebooks/mine/access/{luis['id']}", json={"role": "viewer"}, headers=ana_h)
    assert r.json()["role"] == "viewer"
    r = client.put(f"/recipes/{rid}", json=marmitako(seeded, title="X"), headers=luis_h)
    assert r.status_code == 404

    # Luis leaves by himself
    r = client.delete(f"/notebooks/{ana['notebook_id']}/access/me", headers=luis_h)
    assert r.status_code == 200
    assert client.get("/notebooks/shared-with-me", headers=luis_h).json() == []
    assert client.get(f"/recipes/{rid}", headers=luis_h).status_code == 404


def test_email_lock_expiry_limit_and_removal(client, seeded, make_user):
    ana_h, ana = make_user("Ana")
    luis_h, luis = make_user("Luis")
    pepa_h, pepa = make_user("Pepa")
    juan_h, _ = make_user("Juan")
    _individual(seeded, "ana@example.com")

    # Locked to Pepa's email: Luis cannot use it, Pepa can
    code = client.post(
        "/notebooks/mine/invitations", json={"role": "viewer", "email": "Pepa@Example.com"},
        headers=ana_h,
    ).json()["code"]  # fmt: skip
    assert client.post("/notebooks/join", json={"code": code}, headers=luis_h).status_code == 400
    assert client.post("/notebooks/join", json={"code": code}, headers=pepa_h).status_code == 200

    # Expired code
    code = client.post("/notebooks/mine/invitations", json={}, headers=ana_h).json()["code"]
    inv = seeded.scalar(select(NotebookInvitation).where(NotebookInvitation.code == code))
    inv.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    seeded.commit()
    assert client.post("/notebooks/join", json={"code": code}, headers=luis_h).status_code == 400
    assert client.get("/notebooks/mine/invitations", headers=ana_h).json() == []

    # Cancel a pending invitation
    inv_id = client.post("/notebooks/mine/invitations", json={}, headers=ana_h).json()["id"]
    assert client.delete(f"/notebooks/mine/invitations/{inv_id}", headers=ana_h).status_code == 200
    assert client.delete(f"/notebooks/mine/invitations/{inv_id}", headers=ana_h).status_code == 404

    # Limit of 2 for the individual plan: Luis fits, Juan does not (the seat is full)
    code = client.post("/notebooks/mine/invitations", json={}, headers=ana_h).json()["code"]
    assert client.post("/notebooks/join", json={"code": code}, headers=luis_h).status_code == 200
    r = client.post("/notebooks/mine/invitations", json={}, headers=ana_h)
    assert r.status_code == 403
    # ...unless the owner frees a seat
    assert client.delete(f"/notebooks/mine/access/{pepa['id']}", headers=ana_h).status_code == 200
    assert client.delete(f"/notebooks/mine/access/{pepa['id']}", headers=ana_h).status_code == 404
    code = client.post("/notebooks/mine/invitations", json={}, headers=ana_h).json()["code"]
    assert client.post("/notebooks/join", json={"code": code}, headers=juan_h).status_code == 200
