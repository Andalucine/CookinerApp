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


def test_the_app_browses_a_shared_notebook(client, seeded, make_user, share):
    """What the app does after 'Unirme' (session 8): portada, categories and search of the other
    notebook with ?notebook_id=; a viewer cannot add; an editor adds to that notebook."""
    ana_h, ana = make_user("Ana")
    luis_h, luis = make_user("Luis")  # free plan: he can still join
    nb = share(ana_h, "ana@example.com", luis_h, role="viewer")
    assert nb == ana["notebook_id"]
    client.post("/recipes", json=marmitako(seeded), headers=ana_h)

    # Portada and lists of Ana's notebook, seen by Luis
    r = client.get(f"/recipes?notebook_id={nb}", headers=luis_h)
    assert r.status_code == 200 and r.json()["total"] == 1
    assert r.json()["items"][0]["notebook_id"] == nb
    # his own notebook is still empty (the Recetas door of Inicio)
    assert client.get("/recipes", headers=luis_h).json()["total"] == 0
    counts = client.get(f"/recipes/category-counts?notebook_id={nb}", headers=luis_h).json()
    assert sum(c["count"] for c in counts) >= 1

    # A viewer cannot add a recipe there (the app does not even show him Nueva receta)
    body = {**marmitako(seeded, title="Lentejas"), "notebook_id": nb}
    assert client.post("/recipes", json=body, headers=luis_h).status_code == 403

    # As editor he can, and it stays in Ana's notebook marked as added by him
    client.patch(f"/notebooks/mine/access/{luis['id']}", json={"role": "editor"}, headers=ana_h)
    r = client.post("/recipes", json=body, headers=luis_h)
    assert r.status_code == 201, r.text
    assert r.json()["notebook_id"] == nb
    items = client.get("/recipes", headers=ana_h).json()["items"]
    assert {i["title"]: i["added_by"] for i in items}["Lentejas"] == "Luis"

    # Someone without access gets 404 (nobody learns whether the notebook exists)
    eva_h, _ = make_user("Eva")
    assert client.get(f"/recipes?notebook_id={nb}", headers=eva_h).status_code == 404
